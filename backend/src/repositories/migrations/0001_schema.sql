CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    prompt TEXT NOT NULL,
    creator_id TEXT NOT NULL,
    status TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    scene_design_version INTEGER NOT NULL DEFAULT 0,
    storyboard_version INTEGER NOT NULL DEFAULT 0,
    final_video_version INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS scenes (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    input_prompt TEXT NOT NULL,
    scene_summary TEXT NOT NULL,
    scene_list_json TEXT NOT NULL,
    review_status TEXT NOT NULL,
    review_comment TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_scenes_project_version ON scenes(project_id, version);

CREATE TABLE IF NOT EXISTS storyboard_shots (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    duration INTEGER NOT NULL,
    description TEXT NOT NULL,
    subtitle_text TEXT NOT NULL,
    voiceover_text TEXT NOT NULL,
    subject_refs_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_storyboard_project_version ON storyboard_shots(project_id, version, sequence);

CREATE TABLE IF NOT EXISTS subjects (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    name TEXT NOT NULL,
    profile TEXT NOT NULL,
    image_path TEXT NOT NULL,
    image_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);

CREATE TABLE IF NOT EXISTS render_tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    shot_id TEXT NOT NULL,
    status TEXT NOT NULL,
    cache_key TEXT NOT NULL,
    cache_hit INTEGER NOT NULL DEFAULT 0,
    render_path TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id),
    FOREIGN KEY(shot_id) REFERENCES storyboard_shots(id)
);
CREATE INDEX IF NOT EXISTS idx_render_project_shot ON render_tasks(project_id, shot_id);

CREATE TABLE IF NOT EXISTS final_videos (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    storage_path TEXT NOT NULL,
    duration INTEGER NOT NULL,
    resolution TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES projects(id)
);
CREATE INDEX IF NOT EXISTS idx_final_video_project_version ON final_videos(project_id, version);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
