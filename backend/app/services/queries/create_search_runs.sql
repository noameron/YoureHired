CREATE TABLE IF NOT EXISTS search_runs (
    id TEXT PRIMARY KEY,
    profile_id TEXT,
    filters TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total_discovered INTEGER DEFAULT 0,
    total_filtered INTEGER DEFAULT 0,
    total_analyzed INTEGER DEFAULT 0,
    FOREIGN KEY (profile_id) REFERENCES developer_profiles(id)
);
