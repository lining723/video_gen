from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4


@dataclass(slots=True)
class TraceContext:
    trace_id: str
    started_at: str


def new_trace_context() -> TraceContext:
    return TraceContext(trace_id=str(uuid4()), started_at=datetime.utcnow().isoformat())
