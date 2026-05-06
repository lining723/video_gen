from __future__ import annotations

from pathlib import Path

from backend.src.settings.config import CACHE_ROOT


class CacheStore:
    def __init__(self) -> None:
        self.root = Path(CACHE_ROOT)

    def path_for(self, cache_key: str) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root / f"{cache_key}.mp4"

    def delete(self, cache_key: str) -> None:
        path = self.path_for(cache_key)
        if path.exists():
            path.unlink()
