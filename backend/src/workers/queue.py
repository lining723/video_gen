from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from backend.src.settings.config import settings


executor = ThreadPoolExecutor(max_workers=settings.render_workers)
