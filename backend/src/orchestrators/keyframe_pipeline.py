from __future__ import annotations

import asyncio
import time
from typing import Optional

from backend.src.schemas.keyframe_grid import KeyframeGrid, KeyframeFrame
from backend.src.settings.logging import log_event
from backend.src.media.cache_key import build_cache_key
from backend.src.utils import utc_now_iso


# 重试配置
MAX_RETRY_COUNT = 3
RETRY_DELAYS = [1, 2, 4]  # 指数退避：1秒、2秒、4秒
THUMBNAIL_WIDTH = 300  # 缩略图宽度


def calculate_grid_size(duration: int) -> tuple[str, int]:
    """
    根据镜头时长计算网格大小和关键帧数量

    Args:
        duration: 镜头时长（秒）

    Returns:
        (grid_type, frame_count): 网格类型和帧数量

    Rules:
        - duration <= 0: 使用默认值6秒（3x3网格）
        - duration <= 3: 2x2（4帧）
        - duration <= 6: 3x3（9帧）
        - duration <= 10: 4x4（16帧）
        - duration > 10: 按10处理（4x4网格）
    """
    # 处理异常值
    if duration <= 0:
        duration = 6  # 默认值

    # 处理超大值
    if duration > 10:
        duration = 10  # 最大值

    # 根据时长计算网格
    if duration <= 3:
        return "2x2", 4
    elif duration <= 6:
        return "3x3", 9
    else:  # 7-10秒
        return "4x4", 16


def calculate_time_ratios(frame_count: int) -> list[float]:
    """
    根据帧数量计算时间进度分布

    Args:
        frame_count: 关键帧数量

    Returns:
        时间进度列表（0.0到1.0）

    Example:
        frame_count=9 → [0.0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875, 1.0]
        frame_count=4 → [0.0, 0.333, 0.667, 1.0]
        frame_count=1 → [0.0]
    """
    if frame_count <= 1:
        return [0.0]

    # 均匀分布
    return [i / (frame_count - 1) for i in range(frame_count)]


def build_keyframe_cache_key(shot: dict, subject_version: int, grid_type: str) -> str:
    """
    构建关键帧缓存Key

    Args:
        shot: 镜头数据
        subject_version: 主体版本号
        grid_type: 网格类型

    Returns:
        缓存Key字符串
    """
    return f"keyframe:{shot['id']}:{subject_version}:{grid_type}"


