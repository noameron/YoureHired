"""Tests for company research timeout behavior."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.services.company_research import research_company_stream


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

            async def slow_runner(agent, input_str):
                await asyncio.sleep(0.1)  # 100ms > 10ms timeout

            with patch("app.services.company_research.Runner.run", side_effect=slow_runner):
                events = await collect_events(research_company_stream("TestCo", "Developer"))

        assert events[-1]["type"] == "error"
        assert "timed out" in events[-1]["message"].lower()

    @pytest.mark.asyncio
    async def test_search_timeout_continues_with_remaining(self):
        """When one search times out, remaining searches continue."""
        with patch("app.services.company_research.settings") as mock_settings:
            mock_settings.company_research_agent_timeout = 0.01  # 10ms

            call_count = [0]

            async def mock_runner(agent, input_str):
                call_count[0] += 1
                # Planner returns quickly with 2 searches
                if call_count[0] == 1:
                    result = MagicMock()
                    result.final_output = MagicMock()
                    result.final_output.searches = [
                        MagicMock(query="q1", reason="r1"),
                        MagicMock(query="q2", reason="r2"),
                    ]
                    return result
                # First search times out
                if call_count[0] == 2:
                    await asyncio.sleep(0.1)  # Exceeds timeout
                # Second search succeeds
                if call_count[0] == 3:
                    result = MagicMock()
                    result.final_output = "search result"
                    return result
                # Summarizer succeeds
                if call_count[0] == 4:
                    result = MagicMock()
                    result.final_output = MagicMock()
                    result.final_output.model_dump = lambda: {"summary": "test"}
                    return result
                return MagicMock()

            with patch("app.services.company_research.Runner.run", side_effect=mock_runner):
                events = await collect_events(research_company_stream("TestCo", "Developer"))

        # Should have continued despite one timeout
        status_messages = [e["message"] for e in events if e["type"] == "status"]
        assert any("timed out" in msg.lower() for msg in status_messages)
        # Should have completed (or at least tried summarizer)
        assert call_count[0] >= 3
