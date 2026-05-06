from __future__ import annotations

import json

from .db import SQLiteDatabase
from backend.src.utils import utc_now_iso


class KeyframeRepository:
    """关键帧数据访问层"""

    def __init__(self, db: SQLiteDatabase) -> None:
        self.db = db

    def save(self, data: dict) -> dict:
        """
        保存关键帧网格

        Args:
            data: 关键帧网格数据字典

        Returns:
            保存后的数据
        """
        exists = self.db.fetchone('SELECT id FROM keyframe_grids WHERE id = ?', (data['id'],))

        # 将 frames 列表转换为 JSON 字符串
        frames_json = json.dumps(data.get('frames', []), ensure_ascii=False)

        params = (
            data['id'],
            data['project_id'],
            data['shot_id'],
            data['subject_name'],
            data.get('grid_type', '3x3'),
            data.get('frame_count', 9),
            frames_json,
            data.get('generated_at', ''),
            data.get('source_model', ''),
            data['created_at'],
            data['updated_at'],
        )

        if exists:
            self.db.execute(
                '''UPDATE keyframe_grids SET
                   project_id=?, shot_id=?, subject_name=?, grid_type=?, frame_count=?,
                   frames=?, generated_at=?, source_model=?, created_at=?, updated_at=?
                   WHERE id=?''',
                params[1:] + (data['id'],),
            )
        else:
            self.db.execute(
                '''INSERT INTO keyframe_grids
                   (id, project_id, shot_id, subject_name, grid_type, frame_count, frames,
                    generated_at, source_model, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                params,
            )

        return data

    def get_by_shot(self, project_id: str, shot_id: str) -> dict | None:
        """
        根据镜头ID获取关键帧网格

        Args:
            project_id: 项目ID
            shot_id: 镜头ID

        Returns:
            关键帧网格数据，如果不存在返回 None
        """
        row = self.db.fetchone(
            'SELECT * FROM keyframe_grids WHERE project_id = ? AND shot_id = ?',
            (project_id, shot_id),
        )
        if not row:
            return None

        result = dict(row)
        # 将 JSON 字符串转换回列表
        if result.get('frames'):
            try:
                result['frames'] = json.loads(result['frames'])
            except json.JSONDecodeError:
                result['frames'] = []
        return result

    def list_by_project(self, project_id: str) -> list[dict]:
        """
        获取项目的所有关键帧网格

        Args:
            project_id: 项目ID

        Returns:
            关键帧网格列表
        """
        rows = self.db.fetchall(
            'SELECT * FROM keyframe_grids WHERE project_id = ? ORDER BY created_at ASC',
            (project_id,),
        )

        results = []
        for row in rows:
            result = dict(row)
            # 将 JSON 字符串转换回列表
            if result.get('frames'):
                try:
                    result['frames'] = json.loads(result['frames'])
                except json.JSONDecodeError:
                    result['frames'] = []
            results.append(result)

        return results

    def get(self, grid_id: str) -> dict | None:
        """
        根据ID获取关键帧网格

        Args:
            grid_id: 关键帧网格ID

        Returns:
            关键帧网格数据，如果不存在返回 None
        """
        row = self.db.fetchone('SELECT * FROM keyframe_grids WHERE id = ?', (grid_id,))
        if not row:
            return None

        result = dict(row)
        # 将 JSON 字符串转换回列表
        if result.get('frames'):
            try:
                result['frames'] = json.loads(result['frames'])
            except json.JSONDecodeError:
                result['frames'] = []
        return result

    def delete(self, shot_id: str) -> bool:
        """
        删除指定镜头的关键帧网格

        Args:
            shot_id: 镜头ID

        Returns:
            是否删除成功
        """
        try:
            self.db.execute('DELETE FROM keyframe_grids WHERE shot_id = ?', (shot_id,))
            return True
        except Exception:
            return False

    def delete_by_project(self, project_id: str) -> bool:
        """
        删除项目的所有关键帧网格

        Args:
            project_id: 项目ID

        Returns:
            是否删除成功
        """
        try:
            self.db.execute('DELETE FROM keyframe_grids WHERE project_id = ?', (project_id,))
            return True
        except Exception:
            return False

    def update_frame_status(self, shot_id: str, position: int, status: str, error_message: str = '') -> bool:
        """
        更新单个关键帧的状态

        Args:
            shot_id: 镜头ID
            position: 关键帧位置
            status: 新状态
            error_message: 错误信息（可选）

        Returns:
            是否更新成功
        """
        grid = self.get_by_shot('', shot_id)
        if not grid:
            return False

        frames = grid.get('frames', [])
        if position < 0 or position >= len(frames):
            return False

        frames[position]['status'] = status
        if error_message:
            frames[position]['error_message'] = error_message

        grid['frames'] = frames
        grid['updated_at'] = utc_now_iso()
        self.save(grid)

        return True
