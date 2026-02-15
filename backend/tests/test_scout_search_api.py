"""Tests for Scout search API endpoints."""

import time
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.scout import (
    DeveloperProfile,
    DeveloperProfileResponse,
    ScoutSearchResult,
    SearchRunResponse,
)


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    from app.api.scout import _active_searches, _ip_search_counts

    _active_searches.clear()
    _ip_search_counts.clear()
    yield
    _active_searches.clear()
    _ip_search_counts.clear()


def _make_profile_response() -> DeveloperProfileResponse:
    return DeveloperProfileResponse(
        id="default",
        profile=DeveloperProfile(
            languages=["Python"], topics=["web"], skill_level="intermediate", goals="contribute"
        ),
        created_at="2024-01-01T00:00:00Z",
    )


async def test_start_search_returns_201(client: AsyncClient):
    # GIVEN a saved developer profile
    filters = {"languages": ["Python"], "min_stars": 10, "max_stars": 5000}

    with (
        patch("app.api.scout.github_repos_db") as mock_db,
    ):
        mock_db.get_profile = AsyncMock(return_value=_make_profile_response())
        mock_db.create_search_run = AsyncMock(return_value="run-123")

        # WHEN starting a search
        response = await client.post("/api/scout/search", json=filters)

    # THEN returns 201 with run_id and status
    assert response.status_code == 201
    data = response.json()
    assert data["run_id"] == "run-123"
    assert data["status"] == "running"


async def test_start_search_without_profile_returns_400(client: AsyncClient):
    # GIVEN no developer profile saved
    filters = {"languages": ["Python"]}

    with patch("app.api.scout.github_repos_db") as mock_db:
        mock_db.get_profile = AsyncMock(return_value=None)

        # WHEN starting a search
        response = await client.post("/api/scout/search", json=filters)

    # THEN returns 400
    assert response.status_code == 400
    assert "profile" in response.json()["detail"].lower()


async def test_start_search_concurrent_returns_429(client: AsyncClient):
    # GIVEN an active search is running
    from app.api.scout import _active_searches

    _active_searches["existing-run"] = True

    filters = {"languages": ["Python"]}

    # WHEN starting another search
    response = await client.post("/api/scout/search", json=filters)

    # THEN returns 429
    assert response.status_code == 429
    assert "already running" in response.json()["detail"].lower()


async def test_start_search_rate_limit_returns_429(client: AsyncClient):
    # GIVEN 5 searches already done this hour from same IP
    from app.api.scout import _ip_search_counts

    now = time.time()
    # httpx ASGITransport sends requests from 127.0.0.1
    _ip_search_counts["127.0.0.1"] = [now - i for i in range(5)]

    filters = {"languages": ["Python"]}

    with patch("app.api.scout.github_repos_db") as mock_db:
        mock_db.get_profile = AsyncMock(return_value=_make_profile_response())

        # WHEN starting another search
        response = await client.post("/api/scout/search", json=filters)

    # THEN returns 429
    assert response.status_code == 429
    assert "rate limit" in response.json()["detail"].lower()


async def test_get_results_returns_200(client: AsyncClient):
    # GIVEN a completed search run with results
    result = ScoutSearchResult(
        run_id="run-123",
        status="completed",
        total_discovered=10,
        total_filtered=5,
        total_analyzed=5,
    )

    with patch("app.api.scout.github_repos_db") as mock_db:
        mock_db.get_search_results = AsyncMock(return_value=result)

        # WHEN retrieving results
        response = await client.get("/api/scout/search/run-123/results")

    # THEN returns 200 with result data
    assert response.status_code == 200
    data = response.json()
    assert data["run_id"] == "run-123"
    assert data["status"] == "completed"
    assert data["total_discovered"] == 10


async def test_get_results_unknown_run_returns_404(client: AsyncClient):
    # GIVEN no search run exists
    with patch("app.api.scout.github_repos_db") as mock_db:
        mock_db.get_search_results = AsyncMock(return_value=None)

        # WHEN retrieving results for unknown run
        response = await client.get("/api/scout/search/unknown-id/results")

    # THEN returns 404
    assert response.status_code == 404


async def test_cancel_search_returns_cancelled(client: AsyncClient):
    # GIVEN a running search
    from app.api.scout import _active_searches

    _active_searches["run-123"] = True

    with (
        patch("app.api.scout.github_repos_db") as mock_db,
        patch("app.api.scout.task_registry") as mock_registry,
    ):
        run_resp = SearchRunResponse(run_id="run-123", status="running")
        mock_db.get_search_run = AsyncMock(return_value=run_resp)
        mock_db.update_search_run = AsyncMock()

        # WHEN cancelling the search
        response = await client.post("/api/scout/search/run-123/cancel")

    # THEN returns status cancelled
    assert response.status_code == 200
    assert response.json() == {"status": "cancelled"}
    mock_registry.cancel_all.assert_called_once_with("run-123")
    mock_db.update_search_run.assert_awaited_once_with(
        "run-123", "cancelled", 0, 0, 0
    )

    # AND active search is cleaned up
    assert "run-123" not in _active_searches


async def test_cancel_unknown_run_returns_404(client: AsyncClient):
    # GIVEN no search run exists
    with patch("app.api.scout.github_repos_db") as mock_db:
        mock_db.get_search_run = AsyncMock(return_value=None)

        # WHEN cancelling unknown run
        response = await client.post("/api/scout/search/unknown/cancel")

    # THEN returns 404
    assert response.status_code == 404


async def test_stream_search_returns_sse_content_type(client: AsyncClient):
    # GIVEN a valid search run
    with (
        patch("app.api.scout.github_repos_db") as mock_db,
        patch("app.api.scout.scout_search_stream") as mock_stream,
    ):
        run_resp = SearchRunResponse(run_id="run-123", status="running")
        mock_db.get_search_run = AsyncMock(return_value=run_resp)
        mock_db.get_profile = AsyncMock(return_value=_make_profile_response())
        mock_db.get_search_run_filters = AsyncMock(
            return_value={"languages": ["Python"], "min_stars": 10, "max_stars": 5000}
        )

        async def fake_stream(*args, **kwargs):
            yield {"type": "status", "message": "test"}
            yield {"type": "complete", "data": {}}

        mock_stream.return_value = fake_stream()

        # WHEN streaming the search
        response = await client.get("/api/scout/search/run-123/stream")

    # THEN returns SSE content type
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
