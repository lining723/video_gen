from __future__ import annotations

import ast
import json
from typing import TYPE_CHECKING

from backend.src.settings.config import settings
from backend.src.settings.logging import log_event

from .dashscope_client import DashScopeClient
from .deepseek_client import DeepSeekClient
from .ollama_client import OllamaClient

if TYPE_CHECKING:
    from .video_provider_registry import VideoProviderRegistry
    from .video_provider_base import VideoGenerationRequest


class AIGateway:
    def __init__(self, video_provider_registry: VideoProviderRegistry | None = None) -> None:
        self.ollama = OllamaClient(settings.ollama_base_url, settings.ollama_text_model, timeout=settings.ollama_timeout)
        self.deepseek = DeepSeekClient(
            settings.deepseek_base_url,
            settings.deepseek_api_key,
            settings.deepseek_text_model,
            timeout=settings.deepseek_timeout,
        )
        self.dashscope = DashScopeClient(
            settings.dashscope_base_url,
            settings.dashscope_api_key,
            settings.dashscope_image_model,
            settings.dashscope_video_model,
            timeout=settings.dashscope_timeout,
            poll_interval=settings.dashscope_poll_interval,
            poll_timeout=settings.dashscope_poll_timeout,
        )
        self.video_registry = video_provider_registry

    def _normalize_error(self, error: Exception, provider: str, capability: str, model: str) -> dict:
        detail = {
            'provider': provider,
            'capability': capability,
            'model': model,
            'message': str(error),
        }
        text = str(error)
        if text.startswith('{') and text.endswith('}'):
            try:
                parsed = ast.literal_eval(text)
                if isinstance(parsed, dict):
                    detail.update(parsed)
            except Exception:
                pass
        return detail

    def _text_model(self, model: str | None = None) -> str:
        return str(model or settings.default_text_model)

    def _text_provider(self) -> str:
        return str(settings.text_provider or '').strip().lower() or 'ollama'

    def _generate_text_json(self, prompt: str, schema_hint: str, model: str) -> dict:
        provider = self._text_provider()
        if provider == 'deepseek':
            return self.deepseek.generate_json(prompt, schema_hint, model=model)
        return self.ollama.generate_json(prompt, schema_hint, model=model)

    def _image_model(self, model: str | None = None) -> str:
        return str(model or settings.dashscope_image_model)

    def _video_model(self, model: str | None = None) -> str:
        return str(model or settings.dashscope_video_model)

    def _fallback_scene(self, prompt: str, scene_count: int) -> dict:
        return {
            'scene_summary': f'围绕“{prompt}”的 {scene_count} 段视频场景设计。',
            'scene_list': [
                {'title': f'场景 {index + 1}', 'description': f'围绕“{prompt[:40]}”展开的镜头场景 {index + 1}'}
                for index in range(scene_count)
            ],
        }

    def generate_scene_design(self, prompt: str, scene_count: int, model: str | None = None) -> dict:
        schema_hint = '{"scene_summary":"string","scene_list":[{"title":"string","description":"string"}]}'
        prompt_text = f'请为以下视频需求输出 {scene_count} 个场景设计，要求中文输出，scene_list 长度固定为 {scene_count}。需求：{prompt}'
        text_model = self._text_model(model)
        try:
            result = self._generate_text_json(prompt_text, schema_hint, model=text_model)
            if result.get('scene_list'):
                return result
        except Exception as error:
            detail = self._normalize_error(error, self._text_provider(), 'text_scene_generation', text_model)
            log_event('text.scene.failed', **detail)
            if not settings.allow_model_fallback:
                raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from error
        return self._fallback_scene(prompt, scene_count)

    def _fallback_storyboard(self, scenes: list[dict], duration_limit: int, storyboard_style: str = '') -> list[dict]:
        shots = []
        style_suffix = f'，整体风格统一为{storyboard_style}' if storyboard_style else ''
        for index, scene in enumerate(scenes, start=1):
            shots.append({
                'sequence': index,
                'duration': min(duration_limit, 6 + index),
                'shot_type': '中景',
                'camera_movement': '缓慢推进',
                'scene_time': '白天',
                'background': f'{scene["description"]}{style_suffix}',
                'sound_effects': '环境氛围声，轻音乐铺底',
                'action_direction': '主体自然出镜并完成核心动作',
                'description': f'{scene["description"]}{style_suffix}',
                'subtitle_text': f'字幕：{scene["title"]}',
                'dubbing_text': f'配音：{scene["description"]}',
                'voiceover_text': '',
                'voiceover_tone': '温暖自然的中文女声',
                'subject_refs': ['主角'],
            })
        return shots

    def generate_storyboard(
        self,
        prompt: str,
        scenes: list[dict],
        duration_limit: int,
        storyboard_style: str = '',
        model: str | None = None,
    ) -> list[dict]:
        schema_hint = '{"shots":[{"sequence":1,"duration":8,"shot_type":"string","camera_movement":"string","scene_time":"string","background":"string","sound_effects":"string","action_direction":"string","description":"string","subtitle_text":"string","dubbing_text":"string","voiceover_text":"string","voiceover_tone":"string","subject_refs":["string"]}]}'
        style_instruction = f'统一风格：{storyboard_style}\n' if storyboard_style else ''
        text_model = self._text_model(model)
        prompt_text = (
            f'请根据用户需求和场景列表生成分镜脚本。\n需求：{prompt}\n{style_instruction}场景：{json.dumps(scenes, ensure_ascii=False)}\n'
            f'要求：输出 JSON，shots 数量与场景数量一致；每个 duration 不超过 {duration_limit}；所有镜头必须保持统一视觉风格，不要每个镜头使用不同美术方向；每个镜头必须包含 shot_type、camera_movement、scene_time、background、sound_effects、action_direction、description、subtitle_text、dubbing_text、voiceover_tone、subject_refs；voiceover_text 为可选旁白字段；全部用中文。'
        )
        try:
            result = self._generate_text_json(prompt_text, schema_hint, model=text_model)
            shots = result.get('shots') or []
            if shots:
                return shots
        except Exception as error:
            detail = self._normalize_error(error, self._text_provider(), 'text_storyboard_generation', text_model)
            log_event('text.storyboard.failed', **detail)
            if not settings.allow_model_fallback:
                raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from error
        return self._fallback_storyboard(scenes, duration_limit, storyboard_style=storyboard_style)

    def generate_subject_image(self, subject_name: str, profile: str, style_prompt: str, model: str | None = None, feature_description: str = '') -> dict:
        prompt_parts = []
        if feature_description:
            prompt_parts.append(f'角色特征（必须保持一致）：{feature_description}')
        prompt_parts.append(f'生成角色统一形象：{subject_name}。角色设定：{profile}。风格要求：{style_prompt}')
        prompt = '。'.join(prompt_parts)
        image_model = self._image_model(model)
        try:
            return self.dashscope.generate_image(prompt, size=settings.dashscope_image_size, model=image_model)
        except Exception as error:
            detail = self._normalize_error(error, 'dashscope', 'image_generation', image_model)
            log_event('dashscope.image.failed', **detail)
            if not settings.allow_model_fallback:
                raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from error
            return {'provider_url': None, 'raw': None, 'model': 'fallback-image', 'fallback_used': True, 'diagnostic': detail}

    def extract_subject_features(self, subject_name: str, image_description: str = '') -> str:
        """使用文本模型为主体的视觉特征生成描述，用于后续变体生成时保持一致性。"""
        schema_hint = '{"gender":"string","age_range":"string","hair_color":"string","hair_style":"string","skin_tone":"string","body_type":"string","clothing_style":"string","distinctive_features":"string","summary":"string"}'
        prompt_text = f'''请分析以下角色并提取其核心视觉特征描述。这些特征将用于确保该角色在不同镜头中保持视觉一致性。

角色名称：{subject_name}
{f"角色描述：{image_description}" if image_description else ""}

请输出 JSON 格式的特征描述，包含以下字段：
- gender: 性别
- age_range: 年龄段（如：青年、中年）
- hair_color: 发色
- hair_style: 发型
- skin_tone: 肤色
- body_type: 体型
- clothing_style: 服装风格
- distinctive_features: 显著特征（如眼镜、胡须、伤疤等）
- summary: 一句话总结该角色的核心视觉特征

要求：全部用中文输出。'''
        text_model = self._text_model()
        try:
            result = self._generate_text_json(prompt_text, schema_hint, model=text_model)
            parts = []
            if result.get('summary'):
                parts.append(result['summary'])
            else:
                for key in ['gender', 'age_range', 'hair_color', 'hair_style', 'clothing_style', 'distinctive_features']:
                    value = result.get(key)
                    if value and value not in ['无', '未知', '']:
                        parts.append(str(value))
            return '，'.join(parts) if parts else f'{subject_name}的统一形象'
        except Exception as error:
            detail = self._normalize_error(error, self._text_provider(), 'feature_extraction', text_model)
            log_event('text.feature_extraction.failed', **detail)
            return f'{subject_name}的统一形象'

    def submit_video(self, prompt: str, duration: int, first_frame_url: str | None = None, model: str | None = None) -> dict:
        # 如果有 VideoProviderRegistry，使用新的 Provider 架构
        if self.video_registry:
            return self._submit_video_via_registry(prompt, duration, first_frame_url, model)

        # 回退到旧的 DashScope 客户端
        video_model = self._video_model(model)
        try:
            return self.dashscope.submit_video_task(
                prompt,
                first_frame_url=first_frame_url,
                duration=duration,
                resolution=settings.dashscope_video_resolution,
                ratio=settings.dashscope_video_ratio,
                model=video_model,
            )
        except Exception as error:
            detail = self._normalize_error(error, 'dashscope', 'video_generation', video_model)
            log_event('dashscope.video.failed', **detail)
            if not settings.allow_model_fallback:
                raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from error
            return {'provider_url': None, 'task_id': None, 'raw': None, 'model': 'fallback-video', 'fallback_used': True, 'diagnostic': detail}

    def _submit_video_via_registry(self, prompt: str, duration: int, first_frame_url: str | None, model: str | None) -> dict:
        """通过 VideoProviderRegistry 提交视频生成任务"""
        from .video_provider_base import VideoGenerationRequest

        # 确定使用的模型
        model_id = model or self.video_registry.default_model

        # 获取对应的 Provider
        provider = self.video_registry.get_provider_for_model(model_id)
        if not provider:
            detail = {'error': f'No provider found for model: {model_id}', 'model': model_id}
            log_event('video.provider_not_found', **detail)
            if not settings.allow_model_fallback:
                raise RuntimeError(json.dumps(detail, ensure_ascii=False))
            return {'provider_url': None, 'task_id': None, 'raw': None, 'model': model_id, 'fallback_used': True, 'diagnostic': detail}

        # 构建请求
        request = VideoGenerationRequest(
            prompt=prompt,
            duration=duration,
            first_frame_url=first_frame_url,
            resolution=settings.dashscope_video_resolution,
            ratio=settings.dashscope_video_ratio,
            model=model_id,
        )

        try:
            result = provider.submit_video_task(request)
            return {
                'task_id': result.task_id,
                'provider_url': result.provider_url,
                'status': result.status,
                'progress_message': result.progress_message,
                'raw': result.raw,
                'model': result.model,
                'diagnostic': result.diagnostic,
            }
        except Exception as error:
            detail = self._normalize_error(error, provider.provider_id, 'video_generation', model_id)
            log_event(f'{provider.provider_id}.video.failed', **detail)
            if not settings.allow_model_fallback:
                raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from error
            return {'provider_url': None, 'task_id': None, 'raw': None, 'model': model_id, 'fallback_used': True, 'diagnostic': detail}

    def poll_video_task(self, task_id: str, provider_id: str | None = None) -> dict:
        # 如果有 VideoProviderRegistry，使用新的 Provider 架构
        if self.video_registry and provider_id:
            return self._poll_video_via_registry(task_id, provider_id)

        # 回退到旧的 DashScope 客户端
        try:
            return self.dashscope.get_task_status(task_id)
        except Exception as error:
            detail = self._normalize_error(error, 'dashscope', 'task_poll', settings.dashscope_video_model)
            log_event('dashscope.video.poll_failed', **detail, task_id=task_id)
            raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from error

    def _poll_video_via_registry(self, task_id: str, provider_id: str) -> dict:
        """通过 VideoProviderRegistry 轮询视频任务状态"""
        provider = self.video_registry.get_provider(provider_id)
        if not provider:
            raise RuntimeError(f'Provider not found: {provider_id}')

        try:
            result = provider.poll_task_status(task_id)
            return {
                'task_id': result.task_id,
                'status': result.status,
                'provider_status': result.provider_status,
                'provider_url': result.provider_url,
                'progress_message': result.progress_message,
                'error_message': result.error_message,
                'raw': result.raw,
            }
        except Exception as error:
            detail = self._normalize_error(error, provider_id, 'task_poll', '')
            log_event(f'{provider_id}.video.poll_failed', **detail, task_id=task_id)
            raise RuntimeError(json.dumps(detail, ensure_ascii=False)) from error
