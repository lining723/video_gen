ALTER TABLE storyboard_shots ADD COLUMN shot_type TEXT NOT NULL DEFAULT '';
ALTER TABLE storyboard_shots ADD COLUMN camera_movement TEXT NOT NULL DEFAULT '';
ALTER TABLE storyboard_shots ADD COLUMN scene_time TEXT NOT NULL DEFAULT '';
ALTER TABLE storyboard_shots ADD COLUMN background TEXT NOT NULL DEFAULT '';
ALTER TABLE storyboard_shots ADD COLUMN sound_effects TEXT NOT NULL DEFAULT '';
ALTER TABLE storyboard_shots ADD COLUMN action_direction TEXT NOT NULL DEFAULT '';
ALTER TABLE storyboard_shots ADD COLUMN voiceover_tone TEXT NOT NULL DEFAULT '';
