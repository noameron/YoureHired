"""
Tests for the Scout orchestrator service.

The orchestrator coordinates the full search pipeline:
discovery → filtering → README fetch → analysis → persistence → completion.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.scout import (
    AnalysisResult,
    RepoMetadata,
    SearchFilters,
)

# Test data factories


def make_filters() -> SearchFilters:
    """Create sample SearchFilters for testing."""
    return SearchFilters(
        languages=["Python"],
        min_stars=10,
        max_stars=5000,
        query="contribute to open source",
    )


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
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

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
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

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
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

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
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

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
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

        # THEN
        # Should have error event
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) > 0

        # Should update run status to failed with zero counts
        mock_db.update_search_run.assert_awaited_once_with(run_id, "failed", 0, 0, 0)


@pytest.mark.asyncio
async def test_cancellation_after_discovery_exits_early():
    """
    GIVEN task_registry.is_cancelled returns True after discovery phase
    WHEN running scout_search_stream
    THEN should yield cancelled status event and exit without proceeding to filtering
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    repos = [make_repo(owner="org1", name="repo1")]

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.task_registry", create=True) as mock_task_registry,
        patch("app.services.scout_orchestrator.apply_filters") as mock_apply_filters,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=(repos, []))
        mock_create_client.return_value = mock_client

        # is_cancelled returns True immediately (cancelled after discovery)
        mock_task_registry.is_cancelled = MagicMock(return_value=True)

        mock_db.upsert_repositories = AsyncMock()
        mock_db.update_search_run = AsyncMock()

        # WHEN
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

        # THEN
        # Should have a cancelled status event
        status_events = [e for e in events if e.get("type") == "status"]
        cancelled_events = [e for e in status_events if e.get("status") == "cancelled"]
        assert len(cancelled_events) > 0

        # Should NOT call filtering (apply_filters should not be called)
        mock_apply_filters.assert_not_called()

        # Should update run status to cancelled
        mock_db.update_search_run.assert_awaited()
        call_args = mock_db.update_search_run.call_args
        assert call_args[0][1] == "cancelled"


@pytest.mark.asyncio
async def test_cancellation_after_filtering_exits_early():
    """
    GIVEN task_registry.is_cancelled returns True after filtering phase
    WHEN running scout_search_stream
    THEN should yield cancelled status event and exit without proceeding to README fetch
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    repos = [make_repo(owner="org1", name="repo1")]

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.task_registry", create=True) as mock_task_registry,
        patch("app.services.scout_orchestrator.apply_filters") as mock_apply_filters,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=(repos, []))
        mock_client.fetch_readmes = AsyncMock()
        mock_create_client.return_value = mock_client

        # is_cancelled returns False first time (discovery), True second time (filtering)
        mock_task_registry.is_cancelled = MagicMock(side_effect=[False, True])

        mock_apply_filters.return_value = repos
        mock_db.upsert_repositories = AsyncMock()
        mock_db.update_search_run = AsyncMock()

        # WHEN
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

        # THEN
        # Should have filtering phase but then cancelled
        status_events = [e for e in events if e.get("type") == "status"]
        phases = [e.get("phase") for e in status_events]
        assert "filtering" in phases

        cancelled_events = [e for e in status_events if e.get("status") == "cancelled"]
        assert len(cancelled_events) > 0

        # Should NOT call fetch_readmes
        mock_client.fetch_readmes.assert_not_called()

        # Should update run status to cancelled
        mock_db.update_search_run.assert_awaited()
        call_args = mock_db.update_search_run.call_args
        assert call_args[0][1] == "cancelled"


@pytest.mark.asyncio
async def test_cancellation_after_readme_fetch_exits_early():
    """
    GIVEN task_registry.is_cancelled returns True after README fetch phase
    WHEN running scout_search_stream
    THEN should yield cancelled status event and exit without proceeding to analysis
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    repos = [make_repo(owner="org1", name="repo1")]

    with (
        patch("app.services.scout_orchestrator.create_github_client") as mock_create_client,
        patch("app.services.scout_orchestrator.task_registry", create=True) as mock_task_registry,
        patch("app.services.scout_orchestrator.apply_filters") as mock_apply_filters,
        patch("app.services.scout_orchestrator.batch_repos"),
        patch(
            "app.services.scout_orchestrator.analyze_batch",
            new_callable=AsyncMock,
        ) as mock_analyze,
        patch("app.services.scout_orchestrator.github_repos_db") as mock_db,
    ):
        # Setup mocks
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=(repos, []))
        mock_client.fetch_readmes = AsyncMock(return_value={"org1/repo1": "# README 1"})
        mock_create_client.return_value = mock_client

        # is_cancelled returns False twice (discovery, filtering), True on third call (after README)
        mock_task_registry.is_cancelled = MagicMock(side_effect=[False, False, True])

        mock_apply_filters.return_value = repos
        mock_db.upsert_repositories = AsyncMock()
        mock_db.update_search_run = AsyncMock()

        # WHEN
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

        # THEN
        # Should have README fetch but then cancelled
        status_events = [e for e in events if e.get("type") == "status"]
        cancelled_events = [e for e in status_events if e.get("status") == "cancelled"]
        assert len(cancelled_events) > 0

        # Should NOT call analyze_batch
        mock_analyze.assert_not_called()

        # Should update run status to cancelled
        mock_db.update_search_run.assert_awaited()
        call_args = mock_db.update_search_run.call_args
        assert call_args[0][1] == "cancelled"


