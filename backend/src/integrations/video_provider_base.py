"""
视频生成提供商抽象层

定义统一的视频生成接口，支持多个提供商的实现。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(slots=True)
class VideoGenerationRequest:
    """标准化的视频生成请求"""
    prompt: str
    duration: int
    first_frame_url: Optional[str] = None
    resolution: str = "720P"
    ratio: str = "16:9"
    model: str = ""

    def validate(self) -> list[str]:
        """验证请求，返回错误消息列表"""
        errors = []
        if self.duration <= 0:
            errors.append("视频时长必须大于0")
        if self.duration > 10:
            errors.append("视频时长不能超过10秒")
        if not self.prompt:
            errors.append("提示词不能为空")
        return errors


@dataclass(slots=True)
class VideoGenerationResult:
    """标准化的视频生成结果"""
    task_id: Optional[str] = None
    provider_url: Optional[str] = None
    status: Literal['submitted', 'running', 'succeeded', 'failed'] = 'submitted'
    progress_message: str = ""
    raw: Optional[dict] = None
    model: str = ""
    diagnostic: Optional[dict] = None


@dataclass(slots=True)
class TaskPollResult:
    """标准化的任务轮询结果"""
    task_id: str
    status: Literal['running', 'succeeded', 'failed']
    provider_url: Optional[str] = None
    provider_status: str = ""
    progress_message: str = ""
    error_message: Optional[str] = None
    raw: Optional[dict] = None


@dataclass(slots=True)
class VideoModelInfo:
    """视频模型信息"""
    id: str                          # 唯一标识符: "dashscope-wan2.7-i2v"
    provider_id: str                 # 提供商ID: "dashscope"
    provider_name: str               # 提供商名称: "阿里云灵积"
    model_type: str                  # 模型类型: "wan2.7-i2v"
    name: str                        # 显示名称: "Wan 2.7 图生视频"
    capabilities: list[str] = None   # 能力列表: ["image_to_video"]
    requires_first_frame: bool = True
    max_duration: int = 10
    default_resolution: str = "720P"
    default_ratio: str = "16:9"

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "provider_name": self.provider_name,
            "model_type": self.model_type,
            "name": self.name,
            "capabilities": self.capabilities,
            "requires_first_frame": self.requires_first_frame,
            "max_duration": self.max_duration,
            "default_resolution": self.default_resolution,
            "default_ratio": self.default_ratio,
        }


class VideoProvider(ABC):
    """视频生成提供商抽象基类"""

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """提供商唯一标识符"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供商显示名称"""
        pass

    @property
    @abstractmethod
    def enabled(self) -> bool:
        """提供商是否启用"""
        pass

    @abstractmethod
    def get_available_models(self) -> list[VideoModelInfo]:
        """返回可用的模型列表"""
        pass

    @abstractmethod
    def submit_video_task(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """提交视频生成任务"""
        pass

    @abstractmethod
    def poll_task_status(self, task_id: str) -> TaskPollResult:
        """轮询任务状态"""
        pass

    def get_model_info(self, model_type: str) -> Optional[VideoModelInfo]:
        """获取指定模型的信息"""
        for model in self.get_available_models():
            if model.model_type == model_type or model.id == model_type:
                return model
        return None

    def validate_request(self, request: VideoGenerationRequest) -> list[str]:
        """验证请求，返回错误消息列表"""
        errors = request.validate()
        model_info = self.get_model_info(request.model)
        if model_info:
            if model_info.requires_first_frame and not request.first_frame_url:
                errors.append(f"模型 {model_info.name} 需要提供首帧图片")
            if request.duration > model_info.max_duration:
                errors.append(f"模型 {model_info.name} 最大支持 {model_info.max_duration} 秒")
        return errors
