from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StoryboardReviewRequest:
    action: str
    comment: str = ""
