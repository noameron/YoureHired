"""Tests for drill Pydantic schemas."""
import pytest
from pydantic import ValidationError

from app.schemas.drill import (
    CandidateEvaluation,
    DifficultyLevel,
    Drill,
    DrillCandidate,
    DrillEvaluation,
    DrillGenerationData,
    DrillGenerationResponse,
    DrillStreamCompleteEvent,
    DrillStreamErrorEvent,
    DrillStreamStatusEvent,
    DrillType,
)


class TestDrillSchema:
    """Tests for the Drill schema."""

    def test_valid_drill_minimal(self):
        """Drill with only required fields is valid."""
        drill = Drill(
            title="Implement a Queue",
            type=DrillType.CODING,
            difficulty=DifficultyLevel.MEDIUM,
            description="Implement a queue using two stacks.",
            requirements=["O(1) amortized enqueue", "O(1) amortized dequeue"],
            expected_time_minutes=30,
        )
        assert drill.title == "Implement a Queue"
        assert drill.hints == []  # default
        assert drill.starter_code is None  # default
        assert drill.tech_stack == []  # default

    def test_valid_drill_full(self):
        """Drill with all fields is valid."""
        drill = Drill(
            title="Debug the Cache",
            type=DrillType.DEBUGGING,
            difficulty=DifficultyLevel.HARD,
            description="Find and fix bugs in this LRU cache.",
            requirements=["Fix all bugs", "Don't change the API"],
            starter_code="class LRUCache:\n    pass",
            hints=["Check the eviction logic", "Look at capacity"],
            expected_time_minutes=45,
            tech_stack=["Python"],
            company_context="Similar to Meta's cache systems",
        )
        assert drill.starter_code is not None
        assert len(drill.hints) == 2
        assert drill.tech_stack == ["Python"]

    def test_invalid_time_too_low(self):
        """Expected time below 5 minutes is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            Drill(
                title="Quick Task",
                type=DrillType.CODING,
                difficulty=DifficultyLevel.EASY,
                description="Too quick",
                requirements=["Done"],
                expected_time_minutes=2,
            )
        assert "expected_time_minutes" in str(exc_info.value)

    def test_invalid_time_too_high(self):
        """Expected time above 120 minutes is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            Drill(
                title="Long Task",
                type=DrillType.CODING,
                difficulty=DifficultyLevel.HARD,
                description="Too long",
                requirements=["Done"],
                expected_time_minutes=180,
            )
        assert "expected_time_minutes" in str(exc_info.value)

    def test_drill_types(self):
        """All drill types are valid."""
        for drill_type in DrillType:
            drill = Drill(
                title=f"Test {drill_type.value}",
                type=drill_type,
                difficulty=DifficultyLevel.MEDIUM,
                description="Test description",
                requirements=["Test"],
                expected_time_minutes=30,
            )
            assert drill.type == drill_type

    def test_difficulty_levels(self):
        """All difficulty levels are valid."""
        for level in DifficultyLevel:
            drill = Drill(
                title=f"Test {level.value}",
                type=DrillType.CODING,
                difficulty=level,
                description="Test description",
                requirements=["Test"],
                expected_time_minutes=30,
            )
            assert drill.difficulty == level


class TestDrillCandidateSchema:
    """Tests for the DrillCandidate schema."""

    def test_valid_candidate(self):
        """Valid candidate with all fields."""
        candidate = DrillCandidate(
            drill=Drill(
                title="Test Drill",
                type=DrillType.CODING,
                difficulty=DifficultyLevel.MEDIUM,
                description="A test",
                requirements=["Complete it"],
                expected_time_minutes=30,
            ),
            generator_type=DrillType.CODING,
            reasoning="This tests fundamental skills",
            confidence_score=0.85,
        )
        assert candidate.confidence_score == 0.85
        assert candidate.generator_type == DrillType.CODING

    def test_invalid_confidence_too_high(self):
        """Confidence score above 1.0 is invalid."""
        with pytest.raises(ValidationError):
            DrillCandidate(
                drill=Drill(
                    title="Test",
                    type=DrillType.CODING,
                    difficulty=DifficultyLevel.EASY,
                    description="Test",
                    requirements=["Test"],
                    expected_time_minutes=10,
                ),
                generator_type=DrillType.CODING,
                reasoning="Test",
                confidence_score=1.5,
            )

    def test_invalid_confidence_negative(self):
        """Confidence score below 0.0 is invalid."""
        with pytest.raises(ValidationError):
            DrillCandidate(
                drill=Drill(
                    title="Test",
                    type=DrillType.CODING,
                    difficulty=DifficultyLevel.EASY,
                    description="Test",
                    requirements=["Test"],
                    expected_time_minutes=10,
                ),
                generator_type=DrillType.CODING,
                reasoning="Test",
                confidence_score=-0.1,
            )


