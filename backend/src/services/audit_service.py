from __future__ import annotations

from backend.src.settings.logging import log_event


class AuditService:
    def record(self, event: str, **payload: object) -> None:
        log_event(event, **payload)
