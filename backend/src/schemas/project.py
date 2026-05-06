from __future__ import annotations

from dataclasses import dataclass, field

from .common import BaseRecord


@dataclass(slots=True)
class Project(BaseRecord):
    name: str = "Untitled Project"
    prompt: str = ""
    storyboard_style: str = ""
    scene_count: int = 3
    text_model: str = ""
    image_model: str = ""
    video_model: str = ""
    creator_id: str = "demo-user"
    status: str = "idea_submitted"
    current_stage: str = "idea_submitted"
    scene_design_version: int = 0
    storyboard_version: int = 0
    final_video_version: int = 0
    final_bgm_path: str = ""
    compose_enable_subtitles: bool = True
    compose_enable_bgm: bool = True
    compose_enable_voiceover: bool = True
    compose_enable_transitions: bool = True
