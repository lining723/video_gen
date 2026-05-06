-- 创建关键帧网格表
CREATE TABLE IF NOT EXISTS keyframe_grids (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    shot_id TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    grid_type TEXT DEFAULT '3x3' CHECK (grid_type IN ('2x2', '3x3', '4x4')),
    frame_count INTEGER DEFAULT 9 CHECK (frame_count IN (4, 9, 16)),
    frames TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    source_model TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (shot_id) REFERENCES storyboard_shots(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_keyframe_project ON keyframe_grids(project_id);
CREATE INDEX IF NOT EXISTS idx_keyframe_shot ON keyframe_grids(shot_id);

-- 创建唯一约束（每个镜头只能有一个关键帧网格）
CREATE UNIQUE INDEX IF NOT EXISTS idx_keyframe_shot_unique ON keyframe_grids(shot_id);