@pytest.mark.asyncio
async def test_run_analysis_cancels_remaining_tasks_on_cancellation():
    """
    GIVEN multiple batches where cancellation happens mid-iteration
    WHEN running _run_analysis
    THEN should cancel remaining asyncio tasks and return partial results
    """
    # GIVEN
    from app.services.scout_orchestrator import scout_search_stream

    filters = make_filters()
    run_id = "test-run-123"
    session_id = "sess-456"

    # 4 repos split into 2 batches
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
        patch("app.services.scout_orchestrator.task_registry", create=True) as mock_task_registry,
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

        # is_cancelled returns False for discovery/filtering/readme, True during analysis
        # We need it to return False enough times to get into analysis, then True
        mock_task_registry.is_cancelled = MagicMock(side_effect=[False, False, False, True])

        mock_apply_filters.return_value = repos
        mock_batch_repos.return_value = [batch1, batch2]

        # First batch succeeds, but cancellation happens before second batch completes
        async def slow_batch_analysis(*args, **kwargs):
            # Simulate slow analysis to ensure cancellation happens mid-iteration
            import asyncio

            await asyncio.sleep(0.1)
            return [make_analysis_result(owner="org3", name="repo3")]

        mock_analyze.side_effect = [results_batch1, slow_batch_analysis()]

        mock_db.upsert_repositories = AsyncMock()
        mock_db.save_analysis_results = AsyncMock()
        mock_db.update_search_run = AsyncMock()

        mock_settings.scout_max_repos = 50
        mock_settings.scout_batch_size = 2

        # WHEN
        events = await collect_events(scout_search_stream(filters, run_id, session_id))

        # THEN
        # Should have cancelled status event
        status_events = [e for e in events if e.get("type") == "status"]
        cancelled_events = [e for e in status_events if e.get("status") == "cancelled"]
        assert len(cancelled_events) > 0

        # Should have partial results (only first batch completed)
        # analyze_batch should have been called at least once
        assert mock_analyze.call_count >= 1

        # Should update run status to cancelled
        mock_db.update_search_run.assert_awaited()
        call_args = mock_db.update_search_run.call_args
        assert call_args[0][1] == "cancelled"


# Tests for _discover() topic relaxation feature


