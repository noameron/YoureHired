"""Tests for drill generation service orchestration."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.company_info import CompanySummary, TechStack
from app.schemas.drill import DrillType
from app.services.drill_generation import (
    _build_evaluator_input,
    _build_generator_input,
    generate_drill_stream,
)
from tests.conftest import mock_streamed_result


class TestBuildGeneratorInput:
    """Tests for _build_generator_input function."""

    def test_minimal_input(self):
        """Input with only required fields."""
        result = _build_generator_input("Google", "Backend Developer", None)
        assert "Company: Google" in result
        assert "Role: Backend Developer" in result
        assert "Role Description" not in result
        assert "Company Context" not in result

    def test_with_role_description(self):
        """Input with role description."""
        result = _build_generator_input("Meta", "Frontend Developer", "React expertise required")
        assert "Role Description: React expertise required" in result

    def test_with_company_summary(self):
        """Input with company summary includes all context."""
        summary = CompanySummary(
            name="Google",
            industry="Technology",
            description="Search and cloud company",
            size="Large",
            tech_stack=TechStack(
                languages=["Python", "Go"],
                frameworks=["TensorFlow"],
                tools=["Kubernetes"],
            ),
            engineering_culture="Data-driven engineering",
            interview_tips="Focus on system design",
            recent_news=["Launched new AI model"],
            sources=["google.com"],
        )
        result = _build_generator_input(
            "Google", "Backend Developer", "Distributed systems", summary
        )

        assert "Company Context:" in result
        assert "Industry: Technology" in result
        assert "Description: Search and cloud company" in result
        assert "Tech Stack: Python, Go, TensorFlow, Kubernetes" in result
        assert "Engineering Culture: Data-driven engineering" in result
        assert "Interview Tips: Focus on system design" in result


class TestBuildEvaluatorInput:
    """Tests for _build_evaluator_input function."""

    def test_evaluator_input_format(self):
        """Evaluator input includes all candidate details."""
        # Create mock candidates inline for this test
        from app.schemas.drill import DifficultyLevel, Drill, DrillCandidate

        def make_drill(title: str, drill_type: DrillType) -> Drill:
            return Drill(
                title=title,
                type=drill_type,
                difficulty=DifficultyLevel.MEDIUM,
                description=f"Description for {title}",
                requirements=["Requirement 1"],
                expected_time_minutes=30,
                tech_stack=["Python"],
            )

        def make_candidate(title: str, drill_type: DrillType) -> DrillCandidate:
            return DrillCandidate(
                drill=make_drill(title, drill_type),
                generator_type=drill_type,
                reasoning=f"Reasoning for {title}",
                confidence_score=0.8,
            )

        candidates = [
            make_candidate("Coding Challenge", DrillType.CODING),
            make_candidate("Debug Task", DrillType.DEBUGGING),
        ]
        result = _build_evaluator_input("Google", "Backend Developer", candidates)

        assert "Company: Google" in result
        assert "Role: Backend Developer" in result
        assert "CANDIDATES TO EVALUATE:" in result
        assert "Candidate 1 (coding)" in result
        assert "Candidate 2 (debugging)" in result
        assert "Coding Challenge" in result
        assert "Debug Task" in result


class TestDrillGenerationTimeout:
    """Tests for timeout behavior in drill generation."""

    @pytest.mark.asyncio
    async def test_all_generators_timeout_yields_error(self):
        """When all generators timeout, error event is yielded."""
        with patch("app.services.drill_generation.settings") as mock_settings:
            mock_settings.drill_generation_agent_timeout = 0.01  # 10ms

            def slow_streamed(agent, input_str):
                mock = MagicMock()
                mock.final_output = None
                mock.is_complete = False

                async def slow_stream():
                    await asyncio.sleep(0.1)  # All exceed timeout
                    yield

                mock.stream_events = slow_stream
                return mock

            with patch(
                "app.services.task_registry.Runner.run_streamed",
                side_effect=slow_streamed,
            ):
                events = []
                async for event in generate_drill_stream(
                    "TestCo", "Developer", "test-session"
                ):
                    events.append(event)

        assert events[-1]["type"] == "error"
        assert (
            "failed" in events[-1]["message"].lower()
            or "try again" in events[-1]["message"].lower()
        )

    @pytest.mark.asyncio
    async def test_partial_generator_timeout_continues(self):
        """When some generators timeout, others continue."""
        with patch("app.services.drill_generation.settings") as mock_settings:
            mock_settings.drill_generation_agent_timeout = 0.01  # 10ms

            call_count = [0]

            def mock_run_streamed(agent, input_str):
                call_count[0] += 1
                current = call_count[0]

                # First generator times out
                if current == 1:
                    mock = MagicMock()
                    mock.final_output = None
                    mock.is_complete = False

                    async def slow_stream():
                        await asyncio.sleep(0.1)  # Exceeds timeout
                        yield

                    mock.stream_events = slow_stream
                    return mock

                # Other generators succeed quickly
                result_mock = MagicMock()
                result_mock.generator_type = DrillType.CODING
                result_mock.drill = MagicMock()
                result_mock.drill.title = "Test Drill"
                result_mock.drill.model_dump = lambda: {"title": "Test"}
                return mock_streamed_result(result_mock)

            with patch(
                "app.services.task_registry.Runner.run_streamed",
                side_effect=mock_run_streamed,
            ):
                events = []
                async for event in generate_drill_stream(
                    "TestCo", "Developer", "test-session"
                ):
                    events.append(event)

        # Should have continued despite one timeout
        status_messages = [e.get("message", "") for e in events if e["type"] == "status"]
        assert any("timed out" in msg.lower() for msg in status_messages)
