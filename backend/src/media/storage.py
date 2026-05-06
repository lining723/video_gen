from __future__ import annotations

from pathlib import Path

from backend.src.settings.config import MEDIA_ROOT


class MediaStorage:
    def __init__(self) -> None:
        self.root = Path(MEDIA_ROOT)

    def project_dir(self, project_id: str) -> Path:
        path = self.root / project_id
        path.mkdir(parents=True, exist_ok=True)
        return path
