from __future__ import annotations

from backend.src.repositories.sqlite_utils import dumps_json, loads_json, row_to_dict

from .db import SQLiteDatabase


class SceneRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save(self, data: dict) -> dict:
        exists = self.db.fetchone('SELECT id FROM scenes WHERE id = ?', (data['id'],))
        params = (
            data['id'], data['project_id'], data['version'], data['input_prompt'], data['scene_summary'],
            dumps_json(data.get('scene_list', [])), data['review_status'], data.get('review_comment', ''),
            data['created_at'], data['updated_at'],
        )
        if exists:
            self.db.execute(
                '''UPDATE scenes SET project_id=?, version=?, input_prompt=?, scene_summary=?, scene_list_json=?, review_status=?, review_comment=?, created_at=?, updated_at=? WHERE id=?''',
                params[1:] + (data['id'],),
            )
        else:
            self.db.execute(
                '''INSERT INTO scenes(id, project_id, version, input_prompt, scene_summary, scene_list_json, review_status, review_comment, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                params,
            )
        return data

    def _deserialize(self, row):
        item = dict(row)
        item['scene_list'] = loads_json(item.pop('scene_list_json'))
        return item

    def list_by_project(self, project_id: str) -> list[dict]:
        rows = self.db.fetchall('SELECT * FROM scenes WHERE project_id = ? ORDER BY version ASC', (project_id,))
        return [self._deserialize(row) for row in rows]

    def latest(self, project_id: str) -> dict | None:
        row = self.db.fetchone('SELECT * FROM scenes WHERE project_id = ? ORDER BY version DESC LIMIT 1', (project_id,))
        return self._deserialize(row) if row else None
