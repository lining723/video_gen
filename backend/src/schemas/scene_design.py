from __future__ import annotations

from dataclasses import dataclass, field

from .common import BaseRecord


@dataclass(slots=True)
class SceneDesign(BaseRecord):
    project_id: str = ""
    version: int = 1
    input_prompt: str = ""
    scene_summary: str = ""
    scene_list: list = field(default_factory=list)
    review_status: str = "scene_reviewing"
    review_comment: str = ""
