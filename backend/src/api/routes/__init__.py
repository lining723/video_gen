from __future__ import annotations

from .projects import register_project_routes
from .scene_design import register_scene_routes
from .storyboard import register_storyboard_routes
from .subjects import register_subject_routes
from .renders import register_render_routes
from .final_video import register_final_video_routes
from .project_timeline import register_timeline_routes
from .keyframes import register_keyframe_routes


def register_all(router, context) -> None:
    register_project_routes(router, context)
    register_scene_routes(router, context)
    register_storyboard_routes(router, context)
    register_subject_routes(router, context)
    register_render_routes(router, context)
    register_final_video_routes(router, context)
    register_timeline_routes(router, context)
    register_keyframe_routes(router, context)
