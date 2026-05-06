from __future__ import annotations

from backend.src.media.composer import Composer
from backend.src.schemas.final_video import FinalVideo
from backend.src.settings.logging import log_event


class ComposePipeline:
    def __init__(self, storyboard_repo, render_repo, final_repo, object_store, project_repo, audit_service) -> None:
        self.storyboard_repo = storyboard_repo
        self.render_repo = render_repo
        self.final_repo = final_repo
        self.object_store = object_store
        self.project_repo = project_repo
        self.audit_service = audit_service
        self.composer = Composer(object_store)

    def assess_readiness(self, project: dict) -> dict:
        version = project.get('storyboard_version') or None
        shots = self.storyboard_repo.list_by_project(project['id'], version)
        latest_by_shot = {}
        for task in self.render_repo.list_by_project(project['id']):
            latest_by_shot[task['shot_id']] = task

        blockers = []
        for shot in shots:
            task = latest_by_shot.get(shot['id'])
            if not task:
                blockers.append({'shot_id': shot['id'], 'sequence': shot['sequence'], 'status': 'missing', 'reason': '尚未创建渲染任务'})
                continue
            if task.get('status') != 'succeeded':
                blockers.append({'shot_id': shot['id'], 'sequence': shot['sequence'], 'status': task.get('status') or 'unknown', 'reason': '镜头仍未渲染完成'})
                continue
            render_path = str(task.get('render_path') or '')
            if not render_path.lower().endswith('.mp4'):
                blockers.append({'shot_id': shot['id'], 'sequence': shot['sequence'], 'status': 'unplayable', 'reason': '镜头没有可播放的视频产物'})

        return {
            'ready': bool(shots) and not blockers,
            'total_shots': len(shots),
            'ready_shots': len(shots) - len(blockers),
            'blockers': blockers,
        }

    def run(self, project: dict) -> dict:
        readiness = self.assess_readiness(project)
        if not readiness['ready']:
            raise ValueError('Final video requires every storyboard shot to finish rendering successfully')

        version = project.get('storyboard_version') or None
        shots = self.storyboard_repo.list_by_project(project['id'], version)
        latest_by_shot = {}
        for task in self.render_repo.list_by_project(project['id']):
            latest_by_shot[task['shot_id']] = task

        shot_files = [
            {
                'sequence': shot['sequence'],
                'path': latest_by_shot[shot['id']]['render_path'],
                'subtitle_text': shot.get('subtitle_text', ''),
                'dubbing_text': shot.get('dubbing_text', ''),
                'voiceover_text': shot.get('voiceover_text', ''),
                'voiceover_tone': shot.get('voiceover_tone', ''),
            }
            for shot in shots
        ]
        compose_options = {
            'enable_subtitles': bool(project.get('compose_enable_subtitles', True)),
            'enable_bgm': bool(project.get('compose_enable_bgm', True)),
            'enable_voiceover': bool(project.get('compose_enable_voiceover', True)),
            'enable_transitions': bool(project.get('compose_enable_transitions', True)),
            'bgm_path': project.get('final_bgm_path', ''),
        }
        version = int(project.get('final_video_version', 0)) + 1
        composed = self.composer.compose_video(shot_files, compose_options)
        storage_path = self.object_store.save_bytes(project['id'], f'final-video-v{version}.mp4', composed['bytes'], content_type='video/mp4')
        final_video = FinalVideo(
            project_id=project['id'],
            version=version,
            storage_path=storage_path,
            duration=composed['duration'],
            resolution=composed['resolution'],
            features=composed.get('features', []),
            bgm_source=composed.get('bgm_source', ''),
        ).to_dict()
        self.final_repo.save(final_video)
        project['final_video_version'] = version
        project['status'] = 'completed'
        project['current_stage'] = 'completed'
        self.project_repo.update(project)
        self.audit_service.record('compose.completed', project_id=project['id'], version=version)
        return final_video
