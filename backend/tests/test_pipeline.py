from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from backend.src.schemas.render_task import RenderTask
from backend.src.schemas.storyboard import StoryboardShot
from backend.src.schemas.subject_asset import SubjectAsset


class PipelineTestCase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        os.environ['APP_API_KEY'] = 'test-key'
        os.environ['APP_PORT'] = '18080'
        os.environ['FRONTEND_URL'] = 'http://127.0.0.1:3100'
        import importlib
        from backend.src.settings import config as config_module
        config_module.DATA_ROOT = Path(self.tempdir.name) / 'data'
        config_module.MEDIA_ROOT = config_module.DATA_ROOT / 'media'
        config_module.CACHE_ROOT = config_module.MEDIA_ROOT / 'cache'
        config_module.OBJECT_ROOT = config_module.MEDIA_ROOT / 'object_store'
        config_module.DB_ROOT = config_module.DATA_ROOT / 'db'
        config_module.LOG_ROOT = config_module.DATA_ROOT / 'logs'
        config_module.SQLITE_PATH = config_module.DB_ROOT / 'app.sqlite3'
        config_module.ensure_dirs()
        import backend.src.media.cache as cache_module
        import backend.src.media.object_store as object_store_module
        importlib.reload(cache_module)
        importlib.reload(object_store_module)
        self.ctx_module = importlib.import_module('backend.src.app_context')
        importlib.reload(self.ctx_module)
        self.ctx = self.ctx_module.AppContext()

    def tearDown(self):
        self.ctx.close()
        self.tempdir.cleanup()

    def test_full_pipeline(self):
        project = self.ctx.project_repo.create({
            'id': 'test-project',
            'name': 'Test Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'idea_submitted',
            'current_stage': 'idea_submitted',
            'scene_design_version': 0,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        self.ctx.scene_service.generate(project, project['prompt'])
        self.ctx.scene_service.review(project, 'approve')
        shots = self.ctx.storyboard_service.generate(project)
        self.assertTrue(shots)
        self.ctx.storyboard_service.review(project, 'approve')
        subjects = self.ctx.subject_pipeline.run(project)
        self.assertTrue(subjects)
        self.ctx.project_repo.update(project)
        renders = self.ctx.render_pipeline.run(project)
        self.assertEqual(len(renders), len(shots))
        readiness = self.ctx.compose_pipeline.assess_readiness(project)
        self.assertEqual(readiness['total_shots'], len(shots))

    def test_scene_design_generate_uses_project_scene_count(self):
        project = self.ctx.project_repo.create({
            'id': 'scene-count-project',
            'name': 'Scene Count Project',
            'prompt': '生成一个宣传视频',
            'scene_count': 5,
            'creator_id': 'tester',
            'status': 'idea_submitted',
            'current_stage': 'idea_submitted',
            'scene_design_version': 0,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        recorded = {}

        def fake_generate_scene_design(prompt, scene_count, model=None):
            recorded['scene_count'] = scene_count
            recorded['model'] = model
            return {
                'scene_summary': '五段场景摘要',
                'scene_list': [{'title': f'场景 {index}', 'description': f'描述 {index}'} for index in range(1, scene_count + 1)],
            }

        self.ctx.ai_gateway.generate_scene_design = fake_generate_scene_design
        result = self.ctx.scene_service.generate(project, project['prompt'])

        self.assertEqual(recorded['scene_count'], 5)
        self.assertEqual(recorded['model'], '')
        self.assertEqual(len(result['scene_list']), 5)

    def test_scene_settings_persist_count(self):
        project = self.ctx.project_repo.create({
            'id': 'scene-settings-project',
            'name': 'Scene Settings Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'idea_submitted',
            'current_stage': 'idea_submitted',
            'scene_design_version': 0,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        updated = self.ctx.scene_service.update_settings(project, {'scene_count': 7})
        stored = self.ctx.project_repo.get(project['id'])

        self.assertEqual(updated['scene_count'], 7)
        self.assertEqual(stored['scene_count'], 7)

    def test_storyboard_generate_passes_project_style(self):
        project = self.ctx.project_repo.create({
            'id': 'storyboard-generate-style-project',
            'name': 'Storyboard Generate Style Project',
            'prompt': '生成一个宣传视频',
            'storyboard_style': '未来科技感',
            'creator_id': 'tester',
            'status': 'scene_approved',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        self.ctx.scene_repo.save({
            'id': 'scene-style-1',
            'project_id': project['id'],
            'version': 1,
            'input_prompt': project['prompt'],
            'scene_summary': '摘要',
            'scene_list': [{'title': '场景一', 'description': '未来展厅内展示产品'}],
            'review_status': 'scene_approved',
            'review_comment': '',
            'created_at': 'now',
            'updated_at': 'now',
        })

        recorded = {}

        def fake_generate_storyboard(prompt, scenes, duration_limit, storyboard_style='', model=None):
            recorded['storyboard_style'] = storyboard_style
            recorded['model'] = model
            return [{
                'sequence': 1,
                'duration': 6,
                'shot_type': '全景',
                'camera_movement': '平稳推进',
                'scene_time': '夜晚',
                'background': '未来展厅内展示产品',
                'sound_effects': '电子氛围音',
                'action_direction': '镜头掠过展台并聚焦产品',
                'description': '产品在科技展厅中缓慢亮相',
                'subtitle_text': '科技感登场',
                'dubbing_text': '让产品在统一风格中保持完整表达。',
                'voiceover_text': '',
                'voiceover_tone': '冷静专业的男声',
                'subject_refs': ['主角'],
            }]

        self.ctx.ai_gateway.generate_storyboard = fake_generate_storyboard
        shots = self.ctx.storyboard_service.generate(project)

        self.assertEqual(recorded['storyboard_style'], '未来科技感')
        self.assertEqual(recorded['model'], '')
        self.assertEqual(len(shots), 1)

    def test_project_model_settings_persist(self):
        project = self.ctx.project_repo.create({
            'id': 'project-model-settings',
            'name': 'Project Model Settings',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'idea_submitted',
            'current_stage': 'idea_submitted',
            'scene_design_version': 0,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        from backend.src.api.app import Router
        from backend.src.api.routes.projects import register_project_routes

        router = Router()
        register_project_routes(router, self.ctx)
        handler, params = router.match('PUT', f"/api/projects/{project['id']}:settings")
        status, payload = handler({
            'method': 'PUT',
            'path': '',
            'query': {},
            'json': {
                'text_model': 'qwen2.5:14b',
                'image_model': 'wanx2.1-image',
                'video_model': 'wan2.7-t2v',
            },
            'context': {},
        }, params)

        self.assertEqual(status, 200)
        self.assertEqual(payload['item']['text_model'], 'qwen2.5:14b')
        self.assertEqual(payload['item']['image_model'], 'wanx2.1-image')
        self.assertEqual(payload['item']['video_model'], 'wan2.7-t2v')

    def test_compose_pipeline_creates_playable_mp4_when_render_outputs_are_mp4(self):
        project = self.ctx.project_repo.create({
            'id': 'compose-project',
            'name': 'Compose Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        clip_one = self._make_test_clip('red')
        clip_two = self._make_test_clip('blue')
        path_one = self.ctx.object_store.save_bytes(project['id'], 'shot-1.mp4', clip_one, content_type='video/mp4')
        path_two = self.ctx.object_store.save_bytes(project['id'], 'shot-2.mp4', clip_two, content_type='video/mp4')

        self.ctx.storyboard_repo.save(StoryboardShot(
            id='shot-1',
            project_id=project['id'],
            version=1,
            sequence=1,
            description='镜头一',
            subtitle_text='第一幕字幕',
            dubbing_text='第一幕配音',
            voiceover_text='',
            voiceover_tone='温暖自然的女声',
        ).to_dict())
        self.ctx.storyboard_repo.save(StoryboardShot(
            id='shot-2',
            project_id=project['id'],
            version=1,
            sequence=2,
            description='镜头二',
            subtitle_text='第二幕字幕',
            dubbing_text='第二幕配音',
            voiceover_text='',
            voiceover_tone='温暖自然的女声',
        ).to_dict())
        self.ctx.render_repo.save(RenderTask(project_id=project['id'], shot_id='shot-1', status='succeeded', render_path=path_one).to_dict())
        self.ctx.render_repo.save(RenderTask(project_id=project['id'], shot_id='shot-2', status='succeeded', render_path=path_two).to_dict())

        final_video = self.ctx.compose_pipeline.run(project)
        self.assertTrue(final_video['storage_path'].endswith('.mp4'))
        self.assertGreaterEqual(final_video['duration'], 1)

        relative = final_video['storage_path'].replace('fs/', '', 1)
        output_path = Path(self.tempdir.name) / 'data' / 'media' / 'object_store' / relative
        probe = subprocess.run(
            [
                'ffprobe',
                '-v',
                'error',
                '-show_entries',
                'format=duration:stream=codec_type',
                '-of',
                'json',
                str(output_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('"codec_type": "video"', probe.stdout)
        self.assertIn('"codec_type": "audio"', probe.stdout)

    def test_fallback_assets_use_text_extensions(self):
        project = self.ctx.project_repo.create({
            'id': 'fallback-project',
            'name': 'Fallback Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'idea_submitted',
            'current_stage': 'idea_submitted',
            'scene_design_version': 0,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        self.ctx.scene_service.generate(project, project['prompt'])
        self.ctx.scene_service.review(project, 'approve')
        shots = self.ctx.storyboard_service.generate(project)
        self.ctx.storyboard_service.review(project, 'approve')
        self.ctx.subject_pipeline.run(project)
        self.ctx.ai_gateway.submit_video = lambda *args, **kwargs: {
            'provider_url': None,
            'task_id': None,
            'raw': None,
            'model': 'fallback-video',
            'fallback_used': True,
            'diagnostic': {'provider': 'test', 'capability': 'video_generation', 'model': 'fallback-video', 'message': 'forced fallback'},
        }

        renders = self.ctx.render_pipeline.run(project, force=True)
        self.assertTrue(all(item['render_path'].endswith('.txt') for item in renders))

        readiness = self.ctx.compose_pipeline.assess_readiness(project)
        self.assertFalse(readiness['ready'])
        self.assertTrue(any(item['status'] == 'unplayable' for item in readiness['blockers']))

        with self.assertRaisesRegex(ValueError, 'requires every storyboard shot'):
            self.ctx.compose_pipeline.run(project)

    def test_render_submission_persists_provider_task_id_and_completes_after_poll(self):
        self.ctx.render_status_poller.stop()
        project = self.ctx.project_repo.create({
            'id': 'async-render-project',
            'name': 'Async Render Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(id='shot-async', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        self.ctx.storyboard_repo.save(shot)
        self.ctx.subject_repo.save(SubjectAsset(project_id=project['id'], name='主角', source_url='https://example.com/frame.png').to_dict())

        self.ctx.ai_gateway.submit_video = lambda *args, **kwargs: {
            'task_id': 'dash-task-1',
            'model': 'wan2.7-i2v',
            'status': 'submitted',
            'progress_message': '任务已提交，等待模型生成',
        }
        self.ctx.ai_gateway.poll_video_task = lambda task_id: {
            'task_id': task_id,
            'status': 'succeeded',
            'provider_url': 'https://example.com/video.mp4',
            'progress_message': '视频生成完成',
        }
        self.ctx.object_store.save_from_url = lambda project_id, name, url, content_type='video/mp4': self.ctx.object_store.save_bytes(
            project_id,
            name,
            self._make_test_clip('yellow'),
            content_type=content_type,
        )

        task = self.ctx.render_pipeline.render_shot(project, shot)
        self.assertEqual(task['status'], 'running')
        self.assertEqual(task['provider_task_id'], 'dash-task-1')
        self.assertEqual(task['render_path'], '')
        self.assertEqual(len(self.ctx.render_repo.list_active_provider_tasks()), 1)

        updated = self.ctx.render_pipeline.poll_render_task(task['id'])
        self.assertEqual(updated['status'], 'succeeded')
        self.assertTrue(updated['render_path'].endswith('.mp4'))
        self.assertEqual(updated['provider_task_id'], '')

    def test_shot_subject_upload_route_persists_shot_scope(self):
        project = self.ctx.project_repo.create({
            'id': 'shot-upload-project',
            'name': 'Shot Upload Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_generated',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(id='shot-upload-1', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        self.ctx.storyboard_repo.save(shot)

        from backend.src.api.app import Router
        from backend.src.api.routes.subjects import register_subject_routes

        router = Router()
        register_subject_routes(router, self.ctx)
        handler, params = router.match('POST', f"/api/projects/{project['id']}/subjects/shots/{shot['id']}:upload")
        status, payload = handler({
            'method': 'POST',
            'path': '',
            'query': {},
            'json': {
                'filename': 'first-frame.png',
                'content_type': 'image/png',
                'data_base64': 'ZmFrZS1wbmctYnl0ZXM=',
            },
            'context': {},
        }, params)

        self.assertEqual(status, 201)
        self.assertEqual(payload['item']['shot_id'], shot['id'])
        self.assertTrue(payload['item']['image_path'].endswith('.png'))
        self.assertIn('/media/', payload['item']['source_url'])

        stored = self.ctx.subject_repo.get_latest_by_shot(project['id'], shot['id'])
        self.assertIsNotNone(stored)
        self.assertEqual(stored['shot_id'], shot['id'])
        self.assertEqual(stored['name'], '镜头 1')

    def test_shot_subject_generate_route_creates_shot_scoped_asset(self):
        project = self.ctx.project_repo.create({
            'id': 'shot-generate-project',
            'name': 'Shot Generate Project',
            'prompt': '生成一个宣传视频',
            'storyboard_style': '电影感写实',
            'image_model': 'wanx2.1-image',
            'creator_id': 'tester',
            'status': 'storyboard_generated',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(
            id='shot-generate-1',
            project_id=project['id'],
            version=1,
            sequence=1,
            description='镜头一',
            background='城市街景',
            shot_type='中景',
            subject_refs=['主角'],
        ).to_dict()
        self.ctx.storyboard_repo.save(shot)

        captured = {}
        self.ctx.ai_gateway.generate_subject_image = lambda subject_name, profile, style_prompt, model=None: (
            captured.update({'subject_name': subject_name, 'profile': profile, 'style_prompt': style_prompt, 'model': model}) or
            {'provider_url': 'https://example.com/shot-subject.png'}
        )
        self.ctx.object_store.save_from_url = lambda project_id, name, url, content_type='image/png': self.ctx.object_store.save_bytes(
            project_id,
            name,
            b'fake-shot-generated-image',
            content_type=content_type,
        )

        from backend.src.api.app import Router
        from backend.src.api.routes.subjects import register_subject_routes

        router = Router()
        register_subject_routes(router, self.ctx)
        handler, params = router.match('POST', f"/api/projects/{project['id']}/subjects/shots/{shot['id']}:generate")
        status, payload = handler({
            'method': 'POST',
            'path': '',
            'query': {},
            'json': {'mode': 'generate'},
            'context': {},
        }, params)

        self.assertEqual(status, 201)
        self.assertEqual(payload['item']['shot_id'], shot['id'])
        self.assertTrue(payload['item']['image_path'].endswith('.png'))
        self.assertEqual(payload['item']['profile'], '镜头直接生成主体图')
        self.assertEqual(captured['subject_name'], '主角')
        self.assertEqual(captured['model'], 'wanx2.1-image')
        self.assertIn('统一风格：电影感写实', captured['style_prompt'])

    def test_shot_subject_generate_route_can_use_previous_shot_tail_frame(self):
        project = self.ctx.project_repo.create({
            'id': 'shot-tail-frame-project',
            'name': 'Shot Tail Frame Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_generated',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        previous_shot = StoryboardShot(id='shot-prev', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        current_shot = StoryboardShot(id='shot-next', project_id=project['id'], version=1, sequence=2, description='镜头二').to_dict()
        self.ctx.storyboard_repo.save(previous_shot)
        self.ctx.storyboard_repo.save(current_shot)

        clip = self._make_test_clip('orange')
        render_path = self.ctx.object_store.save_bytes(project['id'], 'shot-prev.mp4', clip, content_type='video/mp4')
        self.ctx.render_repo.save(RenderTask(project_id=project['id'], shot_id=previous_shot['id'], status='succeeded', render_path=render_path).to_dict())

        from backend.src.api.app import Router
        from backend.src.api.routes.subjects import register_subject_routes

        router = Router()
        register_subject_routes(router, self.ctx)
        handler, params = router.match('POST', f"/api/projects/{project['id']}/subjects/shots/{current_shot['id']}:generate")
        status, payload = handler({
            'method': 'POST',
            'path': '',
            'query': {},
            'json': {'mode': 'previous_tail_frame'},
            'context': {},
        }, params)

        self.assertEqual(status, 201)
        self.assertEqual(payload['item']['shot_id'], current_shot['id'])
        self.assertTrue(payload['item']['image_path'].endswith('.png'))
        self.assertIn('上一镜头尾帧', payload['item']['profile'])
        self.assertGreater(len(self.ctx.object_store.read_bytes(payload['item']['image_path'])), 0)
        stored = self.ctx.subject_repo.get_latest_by_shot(project['id'], current_shot['id'])
        self.assertEqual(stored['shot_id'], current_shot['id'])

    def test_render_prefers_shot_scoped_subject_asset(self):
        project = self.ctx.project_repo.create({
            'id': 'shot-scoped-render-project',
            'name': 'Shot Scoped Render Project',
            'prompt': '生成一个宣传视频',
            'storyboard_style': '高级广告片',
            'video_model': 'wan2.7-t2v',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(id='shot-scoped-1', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        self.ctx.storyboard_repo.save(shot)
        self.ctx.subject_repo.save(SubjectAsset(project_id=project['id'], name='主角', source_url='https://example.com/global.png', image_version=1).to_dict())
        storage_path = self.ctx.object_store.save_bytes(
            project['id'],
            'shot-1-subject.png',
            b'fake-png-bytes',
            content_type='image/png',
        )
        self.ctx.subject_repo.save(SubjectAsset(project_id=project['id'], shot_id=shot['id'], name='镜头 1', image_path=storage_path, image_version=2).to_dict())

        captured = {}

        def fake_submit_video(prompt, duration, first_frame_url=None, model=None):
            captured['prompt'] = prompt
            captured['duration'] = duration
            captured['first_frame_url'] = first_frame_url
            captured['model'] = model
            return {
                'provider_url': None,
                'task_id': None,
                'raw': None,
                'model': 'fallback-video',
                'fallback_used': True,
                'diagnostic': {'provider': 'test', 'capability': 'video_generation', 'model': 'fallback-video', 'message': 'forced fallback'},
            }

        self.ctx.ai_gateway.submit_video = fake_submit_video
        self.ctx.render_pipeline.render_shot(project, shot, force=True)

        self.assertTrue(captured['first_frame_url'].startswith('data:image/png;base64,'))
        self.assertNotEqual(captured['first_frame_url'], 'https://example.com/global.png')
        self.assertIn('统一风格：高级广告片；', captured['prompt'])
        self.assertEqual(captured['model'], 'wan2.7-t2v')

    def test_render_skips_non_image_shot_asset_and_uses_valid_source_url(self):
        project = self.ctx.project_repo.create({
            'id': 'shot-scoped-invalid-asset-project',
            'name': 'Shot Scoped Invalid Asset Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(id='shot-invalid-asset-1', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        self.ctx.storyboard_repo.save(shot)

        invalid_path = self.ctx.object_store.save_text(project['id'], 'shot-1-subject-v1.txt', 'not-an-image')
        self.ctx.subject_repo.save(SubjectAsset(
            project_id=project['id'],
            shot_id=shot['id'],
            name='镜头 1',
            image_path=invalid_path,
            image_version=1,
        ).to_dict())
        self.ctx.subject_repo.save(SubjectAsset(
            project_id=project['id'],
            shot_id=shot['id'],
            name='镜头 1',
            source_url='https://example.com/shot-1.png',
            image_version=2,
        ).to_dict())

        captured = {}

        def fake_submit_video(prompt, duration, first_frame_url=None, model=None):
            captured['first_frame_url'] = first_frame_url
            return {
                'provider_url': None,
                'task_id': None,
                'raw': None,
                'model': 'fallback-video',
                'fallback_used': True,
                'diagnostic': {'provider': 'test', 'capability': 'video_generation', 'model': 'fallback-video', 'message': 'forced fallback'},
            }

        self.ctx.ai_gateway.submit_video = fake_submit_video
        self.ctx.render_pipeline.render_shot(project, shot, force=True)

        self.assertEqual(captured['first_frame_url'], 'https://example.com/shot-1.png')

    def test_manual_render_status_query_polls_provider_and_updates_task(self):
        self.ctx.render_status_poller.stop()
        project = self.ctx.project_repo.create({
            'id': 'manual-query-project',
            'name': 'Manual Query Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(id='shot-query', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        self.ctx.storyboard_repo.save(shot)
        self.ctx.subject_repo.save(SubjectAsset(project_id=project['id'], name='主角', source_url='https://example.com/frame.png').to_dict())

        self.ctx.ai_gateway.submit_video = lambda *args, **kwargs: {
            'task_id': 'dash-task-2',
            'model': 'wan2.7-i2v',
            'status': 'submitted',
            'progress_message': '任务已提交，等待模型生成',
        }
        self.ctx.ai_gateway.poll_video_task = lambda task_id: {
            'task_id': task_id,
            'status': 'succeeded',
            'provider_url': 'https://example.com/video.mp4',
            'progress_message': '视频生成完成',
        }
        self.ctx.object_store.save_from_url = lambda project_id, name, url, content_type='video/mp4': self.ctx.object_store.save_bytes(
            project_id,
            name,
            self._make_test_clip('purple'),
            content_type=content_type,
        )

        task = self.ctx.render_pipeline.render_shot(project, shot)

        from backend.src.api.app import Router
        from backend.src.api.routes.renders import register_render_routes

        router = Router()
        register_render_routes(router, self.ctx)
        handler, params = router.match('GET', f"/api/projects/{project['id']}/renders/shots/{shot['id']}")
        status, payload = handler({'method': 'GET', 'path': '', 'query': {}, 'json': {}, 'context': {}}, params)

        self.assertEqual(status, 200)
        self.assertEqual(payload['item']['status'], 'succeeded')
        self.assertTrue(payload['item']['render_path'].endswith('.mp4'))
        self.assertNotEqual(payload['item']['last_polled_at'], '')

        refreshed = self.ctx.render_repo.get(task['id'])
        self.assertEqual(refreshed['status'], 'succeeded')

    def test_render_dispatch_submits_each_shot_as_separate_worker_task(self):
        project = self.ctx.project_repo.create({
            'id': 'dispatch-project',
            'name': 'Dispatch Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        self.ctx.storyboard_repo.save(StoryboardShot(id='shot-dispatch-1', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict())
        self.ctx.storyboard_repo.save(StoryboardShot(id='shot-dispatch-2', project_id=project['id'], version=1, sequence=2, description='镜头二').to_dict())

        import backend.src.orchestrators.render_pipeline as render_pipeline_module

        scheduled = []
        original_submit_task = render_pipeline_module.submit_task
        try:
            render_pipeline_module.submit_task = lambda func, *args, **kwargs: scheduled.append((func, args, kwargs)) or {'queued': True}
            futures = self.ctx.render_pipeline.dispatch(project, force=True)
        finally:
            render_pipeline_module.submit_task = original_submit_task

        self.assertEqual(len(futures), 2)
        self.assertEqual(len(scheduled), 2)
        self.assertEqual([item[1][1]['id'] for item in scheduled], ['shot-dispatch-1', 'shot-dispatch-2'])
        refreshed_project = self.ctx.project_repo.get(project['id'])
        self.assertEqual(refreshed_project['status'], 'renders_running')

    def test_final_video_settings_route_and_bgm_upload_persist_on_project(self):
        project = self.ctx.project_repo.create({
            'id': 'compose-settings-project',
            'name': 'Compose Settings Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        from backend.src.api.app import Router
        from backend.src.api.routes.final_video import register_final_video_routes

        router = Router()
        register_final_video_routes(router, self.ctx)

        handler, params = router.match('PUT', f"/api/projects/{project['id']}/final-video:settings")
        status, payload = handler({
            'method': 'PUT',
            'path': '',
            'query': {},
            'json': {
                'compose_enable_subtitles': False,
                'compose_enable_voiceover': False,
                'compose_enable_bgm': True,
                'compose_enable_transitions': False,
            },
            'context': {},
        }, params)
        self.assertEqual(status, 200)
        self.assertFalse(payload['item']['compose_enable_subtitles'])
        self.assertFalse(payload['item']['compose_enable_voiceover'])
        self.assertFalse(payload['item']['compose_enable_transitions'])

        upload_handler, upload_params = router.match('POST', f"/api/projects/{project['id']}/final-video/bgm:upload")
        upload_status, upload_payload = upload_handler({
            'method': 'POST',
            'path': '',
            'query': {},
            'json': {
                'filename': 'bgm.m4a',
                'content_type': 'audio/mp4',
                'data_base64': 'ZmFrZS1iZ20=',
            },
            'context': {},
        }, upload_params)
        self.assertEqual(upload_status, 201)
        self.assertTrue(upload_payload['item']['final_bgm_path'].endswith('.m4a'))

        refreshed = self.ctx.project_repo.get(project['id'])
        self.assertFalse(refreshed['compose_enable_subtitles'])
        self.assertFalse(refreshed['compose_enable_voiceover'])
        self.assertFalse(refreshed['compose_enable_transitions'])
        self.assertTrue(refreshed['compose_enable_bgm'])
        self.assertTrue(refreshed['final_bgm_path'].endswith('.m4a'))

        clear_handler, clear_params = router.match('POST', f"/api/projects/{project['id']}/final-video/bgm:clear")
        clear_status, clear_payload = clear_handler({
            'method': 'POST',
            'path': '',
            'query': {},
            'json': {},
            'context': {},
        }, clear_params)
        self.assertEqual(clear_status, 200)
        self.assertEqual(clear_payload['item']['final_bgm_path'], '')

    def test_compose_pipeline_uses_project_level_compose_options(self):
        project = self.ctx.project_repo.create({
            'id': 'compose-options-project',
            'name': 'Compose Options Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'final_bgm_path': 'fs/compose-options-project/project-bgm.m4a',
            'compose_enable_subtitles': False,
            'compose_enable_bgm': True,
            'compose_enable_voiceover': False,
            'compose_enable_transitions': False,
            'created_at': 'now',
            'updated_at': 'now',
        })
        path_one = self.ctx.object_store.save_bytes(project['id'], 'shot-1.mp4', self._make_test_clip('orange'), content_type='video/mp4')
        self.ctx.storyboard_repo.save(StoryboardShot(id='compose-options-shot', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict())
        self.ctx.render_repo.save(RenderTask(project_id=project['id'], shot_id='compose-options-shot', status='succeeded', render_path=path_one).to_dict())

        captured = {}
        original_compose = self.ctx.compose_pipeline.composer.compose_video
        self.ctx.compose_pipeline.composer.compose_video = lambda shot_files, options=None: captured.update({
            'shot_files': shot_files,
            'options': options,
        }) or {
            'bytes': self._make_test_clip('black'),
            'duration': 1,
            'resolution': '320x240',
        }
        try:
            self.ctx.compose_pipeline.run(project)
        finally:
            self.ctx.compose_pipeline.composer.compose_video = original_compose

        self.assertFalse(captured['options']['enable_subtitles'])
        self.assertFalse(captured['options']['enable_voiceover'])
        self.assertFalse(captured['options']['enable_transitions'])
        self.assertTrue(captured['options']['enable_bgm'])
        self.assertEqual(captured['options']['bgm_path'], 'fs/compose-options-project/project-bgm.m4a')

    def test_final_video_repository_persists_features_and_bgm_source(self):
        self.ctx.project_repo.create({
            'id': 'meta-project',
            'name': 'Meta Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'completed',
            'current_stage': 'completed',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 1,
            'created_at': 'now',
            'updated_at': 'now',
        })
        record = self.ctx.final_repo.save({
            'id': 'final-video-meta',
            'project_id': 'meta-project',
            'version': 1,
            'storage_path': 'fs/meta-project/final-video-v1.mp4',
            'duration': 12,
            'resolution': '1280x720',
            'features': ['subtitles', 'background_music'],
            'bgm_source': 'custom',
            'created_at': 'now',
            'updated_at': 'now',
        })
        self.assertEqual(record['bgm_source'], 'custom')

        latest = self.ctx.final_repo.latest('meta-project')
        self.assertEqual(latest['features'], ['subtitles', 'background_music'])
        self.assertEqual(latest['bgm_source'], 'custom')

    def test_storyboard_update_persists_extended_shot_fields(self):
        project = self.ctx.project_repo.create({
            'id': 'storyboard-fields-project',
            'name': 'Storyboard Fields Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_generated',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(id='shot-fields', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        self.ctx.storyboard_repo.save(shot)

        updated = self.ctx.storyboard_service.update_shot(project, 'shot-fields', {
            'sequence': 2,
            'duration': 8,
            'shot_type': '特写',
            'camera_movement': '缓慢推进',
            'scene_time': '黄昏',
            'background': '海边栈道与金色天空',
            'sound_effects': '海浪声与轻柔钢琴',
            'action_direction': '主角转身看向镜头并抬手示意',
            'description': '在海边栈道上展示产品细节',
            'subtitle_text': '把灵感留在海风里',
            'dubbing_text': '当灵感涌现，创作也能一气呵成。',
            'voiceover_text': '',
            'voiceover_tone': '温暖坚定的女声',
        })

        self.assertEqual(updated['shot_type'], '特写')
        self.assertEqual(updated['camera_movement'], '缓慢推进')
        self.assertEqual(updated['scene_time'], '黄昏')
        self.assertEqual(updated['background'], '海边栈道与金色天空')
        self.assertEqual(updated['sound_effects'], '海浪声与轻柔钢琴')
        self.assertEqual(updated['action_direction'], '主角转身看向镜头并抬手示意')
        self.assertEqual(updated['voiceover_tone'], '温暖坚定的女声')

        stored = self.ctx.storyboard_repo.get('shot-fields')
        self.assertEqual(stored['sequence'], 2)
        self.assertEqual(stored['duration'], 8)
        self.assertEqual(stored['subtitle_text'], '把灵感留在海风里')
        self.assertEqual(stored['dubbing_text'], '当灵感涌现，创作也能一气呵成。')

    def test_storyboard_regenerate_shot_replaces_detail_fields(self):
        project = self.ctx.project_repo.create({
            'id': 'storyboard-regenerate-project',
            'name': 'Storyboard Regenerate Project',
            'prompt': '生成一个宣传视频',
            'storyboard_style': '电影感写实',
            'creator_id': 'tester',
            'status': 'storyboard_generated',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        self.ctx.scene_repo.save({
            'id': 'scene-1',
            'project_id': project['id'],
            'version': 1,
            'input_prompt': project['prompt'],
            'scene_summary': '摘要',
            'scene_list': [{'title': '场景一', 'description': '阳光下的街道场景'}],
            'review_status': 'scene_approved',
            'review_comment': '',
            'created_at': 'now',
            'updated_at': 'now',
        })
        self.ctx.storyboard_repo.save(StoryboardShot(
            id='shot-regenerate',
            project_id=project['id'],
            version=1,
            sequence=1,
            duration=6,
            description='旧描述',
            subtitle_text='旧字幕',
            dubbing_text='旧配音',
            voiceover_text='旧旁白',
            shot_type='中景',
            camera_movement='固定',
            scene_time='白天',
            background='旧背景',
            sound_effects='旧音效',
            action_direction='旧动作',
            voiceover_tone='旧音色',
        ).to_dict())

        recorded = {}

        def fake_generate_storyboard(prompt, scenes, duration_limit, storyboard_style='', model=None):
            recorded['storyboard_style'] = storyboard_style
            recorded['model'] = model
            return [{
                'sequence': 1,
                'duration': 9,
                'shot_type': '特写',
                'camera_movement': '快速推进',
                'scene_time': '黄昏',
                'background': '金色街道与逆光人群',
                'sound_effects': '风声与节奏鼓点',
                'action_direction': '主角回头看向镜头后向前奔跑',
                'description': '主角在街道中穿行并展示产品',
                'subtitle_text': '追上灵感出现的那一刻',
                'dubbing_text': '每一次灵感出现，都值得被及时捕捉。',
                'voiceover_text': '',
                'voiceover_tone': '明亮有力的男声',
                'subject_refs': ['主角'],
            }]

        self.ctx.ai_gateway.generate_storyboard = fake_generate_storyboard

        regenerated = self.ctx.storyboard_service.regenerate_shot(project, 'shot-regenerate')
        self.assertEqual(regenerated['shot_type'], '特写')
        self.assertEqual(regenerated['camera_movement'], '快速推进')
        self.assertEqual(regenerated['background'], '金色街道与逆光人群')
        self.assertEqual(regenerated['subtitle_text'], '追上灵感出现的那一刻')
        self.assertEqual(regenerated['dubbing_text'], '每一次灵感出现，都值得被及时捕捉。')
        self.assertEqual(recorded['storyboard_style'], '电影感写实')
        self.assertEqual(recorded['model'], '')

    def test_storyboard_settings_persist_style(self):
        project = self.ctx.project_repo.create({
            'id': 'storyboard-style-project',
            'name': 'Storyboard Style Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'scene_approved',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        updated = self.ctx.storyboard_service.update_settings(project, {'storyboard_style': '高级广告片'})
        stored = self.ctx.project_repo.get(project['id'])

        self.assertEqual(updated['storyboard_style'], '高级广告片')
        self.assertEqual(stored['storyboard_style'], '高级广告片')

    def test_scene_and_storyboard_use_project_text_model(self):
        project = self.ctx.project_repo.create({
            'id': 'project-text-model',
            'name': 'Project Text Model',
            'prompt': '生成一个宣传视频',
            'text_model': 'qwen2.5:32b',
            'creator_id': 'tester',
            'status': 'idea_submitted',
            'current_stage': 'idea_submitted',
            'scene_design_version': 0,
            'storyboard_version': 0,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        recorded = {'scene': None, 'storyboard': None}

        def fake_generate_scene_design(prompt, scene_count, model=None):
            recorded['scene'] = model
            return {
                'scene_summary': '摘要',
                'scene_list': [{'title': '场景一', 'description': '场景描述'}],
            }

        def fake_generate_storyboard(prompt, scenes, duration_limit, storyboard_style='', model=None):
            recorded['storyboard'] = model
            return [{
                'sequence': 1,
                'duration': 6,
                'shot_type': '中景',
                'camera_movement': '缓慢推进',
                'scene_time': '白天',
                'background': '场景描述',
                'sound_effects': '环境声',
                'action_direction': '主体出镜',
                'description': '镜头描述',
                'subtitle_text': '字幕',
                'dubbing_text': '配音',
                'voiceover_text': '',
                'voiceover_tone': '温暖女声',
                'subject_refs': ['主角'],
            }]

        self.ctx.ai_gateway.generate_scene_design = fake_generate_scene_design
        self.ctx.ai_gateway.generate_storyboard = fake_generate_storyboard

        self.ctx.scene_service.generate(project, project['prompt'])
        self.ctx.scene_service.review(project, 'approve')
        self.ctx.storyboard_service.generate(project)

        self.assertEqual(recorded['scene'], 'qwen2.5:32b')
        self.assertEqual(recorded['storyboard'], 'qwen2.5:32b')

    def test_storyboard_allows_empty_voiceover_but_requires_dubbing(self):
        project = self.ctx.project_repo.create({
            'id': 'storyboard-voiceover-optional-project',
            'name': 'Storyboard Voiceover Optional Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_generated',
            'current_stage': 'storyboard_reviewing',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })
        shot = StoryboardShot(id='shot-optional-voiceover', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict()
        self.ctx.storyboard_repo.save(shot)

        updated = self.ctx.storyboard_service.update_shot(project, 'shot-optional-voiceover', {
            'sequence': 1,
            'duration': 6,
            'shot_type': '中景',
            'camera_movement': '缓慢推进',
            'scene_time': '白天',
            'background': '办公室与产品陈列桌',
            'sound_effects': '轻柔环境声',
            'action_direction': '主角走向桌面并拿起产品',
            'description': '展示产品的近距离使用过程',
            'subtitle_text': '把流程简化到一步',
            'dubbing_text': '现在开始，只保留真正重要的表达。',
            'voiceover_text': '',
            'voiceover_tone': '温暖自然的女声',
        })
        self.assertEqual(updated['voiceover_text'], '')

        with self.assertRaisesRegex(ValueError, 'Dubbing is required'):
            self.ctx.storyboard_service.update_shot(project, 'shot-optional-voiceover', {
                'sequence': 1,
                'duration': 6,
                'shot_type': '中景',
                'camera_movement': '缓慢推进',
                'scene_time': '白天',
                'background': '办公室与产品陈列桌',
                'sound_effects': '轻柔环境声',
                'action_direction': '主角走向桌面并拿起产品',
                'description': '展示产品的近距离使用过程',
                'subtitle_text': '把流程简化到一步',
                'dubbing_text': '',
                'voiceover_text': '',
                'voiceover_tone': '温暖自然的女声',
            })

    def test_compose_requires_all_storyboard_shots_rendered(self):
        project = self.ctx.project_repo.create({
            'id': 'strict-compose-project',
            'name': 'Strict Compose Project',
            'prompt': '生成一个宣传视频',
            'creator_id': 'tester',
            'status': 'storyboard_approved',
            'current_stage': 'storyboard_approved',
            'scene_design_version': 1,
            'storyboard_version': 1,
            'final_video_version': 0,
            'created_at': 'now',
            'updated_at': 'now',
        })

        self.ctx.storyboard_repo.save(StoryboardShot(id='shot-a', project_id=project['id'], version=1, sequence=1, description='镜头一').to_dict())
        self.ctx.storyboard_repo.save(StoryboardShot(id='shot-b', project_id=project['id'], version=1, sequence=2, description='镜头二').to_dict())

        clip_one = self._make_test_clip('green')
        path_one = self.ctx.object_store.save_bytes(project['id'], 'shot-a.mp4', clip_one, content_type='video/mp4')
        self.ctx.render_repo.save(RenderTask(project_id=project['id'], shot_id='shot-a', status='succeeded', render_path=path_one).to_dict())
        self.ctx.render_repo.save(RenderTask(project_id=project['id'], shot_id='shot-b', status='running').to_dict())

        readiness = self.ctx.compose_pipeline.assess_readiness(project)
        self.assertFalse(readiness['ready'])
        self.assertEqual(readiness['blockers'][0]['sequence'], 2)

        with self.assertRaisesRegex(ValueError, 'requires every storyboard shot'):
            self.ctx.compose_pipeline.run(project)

    def _make_test_clip(self, color: str) -> bytes:
        output = Path(self.tempdir.name) / f'{color}.mp4'
        subprocess.run(
            [
                'ffmpeg',
                '-y',
                '-loglevel',
                'error',
                '-f',
                'lavfi',
                '-i',
                f'color=c={color}:s=320x240:d=1.2:r=24',
                '-f',
                'lavfi',
                '-i',
                'anullsrc=channel_layout=stereo:sample_rate=44100',
                '-shortest',
                '-c:v',
                'libx264',
                '-pix_fmt',
                'yuv420p',
                '-c:a',
                'aac',
                str(output),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return output.read_bytes()


if __name__ == '__main__':
    unittest.main()
