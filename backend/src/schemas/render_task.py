from __future__ import annotations

from dataclasses import dataclass

from .common import BaseRecord


@dataclass(slots=True)
class RenderTask(BaseRecord):
    project_id: str = ""
    shot_id: str = ""
    status: str = "queued"
    cache_key: str = ""
    cache_hit: bool = False
    force_refresh: bool = False
    render_path: str = ""
    provider_name: str = ""
    provider_task_id: str = ""
    progress_message: str = ""
    last_polled_at: str = ""
    retry_count: int = 0
    error_message: str = ""
    started_at: str = ""
    finished_at: str = ""
