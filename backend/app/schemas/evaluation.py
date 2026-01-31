"""
Pydantic models for solution evaluation.
"""

from pydantic import BaseModel, Field


class StrengthItem(BaseModel):
    """A strength identified in the user's solution."""

    title: str = Field(description="Brief title of the strength")
    description: str = Field(description="Detailed explanation with code examples")


class ImprovementItem(BaseModel):
    """An area for improvement in the user's solution."""

    title: str = Field(description="Brief title of the improvement area")
    description: str = Field(description="Detailed explanation of what to improve")
    suggestion: str = Field(description="Concrete suggestion for improvement")


class SolutionFeedback(BaseModel):
    """Structured feedback on a user's solution."""

    score: float = Field(ge=0.0, le=10.0, description="Overall score from 0-10")
    strengths: list[StrengthItem] = Field(description="List of strengths in the solution")
    improvements: list[ImprovementItem] = Field(description="List of areas for improvement")
    summary_for_next_drill: str = Field(
        max_length=500,
        description="Concise summary for drill generator (max 500 chars)",
    )


# API Request/Response Models
class EvaluationRequest(BaseModel):
    """Request payload for solution evaluation."""

    solution: str = Field(min_length=1, description="The user's submitted solution")


class EvaluationData(BaseModel):
    """Data payload for evaluation response."""

    session_id: str
    feedback: SolutionFeedback
    feedback_file_path: str = Field(description="Path to the saved feedback markdown file")


class EvaluationResponse(BaseModel):
    """Successful evaluation response."""

    success: bool = True
    data: EvaluationData


class EvaluationErrorDetail(BaseModel):
    """Error detail for evaluation."""

    code: str
    message: str


class EvaluationErrorResponse(BaseModel):
    """Error response for evaluation."""

    success: bool = False
    error: EvaluationErrorDetail
