ALTER TABLE subjects ADD COLUMN shot_id TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_subjects_project_shot ON subjects(project_id, shot_id, image_version);
