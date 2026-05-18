from __future__ import annotations

from backend.src.schemas.subject_asset import SubjectAsset
from backend.src.settings.logging import log_event


class SubjectPipeline:
    def __init__(self, storyboard_repo, subject_repo, object_store, audit_service, ai_gateway, keyframe_pipeline=None) -> None:
        self.storyboard_repo = storyboard_repo
        self.subject_repo = subject_repo
        self.object_store = object_store
        self.audit_service = audit_service
        self.ai_gateway = ai_gateway
        self.keyframe_pipeline = keyframe_pipeline

    def run(self, project: dict) -> dict:
        shots = self.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version'))
        names = sorted({ref for shot in shots for ref in shot.get('subject_refs', ['主角'])}) or ['主角']
        style_prompt = f"项目风格：{project.get('prompt', '')}"
        image_model = str(project.get('image_model') or '').strip()
        results = []
        diagnostics = []
        for name in names:
            # 跳过已锁定的主体
            existing = self.subject_repo.get_by_name(project['id'], name)
            if existing and existing.get('is_locked'):
                log_event('subject.skipped_locked', project_id=project['id'], subject_name=name)
                results.append(existing)
                continue

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

        # 触发关键帧生成（主体一致的关键帧序列 2x2/3x3/4x4）—— 默认 Composite 模式
        if self.keyframe_pipeline:
            try:
                keyframe_results = []
                for shot in shots:
                    subject_refs = shot.get('subject_refs', ['主角'])
                    subject_name = subject_refs[0] if subject_refs else '主角'
                    # 查找匹配的主体资产
                    subject = next((r for r in results if r['name'] == subject_name), results[0] if results else {'name': subject_name, 'feature_description': '', 'image_version': 1})
                    composite = self.keyframe_pipeline.generate_composite_grid(shot, subject, project)
                    keyframe_results.append(composite)
                log_event('keyframes.generated_from_subjects', project_id=project['id'], shot_count=len(keyframe_results))
            except Exception as error:
                log_event('keyframes.generation_failed', project_id=project['id'], error=str(error))

        project['status'] = 'keyframe_generating'
        project['current_stage'] = 'keyframe_generating'
        log_event('subject.completed', project_id=project['id'], count=len(results))

        self.audit_service.record('subjects.generated', project_id=project['id'], count=len(results), fallback_count=len(diagnostics))
        return {'items': results, 'diagnostics': diagnostics}

