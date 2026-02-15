# Plan 7: Orchestrator & Search API

**Branch:** `scout/07-orchestrator-and-search-api`
**Depends on:** plan_2, plan_3, plan_4, plan_5, plan_6 (all backend components)
**Blocks:** plan_8 (integration), plan_9

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "SSE streaming for real-time progress", "New API endpoints for triggering searches"
- Design: `openspec/changes/add-github-scout/design.md` — Decision 7 (SSE streaming), Decision 9 (orchestrator decomposition), Decision 10 (rate limiting)
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 7.1-7.7 (orchestrator), Task 8.1-8.5 (API endpoints)

## Production Files (3)

### 1. CREATE `backend/app/services/scout_orchestrator.py`

Thin coordinator following `backend/app/services/company_research.py` pattern (`research_company_stream`).

```python
import logging
from collections.abc import AsyncGenerator

from app.config import settings
from app.schemas.scout import (
    AnalysisResult,
    DeveloperProfile,
    ScoutSearchResult,
    SearchFilters,
)
from app.services.github_client import create_github_client
from app.services.repo_filtering import apply_filters
from app.services.scout_analysis import analyze_repos_streamed
from app.services.scout_db import scout_db

logger = logging.getLogger(__name__)


async def scout_search_stream(
    filters: SearchFilters,
    profile: DeveloperProfile,
    run_id: str,
    session_id: str,
) -> AsyncGenerator[dict[str, object], None]:
    """Stream the full scout pipeline: discover → filter → fetch READMEs → analyze → persist."""
    try:
        # Phase 1: Discovery
        yield {"type": "status", "message": "Searching GitHub...", "phase": "discovering"}
        client = create_github_client()
        repos, warnings = await client.search_repositories(filters)
        yield {"type": "status", "message": f"Discovered {len(repos)} repositories", "phase": "discovering"}

        if not repos:
            yield {"type": "error", "message": "No repositories found. Try broadening your filters."}
            await scout_db.update_search_run(run_id, "completed", 0, 0, 0)
            return

        await scout_db.upsert_repositories(repos)

        # Phase 2: Filtering
        yield {"type": "status", "message": "Filtering candidates...", "phase": "filtering"}
        filtered = apply_filters(repos, min_stars=filters.min_stars, max_stars=filters.max_stars)
        yield {"type": "status", "message": f"{len(filtered)} repos passed filters", "phase": "filtering"}

        if not filtered:
            yield {"type": "error", "message": "All repos filtered out. Try adjusting your filters."}
            await scout_db.update_search_run(run_id, "completed", len(repos), 0, 0)
            return

        # Phase 2.5: Fetch READMEs for filtered repos (capped)
        capped = filtered[: settings.scout_max_repos]
        yield {"type": "status", "message": f"Fetching READMEs for {len(capped)} repos...", "phase": "filtering"}
        readme_pairs = [(r.owner, r.name) for r in capped]
        readmes = await client.fetch_readmes(readme_pairs)

        # Phase 3: Analysis
        yield {"type": "status", "message": "Starting AI analysis...", "phase": "analyzing"}
        all_results: list[AnalysisResult] = []
        async for results, event in analyze_repos_streamed(profile, filtered, readmes, session_id):
            all_results = results
            yield event

        # Persist and finalize
        await scout_db.save_analysis_results(run_id, all_results)
        status = "partial" if len(all_results) < len(capped) else "completed"
        await scout_db.update_search_run(run_id, status, len(repos), len(filtered), len(all_results))

        visible_results = sorted(
            [r for r in all_results if not r.reject],
            key=lambda r: r.fit_score,
            reverse=True,
        )

        result = ScoutSearchResult(
            run_id=run_id,
            status=status,
            total_discovered=len(repos),
            total_filtered=len(filtered),
            total_analyzed=len(all_results),
            results=visible_results,
            repos=capped,
            warnings=warnings,
        )
        yield {"type": "complete", "data": result.model_dump()}

    except Exception as e:
        logger.exception("Scout search failed for run %s", run_id)
        await scout_db.update_search_run(run_id, "failed", 0, 0, 0)
        yield {"type": "error", "message": f"Scout search failed: {e!s}"}
```

### 2. MODIFY `backend/app/api/scout.py`

Add search/stream/results/cancel endpoints to the existing profile router.

