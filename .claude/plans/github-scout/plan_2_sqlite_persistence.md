# Plan 2: SQLite Persistence

**Branch:** `scout/02-sqlite-persistence`
**Depends on:** plan_1 (config for `scout_db_path`, schemas for models)
**Blocks:** plan_3, plan_7

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "SQLite persistence layer"
- Design: `openspec/changes/add-github-scout/design.md` — Decision 6 (SQLite for persistence, schema highlights, WAL mode)
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 1.3 (DB init), Task 1.4 (DB tests), Task 1.5 (repo TTL/pruning), Task 3.1 (profile CRUD)

## Production Files (1)

### 1. CREATE `backend/app/services/scout_db.py`

Follow the singleton pattern from `backend/app/services/session_store.py`.

**Class: `ScoutDB`**

```python
class ScoutDB:
    def __init__(self, db_path: str) -> None
    async def _ensure_init(self) -> None
    async def save_profile(self, profile: DeveloperProfile) -> str
    async def get_profile(self) -> DeveloperProfileResponse | None
    async def create_search_run(self, profile_id: str, filters: SearchFilters, run_id: str) -> None
    async def update_search_run(self, run_id: str, status: str, discovered: int, filtered: int, analyzed: int) -> None
    async def get_search_run(self, run_id: str) -> SearchRunResponse | None
    async def get_search_run_filters(self, run_id: str) -> SearchFilters | None
    async def upsert_repositories(self, repos: list[RepoMetadata]) -> None
    async def save_analysis_results(self, run_id: str, results: list[AnalysisResult]) -> None
    async def get_search_results(self, run_id: str) -> ScoutSearchResult | None
    async def prune_stale_repos(self, days: int = 30) -> int

scout_db = ScoutDB(settings.scout_db_path)
```

**SQLite Schema (4 tables):**

```sql
CREATE TABLE IF NOT EXISTS developer_profiles (
    id TEXT PRIMARY KEY,
    languages TEXT NOT NULL,       -- JSON array
    topics TEXT NOT NULL,           -- JSON array
    skill_level TEXT NOT NULL DEFAULT 'intermediate',
    goals TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS search_runs (
    id TEXT PRIMARY KEY,
    profile_id TEXT,
    filters TEXT NOT NULL,          -- JSON object (SearchFilters)
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    finished_at TEXT,
    total_discovered INTEGER DEFAULT 0,
    total_filtered INTEGER DEFAULT 0,
    total_analyzed INTEGER DEFAULT 0,
    FOREIGN KEY (profile_id) REFERENCES developer_profiles(id)
);

CREATE TABLE IF NOT EXISTS repositories (
    github_id INTEGER PRIMARY KEY,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    description TEXT,
    primary_language TEXT,
    languages TEXT,                 -- JSON array
    star_count INTEGER DEFAULT 0,
    fork_count INTEGER DEFAULT 0,
    open_issue_count INTEGER DEFAULT 0,
    topics TEXT,                    -- JSON array
    license TEXT,
    pushed_at TEXT,
    created_at TEXT,
    good_first_issue_count INTEGER DEFAULT 0,
    help_wanted_count INTEGER DEFAULT 0,
    last_seen_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    github_id INTEGER NOT NULL,
    fit_score REAL NOT NULL,
    reason TEXT NOT NULL,
    contributions TEXT,            -- JSON array
    reject INTEGER DEFAULT 0,
    reject_reason TEXT,
    analyzed_at TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES search_runs(id),
    FOREIGN KEY (github_id) REFERENCES repositories(github_id)
);
```

**Key implementation details:**

- **Lazy init:** `_initialized: bool = False` flag. `_ensure_init()` called at top of each public method, runs schema creation only once.
- **Directory creation:** `_ensure_init()` calls `Path(db_path).parent.mkdir(parents=True, exist_ok=True)` before connecting.
- **WAL mode:** `await db.execute("PRAGMA journal_mode=WAL")` on every connection open.
- **Foreign keys:** `await db.execute("PRAGMA foreign_keys=ON")` on every connection open.
- **Connection per method:** `async with aiosqlite.connect(self.db_path) as db:` — no persistent connection, no pool.
- **Single-profile mode:** `id="default"` always. `save_profile` uses `INSERT OR REPLACE`.
- **JSON columns:** Stored via `json.dumps(list)`, read back via `json.loads(str)`.
- **Pruning query:** `DELETE FROM repositories WHERE github_id NOT IN (SELECT DISTINCT github_id FROM analysis_results) AND last_seen_at < ?`
- **Pruning trigger:** Called lazily on first `_ensure_init()`.
- **Also add `data/` to `.gitignore`** at project root.

## Test Files

- `backend/tests/test_scout_db.py`
  - DB initialization creates all 4 tables
  - WAL mode is activated
  - Profile save returns `"default"`
  - Profile get returns saved profile
  - Profile save overwrites previous (single-profile mode)
  - Profile get returns `None` when empty
  - Search run create + get lifecycle
  - Search run update status and totals
  - `get_search_run_filters` returns stored filters
  - Repo upsert deduplicates by `github_id` (insert then update `last_seen_at`)
  - Analysis result save + retrieval (joined with repos, sorted by `fit_score` desc)
  - `get_search_results` for unknown run returns `None`
  - `get_search_results` for run with no results returns object with empty list
  - Pruning deletes stale repos not referenced by analysis
  - Pruning keeps repos that are referenced by analysis results
  - Pruning keeps repos seen within 30 days

**Test fixture:** Use `tmp_path` for DB file to avoid polluting the filesystem.

## Edge Cases

- `data/` directory doesn't exist → created by `_ensure_init()`
- DB file doesn't exist → `aiosqlite.connect()` creates it
- `get_profile()` when no profile → returns `None`
- `get_search_results()` for incomplete run → returns `ScoutSearchResult` with empty `results` list
- `upsert_repositories([])` → no-op
- `save_analysis_results(run_id, [])` → no-op
- `prune_stale_repos()` with nothing to prune → returns 0
- Concurrent access → WAL mode handles it safely

## Verification

```bash
cd backend && uv run pytest tests/test_scout_db.py -v
```
