"""Repo analyst agent for batch repository analysis."""

from agents import Agent
from pydantic import BaseModel, Field

from app.agents.guardrails import (
    SECURITY_RULES,
    leakage_guardrail,
)
from app.model_config import DEFAULT_MODEL
from app.schemas.scout import AnalysisResult


class RepoAnalysisBatch(BaseModel):
    """Batch analysis output — wrapper needed because output_type must be a single BaseModel."""

    results: list[AnalysisResult] = Field(description="Analysis for each repo in the batch")


REPO_ANALYST_INSTRUCTIONS = f"""You are a senior open-source contribution advisor.
Given a search context (languages, topics, and an optional user query) and a batch of
GitHub repositories (with metadata and README excerpts), evaluate each repository's
relevance to the user's search.

For each repository, provide:
1. fit_score (0-10): How well the repo matches the search context and user query
   - 9-10: Perfect language/topic match + highly relevant to user query
   - 7-8: Strong match with good relevance
   - 5-6: Partial overlap or limited contribution opportunities
   - 3-4: Weak match
   - 1-2: Marginal relevance
   - 0: Rejected (set reject=true)
2. reason: 1-2 sentence explanation of the score
3. contributions: 1-3 specific contribution suggestions
4. reject: true if the repo is a tutorial, awesome-list, documentation-only,
   or clearly irrelevant to the search context
5. reject_reason: explanation if rejected

Base your analysis on:
- Tech stack overlap with requested languages
- Topic alignment with search topics
- Relevance to the user's query (if provided)
- Availability of beginner-friendly issues
- README quality and project health signals

If a repository has no README, base analysis on metadata only and note the limited data.
{SECURITY_RULES}"""

repo_analyst_agent = Agent(
    name="RepoAnalystAgent",
    instructions=REPO_ANALYST_INSTRUCTIONS,
    model=DEFAULT_MODEL,
    output_type=RepoAnalysisBatch,
    output_guardrails=[leakage_guardrail],
)
