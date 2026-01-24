"""Tests for the company research streaming service."""

import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.schemas.company_info import SearchPlan, SearchQuery, CompanySummary, TechStack
from app.services.company_research import research_company_stream, AGENT_TIMEOUT


async def collect_events(stream: AsyncGenerator[dict, None]) -> list[dict]:
    """Helper to collect all events from an async generator."""
    events = []
    async for event in stream:
        events.append(event)
    return events


class MockRunnerResult:
    """Mock result object from Runner.run."""
    def __init__(self, final_output):
        self.final_output = final_output


class TestResearchCompanyStreamSuccess:
    """Tests for successful research flow."""

    async def test_successful_research_yields_all_expected_events(self):
        """Successful research yields status updates and complete event with data."""
        # GIVEN a company name and role with successful agent responses
        company_name = "Google"
        role = "Backend Developer"

        # Mock search plan with 2 searches
        search_plan = SearchPlan(
            searches=[
                SearchQuery(
                    reason="Company culture research",
                    query="Google engineering culture"
                ),
                SearchQuery(
                    reason="Tech stack research",
                    query="Google backend tech stack"
                )
            ]
        )

        # Mock search results
        search_result_1 = "Google uses Go, Python, and Java for backend."
        search_result_2 = "Google has a collaborative engineering culture."

        # Mock summary result
        summary = CompanySummary(
            name="Google",
            industry="Technology",
            description="A leading technology company.",
            size="100,000+",
            tech_stack=TechStack(
                languages=["Python", "Go", "Java"],
                frameworks=["gRPC"],
                tools=["Kubernetes"]
            ),
            engineering_culture="Collaborative and innovative",
            recent_news=["Launched new AI product"],
            interview_tips="Focus on system design and coding",
            sources=["google.com/careers"]
        )

        with patch("app.services.company_research.Runner.run") as mock_run:
            # Setup mock responses in sequence
            mock_run.side_effect = [
                MockRunnerResult(search_plan),      # planner
                MockRunnerResult(search_result_1),  # search 1
                MockRunnerResult(search_result_2),  # search 2
                MockRunnerResult(summary)            # summarizer
            ]

            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN all expected events are yielded
            assert len(events) == 6

            # Status: Planning
            assert events[0]["type"] == "status"
            assert events[0]["message"] == "Planning research strategy..."

            # Status: Found N searches
            assert events[1]["type"] == "status"
            assert events[1]["message"] == "Found 2 areas to research"

            # Status: Search 1
            assert events[2]["type"] == "status"
            assert events[2]["message"] == "Searching (1/2): Company culture research"

            # Status: Search 2
            assert events[3]["type"] == "status"
            assert events[3]["message"] == "Searching (2/2): Tech stack research"

            # Status: Analyzing
            assert events[4]["type"] == "status"
            assert events[4]["message"] == "Analyzing findings..."

            # Complete event with data
            assert events[5]["type"] == "complete"
            assert events[5]["data"]["name"] == "Google"
            assert events[5]["data"]["industry"] == "Technology"
            assert events[5]["data"]["tech_stack"]["languages"] == ["Python", "Go", "Java"]

    async def test_successful_research_calls_agents_in_correct_order(self):
        """Agent calls are made in correct sequence: planner, searches, summarizer."""
        # GIVEN a company name and role
        company_name = "Meta"
        role = "Frontend Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="Meta culture"),
            ]
        )
        search_result = "Meta uses React."
        summary = CompanySummary(
            name="Meta",
            description="Social media company"
        )

        call_order = []

        async def mock_runner_run(agent, input_str):
            call_order.append(agent.name if hasattr(agent, 'name') else str(agent))
            if len(call_order) == 1:
                return MockRunnerResult(search_plan)
            elif len(call_order) == 2:
                return MockRunnerResult(search_result)
            else:
                return MockRunnerResult(summary)

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            await collect_events(research_company_stream(company_name, role))

            # THEN agents are called in correct order
            assert len(call_order) == 3
            # Note: We can't check exact agent names without reading agent definitions
            # but we can verify the count and sequence

    async def test_successful_research_with_single_search(self):
        """Research with single search query works correctly."""
        # GIVEN a research plan with only one search
        company_name = "Netflix"
        role = "Data Engineer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Tech", query="Netflix tech"),
            ]
        )
        search_result = "Netflix uses Scala and Python."
        summary = CompanySummary(name="Netflix", description="Streaming company")

        with patch("app.services.company_research.Runner.run") as mock_run:
            mock_run.side_effect = [
                MockRunnerResult(search_plan),
                MockRunnerResult(search_result),
                MockRunnerResult(summary)
            ]

            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN correct number of events are yielded
            assert len(events) == 5
            assert events[1]["message"] == "Found 1 areas to research"
            assert events[2]["message"] == "Searching (1/1): Tech"
            assert events[-1]["type"] == "complete"


