PROJECT_STATES = {
    "idea_submitted",
    "scene_generated",
    "scene_reviewing",
    "scene_approved",
    "storyboard_generated",
    "storyboard_reviewing",
    "storyboard_approved",
    "subject_generating",
    "keyframe_generating",  # 新增：关键帧生成中
    "subject_ready",
    "video_rendering",
    "video_render_partial_failed",
    "compositing",
    "completed",
    "failed",
}

REVIEW_ACTIONS = {"approve", "reject", "regenerate"}
RENDER_STATES = {"queued", "running", "succeeded", "failed"}
