from __future__ import annotations

from dataclasses import dataclass

from .common import BaseRecord


@dataclass(slots=True)
class SubjectAsset(BaseRecord):
    project_id: str = ""
    shot_id: str = ""
    name: str = ""
    profile: str = ""
    image_path: str = ""
    source_url: str = ""
    image_version: int = 1
    feature_description: str = ""
    base_subject_id: str = ""
    variant_type: str = "base"
    variant_hint: str = ""
    is_locked: int = 0
