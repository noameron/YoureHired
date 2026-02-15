CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    github_id INTEGER NOT NULL,
    fit_score REAL NOT NULL,
    reason TEXT NOT NULL,
    contributions TEXT,
    reject INTEGER DEFAULT 0,
    reject_reason TEXT,
    analyzed_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES search_runs(id),
    FOREIGN KEY (github_id) REFERENCES repositories(github_id)
);
