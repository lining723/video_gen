from __future__ import annotations

from backend.src.repositories.sqlite_utils import dumps_json, loads_json

from .db import SQLiteDatabase


class FinalVideoRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save(self, data: dict) -> dict:
        exists = self.db.fetchone('SELECT id FROM final_videos WHERE id = ?', (data['id'],))
        params = (
            data['id'],
            data['project_id'],
            data['version'],
            data['storage_path'],
            data['duration'],
            data['resolution'],
            dumps_json(data.get('features', [])),
            data.get('bgm_source', ''),
            data['created_at'],
            data['updated_at'],
        )
        if exists:
            self.db.execute(
                'UPDATE final_videos SET project_id=?, version=?, storage_path=?, duration=?, resolution=?, features_json=?, bgm_source=?, created_at=?, updated_at=? WHERE id=?',
                params[1:] + (data['id'],),
            )
        else:
            self.db.execute(
                'INSERT INTO final_videos(id, project_id, version, storage_path, duration, resolution, features_json, bgm_source, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                params,
            )
        return data

    def latest(self, project_id: str) -> dict | None:
        row = self.db.fetchone('SELECT * FROM final_videos WHERE project_id = ? ORDER BY version DESC LIMIT 1', (project_id,))
        return self._hydrate(row)

    def _hydrate(self, row) -> dict | None:
        if not row:
            return None
        item = dict(row)
        item['features'] = loads_json(item.pop('features_json', '[]'))
        return item
