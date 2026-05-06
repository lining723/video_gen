from __future__ import annotations

from backend.src.repositories.sqlite_utils import dumps_json, loads_json

from .db import SQLiteDatabase


class StoryboardRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save(self, data: dict) -> dict:
        exists = self.db.fetchone('SELECT id FROM storyboard_shots WHERE id = ?', (data['id'],))
        params = (
            data['id'], data['project_id'], data['version'], data['sequence'], data['duration'], data.get('shot_type', ''),
            data.get('camera_movement', ''), data.get('scene_time', ''), data.get('background', ''), data.get('sound_effects', ''),
            data.get('action_direction', ''), data['description'], data['subtitle_text'], data.get('dubbing_text', ''), data['voiceover_text'], data.get('voiceover_tone', ''),
            dumps_json(data.get('subject_refs', [])),
            data['status'], data['created_at'], data['updated_at'],
        )
        if exists:
            self.db.execute(
                '''UPDATE storyboard_shots SET project_id=?, version=?, sequence=?, duration=?, shot_type=?, camera_movement=?, scene_time=?, background=?, sound_effects=?, action_direction=?, description=?, subtitle_text=?, dubbing_text=?, voiceover_text=?, voiceover_tone=?, subject_refs_json=?, status=?, created_at=?, updated_at=? WHERE id=?''',
                params[1:] + (data['id'],),
            )
        else:
            self.db.execute(
                '''INSERT INTO storyboard_shots(id, project_id, version, sequence, duration, shot_type, camera_movement, scene_time, background, sound_effects, action_direction, description, subtitle_text, dubbing_text, voiceover_text, voiceover_tone, subject_refs_json, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                params,
            )
        return data

    def _deserialize(self, row):
        item = dict(row)
        item['subject_refs'] = loads_json(item.pop('subject_refs_json'))
        return item

    def list_by_project(self, project_id: str, version: int | None = None) -> list[dict]:
        if version is None:
            rows = self.db.fetchall('SELECT * FROM storyboard_shots WHERE project_id = ? ORDER BY sequence ASC', (project_id,))
        else:
            rows = self.db.fetchall('SELECT * FROM storyboard_shots WHERE project_id = ? AND version = ? ORDER BY sequence ASC', (project_id, version))
        return [self._deserialize(row) for row in rows]

    def get(self, shot_id: str) -> dict | None:
        row = self.db.fetchone('SELECT * FROM storyboard_shots WHERE id = ?', (shot_id,))
        return self._deserialize(row) if row else None
