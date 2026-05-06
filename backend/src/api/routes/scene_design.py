from __future__ import annotations


def register_scene_routes(router, context) -> None:
    def update_scene_settings(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        result = context.scene_service.update_settings(project, request.get("json") or {})
        return 200, {"ok": True, "item": result}

    def generate_scene(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        payload = request.get("json") or {}
        result = context.scene_service.generate(
            project,
            payload.get("prompt") or project.get("prompt", ""),
            payload.get("comment", ""),
            payload.get("scene_count"),
        )
        return 202, {"ok": True, "item": result}

    def review_scene(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        payload = request.get("json") or {}
        result = context.scene_service.review(project, payload.get("action", "approve"), payload.get("comment", ""))
        return 200, {"ok": True, "item": result}

    router.add("PUT", "/api/projects/{projectId}/scene-design:settings", update_scene_settings)
    router.add("POST", "/api/projects/{projectId}/scene-design:generate", generate_scene)
    router.add("POST", "/api/projects/{projectId}/scene-design:review", review_scene)