```python
import json
import time
import uuid
from collections import defaultdict
from collections.abc import AsyncGenerator

from fastapi import Request
from fastapi.responses import StreamingResponse

from app.constants import SSE_HEADERS
from app.schemas.scout import SearchFilters, SearchRunResponse, ScoutSearchResult
from app.services.scout_orchestrator import scout_search_stream
from app.services.task_registry import task_registry

# --- Rate limiting state (in-memory, per-process) ---
_active_searches: dict[str, bool] = {}
_ip_search_counts: dict[str, list[float]] = defaultdict(list)
SEARCH_RATE_LIMIT = 5
SEARCH_RATE_WINDOW = 3600  # seconds


def _check_rate_limit(ip: str) -> str | None:
    """Returns error message if rate limited, None if OK."""
    if any(_active_searches.values()):
        return "A search is already running. Please wait for it to complete."
    now = time.time()
    _ip_search_counts[ip] = [t for t in _ip_search_counts[ip] if now - t < SEARCH_RATE_WINDOW]
    if len(_ip_search_counts[ip]) >= SEARCH_RATE_LIMIT:
        return f"Rate limit exceeded. Maximum {SEARCH_RATE_LIMIT} searches per hour."
    return None


@router.post("/scout/search", response_model=SearchRunResponse, status_code=201)
async def start_search(filters: SearchFilters, request: Request) -> SearchRunResponse:
    ip = request.client.host if request.client else "unknown"
    rate_error = _check_rate_limit(ip)
    if rate_error:
        raise HTTPException(status_code=429, detail=rate_error)

    profile_resp = await scout_db.get_profile()
    if not profile_resp:
        raise HTTPException(status_code=400, detail="Save a developer profile before searching")

    run_id = str(uuid.uuid4())
    await scout_db.create_search_run(profile_resp.id, filters, run_id)
    _active_searches[run_id] = True
    _ip_search_counts[ip].append(time.time())
    return SearchRunResponse(run_id=run_id, status="running")


async def _stream_scout_events(run_id: str, filters: SearchFilters, profile, session_id: str) -> AsyncGenerator[str, None]:
    try:
        async for event in scout_search_stream(filters, profile, run_id, session_id):
            yield f"data: {json.dumps(event)}\n\n"
    finally:
        _active_searches.pop(run_id, None)
        task_registry.cleanup(run_id)


@router.get("/scout/search/{run_id}/stream")
async def stream_search(run_id: str) -> StreamingResponse:
    run = await scout_db.get_search_run(run_id)
    if not run:
        return StreamingResponse(
            _sse_single_error("Search run not found"),
            media_type="text/event-stream", headers=SSE_HEADERS,
        )
    if run_id in _active_searches:
        return StreamingResponse(
            _sse_single_error("Search already in progress"),
            media_type="text/event-stream", headers=SSE_HEADERS,
        )

    profile_resp = await scout_db.get_profile()
    filters = await scout_db.get_search_run_filters(run_id)
    if not profile_resp or not filters:
        return StreamingResponse(
            _sse_single_error("Profile or filters not found"),
            media_type="text/event-stream", headers=SSE_HEADERS,
        )

    _active_searches[run_id] = True
    return StreamingResponse(
        _stream_scout_events(run_id, filters, profile_resp.profile, run_id),
        media_type="text/event-stream", headers=SSE_HEADERS,
    )


@router.get("/scout/search/{run_id}/results")
async def get_results(run_id: str) -> ScoutSearchResult:
    result = await scout_db.get_search_results(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Search run not found")
    return result


@router.post("/scout/search/{run_id}/cancel")
async def cancel_search(run_id: str) -> dict[str, str]:
    task_registry.cancel_all(run_id)
    _active_searches.pop(run_id, None)
    await scout_db.update_search_run(run_id, "cancelled", 0, 0, 0)
    return {"status": "cancelled"}


async def _sse_single_error(message: str) -> AsyncGenerator[str, None]:
    yield f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"
```

### 3. MODIFY `backend/app/services/scout_db.py` (if needed)

Add `get_search_run_filters()` method if not already present from plan_2:

```python
async def get_search_run_filters(self, run_id: str) -> SearchFilters | None:
    await self._ensure_init()
    async with aiosqlite.connect(self.db_path) as db:
        cursor = await db.execute("SELECT filters FROM search_runs WHERE id = ?", (run_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return SearchFilters.model_validate_json(row[0])
```

## Test Files

- `backend/tests/test_scout_orchestrator.py`
  - Full pipeline with mocked github_client and mocked agent → yields status + complete events
  - Empty discovery → yields error event
  - All repos filtered out → yields error event
  - Partial batch failure → yields partial results with status "partial"
  - Cancellation → agents cancelled via task_registry

- `backend/tests/test_scout_search_api.py`
  - `POST /api/scout/search` → 201 with `run_id`
  - `POST /api/scout/search` without profile → 400
  - `POST /api/scout/search` with concurrent search active → 429
  - `POST /api/scout/search` after 5 searches in an hour → 429
  - `GET /api/scout/search/{run_id}/results` → returns results
  - `GET /api/scout/search/{unknown_id}/results` → 404
  - `POST /api/scout/search/{run_id}/cancel` → cancels and returns status
  - `GET /api/scout/search/{run_id}/stream` → returns SSE content type

## Edge Cases

- Cancel during discovery phase → agents auto-cancelled on registration (task_registry `_cancelled` set triggers immediate cancel for any new `register()` call)
- Double-stream connection → SSE error "Search already in progress" (checks `_active_searches`)
- `_active_searches` cleanup → `finally` block in `_stream_scout_events` always removes entry
- Rate limit pruning → old timestamps removed on every `_check_rate_limit` call
- Server restart → `_active_searches` is empty (no stale entries)
- `request.client` is `None` (e.g., behind certain proxies) → defaults to `"unknown"` IP

## Verification

```bash
cd backend && uv run pytest tests/test_scout_orchestrator.py tests/test_scout_search_api.py -v
```
