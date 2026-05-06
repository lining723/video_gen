ALTER TABLE final_videos ADD COLUMN features_json TEXT NOT NULL DEFAULT '[]';
ALTER TABLE final_videos ADD COLUMN bgm_source TEXT NOT NULL DEFAULT '';
