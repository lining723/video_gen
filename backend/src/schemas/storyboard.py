from __future__ import annotations

from dataclasses import dataclass, field

from .common import BaseRecord


@dataclass(slots=True)
class StoryboardShot(BaseRecord):
    project_id: str = ""
    version: int = 1
    sequence: int = 1
    duration: int = 6
    shot_type: str = ""
    camera_movement: str = ""
    scene_time: str = ""
    background: str = ""
    sound_effects: str = ""
    action_direction: str = ""
    description: str = ""
    subtitle_text: str = ""
    dubbing_text: str = ""
    voiceover_text: str = ""
    voiceover_tone: str = ""
    subject_refs: list = field(default_factory=list)
    status: str = "storyboard_generated"
