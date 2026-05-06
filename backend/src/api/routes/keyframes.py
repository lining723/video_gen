from __future__ import annotations

from urllib.parse import quote

from backend.src.settings.config import settings
from backend.src.settings.logging import log_event


def _media_url(storage_path: str) -> str:
    """生成媒体文件URL"""
    host = settings.host if settings.host not in {'0.0.0.0', '::'} else '127.0.0.1'
    return f'http://{host}:{settings.port}/media/{quote(storage_path, safe="")}'


def register_keyframe_routes(router, context) -> None:
    """注册关键帧相关路由"""

    def get_shot_keyframes(_request, params):
        """
        获取指定镜头的关键帧

        GET /api/projects/{projectId}/shots/{shotId}/keyframes
        """
        project_id = params.get('projectId')
        shot_id = params.get('shotId')

        if not project_id or not shot_id:
            return 400, {"ok": False, "error": "Missing projectId or shotId"}

        # 检查项目是否存在
        project = context.project_repo.get(project_id)
        if not project:
            return 404, {"ok": False, "error": "Project not found"}

        # 获取关键帧网格
        grid = context.keyframe_repo.get_by_shot(project_id, shot_id)
        if not grid:
            return 404, {"ok": False, "error": "Keyframe grid not found for this shot"}

        # 构建响应
        frames = []
        for frame in grid.get('frames', []):
            frame_data = {
                'position': frame.get('position'),
                'time_ratio': frame.get('time_ratio'),
                'status': frame.get('status', 'pending'),
            }

            # 添加图片URL
            if frame.get('image_path'):
                frame_data['image_url'] = _media_url(frame['image_path'])

            # 添加错误信息
            if frame.get('error_message'):
                frame_data['error_message'] = frame['error_message']

            frames.append(frame_data)

        return 200, {
            "ok": True,
            "grid_type": grid.get('grid_type', '3x3'),
            "frame_count": grid.get('frame_count', 9),
            "frames": frames,
        }

    def get_project_keyframes_status(_request, params):
        """
        获取项目关键帧状态汇总

        GET /api/projects/{projectId}/keyframes/status
        """
        project_id = params.get('projectId')

        if not project_id:
            return 400, {"ok": False, "error": "Missing projectId"}

        # 检查项目是否存在
        project = context.project_repo.get(project_id)
        if not project:
            return 404, {"ok": False, "error": "Project not found"}

        # 获取项目的所有关键帧网格
        grids = context.keyframe_repo.list_by_project(project_id)

        # 计算汇总信息
        total_shots = len(grids)
        total_frames = sum(g.get('frame_count', 0) for g in grids)
        succeeded_frames = 0
        failed_frames = 0
        completed_shots = 0
        generating_shots = 0
        failed_shots = 0

        shot_statuses = []
        for grid in grids:
            frames = grid.get('frames', [])
            succeeded = sum(1 for f in frames if f.get('status') == 'succeeded')
            failed = sum(1 for f in frames if f.get('status') == 'failed')

            succeeded_frames += succeeded
            failed_frames += failed

            # 判断镜头状态
            if failed > 0 and succeeded + failed < grid.get('frame_count', 0):
                status = 'partial_failed'
                failed_shots += 1
            elif succeeded == grid.get('frame_count', 0):
                status = 'completed'
                completed_shots += 1
            elif succeeded > 0 or failed > 0:
                status = 'generating'
                generating_shots += 1
            else:
                status = 'pending'
                generating_shots += 1

            shot_statuses.append({
                'shot_id': grid.get('shot_id'),
                'status': status,
                'grid_type': grid.get('grid_type'),
                'frame_count': grid.get('frame_count'),
                'succeeded_count': succeeded,
                'failed_count': failed,
            })

        return 200, {
            "ok": True,
            "project_id": project_id,
            "total_shots": total_shots,
            "completed_shots": completed_shots,
            "generating_shots": generating_shots,
            "failed_shots": failed_shots,
            "total_frames": total_frames,
            "succeeded_frames": succeeded_frames,
            "failed_frames": failed_frames,
            "shots": shot_statuses,
        }

    def retry_keyframe(_request, params):
        """
        重试生成指定的关键帧

        POST /api/projects/{projectId}/shots/{shotId}/keyframes/{position}/retry
        """
        project_id = params.get('projectId')
        shot_id = params.get('shotId')
        position = params.get('position')

        if not project_id or not shot_id or position is None:
            return 400, {"ok": False, "error": "Missing required parameters"}

        try:
            position = int(position)
        except (ValueError, TypeError):
            return 400, {"ok": False, "error": "Invalid position parameter"}

        # 检查项目是否存在
        project = context.project_repo.get(project_id)
        if not project:
            return 404, {"ok": False, "error": "Project not found"}

        # 获取关键帧网格
        grid = context.keyframe_repo.get_by_shot(project_id, shot_id)
        if not grid:
            return 404, {"ok": False, "error": "Keyframe grid not found"}

        # 检查位置是否有效
        frames = grid.get('frames', [])
        if position < 0 or position >= len(frames):
            return 400, {"ok": False, "error": f"Invalid position: {position}"}

        frame = frames[position]

        # 检查重试次数
        MAX_RETRY_COUNT = 3
        retry_count = frame.get('retry_count', 0)
        if retry_count >= MAX_RETRY_COUNT:
            return 400, {
                "ok": False,
                "error": f"Retry limit exceeded ({MAX_RETRY_COUNT})",
                "retry_count": retry_count,
            }

        # 更新重试状态
        frame['retry_count'] = retry_count + 1
        frame['status'] = 'generating'
        frame['error_message'] = ''

        # 保存更新
        context.keyframe_repo.save(grid)

        log_event(
            'keyframe.retry_submitted',
            project_id=project_id,
            shot_id=shot_id,
            position=position,
            retry_count=retry_count + 1,
        )

        return 200, {
            "ok": True,
            "status": "retrying",
            "retry_count": retry_count + 1,
            "message": "Keyframe retry task submitted",
        }

    # 注册路由
    router.add_route('GET', '/projects/{projectId}/shots/{shotId}/keyframes', get_shot_keyframes)
    router.add_route('GET', '/projects/{projectId}/keyframes/status', get_project_keyframes_status)
    router.add_route('POST', '/projects/{projectId}/shots/{shotId}/keyframes/{position}/retry', retry_keyframe)
