from __future__ import annotations


def error_response(message: str, status: int = 400) -> tuple[int, dict]:
    return status, {"ok": False, "error": message}
