from __future__ import annotations

from backend.src.schemas.subject_asset import SubjectAsset
from backend.src.settings.logging import log_event


class SubjectPipeline:
    def __init__(self, storyboard_repo, subject_repo, object_store, audit_service, ai_gateway) -> None:
        self.storyboard_repo = storyboard_repo
        self.subject_repo = subject_repo
        self.object_store = object_store
        self.audit_service = audit_service
        self.ai_gateway = ai_gateway

    def run(self, project: dict) -> dict:
        shots = self.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version'))
        names = sorted({ref for shot in shots for ref in shot.get('subject_refs', ['主角'])}) or ['主角']
        style_prompt = f"项目风格：{project.get('prompt', '')}"
        image_model = str(project.get('image_model') or '').strip()
        results = []
        diagnostics = []
        for name in names:
            profile = f'{name} 的统一形象'
            generated = self.ai_gateway.generate_subject_image(name, profile, style_prompt, model=image_model)
            provider_url = generated.get('provider_url')
            diagnostic = generated.get('diagnostic')
            if provider_url:
                storage_path = self.object_store.save_from_url(project['id'], f'subject-{name}.png', provider_url, content_type='image/png')
            else:
                storage_path = self.object_store.save_text(project['id'], f'subject-{name}.txt', f'DEMO SUBJECT IMAGE for {name}')

            # 提取主体特征描述
            feature_description = ''
            try:
                feature_description = self.ai_gateway.extract_subject_features(name, profile)
                log_event('subject.feature_extracted', project_id=project['id'], subject_name=name, feature_length=len(feature_description))
            except Exception as error:
                log_event('subject.feature_extraction_failed', project_id=project['id'], subject_name=name, error=str(error))

            asset = SubjectAsset(
                project_id=project['id'],
                name=name,
                profile=profile,
                image_path=storage_path,
                source_url=provider_url or '',
                image_version=1,
                feature_description=feature_description,
                variant_type='base',
            ).to_dict()
            if diagnostic:
                asset['generation_warning'] = diagnostic
                diagnostics.append({'subject_name': name, **diagnostic})
                log_event('subject.fallback_used', project_id=project['id'], subject_name=name, **diagnostic)
            self.subject_repo.save(asset)
            results.append(asset)
        project['status'] = 'subject_ready'
        project['current_stage'] = 'subject_ready'
        self.audit_service.record('subjects.generated', project_id=project['id'], count=len(results), fallback_count=len(diagnostics))
        return {'items': results, 'diagnostics': diagnostics}
