# Plan 1: Config, Dependencies & Schemas

**Branch:** `scout/01-config-deps-schemas`
**Depends on:** `feature/github-scout-base` (nothing else)
**Blocks:** All other plans

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — sections "What Changes" (config, schemas) and "Impact" (affected code list)
- Design: `openspec/changes/add-github-scout/design.md` — Decision 6 (SQLite config), Decision 8 (GitHub token)
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 1.1 (config), Task 1.2 (deps), Task 2.1 (schemas)

## Production Files (4)

### 1. MODIFY `backend/app/config.py`

Add to the `Settings` class (after line 36, before the closing of the class):

```python
# GitHub Scout Configuration
github_token: str = ""
scout_db_path: str = "data/scout.db"
scout_analysis_timeout: float = 60.0
scout_max_repos: int = 50
scout_max_daily_analyses: int = 100
scout_batch_size: int = 10
```

Follow the existing pattern: flat fields with defaults, loaded from `.env` via `pydantic-settings`.

### 2. MODIFY `backend/pyproject.toml`

- Add `aiosqlite>=0.20.0` to `[project] dependencies`
- Move `httpx>=0.26.0` from `[dependency-groups] dev` to `[project] dependencies` (it's needed at runtime for the GitHub GraphQL client)
- Run `uv sync` after modification

### 3. CREATE `backend/app/schemas/scout.py`

Follow patterns from `backend/app/schemas/drill.py` and `backend/app/schemas/company_info.py`.

**Models:**

```python
class DeveloperProfile(BaseModel):
    languages: list[str] = Field(min_length=1)
    topics: list[str] = Field(default_factory=list)
    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    goals: str = Field(default="", max_length=500)

class DeveloperProfileResponse(BaseModel):
    id: str
    profile: DeveloperProfile
    created_at: str
    updated_at: str | None = None

class SearchFilters(BaseModel):
    languages: list[str] = Field(min_length=1)
    min_stars: int = Field(default=10, ge=0)
    max_stars: int = Field(default=50000, ge=0)
    topics: list[str] = Field(default_factory=list)
    min_activity_date: str | None = Field(default=None)  # ISO date, e.g. "2025-08-01"
    license: str | None = None  # SPDX ID, e.g. "mit", "apache-2.0"

    @model_validator(mode="after")
    def validate_star_range(self) -> Self:
        if self.min_stars > self.max_stars:
            raise ValueError("min_stars must be <= max_stars")
        return self

class RepoMetadata(BaseModel):
    github_id: int
    owner: str
    name: str
    url: str
    description: str | None = None
    primary_language: str | None = None
    languages: list[str] = Field(default_factory=list)
    star_count: int = 0
    fork_count: int = 0
    open_issue_count: int = 0
    topics: list[str] = Field(default_factory=list)
    license: str | None = None
    pushed_at: str | None = None
    created_at: str | None = None
    good_first_issue_count: int = 0
    help_wanted_count: int = 0

class AnalysisResult(BaseModel):
    repo: str  # "owner/name"
    fit_score: float = Field(ge=0.0, le=10.0)
    reason: str
    contributions: list[str] = Field(default_factory=list)
    reject: bool = False
    reject_reason: str | None = None

class SearchRunResponse(BaseModel):
    run_id: str
    status: Literal["running", "completed", "failed", "cancelled", "partial"]

class ScoutSearchResult(BaseModel):
    run_id: str
    status: str
    total_discovered: int = 0
    total_filtered: int = 0
    total_analyzed: int = 0
    results: list[AnalysisResult] = Field(default_factory=list)
    repos: list[RepoMetadata] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
```

**SSE event models** (matching `DrillStreamStatusEvent` etc. in `schemas/drill.py:135-163`):

```python
class ScoutStreamStatusEvent(BaseModel):
    type: Literal["status"] = "status"
    message: str
    phase: Literal["discovering", "filtering", "analyzing"] | None = None

class ScoutStreamCompleteEvent(BaseModel):
    type: Literal["complete"] = "complete"
    data: ScoutSearchResult

class ScoutStreamErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str
```

### 4. MODIFY `.env.example`

Add after the Backend Settings section:

```
# GitHub Scout (requires personal access token with public_repo read access)
GITHUB_TOKEN=
SCOUT_DB_PATH=data/scout.db
```

## Test Files

- `backend/tests/test_scout_schemas.py`
  - `DeveloperProfile` rejects empty `languages` list
  - `SearchFilters` rejects `min_stars > max_stars`
  - `AnalysisResult` rejects `fit_score` outside 0-10
  - `DeveloperProfile.goals` rejects over 500 chars
  - Valid instances serialize/deserialize correctly

## Edge Cases

- `SearchFilters(min_stars=100, max_stars=50)` → `ValidationError` from model_validator
- `DeveloperProfile(languages=[])` → `ValidationError` from `min_length=1`
- `SearchFilters.license` accepts any string (GitHub accepts SPDX IDs as qualifiers)
- `SearchFilters.min_activity_date` defaults to `None` — the GitHub client fills in 6 months ago if `None`

## Verification

```bash
cd backend && uv sync && uv run pytest tests/test_scout_schemas.py -v
```
