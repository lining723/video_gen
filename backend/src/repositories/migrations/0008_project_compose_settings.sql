ALTER TABLE projects ADD COLUMN final_bgm_path TEXT NOT NULL DEFAULT '';
ALTER TABLE projects ADD COLUMN compose_enable_subtitles INTEGER NOT NULL DEFAULT 1;
ALTER TABLE projects ADD COLUMN compose_enable_bgm INTEGER NOT NULL DEFAULT 1;
ALTER TABLE projects ADD COLUMN compose_enable_voiceover INTEGER NOT NULL DEFAULT 1;
ALTER TABLE projects ADD COLUMN compose_enable_transitions INTEGER NOT NULL DEFAULT 1;
