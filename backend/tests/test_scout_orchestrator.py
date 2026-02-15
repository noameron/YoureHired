"""
Tests for the Scout orchestrator service.

The orchestrator coordinates the full search pipeline:
discovery → filtering → README fetch → analysis → persistence → completion.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.scout import (
    AnalysisResult,
    DeveloperProfile,
    RepoMetadata,
    SearchFilters,
)

# Test data factories


def make_profile() -> DeveloperProfile:
    """Create a sample DeveloperProfile for testing."""
    return DeveloperProfile(
        languages=["Python"],
        topics=["web"],
        skill_level="intermediate",
        goals="contribute to open source",
    )


def make_filters() -> SearchFilters:
    """Create sample SearchFilters for testing."""
    return SearchFilters(languages=["Python"], min_stars=10, max_stars=5000)


def make_repo(
    owner: str = "org",
    name: str = "repo",
    stars: int = 100,
    issues: int = 5,
    gfi: int = 2,
    hw: int = 1,
) -> RepoMetadata:
    """Create a sample RepoMetadata for testing."""
    return RepoMetadata(
        github_id=1,
        owner=owner,
        name=name,
        url=f"https://github.com/{owner}/{name}",
        description="A test repo",
        primary_language="Python",
        languages=["Python"],
        star_count=stars,
        fork_count=10,
        open_issue_count=issues,
        topics=["web"],
        license="MIT",
        pushed_at="2024-01-01T00:00:00Z",
        created_at="2023-01-01T00:00:00Z",
        good_first_issue_count=gfi,
        help_wanted_count=hw,
    )


def make_analysis_result(owner: str = "org", name: str = "repo") -> AnalysisResult:
    """Create a sample AnalysisResult for testing."""
    return AnalysisResult(
        repo=f"{owner}/{name}",
        fit_score=8.5,
        reason="Great fit",
        contributions=["Fix bugs"],
        reject=False,
    )


# Helper for collecting async generator events


async def collect_events(gen):
    """Collect all events from an async generator."""
    events = []
    async for event in gen:
        events.append(event)
    return events


# Tests


@pytest.mark.asyncio
async def test_full_successful_pipeline():
    """
    GIVEN all dependencies mocked successfully
    WHEN running scout_search_stream
    THEN should yield status events through all phases and complete with ScoutSearchResult
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    profile = make_profile()
    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    repo1 = make_repo(owner="org1", name="repo1")
    repo2 = make_repo(owner="org2", name="repo2")
    repos = [repo1, repo2]

    result1 = make_analysis_result(owner="org1", name="repo1")
    result2 = make_analysis_result(owner="org2", name="repo2")
    analysis_results = [result1, result2]

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.apply_filters") as mock_apply_filters,
        patch("app.services.scout_orchestrator.batch_repos") as mock_batch_repos,
        patch(
            "app.services.scout_orchestrator.analyze_batch",
            new_callable=AsyncMock,
        ) as mock_analyze,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
        patch("app.services.scout_orchestrator.settings") as mock_settings,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=(repos, []))
        mock_client.fetch_readmes = AsyncMock(
            return_value={"org1/repo1": "# README 1", "org2/repo2": "# README 2"}
        )
        mock_create_client.return_value = mock_client

        mock_apply_filters.return_value = repos
        mock_batch_repos.return_value = [repos]  # Single batch
        mock_analyze.return_value = analysis_results

        mock_db.upsert_repositories = AsyncMock()
        mock_db.save_analysis_results = AsyncMock()
        mock_db.update_search_run = AsyncMock()

        mock_settings.scout_max_repos = 50
        mock_settings.scout_batch_size = 5

        # WHEN
        events = await collect_events(scout_search_stream(filters, profile, run_id, session_id))

        # THEN
        # Verify we got events for all phases
        event_types = [e.get("type") for e in events]
        assert "status" in event_types
        assert "complete" in event_types

        # Find status events by phase
        status_events = [e for e in events if e.get("type") == "status"]
        phases = [e.get("phase") for e in status_events]
        assert "discovering" in phases
        assert "filtering" in phases
        assert "analyzing" in phases

        # Verify complete event has correct structure
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) == 1
        complete_data = complete_events[0].get("data")
        assert complete_data is not None
        assert complete_data["run_id"] == run_id
        assert complete_data["status"] == "completed"
        assert complete_data["total_discovered"] == 2
        assert complete_data["total_filtered"] == 2
        assert complete_data["total_analyzed"] == 2

        # Verify database calls
        mock_db.upsert_repositories.assert_awaited_once_with(repos)
        mock_db.save_analysis_results.assert_awaited_once_with(run_id, analysis_results)
        mock_db.update_search_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_empty_discovery_yields_error():
    """
    GIVEN search_repositories returns no repos
    WHEN running scout_search_stream
    THEN should yield error event and update run status to completed with zero counts
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    profile = make_profile()
    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=([], []))
        mock_create_client.return_value = mock_client

        mock_db.update_search_run = AsyncMock()

        # WHEN
        events = await collect_events(scout_search_stream(filters, profile, run_id, session_id))

        # THEN
        # Should have error event about no repositories found
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) > 0
        assert any("No repositories found" in e.get("message", "") for e in error_events)

        # Should update run status to completed with zero counts
        mock_db.update_search_run.assert_awaited_once_with(run_id, "completed", 0, 0, 0)


@pytest.mark.asyncio
async def test_all_repos_filtered_out_yields_error():
    """
    GIVEN search returns repos but apply_filters returns empty list
    WHEN running scout_search_stream
    THEN should yield error event and update run status with discovered count
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    profile = make_profile()
    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    repos = [make_repo(owner="org1", name="repo1"), make_repo(owner="org2", name="repo2")]

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.apply_filters") as mock_apply_filters,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=(repos, []))
        mock_create_client.return_value = mock_client

        mock_apply_filters.return_value = []  # All filtered out
        mock_db.upsert_repositories = AsyncMock()
        mock_db.update_search_run = AsyncMock()

        # WHEN
        events = await collect_events(scout_search_stream(filters, profile, run_id, session_id))

        # THEN
        # Should have error event about filtering
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) > 0
        assert any("All repos filtered out" in e.get("message", "") for e in error_events)

        # Should update run status to completed with discovered=2, filtered=0, analyzed=0
        mock_db.update_search_run.assert_awaited_once_with(run_id, "completed", 2, 0, 0)


