from __future__ import annotations

import hashlib
import json


def build_cache_key(shot: dict, subject_version: int, model_version: str = "demo-v1", render_config: dict | None = None) -> str:
    payload = {
        "description": shot.get("description"),
        "subtitle": shot.get("subtitle_text"),
        "dubbing": shot.get("dubbing_text"),
        "voiceover": shot.get("voiceover_text"),
        "duration": shot.get("duration"),
        "subject_version": subject_version,
        "model_version": model_version,
        "render_config": render_config or {},
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:24]
