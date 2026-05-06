from __future__ import annotations
from backend.src.utils import utc_now_iso

from dataclasses import asdict, dataclass, field
from uuid import uuid4


@dataclass(slots=True)
class BaseRecord:
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: utc_now_iso())
    updated_at: str = field(default_factory=lambda: utc_now_iso())

    def to_dict(self) -> dict:
        return asdict(self)
