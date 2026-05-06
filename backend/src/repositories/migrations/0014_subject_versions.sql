-- Subject consistency control: create subject_versions table for version history
CREATE TABLE IF NOT EXISTS subject_versions (
    id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    source_url TEXT DEFAULT '',
    feature_description TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subject_versions_subject_id ON subject_versions(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_versions_version ON subject_versions(subject_id, version);
