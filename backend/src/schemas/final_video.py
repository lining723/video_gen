from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from .common import BaseRecord


@dataclass(slots=True)
class FinalVideo(BaseRecord):
    project_id: str = ""
    version: int = 1
    storage_path: str = ""
    duration: int = 0
    resolution: str = "1920x1080"
    features: list[str] = field(default_factory=list)
    bgm_source: str = ""
