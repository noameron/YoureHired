"""Repo analyst agent for batch repository analysis."""

from agents import Agent
from pydantic import BaseModel, Field

from app.agents.guardrails import (
    SECURITY_RULES,
    injection_guardrail,
    leakage_guardrail,
)
from app.model_config import DEFAULT_MODEL
from app.schemas.scout import AnalysisResult


class RepoAnalysisBatch(BaseModel):
    """Batch analysis output — wrapper needed because output_type must be a single BaseModel."""

    results: list[AnalysisResult] = Field(description="Analysis for each repo in the batch")


REPO_ANALYST_INSTRUCTIONS = f"""You are a senior open-source contribution advisor.
Given a developer profile and a batch of GitHub repositories (with metadata and README excerpts),
evaluate each repository's fit for the developer.

For each repository, provide:
1. fit_score (0-10): How well the repo matches the developer's skills and goals
   - 9-10: Perfect tech stack match + active issues in developer's domain
   - 7-8: Strong match with some relevant issues
   - 5-6: Partial tech stack overlap or limited contribution opportunities
   - 3-4: Weak match
   - 1-2: Marginal relevance
   - 0: Rejected (set reject=true)
2. reason: 1-2 sentence explanation of the score
3. contributions: 1-3 specific contribution suggestions
4. reject: true if the repo is a tutorial, awesome-list, documentation-only,
   or clearly outside the developer's domain
5. reject_reason: explanation if rejected

Base your analysis on:
- Tech stack overlap with developer's languages
- Topic alignment with developer's interests
- Availability of beginner-friendly issues (for beginner/intermediate developers)
- Project complexity vs developer skill level
- Contribution goal alignment
- README quality and project health signals

If a repository has no README, base analysis on metadata only and note the limited data.
{SECURITY_RULES}"""

repo_analyst_agent = Agent(
    name="RepoAnalystAgent",
    instructions=REPO_ANALYST_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=RepoAnalysisBatch,
    input_guardrails=[injection_guardrail],
    output_guardrails=[leakage_guardrail],
)
