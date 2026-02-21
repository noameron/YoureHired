import json
import logging
import time
from collections import defaultdict
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.constants import SSE_HEADERS
from app.schemas.scout import (
    ScoutSearchResult,
    SearchFilters,
    SearchRunResponse,
)
from app.services.github_repos_db import github_repos_db
from app.services.scout_orchestrator import scout_search_stream
from app.services.task_registry import task_registry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scout"])

# Rate limiting state (in-memory, per-process). In a multi-worker deployment
# these dicts are not shared across workers — a shared store (e.g. Redis)
# would be needed for strict enforcement. Acceptable for single-worker dev.
_active_searches: dict[str, bool] = {}
_ip_search_counts: dict[str, list[float]] = defaultdict(list)
SEARCH_RATE_LIMIT = 5
SEARCH_RATE_WINDOW = 3600  # seconds


def _check_rate_limit(ip: str) -> str | None:
    """Return error message if rate limited, None if OK."""
    if any(_active_searches.values()):
        return "A search is already running. Please wait for it to complete."
    now = time.time()
    _ip_search_counts[ip] = [t for t in _ip_search_counts[ip] if now - t < SEARCH_RATE_WINDOW]
    if len(_ip_search_counts[ip]) >= SEARCH_RATE_LIMIT:
        return f"Rate limit exceeded. Maximum {SEARCH_RATE_LIMIT} searches per hour."
    return None


@router.post("/scout/search", response_model=SearchRunResponse, status_code=201)
async def start_search(filters: SearchFilters, request: Request) -> SearchRunResponse:
    """Start a new scout search run."""
    ip = request.client.host if request.client else "unknown"
    rate_error = _check_rate_limit(ip)
    if rate_error:
        raise HTTPException(status_code=429, detail=rate_error)

    run_id = await github_repos_db.create_search_run(filters)
    # Note: _active_searches is set by stream_search, not here.
    # start_search only creates the DB record; stream_search starts the pipeline.
    _ip_search_counts[ip].append(time.time())
    return SearchRunResponse(run_id=run_id, status="running")


async def _stream_scout_events(
    run_id: str, filters: SearchFilters
) -> AsyncGenerator[str, None]:
    try:
        async for event in scout_search_stream(filters, run_id):
            yield f"data: {json.dumps(event)}\n\n"
    finally:
        _active_searches.pop(run_id, None)
        task_registry.cleanup(run_id)


async def _validate_stream_request(
    run_id: str,
) -> SearchFilters | str:
    """Validate a stream request. Returns filters or an error message."""
    run = await github_repos_db.get_search_run(run_id)
    if not run:
        return "Search run not found"
    if run_id in _active_searches:
        return "Search already in progress"
    filters = await github_repos_db.get_search_run_filters(run_id)
    if not filters:
        return "Filters not found"
    return filters


@router.get("/scout/search/{run_id}/stream")
async def stream_search(run_id: str) -> StreamingResponse:
    """Stream search progress via Server-Sent Events."""
    result = await _validate_stream_request(run_id)
    if isinstance(result, str):
        return StreamingResponse(
            _sse_single_error(result),
            media_type="text/event-stream",
            headers=SSE_HEADERS,
        )

    filters = result
    _active_searches[run_id] = True
    return StreamingResponse(
        _stream_scout_events(run_id, filters),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )


@router.get("/scout/search/{run_id}/results")
async def get_results(run_id: str) -> ScoutSearchResult:
    """Get stored results for a completed search run."""
    result = await github_repos_db.get_search_results(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Search run not found")
    return result


@router.post("/scout/search/{run_id}/cancel")
async def cancel_search(run_id: str) -> dict[str, str]:
    """Cancel a running search."""
    run = await github_repos_db.get_search_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Search run not found")
    task_registry.cancel_all(run_id)
    _active_searches.pop(run_id, None)
    await github_repos_db.update_search_run(run_id, "cancelled", 0, 0, 0)
    return {"status": "cancelled"}


async def _sse_single_error(message: str) -> AsyncGenerator[str, None]:
    yield f"data: {json.dumps({'type': 'error', 'message': message})}\n\n"
