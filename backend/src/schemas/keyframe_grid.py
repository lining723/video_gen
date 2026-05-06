from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .common import BaseRecord


@dataclass(slots=True)
class KeyframeFrame:
    """单个关键帧"""
    position: int
    time_ratio: float
    image_path: str = ""
    source_url: str = ""
    prompt_used: str = ""
    status: str = "pending"  # pending, generating, succeeded, failed
    error_message: str = ""
    retry_count: int = 0

    def validate(self) -> bool:
        """验证字段有效性"""
        if self.position < 0:
            raise ValueError("position must be non-negative")
        if not 0.0 <= self.time_ratio <= 1.0:
            raise ValueError("time_ratio must be between 0.0 and 1.0")
        if self.status not in ["pending", "generating", "succeeded", "failed"]:
            raise ValueError(f"invalid status: {self.status}")
        if self.retry_count < 0 or self.retry_count > 3:
            raise ValueError("retry_count must be between 0 and 3")
        return True

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "position": self.position,
            "time_ratio": self.time_ratio,
            "image_path": self.image_path,
            "source_url": self.source_url,
            "prompt_used": self.prompt_used,
            "status": self.status,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
        }


@dataclass(slots=True)
class KeyframeGrid(BaseRecord):
    """关键帧网格"""
    project_id: str = ""
    shot_id: str = ""
    subject_name: str = ""
    grid_type: str = "3x3"
    frame_count: int = 9
    frames: List[dict] = field(default_factory=list)
    generated_at: str = ""
    source_model: str = ""

    def validate(self) -> bool:
        """验证字段有效性"""
        valid_grid_types = {"2x2": 4, "3x3": 9, "4x4": 16}
        if self.grid_type not in valid_grid_types:
            raise ValueError(f"invalid grid_type: {self.grid_type}")
        if self.frame_count != valid_grid_types[self.grid_type]:
            raise ValueError(f"frame_count {self.frame_count} does not match grid_type {self.grid_type}")
        if len(self.frames) != self.frame_count:
            raise ValueError(f"frames length {len(self.frames)} does not match frame_count {self.frame_count}")
        return True

    def to_dict(self) -> dict:
        """转换为字典"""
        from dataclasses import asdict
        result = asdict(self)
        # frames 已经是 dict 列表，无需转换
        return result
