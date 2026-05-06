from __future__ import annotations

import uuid
from datetime import UTC, datetime


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def new_uuid() -> str:
    return str(uuid.uuid4())
