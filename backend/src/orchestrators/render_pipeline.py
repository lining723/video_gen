from __future__ import annotations

import base64
import json
import mimetypes
from urllib.parse import quote

from backend.src.media.cache_key import build_cache_key
from backend.src.schemas.render_task import RenderTask
from backend.src.settings.config import settings
from backend.src.settings.logging import log_event
from backend.src.utils import utc_now_iso
from backend.src.workers.tasks import submit_task


class RenderPipeline:
    def __init__(self, storyboard_repo, subject_repo, render_repo, cache_store, object_store, project_repo, audit_service, ai_gateway, keyframe_repo=None) -> None:
        self.storyboard_repo = storyboard_repo
        self.subject_repo = subject_repo
        self.render_repo = render_repo
        self.cache_store = cache_store
        self.object_store = object_store
        self.project_repo = project_repo
        self.audit_service = audit_service
        self.ai_gateway = ai_gateway
        self.keyframe_repo = keyframe_repo

    def _fallback_content(self, shot: dict) -> str:
        return f"DEMO VIDEO for {shot['description']}\n{shot['subtitle_text']}\n{shot.get('dubbing_text', '')}\n{shot.get('voiceover_text', '')}"

    def _fallback_name(self, shot: dict) -> str:
        return f"shot-{shot['sequence']}.txt"

    def _media_url(self, storage_path: str) -> str:
        host = settings.host if settings.host not in {'0.0.0.0', '::'} else '127.0.0.1'
        return f'http://{host}:{settings.port}/media/{quote(storage_path, safe="")}'

    def _image_content_type(self, storage_path: str) -> str | None:
        content_type, _ = mimetypes.guess_type(storage_path)
        if not content_type or not content_type.startswith('image/'):
            return None
        return content_type

    def _storage_path_to_data_url(self, storage_path: str) -> str | None:
        if not storage_path:
            return None
        content_type = self._image_content_type(storage_path)
        if not content_type:
            return None
        try:
            content = self.object_store.read_bytes(storage_path)
        except Exception:
            return None
        if not content:
            return None
        encoded = base64.b64encode(content).decode('ascii')
        return f'data:{content_type};base64,{encoded}'

    def _subject_source_url(self, subject: dict | None) -> str | None:
        if not subject:
            return None
        if subject.get('source_url'):
            return subject['source_url']
        image_path = str(subject.get('image_path') or '').strip()
        if not image_path:
            return None
        if not self._image_content_type(image_path):
            return None
        if subject.get('shot_id'):
            data_url = self._storage_path_to_data_url(image_path)
            if data_url:
                return data_url
        return self._media_url(image_path)

    def _pick_first_frame_url(self, shot: dict, subjects: list[dict]) -> str | None:
        # 优先使用 composite 关键帧网格图（包含完整时序信息）
        if self.keyframe_repo:
            try:
                grid = self.keyframe_repo.get_by_shot(shot.get('project_id', ''), shot['id'])
                if grid and grid.get('composite_image_path'):
                    composite_path = grid['composite_image_path']
                    if self._image_content_type(composite_path):
                        composite_url = self._media_url(composite_path)
                        log_event('render.using_composite_grid', shot_id=shot['id'], grid_type=grid.get('composite_grid_type', ''))
                        return composite_url
            except Exception:
                pass

        latest_global_by_name = {}
        latest_global = []

        for subject in subjects:
            if subject.get('shot_id') == shot['id']:
                url = self._subject_source_url(subject)
                if url:
                    return url
                continue
            if subject.get('shot_id'):
                continue
            latest_global.append(subject)
            latest_global_by_name[subject.get('name', '')] = subject

        for subject_name in shot.get('subject_refs') or []:
            url = self._subject_source_url(latest_global_by_name.get(subject_name))
            if url:
                return url

        for subject in reversed(latest_global):
            url = self._subject_source_url(subject)
            if url:
                return url
        return None

    def _save_task(self, task: dict) -> dict:
        task['updated_at'] = utc_now_iso()
        return self.render_repo.save(task)

    def _mark_running(self, task: dict, cache_key: str, force: bool) -> dict:
        task['status'] = 'running'
        task['cache_key'] = cache_key
        task['cache_hit'] = False
        task['force_refresh'] = force
        task['render_path'] = ''
        task['provider_name'] = ''
        task['provider_task_id'] = ''
        task['progress_message'] = '镜头任务已创建，准备提交模型生成'
        task['last_polled_at'] = ''
        task['started_at'] = utc_now_iso()
        task['finished_at'] = ''
        task['error_message'] = ''
        return self._save_task(task)

    def _mark_succeeded(
        self,
        task: dict,
        storage_path: str,
        progress_message: str,
        cache_hit: bool = False,
        clear_error_message: bool = True,
    ) -> dict:
        task['status'] = 'succeeded'
        task['cache_hit'] = cache_hit
        task['render_path'] = storage_path
        task['progress_message'] = progress_message
        task['provider_name'] = ''
        task['provider_task_id'] = ''
        task['last_polled_at'] = utc_now_iso()
        task['finished_at'] = utc_now_iso()
        if clear_error_message:
            task['error_message'] = ''
        return self._save_task(task)

    def _mark_failed(self, task: dict, error_message: str, progress_message: str) -> dict:
        task['status'] = 'failed'
        task['progress_message'] = progress_message
        task['last_polled_at'] = utc_now_iso()
        task['finished_at'] = utc_now_iso()
        task['error_message'] = error_message
        return self._save_task(task)

    def _start_project_rendering(self, project: dict) -> None:
        project['status'] = 'renders_running'
        project['current_stage'] = 'video_rendering'
        self.project_repo.update(project)

    def dispatch(self, project: dict, force: bool = False) -> list:
        shots = self.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version'))
        self._start_project_rendering(project)
        return [submit_task(self.render_shot, project, shot, force=force) for shot in shots]

    def render_shot(self, project: dict, shot: dict, force: bool = False) -> dict:
        subjects = self.subject_repo.list_by_project(project['id'])
        subject_version = max([item.get('image_version', 1) for item in subjects] or [1])
        first_frame_url = self._pick_first_frame_url(shot, subjects)
        storyboard_style = str(project.get('storyboard_style') or '').strip()
        cache_key = build_cache_key(shot, subject_version, render_config={'storyboard_style': storyboard_style})
        cache_path = self.cache_store.path_for(cache_key)
        existing = self.render_repo.get_by_shot(project['id'], shot['id'])
        task = existing or RenderTask(project_id=project['id'], shot_id=shot['id'], cache_key=cache_key).to_dict()

        self._start_project_rendering(project)
        self._mark_running(task, cache_key, force)

        if force and cache_path.exists():
            self.cache_store.delete(cache_key)
            log_event('render.cache.bypassed', project_id=project['id'], shot_id=shot['id'], cache_key=cache_key)

        if cache_path.exists():
            cache_value = cache_path.read_text(encoding='utf-8')
            if cache_value.startswith('storage:'):
                storage_path = cache_value.replace('storage:', '', 1)
            else:
                storage_path = self.object_store.save_text(project['id'], self._fallback_name(shot), cache_value)
                cache_path.write_text(f'storage:{storage_path}', encoding='utf-8')
            task['cache_hit'] = True
            task = self._mark_succeeded(task, storage_path, '镜头已完成，当前结果来自缓存', cache_hit=True)
            self.audit_service.record('render.succeeded', project_id=project['id'], shot_id=shot['id'], cache_hit=True, force=force)
            return task

        style_prompt = f"统一风格：{storyboard_style}；" if storyboard_style else ""
        video_model = str(project.get('video_model') or '').strip()
        prompt = (
            style_prompt +
            f"镜头类型：{shot.get('shot_type', '')}；"
            f"运镜方式：{shot.get('camera_movement', '')}；"
            f"时间：{shot.get('scene_time', '')}；"
            f"背景：{shot.get('background', '')}；"
            f"音效：{shot.get('sound_effects', '')}；"
            f"动作指导：{shot.get('action_direction', '')}；"
            f"镜头描述：{shot['description']}；"
            f"字幕：{shot['subtitle_text']}；"
            f"配音：{shot.get('dubbing_text', '')}；"
            f"旁白：{shot.get('voiceover_text', '')}；"
            f"配音音色：{shot.get('voiceover_tone', '')}"
        )
        generated = self.ai_gateway.submit_video(
            prompt,
            shot.get('duration', 6),
            first_frame_url=first_frame_url,
            model=video_model,
        )
        provider_task_id = generated.get('task_id') or ''
        diagnostic = generated.get('diagnostic')

        if provider_task_id:
            task['provider_name'] = 'dashscope'
            task['provider_task_id'] = provider_task_id
            task['progress_message'] = generated.get('progress_message') or '任务已提交，等待模型生成'
            if diagnostic:
                task['error_message'] = json.dumps(diagnostic, ensure_ascii=False)
            task = self._save_task(task)
            self.audit_service.record('render.submitted', project_id=project['id'], shot_id=shot['id'], task_id=provider_task_id, force=force)
            return task

        provider_url = generated.get('provider_url')
        if provider_url:
            storage_path = self.object_store.save_from_url(project['id'], f"shot-{shot['sequence']}.mp4", provider_url, content_type='video/mp4')
            cache_path.write_text(f'storage:{storage_path}', encoding='utf-8')
            task = self._mark_succeeded(task, storage_path, '镜头已生成完成')
            self.audit_service.record('render.succeeded', project_id=project['id'], shot_id=shot['id'], cache_hit=False, force=force)
            return task

        content = self._fallback_content(shot)
        storage_path = self.object_store.save_text(project['id'], self._fallback_name(shot), content)
        cache_path.write_text(f'storage:{storage_path}', encoding='utf-8')
        if diagnostic:
            task['error_message'] = json.dumps(diagnostic, ensure_ascii=False)
            log_event('render.fallback_used', project_id=project['id'], shot_id=shot['id'], sequence=shot.get('sequence'), **diagnostic)
        task = self._mark_succeeded(task, storage_path, '模型已回退，当前为文本占位产物', clear_error_message=False)
        self.audit_service.record('render.succeeded', project_id=project['id'], shot_id=shot['id'], cache_hit=False, force=force)
        return task

    def poll_render_task(self, task_id: str) -> dict | None:
        task = self.render_repo.get(task_id)
        if not task:
            return None
        if task.get('status') != 'running' or not task.get('provider_task_id'):
            return task

        shot = self.storyboard_repo.get(task['shot_id'])
        if not shot:
            return self._mark_failed(task, '关联镜头不存在，无法完成轮询', '镜头数据缺失，任务已终止')

        polled_at = utc_now_iso()
        task['last_polled_at'] = polled_at
        try:
            result = self.ai_gateway.poll_video_task(task['provider_task_id'])
        except Exception as error:
            task['progress_message'] = '查询任务进度失败，稍后将继续重试'
            task['error_message'] = str(error)
            return self._save_task(task)
        task['progress_message'] = result.get('progress_message') or task.get('progress_message') or '镜头正在生成中'

        if result.get('status') == 'running':
            return self._save_task(task)

        if result.get('status') == 'succeeded':
            provider_url = result.get('provider_url')
            if not provider_url:
                return self._mark_failed(task, '模型任务完成但未返回视频地址', '模型返回异常，任务已失败')
            storage_path = self.object_store.save_from_url(task['project_id'], f"shot-{shot['sequence']}.mp4", provider_url, content_type='video/mp4')
            self.cache_store.path_for(task['cache_key']).write_text(f'storage:{storage_path}', encoding='utf-8')
            task = self._mark_succeeded(task, storage_path, result.get('progress_message') or '镜头已生成完成')
            self.audit_service.record('render.succeeded', project_id=task['project_id'], shot_id=task['shot_id'], cache_hit=False, force=task.get('force_refresh', False))
            return task

        error_message = result.get('error_message') or result.get('progress_message') or '镜头生成失败'
        task = self._mark_failed(task, error_message, result.get('progress_message') or '镜头生成失败，可重试')
        self.audit_service.record('render.failed', project_id=task['project_id'], shot_id=task['shot_id'], task_id=task.get('provider_task_id', ''))
        return task

    def run(self, project: dict, force: bool = False) -> list[dict]:
        shots = self.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version'))
        self._start_project_rendering(project)
        return [self.render_shot(project, shot, force=force) for shot in shots]
