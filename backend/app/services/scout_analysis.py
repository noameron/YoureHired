"""Batch analysis service for scout repository evaluation."""

import logging

from app.agents.repo_analyst_agent import RepoAnalysisBatch, repo_analyst_agent
from app.config import settings
from app.schemas.scout import AnalysisResult, RepoMetadata, SearchFilters
from app.services.task_registry import run_agent_streamed

# Approximately 4K tokens for GPT-4o-mini context window
_README_MAX_CHARS = 16_000

logger = logging.getLogger(__name__)


def _format_repo_section(repo: RepoMetadata, readme: str | None) -> str:
    """Format a single repo + readme into a text block for the analysis prompt."""
    lines = [
        f"--- {repo.owner}/{repo.name} ---",
        f"URL: {repo.url}",
        f"Description: {repo.description or 'N/A'}",
        f"Primary Language: {repo.primary_language or 'N/A'}",
        f"Languages: {', '.join(repo.languages)}",
        f"Stars: {repo.star_count}",
        f"Open Issues: {repo.open_issue_count}",
        f"Good First Issues: {repo.good_first_issue_count}",
        f"Help Wanted: {repo.help_wanted_count}",
        f"Topics: {', '.join(repo.topics)}",
        f"License: {repo.license or 'N/A'}",
        f"Last Pushed: {repo.pushed_at or 'N/A'}",
    ]
    if readme:
        lines.append(f"README (excerpt):\n{readme[:_README_MAX_CHARS]}")
    else:
        lines.append("README: Not available")
    return "\n".join(lines)


def _build_batch_input(
    filters: SearchFilters,
    repos: list[RepoMetadata],
    readmes: list[str | None],
) -> str:
    """Build the text prompt for a batch of repos.

    Raises:
        ValueError: If repos and readmes have different lengths
    """
    if len(repos) != len(readmes):
        raise ValueError(
            f"repos and readmes must have same length: {len(repos)} vs {len(readmes)}"
        )

    header_lines = [
        "SEARCH CONTEXT:",
        f"Languages: {', '.join(filters.languages)}",
        f"Topics: {', '.join(filters.topics)}",
    ]
    if filters.query:
        header_lines.append(f"Query: {filters.query}")
    header_lines.extend(["", "REPOSITORIES TO ANALYZE:"])

    sections = [_format_repo_section(repo, readme) for repo, readme in zip(repos, readmes)]
    return "\n".join(header_lines) + "\n\n" + "\n\n".join(sections)


def batch_repos(repos: list[RepoMetadata], batch_size: int) -> list[list[RepoMetadata]]:
    """Split repos into batches of batch_size."""
    return [repos[i : i + batch_size] for i in range(0, len(repos), batch_size)]


async def analyze_batch(
    filters: SearchFilters,
    repos: list[RepoMetadata],
    readmes: list[str | None],
    session_id: str,
) -> list[AnalysisResult]:
    """Analyze a single batch via the repo_analyst_agent."""
    batch_input = _build_batch_input(filters, repos, readmes)
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
