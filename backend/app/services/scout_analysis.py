"""Batch analysis service for scout repository evaluation."""

import asyncio
import logging
import uuid
from collections.abc import AsyncGenerator

from app.agents.repo_analyst_agent import RepoAnalysisBatch, repo_analyst_agent
from app.config import settings
from app.schemas.scout import AnalysisResult, DeveloperProfile, RepoMetadata
from app.services.task_registry import run_agent_streamed

# Approximately 4K tokens for GPT-4o-mini context window
_README_MAX_CHARS = 16_000

logger = logging.getLogger(__name__)


def _build_batch_input(
    profile: DeveloperProfile,
    repos: list[RepoMetadata],
    readmes: list[str | None],
) -> str:
    """Build the text prompt for a batch of repos.

    Args:
        profile: Developer profile with languages, topics, skill level, goals
        repos: List of repository metadata
        readmes: List of README content (must match length of repos)

    Raises:
        ValueError: If repos and readmes have different lengths
    """
    if len(repos) != len(readmes):
        raise ValueError(
            f"repos and readmes must have same length: {len(repos)} vs {len(readmes)}"
        )

    lines = [
        "DEVELOPER PROFILE:",
        f"Languages: {', '.join(profile.languages)}",
        f"Topics: {', '.join(profile.topics)}",
        f"Skill Level: {profile.skill_level}",
        f"Goals: {profile.goals}",
        "",
        "REPOSITORIES TO ANALYZE:",
    ]

    for i, repo in enumerate(repos):
        readme = readmes[i]
        lines.append("")
        lines.append(f"--- {repo.owner}/{repo.name} ---")
        lines.append(f"URL: {repo.url}")
        lines.append(f"Description: {repo.description or 'N/A'}")
        lines.append(f"Primary Language: {repo.primary_language or 'N/A'}")
        lines.append(f"Languages: {', '.join(repo.languages)}")
        lines.append(f"Stars: {repo.star_count}")
        lines.append(f"Open Issues: {repo.open_issue_count}")
        lines.append(f"Good First Issues: {repo.good_first_issue_count}")
        lines.append(f"Help Wanted: {repo.help_wanted_count}")
        lines.append(f"Topics: {', '.join(repo.topics)}")
        lines.append(f"License: {repo.license or 'N/A'}")
        lines.append(f"Last Pushed: {repo.pushed_at or 'N/A'}")
        if readme:
            lines.append(f"README (excerpt):\n{readme[:_README_MAX_CHARS]}")
        else:
            lines.append("README: Not available")

    return "\n".join(lines)


def batch_repos(repos: list[RepoMetadata], batch_size: int) -> list[list[RepoMetadata]]:
    """Split repos into batches of batch_size."""
    return [repos[i : i + batch_size] for i in range(0, len(repos), batch_size)]


async def analyze_batch(
    profile: DeveloperProfile,
    repos: list[RepoMetadata],
    readmes: list[str | None],
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


def _create_progress_event(analyzed: int, total: int) -> dict[str, object]:
    """Create a progress event dict."""
    return {
        "type": "progress",
        "message": f"Analyzed {analyzed}/{total} repos...",
        "phase": "analysis",
    }


def _create_error_event(message: str, analyzed: int, total: int) -> dict[str, object]:
    """Create an error event dict."""
    return {
        "type": "error",
        "message": f"{message} ({analyzed}/{total})",
        "phase": "analysis",
    }


async def analyze_repos_streamed(
    profile: DeveloperProfile,
    repos: list[RepoMetadata],
    readmes: list[str | None],
) -> AsyncGenerator[dict[str, object], None]:
    """Run batched analysis with concurrent execution and progress streaming.

    Yields progress/error events after each batch completes.
    """
    capped_repos = repos[: settings.scout_max_repos]
    capped_readmes = readmes[: settings.scout_max_repos]
    bs = settings.scout_batch_size
    total = len(capped_repos)
    session_id = uuid.uuid4().hex
    analyzed = 0

    repo_batches = batch_repos(capped_repos, bs)
    readme_batches = [capped_readmes[i : i + bs] for i in range(0, total, bs)]

    tasks = [
        asyncio.create_task(analyze_batch(profile, repo_batch, readme_batch, session_id))
        for repo_batch, readme_batch in zip(repo_batches, readme_batches)
    ]

    for coro in asyncio.as_completed(tasks):
        try:
            batch_results = await coro
            analyzed += len(batch_results)
            yield _create_progress_event(analyzed, total)
        except TimeoutError:
            analyzed += bs
            yield _create_error_event("Batch timed out, skipping...", analyzed, total)
        except Exception as e:
            logger.exception("Batch analysis failed: %s", e)
            analyzed += bs
            yield _create_error_event("Batch failed, continuing...", analyzed, total)