class TestCandidateEvaluationSchema:
    """Tests for the CandidateEvaluation schema."""

    def test_valid_evaluation(self):
        """Valid evaluation with all scores."""
        evaluation = CandidateEvaluation(
            generator_type=DrillType.DEBUGGING,
            relevance_score=0.9,
            difficulty_appropriateness=0.8,
            company_fit_score=0.7,
            overall_score=0.82,
            strengths=["Realistic scenario", "Good complexity"],
            weaknesses=["Could be more specific"],
        )
        assert evaluation.overall_score == 0.82
        assert len(evaluation.strengths) == 2
        assert len(evaluation.weaknesses) == 1

    def test_boundary_scores(self):
        """Boundary scores (0.0 and 1.0) are valid."""
        evaluation = CandidateEvaluation(
            generator_type=DrillType.SYSTEM_DESIGN,
            relevance_score=0.0,
            difficulty_appropriateness=1.0,
            company_fit_score=0.5,
            overall_score=0.5,
            strengths=[],
            weaknesses=[],
        )
        assert evaluation.relevance_score == 0.0
        assert evaluation.difficulty_appropriateness == 1.0


class TestDrillEvaluationSchema:
    """Tests for the DrillEvaluation schema."""

    def test_valid_drill_evaluation(self):
        """Valid drill evaluation with selected drill."""
        selected_drill = Drill(
            title="Selected Drill",
            type=DrillType.DEBUGGING,
            difficulty=DifficultyLevel.MEDIUM,
            description="The best drill",
            requirements=["Fix bugs"],
            expected_time_minutes=30,
        )
        evaluation = DrillEvaluation(
            selected_drill=selected_drill,
            selected_generator=DrillType.DEBUGGING,
            selection_reasoning="Best fit for backend role",
            evaluations=[
                CandidateEvaluation(
                    generator_type=DrillType.DEBUGGING,
                    relevance_score=0.9,
                    difficulty_appropriateness=0.9,
                    company_fit_score=0.8,
                    overall_score=0.87,
                    strengths=["Great"],
                    weaknesses=["None"],
                ),
            ],
        )
        assert evaluation.selected_drill.title == "Selected Drill"
        assert evaluation.selected_generator == DrillType.DEBUGGING


class TestAPIResponseSchemas:
    """Tests for API response schemas."""

    def test_drill_generation_response(self):
        """DrillGenerationResponse serializes correctly."""
        drill = Drill(
            title="API Test Drill",
            type=DrillType.CODING,
            difficulty=DifficultyLevel.EASY,
            description="Test",
            requirements=["Test"],
            expected_time_minutes=15,
        )
        response = DrillGenerationResponse(
            data=DrillGenerationData(
                session_id="test-session",
                company_name="TestCorp",
                role="backend_developer",
                drill=drill,
                generation_metadata={"generators_used": ["coding"]},
            )
        )
        assert response.success is True
        assert response.data.session_id == "test-session"
        assert response.data.drill.title == "API Test Drill"


class TestStreamingEventSchemas:
    """Tests for streaming event schemas."""

    def test_status_event(self):
        """Status event serializes correctly."""
        event = DrillStreamStatusEvent(message="Generating drills...")
        assert event.type == "status"
        assert event.message == "Generating drills..."
        assert event.generator is None

    def test_status_event_with_generator(self):
        """Status event with generator type."""
        event = DrillStreamStatusEvent(
            message="Coding generator complete",
            generator=DrillType.CODING,
        )
        assert event.generator == DrillType.CODING

    def test_complete_event(self):
        """Complete event contains drill data."""
        drill = Drill(
            title="Complete Drill",
            type=DrillType.SYSTEM_DESIGN,
            difficulty=DifficultyLevel.HARD,
            description="Design a system",
            requirements=["Scalable"],
            expected_time_minutes=60,
        )
        event = DrillStreamCompleteEvent(data=drill)
        assert event.type == "complete"
        assert event.data.title == "Complete Drill"

    def test_error_event(self):
        """Error event contains message."""
        event = DrillStreamErrorEvent(message="Generation failed")
        assert event.type == "error"
        assert event.message == "Generation failed"
