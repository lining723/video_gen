from __future__ import annotations

import base64
import binascii
from pathlib import Path

from backend.src.workers.tasks import submit_task


def register_final_video_routes(router, context) -> None:
    def compose_video(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        readiness = context.compose_pipeline.assess_readiness(project)
        if not readiness["ready"]:
            return 409, {
                "ok": False,
                "error": "Final video is not ready to compose",
                "details": readiness,
            }
        submit_task(context.compose_pipeline.run, project)
        return 202, {"ok": True, "message": "Compose started", "projectId": project["id"]}

    def update_final_video_settings(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        payload = request.get("json") or {}
        for key in (
            'compose_enable_subtitles',
            'compose_enable_bgm',
            'compose_enable_voiceover',
            'compose_enable_transitions',
        ):
            if key in payload:
                project[key] = bool(payload.get(key))
        context.project_repo.update(project)
        return 200, {"ok": True, "item": project}

    def upload_final_video_bgm(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}

        payload = request.get("json") or {}
        filename = str(payload.get('filename') or '').strip()
        content_type = str(payload.get('content_type') or '').strip().lower()
        data_base64 = str(payload.get('data_base64') or '').strip()

        if not data_base64:
            raise ValueError('Missing audio data')
        if not content_type.startswith('audio/'):
            raise ValueError('Only audio uploads are supported')
        try:
            content = base64.b64decode(data_base64, validate=True)
        except binascii.Error as error:
            raise ValueError('Invalid base64 audio data') from error
        if not content:
            raise ValueError('Audio payload is empty')

        suffix = Path(filename).suffix.lower() or {
            'audio/mpeg': '.mp3',
            'audio/mp4': '.m4a',
            'audio/x-m4a': '.m4a',
            'audio/wav': '.wav',
            'audio/x-wav': '.wav',
            'audio/aac': '.aac',
        }.get(content_type, '.m4a')
        storage_path = context.object_store.save_bytes(
            project['id'],
            f'project-bgm{suffix}',
            content,
            content_type=content_type,
        )
        project['final_bgm_path'] = storage_path
        project['compose_enable_bgm'] = True
        context.project_repo.update(project)
        return 201, {"ok": True, "item": project}

    def clear_final_video_bgm(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        project['final_bgm_path'] = ''
        context.project_repo.update(project)
        return 200, {"ok": True, "item": project}

    def get_final_video(_request, params):
        item = context.final_repo.latest(params["projectId"])
        if not item:
            return 404, {"ok": False, "error": "Final video not ready"}
        return 200, {"ok": True, "item": item}

    router.add("POST", "/api/projects/{projectId}/final-video:compose", compose_video)
    router.add("PUT", "/api/projects/{projectId}/final-video:settings", update_final_video_settings)
    router.add("POST", "/api/projects/{projectId}/final-video/bgm:upload", upload_final_video_bgm)
    router.add("POST", "/api/projects/{projectId}/final-video/bgm:clear", clear_final_video_bgm)
    router.add("GET", "/api/projects/{projectId}/final-video", get_final_video)
