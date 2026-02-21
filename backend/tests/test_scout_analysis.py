"""
Tests for the scout analysis service module.

These tests verify the batch processing, input building, and
streaming analysis functionality for repository analysis.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.agents.repo_analyst_agent import RepoAnalysisBatch
from app.schemas.scout import AnalysisResult, RepoMetadata, SearchFilters
from app.services.scout_analysis import (
    _build_batch_input,
    analyze_batch,
    batch_repos,
)

# Fixtures


@pytest.fixture
def sample_filters() -> SearchFilters:
    """Sample search filters for testing."""
    return SearchFilters(
        languages=["Python", "Go"],
        topics=["web-framework", "api"],
        query="Contribute to API frameworks",
    )


@pytest.fixture
def sample_repo():
    """Factory fixture to create sample RepoMetadata instances."""

    def _make_repo(owner: str = "test", name: str = "repo", **kwargs) -> RepoMetadata:
        defaults = {
            "github_id": 12345,
            "owner": owner,
            "name": name,
            "url": f"https://github.com/{owner}/{name}",
            "description": "A test repository",
            "primary_language": "Python",
            "languages": ["Python"],
            "star_count": 100,
            "fork_count": 20,
            "open_issue_count": 5,
            "topics": ["test"],
            "license": "MIT",
            "pushed_at": "2025-01-01T00:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "good_first_issue_count": 2,
            "help_wanted_count": 1,
        }
        defaults.update(kwargs)
        return RepoMetadata(**defaults)

    return _make_repo


@pytest.fixture
def sample_result():
    """Factory fixture to create sample AnalysisResult instances."""

    def _make_result(repo: str = "owner/repo", **kwargs) -> AnalysisResult:
        defaults = {
            "repo": repo,
            "fit_score": 7.5,
            "reason": "Good match",
            "contributions": ["Improve docs"],
            "reject": False,
        }
        defaults.update(kwargs)
        return AnalysisResult(**defaults)

    return _make_result


# Tests for batch_repos


def test_batch_repos_splits_correctly(sample_repo):
    """
    GIVEN 25 repositories and batch_size=10
    WHEN batching the repos
    THEN should return 3 batches: [10, 10, 5]
    """
    # GIVEN
    repos = [sample_repo(owner="org", name=f"repo{i}") for i in range(25)]

    # WHEN
    batches = batch_repos(repos, batch_size=10)

    # THEN
    assert len(batches) == 3
    assert len(batches[0]) == 10
    assert len(batches[1]) == 10
    assert len(batches[2]) == 5


def test_batch_repos_empty():
    """
    GIVEN an empty list of repositories
    WHEN batching the repos
    THEN should return empty list
    """
    # GIVEN
    repos = []

    # WHEN
    batches = batch_repos(repos, batch_size=10)

    # THEN
    assert batches == []


def test_batch_repos_fewer_than_batch_size(sample_repo):
    """
    GIVEN 5 repositories and batch_size=10
    WHEN batching the repos
    THEN should return 1 batch with all 5 repos
    """
    # GIVEN
    repos = [sample_repo(owner="org", name=f"repo{i}") for i in range(5)]

    # WHEN
    batches = batch_repos(repos, batch_size=10)

    # THEN
    assert len(batches) == 1
    assert len(batches[0]) == 5


# Tests for _build_batch_input


def test_build_batch_input_includes_profile_and_metadata(sample_filters, sample_repo):
    """
    GIVEN search filters and batch of repos with metadata
    WHEN building batch input
    THEN output should contain search context and repo details
    """
    # GIVEN
    repos = [
        sample_repo(
            owner="fastapi",
            name="fastapi",
            star_count=50000,
            primary_language="Python",
        )
    ]
    readmes = [None]

    # WHEN
    output = _build_batch_input(sample_filters, repos, readmes)

    # THEN
    assert "Python" in output
    assert "Go" in output
    assert "web-framework" in output
    assert "api" in output
    assert "Contribute to API frameworks" in output
    assert "fastapi/fastapi" in output
    assert "50000" in output or "50,000" in output  # Star count


def test_build_batch_input_includes_readme(sample_filters, sample_repo):
    """
    GIVEN a repo with README content
    WHEN building batch input
    THEN output should contain the README text
    """
    # GIVEN
    repos = [sample_repo(owner="org", name="repo")]
    readmes = ["# Test README\n\nThis is a test project."]

    # WHEN
    output = _build_batch_input(sample_filters, repos, readmes)

    # THEN
    assert "# Test README" in output
    assert "This is a test project" in output


def test_build_batch_input_no_readme(sample_filters, sample_repo):
    """
    GIVEN a repo without README
    WHEN building batch input
    THEN output should show "Not available"
    """
    # GIVEN
    repos = [sample_repo(owner="org", name="repo")]
    readmes = [None]

    # WHEN
    output = _build_batch_input(sample_filters, repos, readmes)

    # THEN
    assert "Not available" in output


def test_build_batch_input_mismatched_lengths(sample_filters, sample_repo):
    """
    GIVEN repos and readmes with different lengths
    WHEN building batch input
    THEN should raise ValueError
    """
    # GIVEN
    repos = [sample_repo(owner="org", name="repo1"), sample_repo(owner="org", name="repo2")]
    readmes = [None]  # Only 1 readme for 2 repos

    # WHEN / THEN
    with pytest.raises(ValueError, match="repos and readmes must have same length"):
        _build_batch_input(sample_filters, repos, readmes)


# Tests for analyze_batch


@pytest.mark.asyncio
async def test_analyze_batch_returns_results(sample_filters, sample_repo, sample_result):
    """
    GIVEN a mocked run_agent_streamed that returns a RepoAnalysisBatch
    WHEN analyzing a batch
    THEN should return the analysis results
    """
    # GIVEN
    repos = [sample_repo(owner="test", name="repo1")]
    readmes = [None]
    expected_result = sample_result(repo="test/repo1")
    batch_response = RepoAnalysisBatch(results=[expected_result])

    with patch(
        "app.services.scout_analysis.run_agent_streamed", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = batch_response

        # WHEN
        results = await analyze_batch(sample_filters, repos, readmes, session_id="test")

        # THEN
        assert len(results) == 1
        assert results[0].repo == "test/repo1"
        assert results[0].fit_score == 7.5
        mock_run.assert_awaited_once()


@pytest.mark.asyncio
async def test_analyze_batch_returns_empty_on_none(sample_filters, sample_repo):
    """
    GIVEN a mocked run_agent_streamed that returns None
    WHEN analyzing a batch
    THEN should return empty list
    """
    # GIVEN
    repos = [sample_repo(owner="test", name="repo1")]
    readmes = [None]

    with patch(
        "app.services.scout_analysis.run_agent_streamed", new_callable=AsyncMock
    ) as mock_run:
        mock_run.return_value = None

        # WHEN
        results = await analyze_batch(sample_filters, repos, readmes, session_id="test")

        # THEN
        assert results == []


def test_build_batch_input_contains_search_context_header(sample_filters, sample_repo):
    """
    GIVEN search filters and batch of repos
    WHEN building batch input
    THEN output should contain "SEARCH CONTEXT" header and not "DEVELOPER PROFILE"
    """
    # GIVEN
    repos = [sample_repo(owner="org", name="repo")]
    readmes = [None]

    # WHEN
    output = _build_batch_input(sample_filters, repos, readmes)

    # THEN
    assert "SEARCH CONTEXT" in output
    assert "DEVELOPER PROFILE" not in output
