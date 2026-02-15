"""Tests for repository filtering engine."""

from app.schemas.scout import RepoMetadata
from app.services.repo_filtering import (
    apply_filters,
    compute_contribution_score,
    has_open_issues,
    is_tutorial_or_awesome_list,
)


def _make_repo(**overrides) -> RepoMetadata:
    """Build a RepoMetadata fixture with sensible defaults.

    Args:
        **overrides: Fields to override in the default RepoMetadata.

    Returns:
        RepoMetadata instance with defaults + overrides applied.
    """
    defaults = {
        "github_id": 1,
        "owner": "o",
        "name": "repo",
        "url": "https://github.com/o/repo",
        "open_issue_count": 5,
        "star_count": 100,
    }
    defaults.update(overrides)
    return RepoMetadata(**defaults)


class TestIsTutorialOrAwesomeList:
    """Tests for detecting tutorial/awesome-list repositories."""

    def test_detects_awesome_list_in_name(self):
        # GIVEN a repo named "awesome-python"
        repo = _make_repo(name="awesome-python")

        # WHEN checking if it's a tutorial/awesome-list
        result = is_tutorial_or_awesome_list(repo)

        # THEN it should be detected as True
        assert result is True

    def test_detects_learn_prefix_in_name(self):
        # GIVEN a repo named "learn-go"
        repo = _make_repo(name="learn-go")

        # WHEN checking if it's a tutorial/awesome-list
        result = is_tutorial_or_awesome_list(repo)

        # THEN it should be detected as True
        assert result is True

    def test_detects_tutorial_in_description(self):
        # GIVEN a repo with "tutorial" in description
        repo = _make_repo(name="my-project", description="A Python tutorial for beginners")

        # WHEN checking if it's a tutorial/awesome-list
        result = is_tutorial_or_awesome_list(repo)

        # THEN it should be detected as True
        assert result is True

    def test_allows_normal_project_name(self):
        # GIVEN a repo with a normal project name
        repo = _make_repo(name="my-project", description="A cool project")

        # WHEN checking if it's a tutorial/awesome-list
        result = is_tutorial_or_awesome_list(repo)

        # THEN it should return False
        assert result is False

    def test_allows_awesome_without_separator(self):
        # GIVEN a repo named "awesomeApp" (no hyphen/underscore)
        repo = _make_repo(name="awesomeApp", description="An awesome application")

        # WHEN checking if it's a tutorial/awesome-list
        result = is_tutorial_or_awesome_list(repo)

        # THEN it should return False (only separated "awesome-*" is filtered)
        assert result is False


class TestHasOpenIssues:
    """Tests for checking if repository has open issues."""

    def test_returns_false_when_zero_issues(self):
        # GIVEN a repo with 0 open issues
        repo = _make_repo(open_issue_count=0)

        # WHEN checking if it has open issues
        result = has_open_issues(repo)

        # THEN it should return False
        assert result is False

    def test_returns_true_when_one_issue(self):
        # GIVEN a repo with 1 open issue
        repo = _make_repo(open_issue_count=1)

        # WHEN checking if it has open issues
        result = has_open_issues(repo)

        # THEN it should return True
        assert result is True


class TestComputeContributionScore:
    """Tests for computing repository contribution score."""

    def test_calculates_score_with_good_first_issues(self):
        # GIVEN a repo with 10 good-first-issues
        repo = _make_repo(good_first_issue_count=10, help_wanted_count=0, open_issue_count=0)

        # WHEN computing contribution score
        result = compute_contribution_score(repo)

        # THEN score should be 20.0 (10 * 2.0)
        assert result == 20.0

    def test_returns_zero_for_empty_repo(self):
        # GIVEN a repo with no issues
        repo = _make_repo(good_first_issue_count=0, help_wanted_count=0, open_issue_count=0)

        # WHEN computing contribution score
        result = compute_contribution_score(repo)

        # THEN score should be 0.0
        assert result == 0.0

    def test_caps_score_at_maximum(self):
        # GIVEN a repo with excessive good-first-issues (>10)
        repo = _make_repo(good_first_issue_count=50, help_wanted_count=0, open_issue_count=0)

        # WHEN computing contribution score
        result = compute_contribution_score(repo)

        # THEN score should be capped at 20.0 (10 * 2.0 max)
        assert result == 20.0


