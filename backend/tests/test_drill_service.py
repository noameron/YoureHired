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

            async def slow_runner(agent, input_str):
                await asyncio.sleep(0.1)  # All exceed timeout

            with patch("app.services.drill_generation.Runner.run", side_effect=slow_runner):
                events = []
                async for event in generate_drill_stream("TestCo", "Developer"):
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

            async def mock_runner(agent, input_str):
                call_count[0] += 1
                # First generator times out
                if call_count[0] == 1:
                    await asyncio.sleep(0.1)  # Exceeds timeout
                # Other generators succeed quickly
                result = MagicMock()
                result.final_output = MagicMock()
                result.final_output.generator_type = DrillType.CODING
                result.final_output.drill = MagicMock()
                result.final_output.drill.title = "Test Drill"
                result.final_output.drill.model_dump = lambda: {"title": "Test"}
                return result

            with patch("app.services.drill_generation.Runner.run", side_effect=mock_runner):
                events = []
                async for event in generate_drill_stream("TestCo", "Developer"):
                    events.append(event)

        # Should have continued despite one timeout
        status_messages = [e.get("message", "") for e in events if e["type"] == "status"]
        assert any("timed out" in msg.lower() for msg in status_messages)
