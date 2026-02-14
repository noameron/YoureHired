CREATE TABLE IF NOT EXISTS repositories (
    github_id INTEGER PRIMARY KEY,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    primary_language TEXT,
    languages TEXT,
    star_count INTEGER DEFAULT 0,
    fork_count INTEGER DEFAULT 0,
    open_issue_count INTEGER DEFAULT 0,
    topics TEXT,
    license TEXT,
    pushed_at TEXT,
    created_at TEXT,
    good_first_issue_count INTEGER DEFAULT 0,
    help_wanted_count INTEGER DEFAULT 0,
    last_seen_at TEXT NOT NULL
);
