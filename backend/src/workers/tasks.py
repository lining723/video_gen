from __future__ import annotations

from backend.src.workers.queue import executor


def submit_task(func, *args, **kwargs):
    return executor.submit(func, *args, **kwargs)