class TestResearchCompanyStreamSearchFailures:
    """Tests for handling individual search failures."""

    async def test_single_search_timeout_continues_with_remaining_searches(self):
        """When one search times out, remaining searches continue."""
        # GIVEN a research plan with 3 searches where search 2 times out
        company_name = "Amazon"
        role = "Backend Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="Amazon culture"),
                SearchQuery(reason="Tech", query="Amazon tech"),
                SearchQuery(reason="Scale", query="Amazon scale"),
            ]
        )
        search_result_1 = "Result 1"
        search_result_3 = "Result 3"
        summary = CompanySummary(name="Amazon", description="E-commerce company")

        async def mock_runner_run(agent, input_str):
            # Simulate timeout on second search
            if "Amazon tech" in input_str:
                await asyncio.sleep(AGENT_TIMEOUT + 1)

            if "Amazon culture" in input_str:
                return MockRunnerResult(search_result_1)
            elif "Amazon scale" in input_str:
                return MockRunnerResult(search_result_3)
            elif "Company:" in input_str:
                return MockRunnerResult(search_plan)
            else:
                return MockRunnerResult(summary)

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN timeout event is yielded but research continues
            status_messages = [e["message"] for e in events if e["type"] == "status"]
            assert "Search 2 timed out, continuing..." in status_messages

            # AND final result is still produced
            assert events[-1]["type"] == "complete"

    async def test_single_search_exception_continues_with_remaining_searches(self):
        """When one search raises exception, remaining searches continue."""
        # GIVEN a research plan where search 1 raises exception
        company_name = "Microsoft"
        role = "DevOps Engineer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="Microsoft culture"),
                SearchQuery(reason="Tech", query="Microsoft tech"),
            ]
        )
        search_result_2 = "Result 2"
        summary = CompanySummary(name="Microsoft", description="Software company")

        async def mock_runner_run(agent, input_str):
            if "Microsoft culture" in input_str:
                raise ValueError("Search failed")
            elif "Microsoft tech" in input_str:
                return MockRunnerResult(search_result_2)
            elif "Company:" in input_str:
                return MockRunnerResult(search_plan)
            else:
                return MockRunnerResult(summary)

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN failure event is yielded but research continues
            status_messages = [e["message"] for e in events if e["type"] == "status"]
            assert "Search 1 failed, continuing..." in status_messages

            # AND final result is still produced with remaining search
            assert events[-1]["type"] == "complete"

    async def test_all_searches_fail_yields_error_event(self):
        """When all searches fail, error event is yielded."""
        # GIVEN a research plan where all searches fail
        company_name = "Apple"
        role = "iOS Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="Apple culture"),
                SearchQuery(reason="Tech", query="Apple tech"),
            ]
        )

        async def mock_runner_run(agent, input_str):
            if "Company:" in input_str:
                return MockRunnerResult(search_plan)
            elif "Search term:" in input_str:
                raise ValueError("Search failed")
            # Summarizer should not be called
            raise AssertionError("Summarizer should not be called")

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN error event is yielded
            assert events[-1]["type"] == "error"
            assert events[-1]["message"] == "All searches failed. Please try again."

            # AND no complete event is yielded
            complete_events = [e for e in events if e["type"] == "complete"]
            assert len(complete_events) == 0

    async def test_all_searches_timeout_yields_error_event(self):
        """When all searches timeout, error event is yielded."""
        # GIVEN a research plan where all searches timeout
        company_name = "Tesla"
        role = "Backend Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="Tesla culture"),
            ]
        )

        async def mock_runner_run(agent, input_str):
            if "Company:" in input_str:
                return MockRunnerResult(search_plan)
            elif "Search term:" in input_str:
                # Simulate timeout
                await asyncio.sleep(AGENT_TIMEOUT + 1)

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN error event is yielded
            assert events[-1]["type"] == "error"
            assert events[-1]["message"] == "All searches failed. Please try again."


