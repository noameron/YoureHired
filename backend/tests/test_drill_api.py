"""Tests for drill API endpoints."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas.company_info import CompanySummary, TechStack
from app.schemas.drill import DifficultyLevel, Drill, DrillType
from app.services.session_store import session_store


@pytest.fixture
def mock_company_summary():
    """Create a mock company summary for testing."""
    return CompanySummary(
        name="TestCorp",
        industry="Technology",
        description="A test company",
        size="100-500",
        tech_stack=TechStack(
            languages=["Python"],
            frameworks=["FastAPI"],
            tools=["Docker"],
        ),
        engineering_culture="Fast-paced",
        recent_news=["Launched new product"],
        interview_tips="Focus on system design",
        sources=["testcorp.com"],
    )


@pytest.fixture
def test_session(mock_company_summary):
    """Create a test session with company summary already set."""
    session = session_store.create(
        session_id="test-drill-session",
        company_name="TestCorp",
        role="backend_developer",
        role_description="Python and FastAPI experience",
    )
    # Set company_summary to avoid triggering research
    session.company_summary = mock_company_summary
    yield session
    # Cleanup
    if "test-drill-session" in session_store._sessions:
        del session_store._sessions["test-drill-session"]


@pytest.fixture
def mock_drill():
    """Create a mock drill for testing."""
    return Drill(
        title="Implement Rate Limiter",
        type=DrillType.CODING,
        difficulty=DifficultyLevel.MEDIUM,
        description="Implement a sliding window rate limiter.",
        requirements=["Support multiple keys", "Thread-safe"],
        expected_time_minutes=45,
        tech_stack=["Python"],
        hints=["Consider using a deque"],
    )


class TestGenerateDrillEndpoint:
    """Tests for POST /api/generate-drill/{session_id}."""

    @pytest.mark.asyncio
    async def test_generate_drill_success(self, test_session, mock_drill):
        """Successful drill generation returns drill data."""
        with patch(
            "app.api.drill.generate_drill",
            new_callable=AsyncMock,
            return_value=mock_drill,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(f"/api/generate-drill/{test_session.session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["drill"]["title"] == "Implement Rate Limiter"
        assert data["data"]["session_id"] == test_session.session_id
        assert data["data"]["company_name"] == "TestCorp"
        assert data["data"]["role"] == "backend_developer"

    @pytest.mark.asyncio
    async def test_generate_drill_session_not_found(self):
        """Missing session returns 404."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post("/api/generate-drill/nonexistent-session")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_drill_includes_metadata(self, test_session, mock_drill):
        """Response includes generation metadata."""
        with patch(
            "app.api.drill.generate_drill",
            new_callable=AsyncMock,
            return_value=mock_drill,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(f"/api/generate-drill/{test_session.session_id}")

        data = response.json()
        assert "generation_metadata" in data["data"]
        assert "generators_used" in data["data"]["generation_metadata"]


class TestStreamDrillEndpoint:
    """Tests for GET /api/generate-drill/{session_id}/stream."""

    @pytest.mark.asyncio
    async def test_stream_session_not_found(self):
        """Missing session streams error event."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/api/generate-drill/nonexistent/stream")

        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

        # Parse SSE event
        content = response.text
        assert "error" in content
        assert "Session not found" in content

    @pytest.mark.asyncio
    async def test_stream_returns_sse_format(self, test_session, mock_drill):
        """Streaming returns valid SSE format."""

        async def mock_stream(*args, **kwargs):
            yield {"type": "status", "message": "Starting..."}
            yield {"type": "complete", "data": mock_drill.model_dump()}

        with patch(
            "app.api.drill.generate_drill_stream",
            return_value=mock_stream(),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/generate-drill/{test_session.session_id}/stream")

        assert response.status_code == 200
        content = response.text

        # SSE format: data: {...}\n\n
        assert "data:" in content
        assert "Starting..." in content
        assert "complete" in content

    @pytest.mark.asyncio
    async def test_stream_headers(self, test_session, mock_drill):
        """Streaming response has correct headers."""

        async def mock_stream(*args, **kwargs):
            yield {"type": "complete", "data": mock_drill.model_dump()}

        with patch(
            "app.api.drill.generate_drill_stream",
            return_value=mock_stream(),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/generate-drill/{test_session.session_id}/stream")

        assert "text/event-stream" in response.headers["content-type"]
        assert response.headers.get("cache-control") == "no-cache"

    @pytest.mark.asyncio
    async def test_stream_multiple_events(self, test_session, mock_drill):
        """Stream contains multiple events."""

        async def mock_stream(*args, **kwargs):
            yield {"type": "status", "message": "Starting drill generation..."}
            yield {"type": "status", "message": "Generating 3 candidates..."}
            yield {
                "type": "candidate",
                "generator": "coding",
                "title": "Coding Challenge",
            }
            yield {"type": "status", "message": "Evaluating candidates..."}
            yield {"type": "complete", "data": mock_drill.model_dump()}

        with patch(
            "app.api.drill.generate_drill_stream",
            return_value=mock_stream(),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/generate-drill/{test_session.session_id}/stream")

        content = response.text
        lines = [line for line in content.split("\n") if line.startswith("data:")]

        # Should have 5 data lines (one per event)
        assert len(lines) == 5

        # Parse and verify events
        events = [json.loads(line.replace("data: ", "")) for line in lines]
        assert events[0]["type"] == "status"
        assert events[2]["type"] == "candidate"
        assert events[-1]["type"] == "complete"

    @pytest.mark.asyncio
    async def test_stream_error_event(self, test_session):
        """Stream can return error events."""

        async def mock_stream(*args, **kwargs):
            yield {"type": "status", "message": "Starting..."}
            yield {"type": "error", "message": "All generators failed"}

        with patch(
            "app.api.drill.generate_drill_stream",
            return_value=mock_stream(),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/generate-drill/{test_session.session_id}/stream")

        content = response.text
        assert "error" in content
        assert "All generators failed" in content

    @pytest.mark.asyncio
    async def test_stream_drill_calls_cleanup_on_completion(self, test_session, mock_drill):
        """Verify that after streaming completes, task_registry.cleanup is called."""
        # GIVEN - streaming is in progress

        async def mock_stream(*args, **kwargs):
            yield {"type": "status", "message": "Starting..."}
            yield {"type": "complete", "data": mock_drill.model_dump()}

        # WHEN - streaming completes
        with patch(
            "app.api.drill.generate_drill_stream",
            return_value=mock_stream(),
        ), patch("app.api.drill.task_registry") as mock_registry:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.get(f"/api/generate-drill/{test_session.session_id}/stream")

        # THEN - cleanup was called with session_id
        assert response.status_code == 200
        mock_registry.cleanup.assert_called_once_with(test_session.session_id)


    @pytest.mark.asyncio
    async def test_stream_drill_calls_cleanup_on_error(self, test_session):
        """Verify that cleanup is called even when streaming raises an exception."""
        # GIVEN - streaming raises an error mid-stream

        async def mock_stream(*args, **kwargs):
            yield {"type": "status", "message": "Starting..."}
            raise ValueError("Simulated error")

        # WHEN - streaming fails (exception propagates through ASGI transport)
        with patch(
            "app.api.drill.generate_drill_stream",
            return_value=mock_stream(),
        ), patch("app.api.drill.task_registry") as mock_registry:
            with pytest.raises(ValueError, match="Simulated error"):
                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    await client.get(f"/api/generate-drill/{test_session.session_id}/stream")

            # THEN - cleanup was still called despite the error
            mock_registry.cleanup.assert_called_once_with(test_session.session_id)


class TestCancelEndpoint:
    """Tests for POST /api/cancel/{session_id}."""

    @pytest.mark.asyncio
    async def test_cancel_returns_200_and_status(self):
        """POST to cancel endpoint returns 200 with status cancelled."""
        # GIVEN - a session id to cancel

        # WHEN - posting to cancel endpoint
        with patch("app.api.drill.task_registry"):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post("/api/cancel/test-session-id")

        # THEN - returns 200 with cancelled status
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "cancelled"}

    @pytest.mark.asyncio
    async def test_cancel_calls_task_registry_cancel_all(self):
        """Verify task_registry.cancel_all is called with correct session_id."""
        # GIVEN - a session id to cancel
        session_id = "test-session-123"

        # WHEN - posting to cancel endpoint
        with patch("app.api.drill.task_registry") as mock_registry:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post(f"/api/cancel/{session_id}")

        # THEN - task_registry.cancel_all was called with session_id
        assert response.status_code == 200
        mock_registry.cancel_all.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_cancel_unknown_session_still_succeeds(self):
        """POST to cancel with nonexistent session still returns 200."""
        # GIVEN - a nonexistent session id

        # WHEN - posting to cancel endpoint
        with patch("app.api.drill.task_registry") as mock_registry:
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test",
            ) as client:
                response = await client.post("/api/cancel/nonexistent-session")

        # THEN - returns 200 (cancel is idempotent)
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "cancelled"}
        # Registry was still called
        mock_registry.cancel_all.assert_called_once_with("nonexistent-session")