@pytest.mark.asyncio
async def test_partial_batch_failure_yields_partial_status():
    """
    GIVEN multiple batches where one succeeds and one raises exception
    WHEN running scout_search_stream
    THEN should yield complete event with partial status since results < capped repos
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    profile = make_profile()
    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    # 4 repos split into 2 batches of 2 each
    repos = [
        make_repo(owner="org1", name="repo1"),
        make_repo(owner="org2", name="repo2"),
        make_repo(owner="org3", name="repo3"),
        make_repo(owner="org4", name="repo4"),
    ]
    batch1 = repos[:2]
    batch2 = repos[2:]
    results_batch1 = [make_analysis_result(owner="org1", name="repo1")]

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.apply_filters") as mock_apply_filters,
        patch("app.services.scout_orchestrator.batch_repos") as mock_batch_repos,
        patch(
            "app.services.scout_orchestrator.analyze_batch",
            new_callable=AsyncMock,
        ) as mock_analyze,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
        patch("app.services.scout_orchestrator.settings") as mock_settings,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=(repos, []))
        mock_client.fetch_readmes = AsyncMock(return_value={})
        mock_create_client.return_value = mock_client

        mock_apply_filters.return_value = repos
        mock_batch_repos.return_value = [batch1, batch2]
        # First batch succeeds with 1 result, second batch raises exception
        mock_analyze.side_effect = [results_batch1, Exception("Analysis failed")]

        mock_db.upsert_repositories = AsyncMock()
        mock_db.save_analysis_results = AsyncMock()
        mock_db.update_search_run = AsyncMock()

        mock_settings.scout_max_repos = 50
        mock_settings.scout_batch_size = 2

        # WHEN
        events = await collect_events(scout_search_stream(filters, profile, run_id, session_id))

        # THEN
        # Should complete but with partial status (1 result < 4 capped repos)
        complete_events = [e for e in events if e.get("type") == "complete"]
        assert len(complete_events) == 1
        complete_data = complete_events[0].get("data")
        assert complete_data["status"] == "partial"
        assert complete_data["total_analyzed"] == 1


@pytest.mark.asyncio
async def test_exception_in_discovery_yields_error():
    """
    GIVEN search_repositories raises an exception
    WHEN running scout_search_stream
    THEN should yield error event and update run status to failed
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    profile = make_profile()
    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(side_effect=Exception("GitHub API error"))
        mock_create_client.return_value = mock_client

        mock_db.update_search_run = AsyncMock()

        # WHEN
        events = await collect_events(scout_search_stream(filters, profile, run_id, session_id))

        # THEN
        # Should have error event
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) > 0

        # Should update run status to failed with zero counts
        mock_db.update_search_run.assert_awaited_once_with(run_id, "failed", 0, 0, 0)
