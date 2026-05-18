from __future__ import annotations

import base64
import binascii
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

from backend.src.schemas.subject_asset import SubjectAsset
from backend.src.settings.config import settings
from backend.src.settings.logging import log_event
from backend.src.utils import utc_now_iso, new_uuid


def _media_url(storage_path: str) -> str:
    host = settings.host if settings.host not in {'0.0.0.0', '::'} else '127.0.0.1'
    return f'http://{host}:{settings.port}/media/{quote(storage_path, safe="")}'


def _image_extension(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {'.png', '.jpg', '.jpeg', '.webp', '.gif'}:
        return suffix
    return {
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'image/webp': '.webp',
        'image/gif': '.gif',
    }.get(content_type, '.png')


def _subject_style_prompt(project: dict, shot: dict = None) -> str:
    parts = []
    if project.get('storyboard_style'):
        parts.append(f"统一风格：{project['storyboard_style']}")
    if project.get('prompt'):
        parts.append(f"项目主题：{project['prompt']}")
    if shot:
        if shot.get('shot_type'):
            parts.append(f"镜头类型：{shot['shot_type']}")
        if shot.get('background'):
            parts.append(f"背景：{shot['background']}")
        if shot.get('description'):
            parts.append(f"镜头描述：{shot['description']}")
    return '；'.join(parts)


def _extract_last_frame(video_bytes: bytes) -> bytes:
    with tempfile.TemporaryDirectory() as tempdir:
        root = Path(tempdir)
        input_path = root / 'input.mp4'
        output_path = root / 'last-frame.png'
        input_path.write_bytes(video_bytes)
        subprocess.run(
            [
                'ffmpeg',
                '-y',
                '-loglevel',
                'error',
                '-sseof',
                '-0.1',
                '-i',
                str(input_path),
                '-frames:v',
                '1',
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return output_path.read_bytes()


def register_subject_routes(router, context) -> None:
    def generate_subjects(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        result = context.subject_pipeline.run(project)
        context.project_repo.update(project)
        response = {"ok": True, "items": result['items']}
        if result.get('diagnostics'):
            response['diagnostics'] = result['diagnostics']
            response['warning'] = 'DashScope image generation failed; fallback assets were used.'
        return 202, response

    def get_subject(_request, params):
        subject = context.subject_repo.get(params["subjectId"])
        if not subject:
            return 404, {"ok": False, "error": "Subject not found"}
        return 200, {"ok": True, "item": subject}

    def update_subject(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        subject = context.subject_repo.get(params["subjectId"])
        if not subject or subject.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Subject not found"}

        payload = request.get('json') or {}
        feature_description = str(payload.get('feature_description') or '').strip()

        if subject.get('is_locked'):
            return 400, {"ok": False, "error": "Subject is locked. Unlock it first to edit."}

        if feature_description:
            context.subject_repo.update_feature_description(subject['id'], feature_description)
            log_event('subject.feature_updated', project_id=project['id'], subject_id=subject['id'])

        updated = context.subject_repo.get(subject['id'])
        return 200, {"ok": True, "item": updated}

    def lock_subject(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        subject = context.subject_repo.get(params["subjectId"])
        if not subject or subject.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Subject not found"}

        context.subject_repo.lock_subject(subject['id'])
        log_event('subject.locked', project_id=project['id'], subject_id=subject['id'])

        updated = context.subject_repo.get(subject['id'])
        return 200, {"ok": True, "item": updated}

    def unlock_subject(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        subject = context.subject_repo.get(params["subjectId"])
        if not subject or subject.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Subject not found"}

        context.subject_repo.unlock_subject(subject['id'])
        log_event('subject.unlocked', project_id=project['id'], subject_id=subject['id'])

        updated = context.subject_repo.get(subject['id'])
        return 200, {"ok": True, "item": updated}

    def upload_shot_subject(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        shot = context.storyboard_repo.get(params["shotId"])
        if not shot or shot.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Shot not found"}

        payload = request.get('json') or {}
        filename = str(payload.get('filename') or '').strip()
        content_type = str(payload.get('content_type') or '').strip().lower()
        data_base64 = str(payload.get('data_base64') or '').strip()

        if not data_base64:
            raise ValueError('Missing image data')
        if not content_type.startswith('image/'):
            raise ValueError('Only image uploads are supported')

        try:
            content = base64.b64decode(data_base64, validate=True)
        except binascii.Error as error:
            raise ValueError('Invalid base64 image data') from error
        if not content:
            raise ValueError('Image payload is empty')

        image_version = context.subject_repo.next_image_version(project['id'])
        extension = _image_extension(filename, content_type)
        asset = SubjectAsset(
            project_id=project['id'],
            shot_id=shot['id'],
            name=f"镜头 {shot['sequence']}",
            profile='镜头上传图',
            image_version=image_version,
        ).to_dict()
        storage_path = context.object_store.save_bytes(
            project['id'],
            f"shot-{shot['sequence']}-subject-v{image_version}{extension}",
            content,
            content_type=content_type,
        )
        asset['image_path'] = storage_path
        asset['source_url'] = _media_url(storage_path)
        context.subject_repo.save(asset)
        return 201, {"ok": True, "item": asset}

    def generate_shot_subject(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        shot = context.storyboard_repo.get(params["shotId"])
        if not shot or shot.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Shot not found"}

        payload = request.get('json') or {}
        mode = str(payload.get('mode') or 'generate').strip()
        variant_hint = str(payload.get('variant_hint') or '').strip()
        image_version = context.subject_repo.next_image_version(project['id'])
        asset = SubjectAsset(
            project_id=project['id'],
            shot_id=shot['id'],
            name=f"镜头 {shot['sequence']}",
            image_version=image_version,
        ).to_dict()

        if mode == 'previous_tail_frame':
            shots = sorted(
                context.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version')),
                key=lambda item: int(item.get('sequence') or 0),
            )
            shot_index = next((index for index, item in enumerate(shots) if item['id'] == shot['id']), None)
            if shot_index is None:
                raise ValueError('Shot not found in current storyboard version')
            if shot_index == 0:
                raise ValueError('First shot cannot reuse previous shot tail frame')

            previous_shot = shots[shot_index - 1]
            previous_task = context.render_repo.get_by_shot(project['id'], previous_shot['id'])
            if not previous_task or previous_task.get('status') != 'succeeded':
                raise ValueError('Previous shot render is not ready')
            render_path = str(previous_task.get('render_path') or '')
            if not render_path.lower().endswith('.mp4'):
                raise ValueError('Previous shot does not have a playable video output')

            frame_bytes = _extract_last_frame(context.object_store.read_bytes(render_path))
            storage_path = context.object_store.save_bytes(
                project['id'],
                f"shot-{shot['sequence']}-subject-tail-v{image_version}.png",
                frame_bytes,
                content_type='image/png',
            )
            asset['profile'] = f"沿用上一镜头尾帧（镜头 {previous_shot['sequence']}）"
            asset['image_path'] = storage_path
            asset['source_url'] = _media_url(storage_path)
        elif mode == 'generate' or mode == 'variant':
            subject_name = '、'.join(shot.get('subject_refs') or ['主角'])
            profile = f"镜头 {shot['sequence']} 主体图，主体：{subject_name}"

            # 获取基础主体的特征描述（用于变体生成）
            feature_description = ''
            base_subject_id = ''
            if variant_hint or mode == 'variant':
                # 查找匹配的基础主体
                base_subjects = context.subject_repo.list_base_subjects(project['id'])
                for base in base_subjects:
                    if base.get('name') in subject_name or subject_name in base.get('name', ''):
                        feature_description = base.get('feature_description', '')
                        base_subject_id = base['id']
                        break
                if not feature_description and base_subjects:
                    # 使用第一个基础主体
                    feature_description = base_subjects[0].get('feature_description', '')
                    base_subject_id = base_subjects[0]['id']

            generated = context.ai_gateway.generate_subject_image(
                subject_name,
                profile,
                _subject_style_prompt(project, shot),
                model=str(project.get('image_model') or '').strip(),
                feature_description=feature_description,
            )
            provider_url = generated.get('provider_url')
            diagnostic = generated.get('diagnostic')
            if provider_url:
                storage_path = context.object_store.save_from_url(
                    project['id'],
                    f"shot-{shot['sequence']}-subject-generated-v{image_version}.png",
                    provider_url,
                    content_type='image/png',
                )
                asset['source_url'] = provider_url
            else:
                storage_path = context.object_store.save_text(
                    project['id'],
                    f"shot-{shot['sequence']}-subject-generated-v{image_version}.txt",
                    f'DEMO SUBJECT IMAGE for shot {shot["sequence"]}',
                )
                asset['source_url'] = ''
            asset['profile'] = '镜头直接生成主体图'
            asset['image_path'] = storage_path

            # 设置变体相关字段
            if variant_hint:
                asset['variant_type'] = 'variant'
                asset['variant_hint'] = variant_hint
                asset['profile'] = f"变体：{variant_hint}"
            if base_subject_id:
                asset['base_subject_id'] = base_subject_id
                asset['feature_description'] = feature_description

            if diagnostic:
                asset['generation_warning'] = diagnostic
        else:
            raise ValueError('Unsupported subject generation mode')

        context.subject_repo.save(asset)
        log_event('subject.shot_generated', project_id=project['id'], shot_id=shot['id'], mode=mode, variant_hint=variant_hint)

        # 触发该镜头的关键帧生成（主体一致的关键帧序列）
        try:
            subject_refs = shot.get('subject_refs', ['主角'])
            subject_name = subject_refs[0] if subject_refs else '主角'
            subject_data = context.subject_repo.get_by_name(project['id'], subject_name) or {
                'name': subject_name,
                'feature_description': '',
                'image_version': 1,
            }
            context.keyframe_pipeline.generate_keyframes_for_shot(shot, subject_data, project)
            log_event('keyframes.triggered_for_shot', project_id=project['id'], shot_id=shot['id'])
        except Exception as error:
            log_event('keyframes.shot_trigger_failed', project_id=project['id'], shot_id=shot['id'], error=str(error))

        return 201, {"ok": True, "item": asset}

    def regenerate_subject(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        subject = context.subject_repo.get(params["subjectId"])
        if not subject or subject.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Subject not found"}

        payload = request.get('json') or {}
        cascade_render = bool(payload.get('cascade_render', False))

        # 保存当前版本
        current_version = subject.get('image_version', 1)
        context.subject_repo.save_version(subject['id'], {
            'version': current_version,
            'image_path': subject.get('image_path', ''),
            'source_url': subject.get('source_url', ''),
            'feature_description': subject.get('feature_description', ''),
        })

        # 重新生成
        new_version = current_version + 1
        generated = context.ai_gateway.generate_subject_image(
            subject.get('name', '主角'),
            subject.get('profile', '统一形象'),
            _subject_style_prompt(project),
            model=str(project.get('image_model') or '').strip(),
            feature_description=subject.get('feature_description', ''),
        )
        provider_url = generated.get('provider_url')
        diagnostic = generated.get('diagnostic')

        if provider_url:
            storage_path = context.object_store.save_from_url(
                project['id'],
                f"subject-{subject.get('name', 'unknown')}-v{new_version}.png",
                provider_url,
                content_type='image/png',
            )
        else:
            storage_path = context.object_store.save_text(
                project['id'],
                f"subject-{subject.get('name', 'unknown')}-v{new_version}.txt",
                f'DEMO SUBJECT IMAGE v{new_version}',
            )

        subject['image_path'] = storage_path
        subject['source_url'] = provider_url or ''
        subject['image_version'] = new_version
        subject['updated_at'] = utc_now_iso()
        if diagnostic:
            subject['generation_warning'] = diagnostic

        context.subject_repo.save(subject)
        log_event('subject.regenerated', project_id=project['id'], subject_id=subject['id'], new_version=new_version, cascade_render=cascade_render)

        # TODO: 如果 cascade_render 为 true，触发相关镜头重新渲染
        # 这需要在 render_pipeline 中实现

        return 200, {"ok": True, "item": subject}

    def list_subject_versions(_request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        subject = context.subject_repo.get(params["subjectId"])
        if not subject or subject.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Subject not found"}

        versions = context.subject_repo.list_versions(subject['id'])
        return 200, {"ok": True, "items": versions}

    def rollback_subject_version(request, params):
        project = context.project_repo.get(params["projectId"])
        if not project:
            return 404, {"ok": False, "error": "Project not found"}
        subject = context.subject_repo.get(params["subjectId"])
        if not subject or subject.get('project_id') != project['id']:
            return 404, {"ok": False, "error": "Subject not found"}

        payload = request.get('json') or {}
        target_version = int(payload.get('target_version', 0))
        if not target_version:
            raise ValueError('target_version is required')

        version_data = context.subject_repo.get_version(subject['id'], target_version)
        if not version_data:
            return 404, {"ok": False, "error": f"Version {target_version} not found"}

        # 保存当前版本
        current_version = subject.get('image_version', 1)
        context.subject_repo.save_version(subject['id'], {
            'version': current_version,
            'image_path': subject.get('image_path', ''),
            'source_url': subject.get('source_url', ''),
            'feature_description': subject.get('feature_description', ''),
        })

        # 恢复到目标版本
        subject['image_path'] = version_data['image_path']
        subject['source_url'] = version_data.get('source_url', '')
        subject['feature_description'] = version_data.get('feature_description', '')
        subject['image_version'] = target_version
        subject['updated_at'] = utc_now_iso()

        context.subject_repo.save(subject)
        log_event('subject.rolled_back', project_id=project['id'], subject_id=subject['id'], target_version=target_version)

        return 200, {"ok": True, "item": subject}

    router.add("POST", "/api/projects/{projectId}/subjects:generate", generate_subjects)
    router.add("GET", "/api/projects/{projectId}/subjects/{subjectId}", get_subject)
    router.add("PUT", "/api/projects/{projectId}/subjects/{subjectId}", update_subject)
    router.add("POST", "/api/projects/{projectId}/subjects/{subjectId}:lock", lock_subject)
    router.add("POST", "/api/projects/{projectId}/subjects/{subjectId}:unlock", unlock_subject)
    router.add("POST", "/api/projects/{projectId}/subjects/{subjectId}:regenerate", regenerate_subject)
    router.add("GET", "/api/projects/{projectId}/subjects/{subjectId}/versions", list_subject_versions)
    router.add("POST", "/api/projects/{projectId}/subjects/{subjectId}:rollback", rollback_subject_version)
    router.add("POST", "/api/projects/{projectId}/subjects/shots/{shotId}:upload", upload_shot_subject)
    router.add("POST", "/api/projects/{projectId}/subjects/shots/{shotId}:generate", generate_shot_subject)
