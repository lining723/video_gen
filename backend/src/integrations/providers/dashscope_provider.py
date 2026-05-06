"""
DashScope 视频生成提供商

封装现有的 DashScopeClient，实现 VideoProvider 接口。
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..video_provider_base import (
    VideoProvider,
    VideoGenerationRequest,
    VideoGenerationResult,
    TaskPollResult,
    VideoModelInfo,
)

if TYPE_CHECKING:
    from ..dashscope_client import DashScopeClient


# DashScope 视频模型配置
DASHSCOPE_VIDEO_MODELS = {
    "wan2.7-i2v": {
        "name": "Wan 2.7 图生视频",
        "capabilities": ["video_generation", "image_to_video"],
        "requires_first_frame": True,
        "max_duration": 10,
    },
    "wan2.7-t2v": {
        "name": "Wan 2.7 文生视频",
        "capabilities": ["video_generation", "text_to_video"],
        "requires_first_frame": False,
        "max_duration": 10,
    },
    "wan2.1-i2v": {
        "name": "Wan 2.1 图生视频",
        "capabilities": ["video_generation", "image_to_video"],
        "requires_first_frame": True,
        "max_duration": 5,
    },
    "wan2.1-t2v": {
        "name": "Wan 2.1 文生视频",
        "capabilities": ["video_generation", "text_to_video"],
        "requires_first_frame": False,
        "max_duration": 5,
    },
}


class DashScopeVideoProvider(VideoProvider):
    """DashScope 视频生成提供商"""

    def __init__(
        self,
        client: DashScopeClient,
        models: list[str] | None = None,
        enabled: bool = True,
    ) -> None:
        self._client = client
        self._enabled = enabled
        self._models = models or [client.video_model]

    @property
    def provider_id(self) -> str:
        return "dashscope"

    @property
    def provider_name(self) -> str:
        return "阿里云灵积"

    @property
    def enabled(self) -> bool:
        return self._enabled and bool(self._client.api_key)

    def get_available_models(self) -> list[VideoModelInfo]:
        """返回可用的模型列表"""
        models = []
        for model_type in self._models:
            config = DASHSCOPE_VIDEO_MODELS.get(model_type, {})
            models.append(VideoModelInfo(
                id=f"dashscope-{model_type}",
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                model_type=model_type,
                name=config.get("name", model_type),
                capabilities=config.get("capabilities", ["video_generation"]),
                requires_first_frame=config.get("requires_first_frame", True),
                max_duration=config.get("max_duration", 10),
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

        # 提取模型类型（去掉前缀）
        model_type = request.model
        if model_type.startswith("dashscope-"):
            model_type = model_type[len("dashscope-"):]

        try:
            result = self._client.submit_video_task(
                prompt=request.prompt,
                first_frame_url=request.first_frame_url,
                duration=request.duration,
                resolution=request.resolution,
                ratio=request.ratio,
                model=model_type,
            )
            return VideoGenerationResult(
                task_id=result.get("task_id"),
                provider_url=result.get("provider_url"),
                status="submitted",
                progress_message=result.get("progress_message", "任务已提交"),
                raw=result.get("raw"),
                model=request.model,
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
            result = self._client.get_task_status(task_id)
            status = result.get("status", "running")
            return TaskPollResult(
                task_id=task_id,
                status=status,
                provider_url=result.get("provider_url"),
                provider_status=result.get("provider_status", ""),
                progress_message=result.get("progress_message", ""),
                error_message=result.get("error_message"),
                raw=result.get("raw"),
            )
        except Exception as error:
            return TaskPollResult(
                task_id=task_id,
                status="failed",
                progress_message=f"轮询任务失败: {error}",
                error_message=str(error),
            )
