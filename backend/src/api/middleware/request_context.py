from __future__ import annotations

from backend.src.settings.observability import new_trace_context


def build_request_context() -> dict:
    trace = new_trace_context()
    return {"trace_id": trace.trace_id, "started_at": trace.started_at}
