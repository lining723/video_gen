"""
火山引擎视频生成提供商

实现火山方舟平台的视频生成API。
"""
from __future__ import annotations

import json
from typing import Optional
from urllib.parse import urljoin

from ..http_utils import http_json, ProviderHttpError
from ..video_provider_base import (
    VideoProvider,
    VideoGenerationRequest,
    VideoGenerationResult,
    TaskPollResult,
    VideoModelInfo,
)


# 火山引擎视频模型配置
VOLCENGINE_VIDEO_MODELS = {
    # Seedance 1.0 lite - 轻量版视频生成模型
    "seedance-1.0-lite": {
        "name": "Seedance 1.0 Lite",
        "capabilities": ["video_generation", "text_to_video"],
        "requires_first_frame": False,
        "max_duration": 10,
    },
    # 通用模型端点（用户自定义）
    "custom": {
        "name": "自定义模型",
        "capabilities": ["video_generation", "text_to_video"],
        "requires_first_frame": False,
        "max_duration": 10,
    },
}


class VolcengineVideoProvider(VideoProvider):
    """火山引擎视频生成提供商"""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        models: list[str],
        resolution: str = "720P",
        max_duration: int = 10,
        timeout: int = 300,
        poll_interval: float = 3.0,
        poll_timeout: int = 360,
        enabled: bool = True,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip('/') + '/'
        self._models = models
        self._resolution = resolution
        self._max_duration = max_duration
        self._timeout = timeout
        self._poll_interval = poll_interval
        self._poll_timeout = poll_timeout
        self._enabled = enabled and bool(api_key)

    @property
    def provider_id(self) -> str:
        return "volcengine"

    @property
    def provider_name(self) -> str:
        return "火山引擎"

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _headers(self) -> dict:
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self._api_key}',
        }

    def get_available_models(self) -> list[VideoModelInfo]:
        """返回可用的模型列表"""
        models = []
        for model_endpoint in self._models:
            # 从环境变量获取的模型端点ID
            config = VOLCENGINE_VIDEO_MODELS.get(model_endpoint, VOLCENGINE_VIDEO_MODELS["custom"])
            models.append(VideoModelInfo(
                id=f"volcengine-{model_endpoint}",
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                model_type=model_endpoint,
                name=config.get("name", model_endpoint),
                capabilities=config.get("capabilities", ["video_generation"]),
                requires_first_frame=config.get("requires_first_frame", False),
                max_duration=min(config.get("max_duration", 10), self._max_duration),
            ))
        return models

    def submit_video_task(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """提交视频生成任务"""
        # 验证请求
        errors = self.validate_request(request)
        if errors:
            return VideoGenerationResult(
                status='failed',
                progress_message="请求验证失败",
                model=request.model,
                diagnostic={"errors": errors},
            )

        # 提取模型端点（去掉前缀）
        model_endpoint = request.model
        if model_endpoint.startswith("volcengine-"):
            model_endpoint = model_endpoint[len("volcengine-"):]

        # 构建请求参数
        # 火山引擎使用 prompt 中的参数控制分辨率、时长等
        prompt_parts = [request.prompt]
        prompt_parts.append(f"--dur {min(request.duration, self._max_duration)}")

        resolution_map = {"720P": "720p", "480P": "480p"}
        res = resolution_map.get(request.resolution, "720p")
        prompt_parts.append(f"--resolution {res}")

        if request.first_frame_url:
            # 图生视频模式
            payload = {
                "model": model_endpoint,
                "content": [
                    {"type": "text", "text": " ".join(prompt_parts)},
                    {"type": "image_url", "image_url": {"url": request.first_frame_url}},
                ],
            }
        else:
            # 文生视频模式
            payload = {
                "model": model_endpoint,
                "content": [
                    {"type": "text", "text": " ".join(prompt_parts)},
                ],
            }

        try:
            response = http_json(
                'POST',
                urljoin(self._base_url, 'api/v3/contents/generations/tasks'),
                self._headers(),
                payload,
                timeout=self._timeout,
                provider='volcengine',
            )

            task_id = response.get('id') or response.get('task_id')
            if not task_id:
                return VideoGenerationResult(
                    status='failed',
                    progress_message="API未返回任务ID",
                    model=request.model,
                    diagnostic={"response": response},
                )

            return VideoGenerationResult(
                task_id=task_id,
                status='submitted',
                progress_message="视频生成任务已提交",
                raw=response,
                model=request.model,
            )

        except ProviderHttpError as error:
            return VideoGenerationResult(
                status='failed',
                progress_message=f"API请求失败: {error}",
                model=request.model,
                diagnostic={"error": str(error), "status_code": error.status_code if hasattr(error, 'status_code') else None},
            )
        except Exception as error:
            return VideoGenerationResult(
                status='failed',
                progress_message=f"提交任务失败: {error}",
                model=request.model,
                diagnostic={"error": str(error)},
            )

    def poll_task_status(self, task_id: str) -> TaskPollResult:
        """轮询任务状态"""
        try:
            response = http_json(
                'GET',
                urljoin(self._base_url, f'api/v3/contents/generations/tasks/{task_id}'),
                self._headers(),
                timeout=self._timeout,
                provider='volcengine',
            )

            status_str = str(response.get('status', '')).upper()
            # 火山引擎状态映射
            status_map = {
                'PENDING': 'running',
                'PROCESSING': 'running',
                'RUNNING': 'running',
                'SUCCESS': 'succeeded',
                'SUCCEEDED': 'succeeded',
                'COMPLETED': 'succeeded',
                'FAILED': 'failed',
                'ERROR': 'failed',
                'CANCELED': 'failed',
            }
            normalized_status = status_map.get(status_str, 'running')

            result = TaskPollResult(
                task_id=task_id,
                status=normalized_status,
                provider_status=status_str,
                progress_message=response.get('message', ''),
                raw=response,
            )

            if normalized_status == 'succeeded':
                # 提取视频URL
                output = response.get('output', {})
                if isinstance(output, dict):
                    # 尝试从 output 中获取视频URL
                    video_url = (
                        output.get('video_url') or
                        output.get('url') or
                        output.get('video', {}).get('url')
                    )
                else:
                    # output 可能是列表
                    video_url = None
                    if isinstance(output, list) and output:
                        first_item = output[0]
                        if isinstance(first_item, dict):
                            video_url = first_item.get('url') or first_item.get('video_url')

                if not video_url:
                    # 尝试从 response 顶层获取
                    video_url = response.get('video_url') or response.get('url')

                result.provider_url = video_url

                if not video_url:
                    result.progress_message = "任务完成但未获取到视频URL"

            elif normalized_status == 'failed':
                result.error_message = response.get('error', {}).get('message', '视频生成失败')

            return result

        except ProviderHttpError as error:
            return TaskPollResult(
                task_id=task_id,
                status='failed',
                progress_message=f"轮询任务失败: {error}",
                error_message=str(error),
            )
        except Exception as error:
            return TaskPollResult(
                task_id=task_id,
                status='failed',
                progress_message=f"轮询任务异常: {error}",
                error_message=str(error),
            )
