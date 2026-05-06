from __future__ import annotations


def validate_shot(shot: dict, duration_limit: int) -> None:
    if int(shot.get("duration", 0)) > duration_limit:
        raise ValueError(f"Shot duration exceeds limit {duration_limit}s")
    required_fields = {
        "shot_type": "Shot type is required",
        "camera_movement": "Camera movement is required",
        "scene_time": "Scene time is required",
        "background": "Background is required",
        "sound_effects": "Sound effects are required",
        "action_direction": "Action direction is required",
        "description": "Description is required",
        "voiceover_tone": "Voiceover tone is required",
    }
    for field, message in required_fields.items():
        if not str(shot.get(field, "")).strip():
            raise ValueError(message)
    if not shot.get("subtitle_text"):
        raise ValueError("Subtitle is required")
    if not str(shot.get("dubbing_text", "")).strip():
        raise ValueError("Dubbing is required")