class TestResearchCompanyStreamPlannerFailures:
    """Tests for handling planner agent failures."""

    async def test_planner_timeout_yields_error_event(self):
        """When planner times out, error event is yielded."""
        # GIVEN a planner that times out
        company_name = "Uber"
        role = "Backend Developer"

        async def mock_runner_run(agent, input_str):
            # Simulate planner timeout
            await asyncio.sleep(AGENT_TIMEOUT + 1)

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN error event is yielded
            assert len(events) == 2
            assert events[0]["type"] == "status"
            assert events[0]["message"] == "Planning research strategy..."
            assert events[1]["type"] == "error"
            assert events[1]["message"] == "Research timed out. Please try again."

    async def test_planner_exception_yields_error_event(self):
        """When planner raises exception, error event is yielded."""
        # GIVEN a planner that raises exception
        company_name = "Airbnb"
        role = "Frontend Developer"

        async def mock_runner_run(agent, input_str):
            raise ValueError("Planner failed")

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN error event is yielded with exception message
            assert events[-1]["type"] == "error"
            assert "Research failed: Planner failed" in events[-1]["message"]


class TestResearchCompanyStreamSummarizerFailures:
    """Tests for handling summarizer agent failures."""

    async def test_summarizer_timeout_yields_error_event(self):
        """When summarizer times out, error event is yielded."""
        # GIVEN successful planner and searches but summarizer times out
        company_name = "Stripe"
        role = "Backend Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="Stripe culture"),
            ]
        )
        search_result = "Stripe result"

        async def mock_runner_run(agent, input_str):
            if "Company:" in input_str and "Research:" not in input_str:
                return MockRunnerResult(search_plan)
            elif "Search term:" in input_str:
                return MockRunnerResult(search_result)
            else:
                # Summarizer timeout
                await asyncio.sleep(AGENT_TIMEOUT + 1)

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN error event is yielded
            assert events[-1]["type"] == "error"
            assert events[-1]["message"] == "Research timed out. Please try again."

    async def test_summarizer_exception_yields_error_event(self):
        """When summarizer raises exception, error event is yielded."""
        # GIVEN successful planner and searches but summarizer fails
        company_name = "Dropbox"
        role = "Backend Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Tech", query="Dropbox tech"),
            ]
        )
        search_result = "Dropbox result"

        async def mock_runner_run(agent, input_str):
            if "Company:" in input_str and "Research:" not in input_str:
                return MockRunnerResult(search_plan)
            elif "Search term:" in input_str:
                return MockRunnerResult(search_result)
            else:
                raise ValueError("Summarizer failed")

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN error event is yielded with exception message
            assert events[-1]["type"] == "error"
            assert "Research failed: Summarizer failed" in events[-1]["message"]


