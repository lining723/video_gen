from __future__ import annotations


class BaseOrchestrator:
    def __init__(self, audit_service) -> None:
        self.audit_service = audit_service
