from __future__ import annotations

from backend.src.workers.tasks import submit_task


def render_progress_label(task) -> str:
    if task.get("progress_message"):
        return str(task["progress_message"])
    if task.get("status") == "running" and task.get("force_refresh"):
        return "镜头正在跳过缓存重生成"
    if task.get("status") == "running":
        return "镜头正在生成中"
    if task.get("status") == "succeeded" and task.get("force_refresh"):
        return "镜头已完成重生成并替换旧产物"
    if task.get("status") == "succeeded" and task.get("cache_hit"):
        return "镜头已完成，当前结果来自缓存"
    if task.get("status") == "succeeded":
        return "镜头已生成完成"
    if task.get("status") == "failed":
        return "镜头生成失败，可重试"
    return "镜头状态未知"


def build_render_progress_item(project_id, shot, task) -> dict:
    if not task:
        return {
            "project_id": project_id,
            "shot_id": shot["id"],
            "sequence": shot["sequence"],
            "status": "missing",
            "progress_label": "尚未创建渲染任务",
            "render_path": "",
            "started_at": "",
            "finished_at": "",
            "updated_at": "",
            "force_refresh": False,
            "cache_hit": False,
            "provider_name": "",
            "provider_task_id": "",
            "progress_message": "",
            "last_polled_at": "",
            "error_message": "",
        }
    return {
        **task,
        "sequence": shot["sequence"],
        "progress_label": render_progress_label(task),
    }


def register_render_routes(router, context) -> None:
    def start_renders(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        payload = request.get("json") or {}
        force = bool(payload.get("force"))
        futures = context.render_pipeline.dispatch(project, force=force)
        return 202, {"ok": True, "message": "Render started", "projectId": project["id"], "force": force, "scheduledShots": len(futures)}

    def retry_render(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        shot = context.storyboard_repo.get(params["shotId"])
        if not shot:
            return 404, {"ok": False, "error": "Shot not found"}
        payload = request.get("json") or {}
        force = bool(payload.get("force"))
        submit_task(context.render_pipeline.render_shot, project, shot, force=force)
        return 202, {"ok": True, "message": "Retry started", "shotId": shot["id"], "force": force}

    def get_render_status(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        shot = context.storyboard_repo.get(params["shotId"])
        if not shot or shot.get("project_id") != project["id"]:
            return 404, {"ok": False, "error": "Shot not found"}
        task = context.render_repo.get_by_shot(project["id"], shot["id"])
        if task and task.get("status") == "running" and task.get("provider_task_id"):
            refreshed = context.render_status_poller.refresh_task(task["id"])
            if refreshed:
                task = refreshed
        return 200, {"ok": True, "item": build_render_progress_item(project["id"], shot, task)}

    router.add("POST", "/api/projects/{projectId}/renders:start", start_renders)
    router.add("POST", "/api/projects/{projectId}/renders/shots/{shotId}:retry", retry_render)
    router.add("GET", "/api/projects/{projectId}/renders/shots/{shotId}", get_render_status)
