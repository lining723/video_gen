from __future__ import annotations

from .db import SQLiteDatabase


class RenderRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save(self, data: dict) -> dict:
        exists = self.db.fetchone('SELECT id FROM render_tasks WHERE id = ?', (data['id'],))
        params = (
            data['id'], data['project_id'], data['shot_id'], data['status'], data['cache_key'], 1 if data.get('cache_hit') else 0,
            1 if data.get('force_refresh') else 0, data.get('render_path', ''), data.get('provider_name', ''), data.get('provider_task_id', ''),
            data.get('progress_message', ''), data.get('last_polled_at', ''), data.get('retry_count', 0), data.get('error_message', ''), data.get('started_at', ''),
            data.get('finished_at', ''), data['created_at'], data['updated_at'],
        )
        if exists:
            self.db.execute(
                '''UPDATE render_tasks SET project_id=?, shot_id=?, status=?, cache_key=?, cache_hit=?, force_refresh=?, render_path=?, provider_name=?, provider_task_id=?, progress_message=?, last_polled_at=?, retry_count=?, error_message=?, started_at=?, finished_at=?, created_at=?, updated_at=? WHERE id=?''',
                params[1:] + (data['id'],),
            )
        else:
            self.db.execute(
                '''INSERT INTO render_tasks(id, project_id, shot_id, status, cache_key, cache_hit, force_refresh, render_path, provider_name, provider_task_id, progress_message, last_polled_at, retry_count, error_message, started_at, finished_at, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                params,
            )
        return data

    def _deserialize(self, row):
        item = dict(row)
        item['cache_hit'] = bool(item.get('cache_hit'))
        item['force_refresh'] = bool(item.get('force_refresh'))
        return item

    def list_by_project(self, project_id: str) -> list[dict]:
        rows = self.db.fetchall('SELECT * FROM render_tasks WHERE project_id = ? ORDER BY created_at ASC', (project_id,))
        return [self._deserialize(row) for row in rows]

    def get(self, task_id: str) -> dict | None:
        row = self.db.fetchone('SELECT * FROM render_tasks WHERE id = ?', (task_id,))
        return self._deserialize(row) if row else None

    def get_by_shot(self, project_id: str, shot_id: str) -> dict | None:
        row = self.db.fetchone('SELECT * FROM render_tasks WHERE project_id = ? AND shot_id = ? ORDER BY created_at DESC LIMIT 1', (project_id, shot_id))
        return self._deserialize(row) if row else None

    def list_active_provider_tasks(self) -> list[dict]:
        rows = self.db.fetchall(
            '''
            SELECT * FROM render_tasks
            WHERE status = ? AND provider_task_id != ''
            ORDER BY updated_at ASC
            ''',
            ('running',),
        )
        return [self._deserialize(row) for row in rows]
