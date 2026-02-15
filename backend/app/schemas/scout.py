"""Pydantic models for GitHub Scout feature."""

from typing import Literal, Self

from pydantic import BaseModel, Field, model_validator


class ProfileIdResponse(BaseModel):
    """Response after saving a developer profile."""

    id: str


class DeveloperProfile(BaseModel):
    """Developer profile for repository matching."""

    languages: list[str] = Field(min_length=1)
    topics: list[str] = Field(default_factory=list)
    skill_level: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    goals: str = Field(default="", max_length=500)


class DeveloperProfileResponse(BaseModel):
    """API response for a stored developer profile."""

    id: str
    profile: DeveloperProfile
    created_at: str
    updated_at: str | None = None


class SearchFilters(BaseModel):
    """Filters for GitHub repository search."""

    languages: list[str] = Field(min_length=1)
    min_stars: int = Field(default=10, ge=0)
    max_stars: int = Field(default=50000, ge=0)
    topics: list[str] = Field(default_factory=list)
    min_activity_date: str | None = Field(default=None)
    license: str | None = None

    @model_validator(mode="after")
    def validate_star_range(self) -> Self:
        if self.min_stars > self.max_stars:
            raise ValueError("min_stars must be <= max_stars")
        return self


class RepoMetadata(BaseModel):
    """Full metadata for a GitHub repository."""

    github_id: int
    owner: str
    name: str
    url: str
    description: str | None = None
    primary_language: str | None = None
    languages: list[str] = Field(default_factory=list)
    star_count: int = 0
    fork_count: int = 0
    open_issue_count: int = 0
    topics: list[str] = Field(default_factory=list)
    license: str | None = None
    pushed_at: str | None = None
    created_at: str | None = None
    good_first_issue_count: int = 0
    help_wanted_count: int = 0


class AnalysisResult(BaseModel):
    """LLM analysis result for a single repository."""

    repo: str
    fit_score: float = Field(ge=0.0, le=10.0)
    reason: str
    contributions: list[str] = Field(default_factory=list)
    reject: bool = False
    reject_reason: str | None = None


SearchRunStatus = Literal["running", "completed", "failed", "cancelled", "partial"]


class SearchRunResponse(BaseModel):
    """Response when starting a scout search run."""

    run_id: str
    status: SearchRunStatus


class ScoutSearchResult(BaseModel):
    """Complete result of a scout search run."""

    run_id: str
    status: SearchRunStatus
    total_discovered: int = 0
    total_filtered: int = 0
    total_analyzed: int = 0
    results: list[AnalysisResult] = Field(default_factory=list)
    repos: list[RepoMetadata] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ScoutStreamStatusEvent(BaseModel):
    """Status update during scout search."""

    type: Literal["status"] = "status"
    message: str
    phase: Literal["discovering", "filtering", "analyzing"] | None = None


class ScoutStreamCompleteEvent(BaseModel):
    """Final result event for scout search."""

    type: Literal["complete"] = "complete"
    data: ScoutSearchResult


class ScoutStreamErrorEvent(BaseModel):
    """Error event for scout search."""

    type: Literal["error"] = "error"
    message: str