class TestApplyFilters:
    """Tests for applying filters to repository list."""

    def test_excludes_tutorial_repositories(self):
        # GIVEN a list with a tutorial repo and a normal repo
        repos = [
            _make_repo(github_id=1, name="awesome-python", open_issue_count=10),
            _make_repo(github_id=2, name="real-project", open_issue_count=10),
        ]

        # WHEN applying filters
        result = apply_filters(repos)

        # THEN tutorial repo should be excluded
        assert len(result) == 1
        assert result[0].name == "real-project"

    def test_excludes_repos_with_zero_open_issues(self):
        # GIVEN repos with and without open issues
        repos = [
            _make_repo(github_id=1, name="has-issues", open_issue_count=5),
            _make_repo(github_id=2, name="no-issues", open_issue_count=0),
        ]

        # WHEN applying filters
        result = apply_filters(repos)

        # THEN repos without issues should be excluded
        assert len(result) == 1
        assert result[0].name == "has-issues"

    def test_excludes_repos_outside_star_range(self):
        # GIVEN repos with various star counts
        repos = [
            _make_repo(github_id=1, name="too-few", star_count=5, open_issue_count=1),
            _make_repo(github_id=2, name="just-right", star_count=50, open_issue_count=1),
            _make_repo(github_id=3, name="too-many", star_count=100000, open_issue_count=1),
        ]

        # WHEN applying filters with min_stars=10, max_stars=1000
        result = apply_filters(repos, min_stars=10, max_stars=1000)

        # THEN only repos in range should remain
        assert len(result) == 1
        assert result[0].name == "just-right"

    def test_returns_sorted_by_contribution_score_desc(self):
        # GIVEN repos with different contribution scores
        repos = [
            _make_repo(github_id=1, name="low", good_first_issue_count=1, open_issue_count=1),
            _make_repo(github_id=2, name="high", good_first_issue_count=10, open_issue_count=1),
            _make_repo(github_id=3, name="medium", good_first_issue_count=5, open_issue_count=1),
        ]

        # WHEN applying filters
        result = apply_filters(repos)

        # THEN results should be sorted by score descending
        assert len(result) == 3
        assert result[0].name == "high"
        assert result[1].name == "medium"
        assert result[2].name == "low"

    def test_returns_empty_list_for_empty_input(self):
        # GIVEN an empty list of repos
        repos = []

        # WHEN applying filters
        result = apply_filters(repos)

        # THEN result should be empty
        assert result == []

    def test_returns_empty_when_all_filtered_out(self):
        # GIVEN repos that all fail filters (no open issues)
        repos = [
            _make_repo(github_id=1, name="repo1", open_issue_count=0),
            _make_repo(github_id=2, name="repo2", open_issue_count=0),
        ]

        # WHEN applying filters
        result = apply_filters(repos)

        # THEN result should be empty
        assert result == []


class TestStarBoundaryConditions:
    """Tests for star count boundary edge cases."""

    def test_includes_repo_at_min_stars_boundary(self):
        # GIVEN a repo with exactly min_stars
        repos = [
            _make_repo(github_id=1, name="at-minimum", star_count=10, open_issue_count=1),
        ]

        # WHEN applying filters with min_stars=10
        result = apply_filters(repos, min_stars=10)

        # THEN repo should be included
        assert len(result) == 1
        assert result[0].name == "at-minimum"

    def test_includes_repo_at_max_stars_boundary(self):
        # GIVEN a repo with exactly max_stars
        repos = [
            _make_repo(github_id=1, name="at-maximum", star_count=100, open_issue_count=1),
        ]

        # WHEN applying filters with max_stars=100
        result = apply_filters(repos, max_stars=100)

        # THEN repo should be included
        assert len(result) == 1
        assert result[0].name == "at-maximum"

    def test_excludes_repo_above_max_stars_boundary(self):
        # GIVEN a repo with max_stars + 1
        repos = [
            _make_repo(github_id=1, name="too-popular", star_count=101, open_issue_count=1),
        ]

        # WHEN applying filters with max_stars=100
        result = apply_filters(repos, max_stars=100)

        # THEN repo should be excluded
        assert result == []
