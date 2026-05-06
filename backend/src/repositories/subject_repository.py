from __future__ import annotations

from .db import SQLiteDatabase
from backend.src.utils import utc_now_iso, new_uuid


class SubjectRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save(self, data: dict) -> dict:
        exists = self.db.fetchone('SELECT id FROM subjects WHERE id = ?', (data['id'],))
        params = (
            data['id'],
            data['project_id'],
            data.get('shot_id', ''),
            data['name'],
            data['profile'],
            data['image_path'],
            data.get('source_url', ''),
            data.get('image_version', 1),
            data.get('feature_description', ''),
            data.get('base_subject_id', ''),
            data.get('variant_type', 'base'),
            data.get('variant_hint', ''),
            data.get('is_locked', 0),
            data['created_at'],
            data['updated_at'],
        )
        if exists:
            self.db.execute(
                '''UPDATE subjects SET project_id=?, shot_id=?, name=?, profile=?, image_path=?, source_url=?,
                   image_version=?, feature_description=?, base_subject_id=?, variant_type=?, variant_hint=?,
                   is_locked=?, created_at=?, updated_at=? WHERE id=?''',
                params[1:] + (data['id'],),
            )
        else:
            self.db.execute(
                '''INSERT INTO subjects(id, project_id, shot_id, name, profile, image_path, source_url,
                   image_version, feature_description, base_subject_id, variant_type, variant_hint, is_locked,
                   created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                params,
            )
        return data

    def list_by_project(self, project_id: str) -> list[dict]:
        rows = self.db.fetchall('SELECT * FROM subjects WHERE project_id = ? ORDER BY created_at ASC', (project_id,))
        return [dict(row) for row in rows]

    def get_latest_by_shot(self, project_id: str, shot_id: str) -> dict | None:
        row = self.db.fetchone(
            'SELECT * FROM subjects WHERE project_id = ? AND shot_id = ? ORDER BY image_version DESC, created_at DESC LIMIT 1',
            (project_id, shot_id),
        )
        return dict(row) if row else None

    def next_image_version(self, project_id: str) -> int:
        row = self.db.fetchone('SELECT COALESCE(MAX(image_version), 0) AS max_version FROM subjects WHERE project_id = ?', (project_id,))
        return int(row['max_version']) + 1 if row else 1

    def get(self, subject_id: str) -> dict | None:
        row = self.db.fetchone('SELECT * FROM subjects WHERE id = ?', (subject_id,))
        return dict(row) if row else None

    def update_feature_description(self, subject_id: str, description: str) -> None:
        self.db.execute(
            'UPDATE subjects SET feature_description = ?, updated_at = ? WHERE id = ?',
            (description, utc_now_iso(), subject_id),
        )

    def lock_subject(self, subject_id: str) -> None:
        self.db.execute(
            'UPDATE subjects SET is_locked = 1, updated_at = ? WHERE id = ?',
            (utc_now_iso(), subject_id),
        )

    def unlock_subject(self, subject_id: str) -> None:
        self.db.execute(
            'UPDATE subjects SET is_locked = 0, updated_at = ? WHERE id = ?',
            (utc_now_iso(), subject_id),
        )

    def save_version(self, subject_id: str, version_data: dict) -> dict:
        version_id = new_uuid()
        now = utc_now_iso()
        self.db.execute(
            '''INSERT INTO subject_versions(id, subject_id, version, image_path, source_url, feature_description, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (version_id, subject_id, version_data['version'], version_data['image_path'],
             version_data.get('source_url', ''), version_data.get('feature_description', ''), now),
        )
        return {'id': version_id, 'subject_id': subject_id, 'version': version_data['version'], 'created_at': now}

    def list_versions(self, subject_id: str) -> list[dict]:
        rows = self.db.fetchall(
            'SELECT * FROM subject_versions WHERE subject_id = ? ORDER BY version DESC',
            (subject_id,),
        )
        return [dict(row) for row in rows]

    def get_version(self, subject_id: str, version: int) -> dict | None:
        row = self.db.fetchone(
            'SELECT * FROM subject_versions WHERE subject_id = ? AND version = ?',
            (subject_id, version),
        )
        return dict(row) if row else None

    def list_base_subjects(self, project_id: str) -> list[dict]:
        """List all base subjects (non-variants) for a project."""
        rows = self.db.fetchall(
            "SELECT * FROM subjects WHERE project_id = ? AND (variant_type = 'base' OR variant_type = '' OR variant_type IS NULL) ORDER BY created_at ASC",
            (project_id,),
        )
        return [dict(row) for row in rows]
