from __future__ import annotations


def register_storyboard_routes(router, context) -> None:
    def update_storyboard_settings(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        result = context.storyboard_service.update_settings(project, request.get("json") or {})
        return 200, {"ok": True, "item": result}

    def generate_storyboard(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        result = context.storyboard_service.generate(project)
        return 202, {"ok": True, "items": result}

    def update_shot(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        result = context.storyboard_service.update_shot(project, params["shotId"], request.get("json") or {})
        return 200, {"ok": True, "item": result}

    def regenerate_shot(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        result = context.storyboard_service.regenerate_shot(project, params["shotId"])
        return 200, {"ok": True, "item": result}

    def review_storyboard(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        payload = request.get("json") or {}
        result = context.storyboard_service.review(project, payload.get("action", "approve"), payload.get("comment", ""))
        return 200, {"ok": True, "item": result}

    router.add("PUT", "/api/projects/{projectId}/storyboard:settings", update_storyboard_settings)
    router.add("POST", "/api/projects/{projectId}/storyboard:generate", generate_storyboard)
    router.add("PUT", "/api/projects/{projectId}/storyboard/shots/{shotId}", update_shot)
    router.add("POST", "/api/projects/{projectId}/storyboard/shots/{shotId}:regenerate", regenerate_shot)
    router.add("POST", "/api/projects/{projectId}/storyboard:review", review_storyboard)
