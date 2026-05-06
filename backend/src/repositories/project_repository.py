from __future__ import annotations

from backend.src.repositories.sqlite_utils import row_to_dict
from backend.src.utils import utc_now_iso

from .db import SQLiteDatabase


class ProjectRepository:
    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def create(self, data: dict) -> dict:
        self.db.execute(
            '''
            INSERT INTO projects(
                id, name, prompt, storyboard_style, scene_count, text_model, image_model, video_model, creator_id, status, current_stage,
                scene_design_version, storyboard_version, final_video_version,
                final_bgm_path, compose_enable_subtitles, compose_enable_bgm,
                compose_enable_voiceover, compose_enable_transitions,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                data['id'], data['name'], data['prompt'], data.get('storyboard_style', ''),
                int(data.get('scene_count', 3) or 3),
                data.get('text_model', ''),
                data.get('image_model', ''),
                data.get('video_model', ''),
                data['creator_id'], data['status'], data['current_stage'],
                data.get('scene_design_version', 0), data.get('storyboard_version', 0), data.get('final_video_version', 0),
                data.get('final_bgm_path', ''),
                1 if data.get('compose_enable_subtitles', True) else 0,
                1 if data.get('compose_enable_bgm', True) else 0,
                1 if data.get('compose_enable_voiceover', True) else 0,
                1 if data.get('compose_enable_transitions', True) else 0,
                data['created_at'], data['updated_at'],
            ),
        )
        return data

    def update(self, data: dict) -> dict:
        data['updated_at'] = utc_now_iso()
        self.db.execute(
            '''
            UPDATE projects SET name = ?, prompt = ?, storyboard_style = ?, scene_count = ?, text_model = ?, image_model = ?, video_model = ?, creator_id = ?, status = ?, current_stage = ?,
            scene_design_version = ?, storyboard_version = ?, final_video_version = ?,
            final_bgm_path = ?, compose_enable_subtitles = ?, compose_enable_bgm = ?,
            compose_enable_voiceover = ?, compose_enable_transitions = ?, updated_at = ?
            WHERE id = ?
            ''',
            (
                data['name'], data['prompt'], data.get('storyboard_style', ''),
                int(data.get('scene_count', 3) or 3),
                data.get('text_model', ''),
                data.get('image_model', ''),
                data.get('video_model', ''),
                data['creator_id'], data['status'], data['current_stage'],
                data.get('scene_design_version', 0), data.get('storyboard_version', 0), data.get('final_video_version', 0),
                data.get('final_bgm_path', ''),
                1 if data.get('compose_enable_subtitles', True) else 0,
                1 if data.get('compose_enable_bgm', True) else 0,
                1 if data.get('compose_enable_voiceover', True) else 0,
                1 if data.get('compose_enable_transitions', True) else 0,
                data['updated_at'], data['id'],
            ),
        )
        return data

    def get(self, project_id: str) -> dict | None:
        return row_to_dict(self.db.fetchone('SELECT * FROM projects WHERE id = ?', (project_id,)))

    def list(self) -> list[dict]:
        rows = self.db.fetchall('SELECT * FROM projects ORDER BY created_at DESC')
        return [dict(row) for row in rows]