class KeyframePipeline:
    """关键帧生成流水线"""

    def __init__(self, storyboard_repo, subject_repo, keyframe_repo, object_store, audit_service, ai_gateway, cache_store=None) -> None:
        self.storyboard_repo = storyboard_repo
        self.subject_repo = subject_repo
        self.keyframe_repo = keyframe_repo
        self.object_store = object_store
        self.audit_service = audit_service
        self.ai_gateway = ai_gateway
        self.cache_store = cache_store

    def _build_frame_prompt(self, shot: dict, subject_name: str, feature_description: str, time_ratio: float, duration: int, style_prompt: str = '') -> str:
        """
        根据镜头设计和时间进度构建关键帧prompt

        Args:
            shot: 镜头数据
            subject_name: 主体名称
            feature_description: 主体特征描述
            time_ratio: 时间进度比例（0.0-1.0）
            duration: 镜头时长（秒）
            style_prompt: 项目风格提示

        Returns:
            构建好的prompt字符串
        """
        # 根据时间比例推断动作阶段
        if time_ratio < 0.33:
            action_phase = "动作起始阶段"
        elif time_ratio < 0.67:
            action_phase = "动作进行中"
        else:
            action_phase = "动作结束阶段"

        # 推断运镜状态
        camera_movement = shot.get('camera_movement', '')
        if '推进' in camera_movement:
            camera_hint = "镜头逐渐推进，画面逐渐放大"
        elif '拉远' in camera_movement:
            camera_hint = "镜头逐渐拉远，画面逐渐缩小"
        elif '平移' in camera_movement:
            camera_hint = "镜头平移中"
        else:
            camera_hint = "镜头固定"

        # 构建prompt
        prompt_parts = []

        # 角色信息
        if feature_description:
            prompt_parts.append(f"角色：{subject_name}，特征：{feature_description}")
        else:
            prompt_parts.append(f"角色：{subject_name}")

        # 镜头信息
        if shot.get('shot_type'):
            prompt_parts.append(f"镜头类型：{shot['shot_type']}")
        prompt_parts.append(f"运镜：{camera_hint}（{time_ratio*100:.0f}%进度）")
        if shot.get('background'):
            prompt_parts.append(f"背景：{shot['background']}")
        if shot.get('action_direction'):
            prompt_parts.append(f"动作指导：{shot['action_direction']}（当前阶段：{action_phase}）")
        if shot.get('description'):
            prompt_parts.append(f"场景描述：{shot['description']}")
        if shot.get('scene_time'):
            prompt_parts.append(f"时间：{shot['scene_time']}")

        # 风格
        if style_prompt:
            prompt_parts.append(f"风格要求：{style_prompt}")

        return '。'.join(prompt_parts)

    def _generate_thumbnail(self, image_path: str, project_id: str, shot_id: str, position: int) -> Optional[str]:
        """
        生成缩略图

        Args:
            image_path: 原图路径
            project_id: 项目ID
            shot_id: 镜头ID
            position: 帧位置

        Returns:
            缩略图路径，如果生成失败返回None
        """
        try:
            # 读取原图
            image_bytes = self.object_store.read_bytes(image_path)
            if not image_bytes:
                return None

            # 使用PIL生成缩略图（如果可用）
            try:
                from PIL import Image
                import io

                img = Image.open(io.BytesIO(image_bytes))

                # 计算缩略图尺寸
                width, height = img.size
                if width > THUMBNAIL_WIDTH:
                    new_height = int(height * THUMBNAIL_WIDTH / width)
                    img.thumbnail((THUMBNAIL_WIDTH, new_height), Image.Resampling.LANCZOS)

                # 保存缩略图
                output = io.BytesIO()
                img.save(output, format='PNG', optimize=True)
                thumbnail_bytes = output.getvalue()

                # 存储缩略图
                thumbnail_path = f'keyframes/{shot_id}/frame_{position}_thumb.png'
                self.object_store.save_bytes(project_id, thumbnail_path, thumbnail_bytes, content_type='image/png')

                return thumbnail_path

            except ImportError:
                # PIL不可用，跳过缩略图生成
                log_event('keyframe.thumbnail_skipped', project_id=project_id, shot_id=shot_id, position=position, reason='PIL not available')
                return None

        except Exception as error:
            log_event('keyframe.thumbnail_failed', project_id=project_id, shot_id=shot_id, position=position, error=str(error))
            return None

    def _generate_single_frame_with_retry(
        self,
        frame_data: dict,
        subject: dict,
        style_prompt: str,
        retry_count: int = 0
    ) -> dict:
        """
        生成单个关键帧，支持指数退避重试

        Args:
            frame_data: 帧数据
            subject: 主体数据
            style_prompt: 风格提示
            retry_count: 当前重试次数

        Returns:
            更新后的帧数据
        """
        try:
            # 调用图片生成API
            result = self.ai_gateway.generate_subject_image(
                subject_name=subject.get('name', '主角'),
                profile=frame_data['prompt_used'],
                style_prompt=style_prompt,
                feature_description=subject.get('feature_description', ''),
            )

            # 存储图片
            provider_url = result.get('provider_url')
            if provider_url:
                storage_path = self.object_store.save_from_url(
                    frame_data['project_id'],
                    f'keyframes/{frame_data["shot_id"]}/frame_{frame_data["position"]}.png',
                    provider_url,
                    content_type='image/png',
                )

                # 生成缩略图
                thumbnail_path = self._generate_thumbnail(
                    storage_path,
                    frame_data['project_id'],
                    frame_data['shot_id'],
                    frame_data['position']
                )
            else:
                storage_path = ''
                thumbnail_path = None

            return {
                **frame_data,
                'image_path': storage_path,
                'thumbnail_path': thumbnail_path,
                'source_url': provider_url or '',
                'status': 'succeeded',
                'error_message': '',
                'retry_count': retry_count,
            }

        except Exception as error:
            # 记录失败
            log_event(
                'keyframe.generation_failed',
                project_id=frame_data.get('project_id'),
                shot_id=frame_data.get('shot_id'),
                position=frame_data.get('position'),
                error=str(error),
                retry_count=retry_count,
            )

            # 检查是否可以重试
            if retry_count < MAX_RETRY_COUNT:
                # 指数退避延迟
                delay = RETRY_DELAYS[retry_count]
                log_event(
                    'keyframe.retry_scheduled',
                    project_id=frame_data.get('project_id'),
                    shot_id=frame_data.get('shot_id'),
                    position=frame_data.get('position'),
                    retry_count=retry_count + 1,
                    delay=delay,
                )
                time.sleep(delay)
                return self._generate_single_frame_with_retry(
                    frame_data,
                    subject,
                    style_prompt,
                    retry_count + 1
                )
            else:
                # 重试次数已达上限
                return {
                    **frame_data,
                    'image_path': '',
                    'thumbnail_path': None,
                    'source_url': '',
                    'status': 'failed',
                    'error_message': f"{error} (重试{retry_count}次后仍失败)",
                    'retry_count': retry_count,
                }

    def generate_keyframes_for_shot(self, shot: dict, subject: dict, project: dict, force: bool = False) -> dict:
        """
        为单个镜头生成关键帧网格

        Args:
            shot: 镜头数据
            subject: 主体数据
            project: 项目数据
            force: 是否强制重新生成

        Returns:
            KeyframeGrid 数据字典
        """
        duration = shot.get('duration', 6)  # 镜头时长（秒），最长10秒
        grid_type, frame_count = calculate_grid_size(duration)

        # 检查缓存
        if self.cache_store and not force:
            subject_version = subject.get('image_version', 1)
            cache_key = build_keyframe_cache_key(shot, subject_version, grid_type)
            cache_path = self.cache_store.path_for(cache_key)

            if cache_path.exists():
                # 缓存命中，直接返回
                log_event('keyframe.cache_hit', project_id=project['id'], shot_id=shot['id'], cache_key=cache_key)

                # 获取已存在的关键帧网格
                existing = self.keyframe_repo.get_by_shot(project['id'], shot['id'])
                if existing:
                    return existing

        # 计算时间进度分布
        time_ratios = calculate_time_ratios(frame_count)

        frames = []
        style_prompt = f"项目风格：{project.get('prompt', '')}" if project.get('prompt') else ""

        for i, time_ratio in enumerate(time_ratios):
            # 构建关键帧prompt
            frame_prompt = self._build_frame_prompt(
                shot,
                subject.get('name', '主角'),
                subject.get('feature_description', ''),
                time_ratio,
                duration,
                style_prompt,
            )

            # 准备帧数据
            frame_data = {
                'position': i,
                'time_ratio': time_ratio,
                'prompt_used': frame_prompt,
                'project_id': project['id'],
                'shot_id': shot['id'],
            }

            # 生成关键帧（带重试）
            result_frame = self._generate_single_frame_with_retry(
                frame_data,
                subject,
                style_prompt,
                retry_count=0
            )

            # 移除临时字段
            result_frame.pop('project_id', None)
            result_frame.pop('shot_id', None)

            frames.append(result_frame)

        # 创建 KeyframeGrid
        grid = KeyframeGrid(
            project_id=project['id'],
            shot_id=shot['id'],
            subject_name=subject.get('name', '主角'),
            grid_type=grid_type,
            frame_count=frame_count,
            frames=frames,
            generated_at=utc_now_iso(),
            source_model=result_frame.get('source_model', '') if result_frame.get('status') == 'succeeded' else '',
        )

        # 保存到数据库
        saved_grid = self.keyframe_repo.save(grid.to_dict())

        # 更新缓存
        if self.cache_store:
            subject_version = subject.get('image_version', 1)
            cache_key = build_keyframe_cache_key(shot, subject_version, grid_type)
            cache_path = self.cache_store.path_for(cache_key)
            cache_path.write_text(saved_grid['id'], encoding='utf-8')
            log_event('keyframe.cache_updated', project_id=project['id'], shot_id=shot['id'], cache_key=cache_key)

        # 记录审计日志
        self.audit_service.record(
            'keyframes.generated',
            project_id=project['id'],
            shot_id=shot['id'],
            grid_type=grid_type,
            frame_count=frame_count,
            succeeded_count=sum(1 for f in frames if f['status'] == 'succeeded'),
            failed_count=sum(1 for f in frames if f['status'] == 'failed'),
            cache_hit=False,
        )

        return saved_grid

    def retry_single_frame(
        self,
        project_id: str,
        shot_id: str,
        position: int
    ) -> dict:
        """
        重试生成指定的关键帧

        Args:
            project_id: 项目ID
            shot_id: 镜头ID
            position: 关键帧位置

        Returns:
            更新后的帧数据
        """
        # 获取关键帧网格
        grid = self.keyframe_repo.get_by_shot(project_id, shot_id)
        if not grid:
            raise ValueError(f"Keyframe grid not found for shot {shot_id}")

        # 获取指定帧
        frames = grid.get('frames', [])
        if position < 0 or position >= len(frames):
            raise ValueError(f"Invalid position: {position}")

        frame = frames[position]

        # 检查重试次数
        retry_count = frame.get('retry_count', 0)
        if retry_count >= MAX_RETRY_COUNT:
            raise ValueError(f"Retry limit exceeded ({MAX_RETRY_COUNT})")

        # 获取项目和主体信息
        project = {'id': project_id, 'prompt': ''}
        subject = {'name': grid.get('subject_name', '主角'), 'feature_description': ''}

        # 准备帧数据
        frame_data = {
            'position': position,
            'time_ratio': frame.get('time_ratio', 0),
            'prompt_used': frame.get('prompt_used', ''),
            'project_id': project_id,
            'shot_id': shot_id,
        }

        # 重新生成（重试次数+1）
        result_frame = self._generate_single_frame_with_retry(
            frame_data,
            subject,
            '',
            retry_count=retry_count
        )

        # 更新帧数据
        result_frame.pop('project_id', None)
        result_frame.pop('shot_id', None)
        frames[position] = result_frame

        # 保存更新
        grid['frames'] = frames
        grid['updated_at'] = utc_now_iso()
        self.keyframe_repo.save(grid)

        log_event(
            'keyframe.retry_completed',
            project_id=project_id,
            shot_id=shot_id,
            position=position,
            status=result_frame['status'],
            retry_count=retry_count + 1,
        )

        return result_frame

    def generate_composite_grid(self, shot: dict, subject: dict, project: dict) -> dict:
        """
        一次 API 调用生成包含所有关键帧的 4x4 网格图

        与逐帧生成不同，此方法构建一个描述完整网格布局的 prompt，
        让模型直接输出一张包含所有帧的 contact sheet。

        Returns:
            {'image_path': str, 'source_url': str, 'grid_type': str, 'frame_count': int}
        """
        duration = shot.get('duration', 6)
        grid_type, frame_count = calculate_grid_size(duration)
        time_ratios = calculate_time_ratios(frame_count)

        # 构建网格格布局描述
        grid_desc_parts = [
            f"生成一张{grid_type}网格布局的序列帧图（contact sheet），共{frame_count}帧。",
            f"每个格子里是同一个角色的不同动作瞬间，角色外观必须完全一致。",
            f"角色：{subject.get('name', '主角')}。",
        ]
        if subject.get('feature_description'):
            grid_desc_parts.append(f"角色特征：{subject['feature_description']}。")
        if shot.get('description'):
            grid_desc_parts.append(f"场景：{shot['description']}。")
        if shot.get('shot_type'):
            grid_desc_parts.append(f"镜头类型：{shot['shot_type']}。")

        # 逐帧描述
        grid_desc_parts.append("各帧内容：")
        for i, tr in enumerate(time_ratios):
            phase = "起始" if tr < 0.33 else ("进行" if tr < 0.67 else "结束")
            grid_desc_parts.append(f"第{i+1}帧（进度{tr*100:.0f}%，{phase}阶段）")

        # 风格
        if project.get('prompt'):
            grid_desc_parts.append(f"整体风格：{project['prompt']}。")
        grid_desc_parts.append("要求：网格线清晰，每格大小一致，角色外观统一。")

        composite_prompt = "。".join(grid_desc_parts)

        # 调用 AI 生成
        result = self.ai_gateway.generate_subject_image(
            subject_name=subject.get('name', '主角'),
            profile=f"4x4网格序列帧：{composite_prompt}",
            style_prompt=project.get('prompt', ''),
            feature_description=subject.get('feature_description', ''),
        )

        provider_url = result.get('provider_url')
        if not provider_url:
            raise RuntimeError("Composite grid generation returned no URL")

        shot_id = shot["id"]
        storage_path = self.object_store.save_from_url(
            project['id'],
            f'keyframes/{shot_id}/composite_grid.png',
            provider_url,
            content_type='image/png',
        )

        log_event(
            'keyframe.composite_generated',
            project_id=project['id'],
            shot_id=shot['id'],
            grid_type=grid_type,
            frame_count=frame_count,
            image_path=storage_path,
        )

        # 持久化 composite 信息到 keyframe_repo
        existing = self.keyframe_repo.get_by_shot(project['id'], shot['id'])
        if existing:
            existing['composite_image_path'] = storage_path
            existing['composite_grid_type'] = grid_type
            self.keyframe_repo.save(existing)

        return {
            'image_path': storage_path,
            'source_url': provider_url,
            'grid_type': grid_type,
            'frame_count': frame_count,
        }

    def run(self, project: dict, force: bool = False) -> list[dict]:
        """
        为项目的所有镜头生成关键帧

        Args:
            project: 项目数据
            force: 是否强制重新生成

        Returns:
            所有关键帧网格列表
        """
        shots = self.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version'))
        subjects = self.subject_repo.list_by_project(project['id'])

        # 创建主体名称到主体数据的映射
        subject_map = {s.get('name'): s for s in subjects}

        results = []
        for shot in shots:
            # 获取镜头的主体引用
            subject_refs = shot.get('subject_refs', ['主角'])
            subject_name = subject_refs[0] if subject_refs else '主角'
            subject = subject_map.get(subject_name)

            if not subject:
                # 使用第一个可用的主体
                subject = subjects[0] if subjects else {'name': '主角', 'feature_description': ''}

            # 生成关键帧
            try:
                grid = self.generate_keyframes_for_shot(shot, subject, project, force=force)
                results.append(grid)
            except Exception as error:
                log_event(
                    'keyframe.shot_failed',
                    project_id=project['id'],
                    shot_id=shot['id'],
                    error=str(error),
                )

        return results
