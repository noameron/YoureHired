"""Orchestrator for the full scout search pipeline."""

import asyncio
import logging
from collections.abc import AsyncGenerator

from app.config import settings
from app.schemas.scout import (
    AnalysisResult,
    RepoMetadata,
    ScoutSearchResult,
    SearchFilters,
    SearchRunStatus,
)
from app.services.github_client import GitHubGraphQLClient, create_github_client
from app.services.github_repos_db import github_repos_db
from app.services.repo_filtering import apply_filters
from app.services.scout_analysis import analyze_batch, batch_repos
from app.services.task_registry import task_registry

logger = logging.getLogger(__name__)

Event = dict[str, object]


def _status(message: str, phase: str) -> Event:
    return {"type": "status", "message": message, "phase": phase}


def _cancelled_event() -> Event:
    """Build the cancellation SSE event (distinct from _check_cancelled)."""
    return {"type": "status", "message": "Search cancelled", "status": "cancelled"}


def _error(message: str, phase: str | None = None) -> Event:
    evt: Event = {"type": "error", "message": message}
    if phase:
        evt["phase"] = phase
    return evt


def _check_cancelled(run_id: str) -> None:
    """Raise CancelledError if the run has been cancelled."""
    if task_registry.is_cancelled(run_id):
        raise asyncio.CancelledError


async def _discover(
    client: GitHubGraphQLClient,
    filters: SearchFilters,
) -> tuple[list[RepoMetadata], list[str]]:
    """Search GitHub and persist discovered repos.

    If no repos match and topic filters are active, retries without topics.
    Topics still influence AI ranking during the analysis phase.
    """
    repos, warnings = await client.search_repositories(filters)

    if not repos and filters.topics:
        topics_str = ", ".join(filters.topics)
        relaxed = filters.model_copy(update={"topics": []})
        repos, relaxed_warnings = await client.search_repositories(relaxed)
        warnings.extend(relaxed_warnings)
        if repos:
            warnings.append(
                f"No repos matched topic filter ({topics_str}). "
                f"Showing results without topic filter — "
                f"topics still influence AI ranking."
            )

    if repos:
        await github_repos_db.upsert_repositories(repos)
    return repos, warnings


def _filter_repos(
    repos: list[RepoMetadata], filters: SearchFilters
) -> tuple[list[RepoMetadata], list[RepoMetadata]]:
    """Apply client-side filters and cap at max repos.

    Returns (filtered, capped) where capped = filtered[:scout_max_repos].
    """
    filtered = apply_filters(
        repos, min_stars=filters.min_stars, max_stars=filters.max_stars
    )
    return filtered, filtered[: settings.scout_max_repos]


async def _fetch_readmes(
    client: GitHubGraphQLClient, capped: list[RepoMetadata]
) -> list[str | None]:
    """Fetch READMEs and return as ordered list matching capped repos."""
    readme_pairs = [(r.owner, r.name) for r in capped]
    readmes_dict = await client.fetch_readmes(readme_pairs)
    return [readmes_dict.get(f"{r.owner}/{r.name}") for r in capped]


