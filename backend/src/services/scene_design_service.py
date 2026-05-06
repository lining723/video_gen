from __future__ import annotations

from backend.src.schemas.scene_design import SceneDesign
from backend.src.utils import utc_now_iso


class SceneDesignService:
    def __init__(self, project_repo, scene_repo, audit_service, ai_gateway, scene_count: int) -> None:
        self.project_repo = project_repo
        self.scene_repo = scene_repo
        self.audit_service = audit_service
        self.ai_gateway = ai_gateway
        self.scene_count = scene_count

    def _text_model(self, project: dict) -> str:
        return str(project.get('text_model') or '').strip()

    def _normalize_scene_count(self, value: int | str | None) -> int:
        count = int(value or self.scene_count)
        return max(1, min(12, count))

    def update_settings(self, project: dict, payload: dict) -> dict:
        if 'scene_count' in payload:
            project['scene_count'] = self._normalize_scene_count(payload.get('scene_count'))
            self.project_repo.update(project)
            self.audit_service.record(
                'scene.settings_updated',
                project_id=project['id'],
                scene_count=project['scene_count'],
            )
        return project

    def generate(self, project: dict, prompt: str, comment: str = '', scene_count: int | None = None) -> dict:
        latest = self.scene_repo.latest(project['id'])
        version = (latest or {}).get('version', 0) + 1
        count = self._normalize_scene_count(scene_count or project.get('scene_count'))
        project['scene_count'] = count
        generated = self.ai_gateway.generate_scene_design(prompt, count, model=self._text_model(project))
        scene_summary = (generated.get('scene_summary') or f'围绕“{prompt}”的视频场景设计').strip()
        if comment:
            scene_summary = f'{scene_summary} {comment}'.strip()
        scenes = generated.get('scene_list') or []
        record = SceneDesign(
            project_id=project['id'],
            version=version,
            input_prompt=prompt,
            scene_summary=scene_summary,
            scene_list=scenes,
            review_status='scene_reviewing',
            review_comment=comment,
        ).to_dict()
        self.scene_repo.save(record)
        project['scene_design_version'] = version
        project['status'] = 'scene_generated'
        project['current_stage'] = 'scene_reviewing'
        self.project_repo.update(project)
        self.audit_service.record('scene.generated', project_id=project['id'], version=version)
        return record

    def review(self, project: dict, action: str, comment: str = '') -> dict:
        latest = self.scene_repo.latest(project['id'])
        if not latest:
            raise ValueError('No scene design to review')
        if action == 'approve':
            latest['review_status'] = 'scene_approved'
            project['status'] = 'scene_approved'
            project['current_stage'] = 'scene_approved'
        elif action == 'reject':
            latest['review_status'] = 'scene_reviewing'
            latest['review_comment'] = comment or '需要调整场景设计'
        elif action == 'regenerate':
            return self.generate(project, latest['input_prompt'], comment, project.get('scene_count'))
        else:
            raise ValueError('Unsupported review action')
        latest['updated_at'] = utc_now_iso()
        self.scene_repo.save(latest)
        self.project_repo.update(project)
        self.audit_service.record('scene.reviewed', project_id=project['id'], action=action)
        return latest
