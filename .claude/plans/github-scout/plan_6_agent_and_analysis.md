# Plan 6: Repo Analyst Agent & Batch Analysis

**Branch:** `scout/06-agent-and-analysis`
**Depends on:** plan_1 (schemas for `AnalysisResult`, `DeveloperProfile`, `RepoMetadata`)
**Blocks:** plan_7
**Parallel with:** plan_4, plan_5

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "New AI agent (`repo_analyst`) that scores repos in batches of 5-10"
- Design: `openspec/changes/add-github-scout/design.md` — Decision 5 (batched AI agent with structured JSON output, 40-60% cheaper than per-repo)
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 6.1-6.3 (agent), Task 7.1 (scout_analysis.py)

## Production Files (2)

### 1. CREATE `backend/app/agents/repo_analyst_agent.py`

Follow pattern from `backend/app/agents/drill/coding_drill_agent.py`.

```python
from pydantic import BaseModel, Field

from agents import Agent

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
4. reject: true if the repo is a tutorial, awesome-list, documentation-only, or clearly outside the developer's domain
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
```

### 2. CREATE `backend/app/services/scout_analysis.py`

Follow pattern from `backend/app/services/drill_generation.py` (parallel execution with `asyncio.as_completed`) and `backend/app/services/company_research.py` (streaming progress events).

```python
import asyncio
from collections.abc import AsyncGenerator

from app.agents.repo_analyst_agent import RepoAnalysisBatch, repo_analyst_agent
from app.config import settings
from app.schemas.scout import AnalysisResult, DeveloperProfile, RepoMetadata
from app.services.task_registry import run_agent_streamed


def _build_batch_input(
    profile: DeveloperProfile,
    repos: list[RepoMetadata],
    readmes: dict[str, str | None],
) -> str:
    """Build the text prompt for a batch of repos."""
    # Includes: DEVELOPER PROFILE section + REPOSITORIES TO ANALYZE section
    # Each repo: key, URL, description, languages, stars, issues, topics, license, README excerpt


def batch_repos(
    repos: list[RepoMetadata], batch_size: int
) -> list[list[RepoMetadata]]:
    """Split repos into batches of batch_size."""
    return [repos[i : i + batch_size] for i in range(0, len(repos), batch_size)]


async def analyze_batch(
    profile: DeveloperProfile,
    repos: list[RepoMetadata],
    readmes: dict[str, str | None],
    session_id: str,
) -> list[AnalysisResult]:
    """Analyze a single batch via the repo_analyst_agent."""
    batch_input = _build_batch_input(profile, repos, readmes)
    output = await run_agent_streamed(
        repo_analyst_agent,
        batch_input,
        session_id,
        timeout=settings.scout_analysis_timeout,
    )
    if output is None:
        return []
    batch_result: RepoAnalysisBatch = output
    return batch_result.results


async def analyze_repos_streamed(
    profile: DeveloperProfile,
    repos: list[RepoMetadata],
    readmes: dict[str, str | None],
    session_id: str,
) -> AsyncGenerator[tuple[list[AnalysisResult], dict[str, object]], None]:
    """Run batched analysis with concurrent execution and progress streaming.
    Yields (accumulated_results, progress_event) after each batch completes.
    """
    capped = repos[: settings.scout_max_repos]
    batches = batch_repos(capped, settings.scout_batch_size)
    total = len(capped)
    analyzed = 0
    all_results: list[AnalysisResult] = []

    tasks = [
        asyncio.create_task(analyze_batch(profile, batch, readmes, session_id))
        for batch in batches
    ]

    for coro in asyncio.as_completed(tasks):
        try:
            batch_results = await coro
            all_results.extend(batch_results)
            analyzed += len(batch_results)
            yield all_results, {
                "type": "status",
                "message": f"Analyzed {analyzed}/{total} repos...",
                "phase": "analyzing",
            }
        except TimeoutError:
            analyzed += settings.scout_batch_size
            yield all_results, {
                "type": "status",
                "message": f"Batch timed out, skipping... ({analyzed}/{total})",
                "phase": "analyzing",
            }
        except Exception:
            analyzed += settings.scout_batch_size
            yield all_results, {
                "type": "status",
                "message": f"Batch failed, continuing... ({analyzed}/{total})",
                "phase": "analyzing",
            }
```

**`_build_batch_input` output format:**

```
DEVELOPER PROFILE:
Languages: Python, Go
Topics: web-framework, api
Skill Level: intermediate
Goals: Contribute to API frameworks

REPOSITORIES TO ANALYZE:

--- owner/repo-name ---
URL: https://github.com/owner/repo-name
Description: A fast web framework
Primary Language: Python
Languages: Python, JavaScript
Stars: 12500
Open Issues: 234
Good First Issues: 15
Help Wanted: 8
Topics: web, api, framework
License: MIT
Last Pushed: 2025-12-01
README (excerpt):
[truncated to 16000 chars]
```

## Test Files

- `backend/tests/test_repo_analyst_agent.py`
  - `RepoAnalysisBatch` validates correctly with valid `AnalysisResult` list
  - `RepoAnalysisBatch` rejects `fit_score` outside 0-10
  - Empty results list is valid

- `backend/tests/test_scout_analysis.py`
  - `batch_repos` splits 25 repos into 3 batches (10, 10, 5) with `batch_size=10`
  - `batch_repos` with empty list → `[]`
  - `batch_repos` with 5 repos and `batch_size=10` → `[[5 repos]]`
  - `_build_batch_input` includes profile and repo metadata in output
  - `_build_batch_input` includes README excerpt when available
  - `_build_batch_input` shows "Not available" when README is `None`
  - `analyze_batch` with mocked `run_agent_streamed` returning `RepoAnalysisBatch`
  - `analyze_batch` when agent returns `None` (cancelled) → returns `[]`
  - `analyze_repos_streamed` yields progress events after each batch
  - `analyze_repos_streamed` handles timeout in one batch, continues with others
  - `analyze_repos_streamed` handles exception in one batch, continues
  - `analyze_repos_streamed` caps repos at `scout_max_repos`
  - All tests mock `run_agent_streamed` (no real LLM calls)

## Edge Cases

- Agent returns fewer results than repos in batch → accept what's returned
- Agent timeout → `TimeoutError` caught per-batch, skipped, remaining batches continue
- Agent cancelled (`run_agent_streamed` returns `None`) → `analyze_batch` returns `[]`
- All batches fail → generator yields empty accumulated results with error events
- Guardrail trip → `InputGuardrailTripwireTriggered` / `OutputGuardrailTripwireTriggered` propagates up (not caught here)
- `session_id` for task_registry: uses `run_id` — UUID collision with practice sessions negligible

## Verification

```bash
cd backend && uv run pytest tests/test_repo_analyst_agent.py tests/test_scout_analysis.py -v
```
