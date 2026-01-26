"""Tests for the company research streaming endpoint."""

import json
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.session_store import session_store


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def test_session_id():
    """Create a test session and return its ID."""
    session_id = "test-session-123"
    session_store.create(
        session_id=session_id,
        company_name="Test Company",
        role="Backend Developer",
    )
    yield session_id
    # Cleanup: remove session after test
    session_store._sessions.pop(session_id, None)


async def collect_sse_events(response) -> list[dict]:
    """Helper to collect all SSE events from a streaming response."""
    events = []
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


class TestStreamCompanyResearchSessionNotFound:
    """Tests for streaming endpoint when session is not found."""

    async def test_invalid_session_returns_error_event(self, client: AsyncClient):
        """Request with non-existent session returns SSE error event."""
        # GIVEN a session ID that doesn't exist

        # WHEN requesting the stream endpoint
        async with client.stream(
            "GET", "/api/company-research/nonexistent-session/stream"
        ) as response:
            # THEN the response is SSE with error event
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            events = await collect_sse_events(response)

        assert len(events) == 1
        assert events[0]["type"] == "error"
        assert events[0]["message"] == "Session not found"


class TestStreamCompanyResearchHeaders:
    """Tests for SSE headers in streaming endpoint."""

    async def test_stream_headers_set_correctly(
        self, client: AsyncClient, test_session_id: str
    ):
        """Stream response has correct SSE headers."""
        # GIVEN a valid session with mocked empty stream
        async def mock_stream(company_name: str, role: str):
            yield {"type": "status", "message": "Test"}

        with patch(
            "app.api.company_info.research_company_stream",
            side_effect=mock_stream,
        ):
            # WHEN requesting the stream endpoint
            async with client.stream(
                "GET", f"/api/company-research/{test_session_id}/stream"
            ) as response:
                # THEN headers are set for SSE
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                assert response.headers["cache-control"] == "no-cache"
                assert response.headers["x-accel-buffering"] == "no"

                # Consume stream
                await collect_sse_events(response)


class TestStreamCompanyResearchSessionData:
    """Tests for session data passing to research function."""

    async def test_stream_passes_session_data_to_research_function(
        self, client: AsyncClient, test_session_id: str
    ):
        """Stream endpoint passes correct session data to research function."""
        # GIVEN a valid session
        captured_args = {}

        async def mock_stream(company_name: str, role: str):
            captured_args["company_name"] = company_name
            captured_args["role"] = role
            yield {"type": "complete", "data": {}}

        with patch(
            "app.api.company_info.research_company_stream",
            side_effect=mock_stream,
        ):
            # WHEN requesting the stream endpoint
            async with client.stream(
                "GET", f"/api/company-research/{test_session_id}/stream"
            ) as response:
                await collect_sse_events(response)

        # THEN correct session data was passed
        assert captured_args["company_name"] == "Test Company"
        assert captured_args["role"] == "Backend Developer"