@pytest.mark.asyncio
async def test_topic_relaxation_retries_without_topics():
    """
    GIVEN filters have topics=["ai-tools", "machine-learning"]
    WHEN _discover() gets 0 repos from first search
    THEN should retry without topics and return repos from second search with warning
    """
    # GIVEN
    from app.services.scout_orchestrator import _discover

    filters = SearchFilters(
        languages=["Python"],
        min_stars=10,
        max_stars=5000,
        topics=["ai-tools", "machine-learning"],
    )
    repo1 = make_repo(owner="org1", name="repo1")
    repo2 = make_repo(owner="org2", name="repo2")

    with patch("app.services.scout_orchestrator.github_repos_db") as mock_db:
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(
            side_effect=[
                ([], []),  # First call with topics returns empty
                ([repo1, repo2], []),  # Second call without topics returns repos
            ]
        )
        mock_db.upsert_repositories = AsyncMock()

        # WHEN
        repos, warnings = await _discover(mock_client, filters)

        # THEN
        # search_repositories called exactly 2 times
        assert mock_client.search_repositories.call_count == 2

        # Second call used filters with topics=[]
        second_call_filters = mock_client.search_repositories.call_args_list[1][0][0]
        assert second_call_filters.topics == []

        # Warning message contains the topic names
        assert len(warnings) == 1
        assert "ai-tools" in warnings[0]
        assert "machine-learning" in warnings[0]
        assert "No repos matched topic filter" in warnings[0]

        # Returned repos are [repo1, repo2]
        assert repos == [repo1, repo2]

        # upsert_repositories was called with the repos
        mock_db.upsert_repositories.assert_awaited_once_with([repo1, repo2])


@pytest.mark.asyncio
async def test_topic_relaxation_both_searches_empty():
    """
    GIVEN filters have topics=["rare-topic"]
    WHEN _discover() gets 0 repos from both searches
    THEN should return empty repos with no relaxation warning
    """
    # GIVEN
    from app.services.scout_orchestrator import _discover

    filters = SearchFilters(
        languages=["Python"],
        min_stars=10,
        max_stars=5000,
        topics=["rare-topic"],
    )

    with patch("app.services.scout_orchestrator.github_repos_db") as mock_db:
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(
            side_effect=[
                ([], []),  # First call with topics returns empty
                ([], []),  # Second call without topics also returns empty
            ]
        )
        mock_db.upsert_repositories = AsyncMock()

        # WHEN
        repos, warnings = await _discover(mock_client, filters)

        # THEN
        # search_repositories called exactly 2 times
        assert mock_client.search_repositories.call_count == 2

        # Returned repos is []
        assert repos == []

        # NO relaxation warning (since no repos were found even after relaxation)
        assert len(warnings) == 0

        # upsert_repositories was NOT called
        mock_db.upsert_repositories.assert_not_called()


@pytest.mark.asyncio
async def test_no_relaxation_when_no_topics():
    """
    GIVEN filters have topics=[]
    WHEN _discover() gets 0 repos
    THEN should NOT retry (no relaxation) and return empty repos
    """
    # GIVEN
    from app.services.scout_orchestrator import _discover

    filters = make_filters()  # No topics
    assert filters.topics == []

    with patch("app.services.scout_orchestrator.github_repos_db") as mock_db:
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=([], []))
        mock_db.upsert_repositories = AsyncMock()

        # WHEN
        repos, warnings = await _discover(mock_client, filters)

        # THEN
        # search_repositories called exactly 1 time (no retry)
        assert mock_client.search_repositories.call_count == 1

        # Returned repos is []
        assert repos == []

        # No warnings
        assert len(warnings) == 0


@pytest.mark.asyncio
async def test_no_relaxation_when_initial_search_succeeds():
    """
    GIVEN filters have topics=["web-dev"]
    WHEN _discover() gets repos from first search
    THEN should NOT retry and return repos from first search
    """
    # GIVEN
    from app.services.scout_orchestrator import _discover

    filters = SearchFilters(
        languages=["Python"],
        min_stars=10,
        max_stars=5000,
        topics=["web-dev"],
    )
    repo1 = make_repo(owner="org1", name="repo1")

    with patch("app.services.scout_orchestrator.github_repos_db") as mock_db:
        mock_client = AsyncMock()
        mock_client.search_repositories = AsyncMock(return_value=([repo1], []))
        mock_db.upsert_repositories = AsyncMock()

        # WHEN
        repos, warnings = await _discover(mock_client, filters)

        # THEN
        # search_repositories called exactly 1 time (no retry since results found)
        assert mock_client.search_repositories.call_count == 1

        # Returned repos is [repo1]
        assert repos == [repo1]

        # No relaxation warning
        assert len(warnings) == 0

        # upsert_repositories was called
        mock_db.upsert_repositories.assert_awaited_once_with([repo1])
