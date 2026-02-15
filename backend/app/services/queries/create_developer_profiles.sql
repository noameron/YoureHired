CREATE TABLE IF NOT EXISTS developer_profiles (
    id TEXT PRIMARY KEY,
    languages TEXT NOT NULL,
    topics TEXT NOT NULL,
    skill_level TEXT NOT NULL DEFAULT 'intermediate',
    goals TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT
);
