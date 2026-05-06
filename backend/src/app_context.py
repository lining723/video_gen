from __future__ import annotations

from backend.src.integrations import AIGateway
from backend.src.integrations.video_provider_registry import VideoProviderRegistry
from backend.src.integrations.providers.dashscope_provider import DashScopeVideoProvider
from backend.src.integrations.dashscope_client import DashScopeClient
from backend.src.media.asset_normalizer import normalize_filesystem_media_paths
from backend.src.media.cache import CacheStore
from backend.src.media.object_store import ObjectStore
from backend.src.orchestrators.compose_pipeline import ComposePipeline
from backend.src.orchestrators.keyframe_pipeline import KeyframePipeline
from backend.src.orchestrators.render_pipeline import RenderPipeline
from backend.src.orchestrators.subject_pipeline import SubjectPipeline
from backend.src.repositories.db import SQLiteDatabase
from backend.src.repositories.final_video_repository import FinalVideoRepository
from backend.src.repositories.keyframe_repository import KeyframeRepository
from backend.src.repositories.project_repository import ProjectRepository
from backend.src.repositories.render_repository import RenderRepository
from backend.src.repositories.scene_repository import SceneRepository
from backend.src.repositories.storyboard_repository import StoryboardRepository
from backend.src.repositories.subject_repository import SubjectRepository
from backend.src.services.audit_service import AuditService
from backend.src.services.project_timeline_service import ProjectTimelineService
from backend.src.services.render_status_poller import RenderStatusPoller
from backend.src.services.scene_design_service import SceneDesignService
from backend.src.services.storyboard_service import StoryboardService
from backend.src.settings.config import OBJECT_ROOT, settings


class AppContext:
    def __init__(self) -> None:
        db = SQLiteDatabase()
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.scene_repo = SceneRepository(db)
        self.storyboard_repo = StoryboardRepository(db)
        self.subject_repo = SubjectRepository(db)
        self.render_repo = RenderRepository(db)
        self.final_repo = FinalVideoRepository(db)
        self.keyframe_repo = KeyframeRepository(db)
        self.audit_service = AuditService()
        self.object_store = ObjectStore()
        if settings.object_store_provider == 'filesystem':
            normalize_filesystem_media_paths(db, OBJECT_ROOT)
        self.cache_store = CacheStore()

        # 初始化视频提供商注册中心
        self.video_provider_registry = self._init_video_provider_registry()

        self.ai_gateway = AIGateway(video_provider_registry=self.video_provider_registry)
        self.scene_service = SceneDesignService(
            self.project_repo,
            self.scene_repo,
            self.audit_service,
            self.ai_gateway,
            settings.scene_max_shots,
        )
        self.storyboard_service = StoryboardService(
            self.project_repo,
            self.scene_repo,
            self.storyboard_repo,
            self.audit_service,
            self.ai_gateway,
            settings.shot_duration_limit,
        )
        self.subject_pipeline = SubjectPipeline(
            self.storyboard_repo,
            self.subject_repo,
            self.object_store,
            self.audit_service,
            self.ai_gateway,
        )
        self.keyframe_pipeline = KeyframePipeline(
            self.storyboard_repo,
            self.subject_repo,
            self.keyframe_repo,
            self.object_store,
            self.audit_service,
            self.ai_gateway,
            cache_store=self.cache_store,
        )
        self.render_pipeline = RenderPipeline(
            self.storyboard_repo,
            self.subject_repo,
            self.render_repo,
            self.cache_store,
            self.object_store,
            self.project_repo,
            self.audit_service,
            self.ai_gateway,
        )
        self.render_status_poller = RenderStatusPoller(
            self.render_repo,
            self.render_pipeline,
            interval_seconds=settings.render_status_poll_interval,
        )
        self.compose_pipeline = ComposePipeline(
            self.storyboard_repo,
            self.render_repo,
            self.final_repo,
            self.object_store,
            self.project_repo,
            self.audit_service,
        )
        self.timeline_service = ProjectTimelineService(
            self.project_repo,
            self.scene_repo,
            self.storyboard_repo,
            self.subject_repo,
            self.render_repo,
            self.final_repo,
        )
        self.render_status_poller.start()

    def _init_video_provider_registry(self) -> VideoProviderRegistry:
        """初始化视频提供商注册中心"""
        registry = VideoProviderRegistry()

        # 注册 DashScope 提供商
        dashscope_client = DashScopeClient(
            base_url=settings.dashscope_base_url,
            api_key=settings.dashscope_api_key,
            image_model=settings.dashscope_image_model,
            video_model=settings.dashscope_video_model,
            timeout=settings.dashscope_timeout,
            poll_interval=settings.dashscope_poll_interval,
            poll_timeout=settings.dashscope_poll_timeout,
        )
        dashscope_provider = DashScopeVideoProvider(
            client=dashscope_client,
            models=settings.get_dashscope_video_models(),
            enabled=True,
        )
        registry.register(dashscope_provider)

        # 设置默认模型
        registry.set_default_model(settings.default_video_model)

        return registry

    def close(self) -> None:
        self.render_status_poller.stop()
