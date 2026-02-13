"""Tests for company research timeout behavior."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.services.company_research import research_company_stream
from tests.conftest import mock_streamed_result


async def collect_events(stream):
    """Helper to collect all events from an async generator."""
    events = []
    async for event in stream:
        events.append(event)
    return events


class TestCompanyResearchTimeout:
    """Tests for timeout behavior in company research."""

    @pytest.mark.asyncio
    async def test_planner_timeout_yields_error_event(self):
        """When planner exceeds timeout, error event is yielded."""
        with patch("app.services.company_research.settings") as mock_settings:
            mock_settings.company_research_agent_timeout = 0.01  # 10ms

            def slow_streamed(agent, input_str):
                mock = MagicMock()
                mock.final_output = None
                mock.is_complete = False

                async def slow_stream():
                    await asyncio.sleep(0.1)  # 100ms > 10ms timeout
                    yield  # makes it an async generator

                mock.stream_events = slow_stream
                return mock

            with patch(
                "app.services.task_registry.Runner.run_streamed",
                side_effect=slow_streamed,
            ):
                events = await collect_events(
                    research_company_stream("TestCo", "Developer", "test-session")
                )

        assert events[-1]["type"] == "error"
        assert "timed out" in events[-1]["message"].lower()

    @pytest.mark.asyncio
    async def test_search_timeout_continues_with_remaining(self):
        """When one search times out, remaining searches continue."""
        with patch("app.services.company_research.settings") as mock_settings:
            mock_settings.company_research_agent_timeout = 0.01  # 10ms

            call_count = [0]

            def mock_run_streamed(agent, input_str):
                call_count[0] += 1
                current = call_count[0]

                # Planner returns quickly with 2 searches
                if current == 1:
                    plan_mock = MagicMock()
                    plan_mock.searches = [
                        MagicMock(query="q1", reason="r1"),
                        MagicMock(query="q2", reason="r2"),
                    ]
                    return mock_streamed_result(plan_mock)

                # First search times out
                if current == 2:
                    mock = MagicMock()
                    mock.final_output = None
                    mock.is_complete = False

                    async def slow_stream():
                        await asyncio.sleep(0.1)
                        yield

                    mock.stream_events = slow_stream
                    return mock

                # Second search succeeds
                if current == 3:
                    return mock_streamed_result("search result")

                # Summarizer succeeds
                if current == 4:
                    summary_mock = MagicMock()
                    summary_mock.model_dump = lambda: {"summary": "test"}
                    return mock_streamed_result(summary_mock)

                return mock_streamed_result(MagicMock())

            with patch(
                "app.services.task_registry.Runner.run_streamed",
                side_effect=mock_run_streamed,
            ):
                events = await collect_events(
                    research_company_stream("TestCo", "Developer", "test-session")
                )

        # Should have continued despite one timeout
        status_messages = [e["message"] for e in events if e["type"] == "status"]
        assert any("timed out" in msg.lower() for msg in status_messages)
        # Should have completed (or at least tried summarizer)
        assert call_count[0] >= 3
