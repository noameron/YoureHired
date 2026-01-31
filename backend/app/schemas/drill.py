"""
Pydantic models for drill generation system.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class DrillType(str, Enum):
    """Types of drill challenges."""

    CODING = "coding"
    DEBUGGING = "debugging"
    SYSTEM_DESIGN = "system_design"


class DifficultyLevel(str, Enum):
    """Drill difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Drill(BaseModel):
    """A complete drill/task for the user to practice."""

    title: str = Field(description="Concise, descriptive title for the drill")
    type: DrillType = Field(description="The type/category of this drill")
    difficulty: DifficultyLevel = Field(description="Difficulty level of the drill")
    description: str = Field(description="Full description of the problem/challenge")
    requirements: list[str] = Field(description="List of specific requirements to fulfill")
    starter_code: str | None = Field(default=None, description="Optional starter code template")
    hints: list[str] = Field(default_factory=list, description="Progressive hints for the user")
    expected_time_minutes: int = Field(
        ge=5, le=120, description="Expected time to complete in minutes"
    )
    tech_stack: list[str] = Field(
        default_factory=list, description="Technologies/languages relevant to this drill"
    )
    company_context: str | None = Field(
        default=None, description="How this drill relates to the target company"
    )


class DrillCandidate(BaseModel):
    """A drill candidate with metadata from a generator agent."""

    drill: Drill = Field(description="The generated drill")
    generator_type: DrillType = Field(description="Which generator produced this drill")
    reasoning: str = Field(description="Why this drill is relevant for the role/company")
    confidence_score: float = Field(
        ge=0.0, le=1.0, description="Generator's confidence in drill quality (0-1)"
    )


class CandidateEvaluation(BaseModel):
    """Evaluation of a single drill candidate."""

    generator_type: DrillType = Field(description="Which generator produced this candidate")
    relevance_score: float = Field(ge=0.0, le=1.0, description="How relevant to the role (0-1)")
    difficulty_appropriateness: float = Field(
        ge=0.0, le=1.0, description="How appropriate the difficulty is (0-1)"
    )
    company_fit_score: float = Field(
        ge=0.0, le=1.0, description="How well it matches company focus (0-1)"
    )
    overall_score: float = Field(ge=0.0, le=1.0, description="Combined score (0-1)")
    strengths: list[str] = Field(description="Drill strengths")
    weaknesses: list[str] = Field(description="Drill weaknesses")


class DrillEvaluation(BaseModel):
    """Evaluation result from the evaluator agent."""

    selected_drill: Drill = Field(description="The chosen best drill")
    selected_generator: DrillType = Field(description="Which generator produced the winning drill")
    selection_reasoning: str = Field(description="Why this drill was selected over others")
    evaluations: list[CandidateEvaluation] = Field(
        description="Individual evaluations of each candidate"
    )


# API Response Models (following existing patterns from company_info.py)
class DrillGenerationData(BaseModel):
    """Data payload for drill generation response."""

    session_id: str
    company_name: str
    role: str
    drill: Drill
    generation_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata about generation"
    )


class DrillGenerationResponse(BaseModel):
    """Successful drill generation response."""

    success: bool = True
    data: DrillGenerationData


class DrillGenerationErrorDetail(BaseModel):
    """Error detail for drill generation."""

    code: str
    message: str


class DrillGenerationError(BaseModel):
    """Error response for drill generation."""

    success: bool = False
    error: DrillGenerationErrorDetail


# Streaming Event Models (following existing patterns)
class DrillStreamStatusEvent(BaseModel):
    """Status update during drill generation."""

    type: Literal["status"] = "status"
    message: str
    generator: DrillType | None = None


class DrillStreamCandidateEvent(BaseModel):
    """Event when a candidate is ready."""

    type: Literal["candidate"] = "candidate"
    generator: DrillType
    title: str


class DrillStreamCompleteEvent(BaseModel):
    """Final result event."""

    type: Literal["complete"] = "complete"
    data: Drill


class DrillStreamErrorEvent(BaseModel):
    """Error event."""

    type: Literal["error"] = "error"
    message: str
