from __future__ import annotations

from urllib.parse import urljoin

from .http_utils import ProviderHttpError, http_json


class DashScopeClient:
    def __init__(self, base_url: str, api_key: str, image_model: str, video_model: str, timeout: int = 300, poll_interval: float = 3.0, poll_timeout: int = 360) -> None:
        self.base_url = base_url.rstrip('/') + '/'
        self.api_key = api_key
        self.image_model = image_model
        self.video_model = video_model
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.poll_timeout = poll_timeout

    def _headers(self, async_task: bool = False) -> dict:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }
        if async_task:
            headers['X-DashScope-Async'] = 'enable'
        return headers

    def _context(self, capability: str) -> dict:
        return {
            'provider': 'dashscope',
            'capability': capability,
            'base_url': self.base_url.rstrip('/'),
            'image_model': self.image_model,
            'video_model': self.video_model,
        }

    def _wrap_error(self, error: Exception, capability: str, model: str) -> RuntimeError:
        if isinstance(error, ProviderHttpError):
            detail = error.to_dict()
        else:
            detail = {'message': str(error)}
        raise RuntimeError(str({**self._context(capability), 'model': model, **detail})) from error

    def _extract_url(self, payload):
        url_keys = {'url', 'image', 'video', 'image_url', 'video_url'}
        if isinstance(payload, dict):
            for key, value in payload.items():
                if key in url_keys and isinstance(value, str) and value.startswith(('http://', 'https://')):
                    return value
            for value in payload.values():
                found = self._extract_url(value)
                if found:
                    return found
        elif isinstance(payload, list):
            for item in payload:
                found = self._extract_url(item)
                if found:
                    return found
        return None

    def _extract_task_id(self, payload):
        if isinstance(payload, dict):
            if 'task_id' in payload and isinstance(payload['task_id'], str):
                return payload['task_id']
            for value in payload.values():
                found = self._extract_task_id(value)
                if found:
                    return found
        elif isinstance(payload, list):
            for item in payload:
                found = self._extract_task_id(item)
                if found:
                    return found
        return None

    def generate_image(self, prompt: str, size: str = '1024*1024', model: str | None = None) -> dict:
        active_model = model or self.image_model
        payload = {
            'model': active_model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': [{'text': prompt}],
                    }
                ]
            },
            'parameters': {
                'size': size,
                'n': 1,
                'watermark': False,
            },
        }
        try:
            response = http_json(
                'POST',
                urljoin(self.base_url, 'api/v1/services/aigc/multimodal-generation/generation'),
                self._headers(),
                payload,
                timeout=self.timeout,
                provider='dashscope',
            )
            url = self._extract_url(response)
            if not url:
                raise ValueError(f'DashScope image generation did not return a usable URL: {response}')
            return {'provider_url': url, 'raw': response, 'model': active_model}
        except Exception as error:
            self._wrap_error(error, 'image_generation', active_model)

    def _task_status_message(self, task_id: str, output: dict, normalized_status: str) -> str:
        message = output.get('message')
        if isinstance(message, str) and message.strip():
            return message.strip()
        if normalized_status == 'succeeded':
            return '视频生成完成'
        if normalized_status == 'failed':
            return '视频生成失败'
        return f'DashScope 任务 {task_id} 正在生成中'

    def submit_video_task(
        self,
        prompt: str,
        first_frame_url: str | None = None,
        duration: int = 10,
        resolution: str = '720P',
        ratio: str = '16:9',
        model: str | None = None,
    ) -> dict:
        active_model = model or self.video_model
        if not first_frame_url:
            raise RuntimeError(str({
                **self._context('video_generation'),
                'model': active_model,
                'message': 'wan2.7-i2v requires input.media with a publicly accessible image URL',
            }))
        payload = {
            'model': active_model,
            'input': {
                'prompt': prompt,
                'media': [
                    {
                        'type': 'first_frame',
                        'url': first_frame_url,
                    }
                ],
            },
            'parameters': {
                'resolution': resolution,
                'duration': duration,
                'prompt_extend': True,
                'watermark': False,
            },
        }
        if ratio:
            payload['parameters']['ratio'] = ratio
        try:
            response = http_json(
                'POST',
                urljoin(self.base_url, 'api/v1/services/aigc/video-generation/video-synthesis'),
                self._headers(async_task=True),
                payload,
                timeout=self.timeout,
                provider='dashscope',
            )
            task_id = self._extract_task_id(response)
            if not task_id:
                raise ValueError(f'DashScope video generation did not return a task_id: {response}')
            return {
                'task_id': task_id,
                'raw': response,
                'model': active_model,
                'status': 'submitted',
                'progress_message': 'DashScope 任务已提交，等待模型开始生成',
            }
        except Exception as error:
            self._wrap_error(error, 'video_generation', active_model)

    def get_task_status(self, task_id: str) -> dict:
        try:
            response = http_json(
                'GET',
                urljoin(self.base_url, f'api/v1/tasks/{task_id}'),
                self._headers(),
                timeout=self.timeout,
                provider='dashscope',
            )
        except Exception as error:
            self._wrap_error(error, 'task_poll', self.video_model)

        output = response.get('output', {})
        provider_status = str(output.get('task_status') or response.get('task_status') or '').upper()
        normalized_status = 'running'
        if provider_status == 'SUCCEEDED':
            normalized_status = 'succeeded'
        elif provider_status in {'FAILED', 'CANCELED', 'CANCELLED'}:
            normalized_status = 'failed'

        result = {
            'task_id': task_id,
            'raw': response,
            'model': self.video_model,
            'status': normalized_status,
            'provider_status': provider_status or 'UNKNOWN',
            'progress_message': self._task_status_message(task_id, output, normalized_status),
            'provider_url': None,
        }

        if normalized_status == 'succeeded':
            url = self._extract_url(output)
            if not url:
                raise RuntimeError(str({**self._context('task_poll'), 'model': self.video_model, 'task_id': task_id, 'message': f'DashScope task succeeded but no URL found: {output}'}))
            result['provider_url'] = url
        elif normalized_status == 'failed':
            result['error_message'] = output.get('message', 'DashScope task failed')

        return result