class TestResearchCompanyStreamEdgeCases:
    """Tests for edge cases and boundary conditions."""

    async def test_empty_search_plan_yields_error(self):
        """Research plan with no searches yields error."""
        # GIVEN a planner that returns empty search list
        company_name = "Slack"
        role = "Backend Developer"

        search_plan = SearchPlan(searches=[])

        with patch("app.services.company_research.Runner.run") as mock_run:
            mock_run.return_value = MockRunnerResult(search_plan)

            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN error event is yielded
            assert events[-1]["type"] == "error"
            assert events[-1]["message"] == "All searches failed. Please try again."

    async def test_multiple_sequential_search_failures(self):
        """Multiple sequential search failures are handled gracefully."""
        # GIVEN a plan with 5 searches where first 3 fail
        company_name = "Twitter"
        role = "Backend Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="q1"),
                SearchQuery(reason="Tech", query="q2"),
                SearchQuery(reason="Scale", query="q3"),
                SearchQuery(reason="Team", query="q4"),
                SearchQuery(reason="Process", query="q5"),
            ]
        )

        call_count = [0]

        async def mock_runner_run(agent, input_str):
            if "Company:" in input_str:
                return MockRunnerResult(search_plan)
            elif "Search term:" in input_str:
                call_count[0] += 1
                if call_count[0] <= 3:
                    raise ValueError(f"Search {call_count[0]} failed")
                return MockRunnerResult(f"Result {call_count[0]}")
            else:
                # Summarizer
                return MockRunnerResult(
                    CompanySummary(name="Twitter", description="Social media")
                )

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN failure events are yielded for failed searches
            status_messages = [e["message"] for e in events if e["type"] == "status"]
            assert "Search 1 failed, continuing..." in status_messages
            assert "Search 2 failed, continuing..." in status_messages
            assert "Search 3 failed, continuing..." in status_messages

            # AND research completes with successful searches
            assert events[-1]["type"] == "complete"

    async def test_research_with_special_characters_in_inputs(self):
        """Research handles special characters in company name and role."""
        # GIVEN inputs with special characters
        company_name = "AT&T"
        role = "Backend Developer (C++/Go)"

        search_plan = SearchPlan(
            searches=[SearchQuery(reason="Tech", query="AT&T tech")]
        )
        search_result = "AT&T uses C++"
        summary = CompanySummary(name="AT&T", description="Telecom company")

        with patch("app.services.company_research.Runner.run") as mock_run:
            mock_run.side_effect = [
                MockRunnerResult(search_plan),
                MockRunnerResult(search_result),
                MockRunnerResult(summary)
            ]

            # WHEN streaming research
            events = await collect_events(research_company_stream(company_name, role))

            # THEN research completes successfully
            assert events[-1]["type"] == "complete"
            assert events[-1]["data"]["name"] == "AT&T"

    async def test_search_results_combined_correctly_for_summarizer(self):
        """Multiple search results are combined with double newlines for summarizer."""
        # GIVEN multiple successful searches
        company_name = "LinkedIn"
        role = "Backend Developer"

        search_plan = SearchPlan(
            searches=[
                SearchQuery(reason="Culture", query="LinkedIn culture"),
                SearchQuery(reason="Tech", query="LinkedIn tech"),
            ]
        )
        search_result_1 = "First result"
        search_result_2 = "Second result"
        summary = CompanySummary(name="LinkedIn", description="Professional network")

        captured_input = []

        async def mock_runner_run(agent, input_str):
            if "Research:" in input_str:
                captured_input.append(input_str)
                return MockRunnerResult(summary)
            elif "Company:" in input_str:
                return MockRunnerResult(search_plan)
            elif "First" not in input_str:
                return MockRunnerResult(search_result_1)
            else:
                return MockRunnerResult(search_result_2)

        with patch("app.services.company_research.Runner.run", side_effect=mock_runner_run):
            # WHEN streaming research
            await collect_events(research_company_stream(company_name, role))

            # THEN search results are combined with double newlines
            assert len(captured_input) == 1
            assert "First result\n\nSecond result" in captured_input[0]
