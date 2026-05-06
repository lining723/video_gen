from __future__ import annotations

from datetime import datetime

from backend.src.schemas.storyboard import StoryboardShot
from backend.src.services.storyboard_validation import validate_shot


class StoryboardService:
    def __init__(self, project_repo, scene_repo, storyboard_repo, audit_service, ai_gateway, duration_limit: int) -> None:
        self.project_repo = project_repo
        self.scene_repo = scene_repo
        self.storyboard_repo = storyboard_repo
        self.audit_service = audit_service
        self.ai_gateway = ai_gateway
        self.duration_limit = duration_limit

    def _storyboard_style(self, project: dict) -> str:
        return str(project.get('storyboard_style') or '').strip()

    def _text_model(self, project: dict) -> str:
        return str(project.get('text_model') or '').strip()

    def update_settings(self, project: dict, payload: dict) -> dict:
        project['storyboard_style'] = str(payload.get('storyboard_style') or '').strip()
        self.project_repo.update(project)
        self.audit_service.record(
            'storyboard.settings_updated',
            project_id=project['id'],
            storyboard_style=project['storyboard_style'],
        )
        return project

    def generate(self, project: dict) -> list[dict]:
        latest_scene = self.scene_repo.latest(project['id'])
        if not latest_scene or latest_scene.get('review_status') != 'scene_approved':
            raise ValueError('Scene must be approved before generating storyboard')
        version = int(project.get('storyboard_version', 0)) + 1
        storyboard_style = self._storyboard_style(project)
        generated_shots = self.ai_gateway.generate_storyboard(
            latest_scene.get('input_prompt', project.get(' ', '')),
            latest_scene.get('scene_list', []),
            self.duration_limit,
            storyboard_style=storyboard_style,
            model=self._text_model(project),
        )
        shots = []
        for index, scene in enumerate(latest_scene.get('scene_list', []), start=1):
            payload = generated_shots[index - 1] if index - 1 < len(generated_shots) else {}
            shot = StoryboardShot(
                project_id=project['id'],
                version=version,
                sequence=int(payload.get('sequence') or index),
                duration=min(self.duration_limit, int(payload.get('duration') or 6 + index)),
                shot_type=payload.get('shot_type') or '中景',
                camera_movement=payload.get('camera_movement') or '缓慢推进',
                scene_time=payload.get('scene_time') or '白天',
                background=payload.get('background') or scene['description'],
                sound_effects=payload.get('sound_effects') or '环境氛围声，轻音乐铺底',
                action_direction=payload.get('action_direction') or '主体自然出镜并完成核心动作',
                description=payload.get('description') or scene['description'],
                subtitle_text=payload.get('subtitle_text') or f'字幕：{scene["title"]}',
                dubbing_text=payload.get('dubbing_text') or f'配音：{scene["description"]}',
                voiceover_text=payload.get('voiceover_text') or '',
                voiceover_tone=payload.get('voiceover_tone') or '温暖自然的中文女声',
                subject_refs=payload.get('subject_refs') or ['主角'],
                status='storyboard_generated',
            ).to_dict()
            validate_shot(shot, self.duration_limit)
            self.storyboard_repo.save(shot)
            shots.append(shot)
        project['storyboard_version'] = version
        project['status'] = 'storyboard_generated'
        project['current_stage'] = 'storyboard_reviewing'
        self.project_repo.update(project)
        self.audit_service.record('storyboard.generated', project_id=project['id'], version=version)
        return shots

    def update_shot(self, project: dict, shot_id: str, payload: dict) -> dict:
        shot = self.storyboard_repo.get(shot_id)
        if not shot:
            raise ValueError('Shot not found')
        editable_fields = {
            'sequence',
            'duration',
            'shot_type',
            'camera_movement',
            'scene_time',
            'background',
            'sound_effects',
            'action_direction',
            'description',
            'subtitle_text',
            'dubbing_text',
            'voiceover_text',
            'voiceover_tone',
            'subject_refs',
        }
        shot.update({key: value for key, value in payload.items() if key in editable_fields})
        shot['status'] = 'storyboard_generated'
        shot['updated_at'] = datetime.utcnow().isoformat()
        validate_shot(shot, self.duration_limit)
        self.storyboard_repo.save(shot)
        self.audit_service.record('storyboard.updated', project_id=project['id'], shot_id=shot_id)
        return shot

    def regenerate_shot(self, project: dict, shot_id: str) -> dict:
        shot = self.storyboard_repo.get(shot_id)
        if not shot:
            raise ValueError('Shot not found')

        latest_scene = self.scene_repo.latest(project['id'])
        if not latest_scene or not latest_scene.get('scene_list'):
            raise ValueError('Scene must exist before regenerating storyboard shot')

        shots = self.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version'))
        ordered_shots = sorted(shots, key=lambda item: int(item.get('sequence') or 0))
        shot_index = next((index for index, item in enumerate(ordered_shots) if item['id'] == shot_id), None)
        if shot_index is None:
            raise ValueError('Shot not found in current storyboard version')

        scene_list = latest_scene.get('scene_list', [])
        scene = scene_list[min(shot_index, len(scene_list) - 1)]
        storyboard_style = self._storyboard_style(project)
        generated = self.ai_gateway.generate_storyboard(
            latest_scene.get('input_prompt', project.get('prompt', '')),
            [scene],
            self.duration_limit,
            storyboard_style=storyboard_style,
            model=self._text_model(project),
        )
        payload = generated[0] if generated else {}

        regenerated = {
            **shot,
            'duration': min(self.duration_limit, int(payload.get('duration') or shot.get('duration') or 6)),
            'shot_type': payload.get('shot_type') or '中景',
            'camera_movement': payload.get('camera_movement') or '缓慢推进',
            'scene_time': payload.get('scene_time') or '白天',
            'background': payload.get('background') or scene.get('description', ''),
            'sound_effects': payload.get('sound_effects') or '环境氛围声，轻音乐铺底',
            'action_direction': payload.get('action_direction') or '主体自然出镜并完成核心动作',
            'description': payload.get('description') or scene.get('description', shot.get('description', '')),
            'subtitle_text': payload.get('subtitle_text') or shot.get('subtitle_text') or '',
            'dubbing_text': payload.get('dubbing_text') or shot.get('dubbing_text') or f'配音：{scene.get("description", "")}',
            'voiceover_text': payload.get('voiceover_text') or shot.get('voiceover_text') or '',
            'voiceover_tone': payload.get('voiceover_tone') or shot.get('voiceover_tone') or '温暖自然的中文女声',
            'subject_refs': payload.get('subject_refs') or shot.get('subject_refs') or ['主角'],
            'status': 'storyboard_generated',
            'updated_at': datetime.utcnow().isoformat(),
        }
        validate_shot(regenerated, self.duration_limit)
        self.storyboard_repo.save(regenerated)
        self.audit_service.record('storyboard.regenerated', project_id=project['id'], shot_id=shot_id)
        return regenerated

    def review(self, project: dict, action: str, comment: str = '') -> dict:
        shots = self.storyboard_repo.list_by_project(project['id'], project.get('storyboard_version'))
        if not shots:
            raise ValueError('No storyboard to review')
        if action == 'approve':
            for shot in shots:
                shot['status'] = 'storyboard_approved'
                self.storyboard_repo.save(shot)
            project['status'] = 'storyboard_approved'
            project['current_stage'] = 'storyboard_approved'
        elif action == 'reject':
            for shot in shots:
                shot['status'] = 'storyboard_generated'
                self.storyboard_repo.save(shot)
        else:
            raise ValueError('Unsupported review action')
        self.project_repo.update(project)
        self.audit_service.record('storyboard.reviewed', project_id=project['id'], action=action, comment=comment)
        return {'project_id': project['id'], 'action': action, 'comment': comment}