async def _run_analysis(
    filters: SearchFilters,
    capped: list[RepoMetadata],
    readmes: list[str | None],
    run_id: str,
) -> AsyncGenerator[tuple[list[AnalysisResult], Event], None]:
    """Run batched analysis concurrently, yielding (cumulative_results, event).

    Uses asyncio.wait instead of as_completed to avoid RuntimeWarning
    from orphaned wrapper coroutines on cancellation.
    """
    all_results: list[AnalysisResult] = []
    bs = settings.scout_batch_size
    total = len(capped)
    analyzed = 0

    repo_batches = batch_repos(capped, bs)
    readme_batches = [readmes[i : i + bs] for i in range(0, total, bs)]

    pending: set[asyncio.Task[list[AnalysisResult]]] = {
        asyncio.create_task(analyze_batch(filters, rb, rmb, run_id))
        for rb, rmb in zip(repo_batches, readme_batches)
    }

    try:
        while pending:
            _check_cancelled(run_id)
            done, pending = await asyncio.wait(
                pending, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                try:
                    batch_results = task.result()
                    all_results.extend(batch_results)
                    analyzed += len(batch_results)
                    yield all_results, {
                        "type": "progress",
                        "message": f"Analyzed {analyzed}/{total} repos...",
                        "phase": "analyzing",
                    }
                except TimeoutError:
                    analyzed = min(analyzed + bs, total)
                    yield all_results, {
                        "type": "error",
                        "message": f"Batch timed out ({analyzed}/{total})",
                        "phase": "analyzing",
                    }
                except Exception as exc:
                    logger.exception("Batch analysis failed: %s", exc)
                    analyzed = min(analyzed + bs, total)
                    yield all_results, {
                        "type": "error",
                        "message": f"Batch failed ({analyzed}/{total})",
                        "phase": "analyzing",
                    }
    finally:
        for task in pending:
            task.cancel()
        if pending:
            await asyncio.gather(*pending, return_exceptions=True)


async def _build_completion_event(
    run_id: str,
    repos: list[RepoMetadata],
    filtered: list[RepoMetadata],
    capped: list[RepoMetadata],
    all_results: list[AnalysisResult],
    warnings: list[str],
) -> Event:
    """Persist results and build the completion SSE event."""
    await github_repos_db.save_analysis_results(run_id, all_results)
    status: SearchRunStatus = (
        "partial" if len(all_results) < len(capped) else "completed"
    )
    await github_repos_db.update_search_run(
        run_id, status, len(repos), len(filtered), len(all_results)
    )

    visible = sorted(
        [r for r in all_results if not r.reject],
        key=lambda r: r.fit_score,
        reverse=True,
    )
    result = ScoutSearchResult(
        run_id=run_id,
        status=status,
        total_discovered=len(repos),
        total_filtered=len(filtered),
        total_analyzed=len(all_results),
        results=visible,
        repos=capped,
        warnings=warnings,
    )
    return {"type": "complete", "data": result.model_dump()}


async def scout_search_stream(
    filters: SearchFilters,
    run_id: str,
) -> AsyncGenerator[Event, None]:
    """Stream the full scout pipeline."""
    try:
        yield _status("Searching GitHub...", "discovering")
        client = create_github_client()
        repos, warnings = await _discover(client, filters)
        yield _status(f"Discovered {len(repos)} repositories", "discovering")

        if not repos:
            yield _error("No repositories found. Try broadening your filters.")
            await github_repos_db.update_search_run(run_id, "completed", 0, 0, 0)
            return

        _check_cancelled(run_id)

        yield _status("Filtering candidates...", "filtering")
        filtered, capped = _filter_repos(repos, filters)
        yield _status(f"{len(filtered)} repos passed filters", "filtering")

        if not filtered:
            yield _error("All repos filtered out. Try adjusting your filters.")
            await github_repos_db.update_search_run(
                run_id, "completed", len(repos), 0, 0
            )
            return

        _check_cancelled(run_id)

        yield _status(f"Fetching READMEs for {len(capped)} repos...", "filtering")
        readmes = await _fetch_readmes(client, capped)

        _check_cancelled(run_id)

        yield _status("Starting AI analysis...", "analyzing")
        all_results: list[AnalysisResult] = []
        async for results, event in _run_analysis(filters, capped, readmes, run_id):
            all_results = results
            yield event

        yield await _build_completion_event(
            run_id, repos, filtered, capped, all_results, warnings
        )

    except asyncio.CancelledError:
        logger.info("Scout search cancelled for run %s", run_id)
        await github_repos_db.update_search_run(run_id, "cancelled", 0, 0, 0)
        yield _cancelled_event()
    except Exception as e:
        logger.exception("Scout search failed for run %s", run_id)
        await github_repos_db.update_search_run(run_id, "failed", 0, 0, 0)
        yield {"type": "error", "message": f"Scout search failed: {e!s}"}
