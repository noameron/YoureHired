from typing import Literal

from pydantic import BaseModel, Field


# Agent structured outputs
class SearchQuery(BaseModel):
    reason: str = Field(description="Why this search helps understand the company")
    query: str = Field(description="The search query to execute")


class SearchPlan(BaseModel):
    searches: list[SearchQuery] = Field(description="List of searches to perform")


class TechStack(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)


class CompanySummary(BaseModel):
    name: str
    industry: str | None = None
    description: str = Field(description="2-3 sentence company overview")
    size: str | None = Field(default=None, description="e.g., '1000-5000 employees'")
    tech_stack: TechStack | None = None
    engineering_culture: str | None = None
    recent_news: list[str] = Field(default_factory=list)
    interview_tips: str | None = Field(default=None, description="Role-specific tips")
    sources: list[str] = Field(default_factory=list)


# API response models
class CompanyInfoData(BaseModel):
    session_id: str
    company_name: str
    role: str
    summary: CompanySummary


class CompanyInfoResponse(BaseModel):
    success: bool = True
    data: CompanyInfoData


class CompanyInfoErrorDetail(BaseModel):
    code: str
    message: str


class CompanyInfoError(BaseModel):
    success: bool = False
    error: CompanyInfoErrorDetail


# Streaming event models
class StreamStatusEvent(BaseModel):
    """Event for streaming status updates to frontend."""
    type: Literal["status"] = "status"
    message: str


class StreamCompleteEvent(BaseModel):
    """Event for streaming final result to frontend."""
    type: Literal["complete"] = "complete"
    data: CompanySummary


class StreamErrorEvent(BaseModel):
    """Event for streaming errors to frontend."""
    type: Literal["error"] = "error"
    message: str
