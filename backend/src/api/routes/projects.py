from __future__ import annotations

from backend.src.schemas.project import Project
from backend.src.settings.config import settings


def register_project_routes(router, context) -> None:
    def list_projects(_request, _params):
        return 200, {"ok": True, "items": context.project_repo.list()}

    def create_project(request, _params):
        payload = request.get("json") or {}
        project = Project(
            name=payload.get("name") or "Demo Project",
            prompt=payload.get("prompt") or "创建一个产品宣传视频",
            scene_count=int(payload.get("scene_count") or 3),
            text_model=str(payload.get("text_model") or settings.default_text_model),
            image_model=str(payload.get("image_model") or settings.dashscope_image_model),
            video_model=str(payload.get("video_model") or settings.dashscope_video_model),
        ).to_dict()
        context.project_repo.create(project)
        context.audit_service.record("project.created", project_id=project["id"])
        return 201, {"ok": True, "item": project}

    def update_project_settings(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        payload = request.get("json") or {}
        for key in ('text_model', 'image_model', 'video_model'):
            if key in payload:
                project[key] = str(payload.get(key) or '').strip()
        context.project_repo.update(project)
        context.audit_service.record(
            "project.settings_updated",
            project_id=project["id"],
            text_model=project.get('text_model', ''),
            image_model=project.get('image_model', ''),
            video_model=project.get('video_model', ''),
        )
        return 200, {"ok": True, "item": project}

    def get_project(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        return 200, {"ok": True, "item": context.timeline_service.build(project["id"])}

    router.add("GET", "/api/projects", list_projects)
    router.add("POST", "/api/projects", create_project)
    router.add("GET", "/api/projects/{projectId}", get_project)
    router.add("PUT", "/api/projects/{projectId}:settings", update_project_settings)
