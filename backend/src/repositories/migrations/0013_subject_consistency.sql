-- Subject consistency control: extend subjects table with feature description and variant fields
ALTER TABLE subjects ADD COLUMN feature_description TEXT NOT NULL DEFAULT '';
ALTER TABLE subjects ADD COLUMN base_subject_id TEXT NOT NULL DEFAULT '';
ALTER TABLE subjects ADD COLUMN variant_type TEXT NOT NULL DEFAULT 'base';
ALTER TABLE subjects ADD COLUMN variant_hint TEXT NOT NULL DEFAULT '';
ALTER TABLE subjects ADD COLUMN is_locked INTEGER NOT NULL DEFAULT 0;
