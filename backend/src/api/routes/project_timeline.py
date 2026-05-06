from __future__ import annotations


def register_timeline_routes(router, context) -> None:
    def get_timeline(_request, params):
        try:
            payload = context.timeline_service.build(params["projectId"])
            return 200, {"ok": True, "item": payload}
        except ValueError as error:
            return 404, {"ok": False, "error": str(error)}

    router.add("GET", "/api/projects/{projectId}/timeline", get_timeline)
