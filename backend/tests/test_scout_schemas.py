"""Tests for scout Pydantic schemas."""

from typing import Literal, cast

import pytest
from pydantic import ValidationError

from app.schemas.scout import (
    AnalysisResult,
    RepoMetadata,
    ScoutSearchResult,
    ScoutStreamCompleteEvent,
    ScoutStreamErrorEvent,
    ScoutStreamStatusEvent,
    SearchFilters,
    SearchRunResponse,
)


class TestSearchFilters:
    """Tests for the SearchFilters schema."""

    def test_valid_filters_minimal(self) -> None:
        """Minimal filters with only required fields."""
        filters = SearchFilters(languages=["Python"])
        assert filters.languages == ["Python"]
        assert filters.min_stars == 10
        assert filters.max_stars == 500000
        assert filters.topics == []
        assert filters.min_activity_date is None
        assert filters.license is None

    def test_min_stars_exceeds_max_rejected(self) -> None:
        """Min stars exceeding max stars is invalid."""
        with pytest.raises(ValidationError):
            SearchFilters(
                languages=["Python"],
                min_stars=100,
                max_stars=50,
            )

    def test_equal_stars_accepted(self) -> None:
        """Equal min and max stars is valid."""
        filters = SearchFilters(
            languages=["Python"],
            min_stars=50,
            max_stars=50,
        )
        assert filters.min_stars == 50
        assert filters.max_stars == 50

    def test_optional_fields_default_none(self) -> None:
        """Optional fields default to None."""
        filters = SearchFilters(languages=["Go"])
        assert filters.license is None
        assert filters.min_activity_date is None

    def test_all_fields_populated(self) -> None:
        """All fields can be populated."""
        filters = SearchFilters(
            languages=["Python", "JavaScript"],
            min_stars=100,
            max_stars=10000,
            topics=["web", "api"],
            min_activity_date="2024-01-01",
            license="MIT",
        )
        assert filters.languages == ["Python", "JavaScript"]
        assert filters.min_stars == 100
        assert filters.max_stars == 10000
        assert filters.topics == ["web", "api"]
        assert filters.min_activity_date == "2024-01-01"
        assert filters.license == "MIT"

    def test_zero_stars_accepted(self) -> None:
        """Zero stars for both min and max is valid."""
        filters = SearchFilters(
            languages=["Python"],
            min_stars=0,
            max_stars=0,
        )
        assert filters.min_stars == 0
        assert filters.max_stars == 0

    def test_query_defaults_to_empty_string(self) -> None:
        """Query field defaults to empty string."""
        # GIVEN - filters created without query field
        filters = SearchFilters(languages=["Python"])

        # WHEN - query is accessed
        # THEN - it should be an empty string
        assert filters.query == ""

    def test_query_max_length_500(self) -> None:
        """Query exceeding 500 characters is invalid."""
        # GIVEN - query with 501 characters
        # WHEN - creating SearchFilters
        # THEN - ValidationError should be raised
        with pytest.raises(ValidationError):
            SearchFilters(languages=["Python"], query="x" * 501)

    def test_query_included_in_model_dump(self) -> None:
        """Query field is included in model_dump output."""
        # GIVEN - filters with query field
        filters = SearchFilters(languages=["Python"], query="find CLI tools")

        # WHEN - model_dump is called
        dumped = filters.model_dump()

        # THEN - query should be in output with correct value
        assert "query" in dumped
        assert dumped["query"] == "find CLI tools"


class TestAnalysisResult:
    """Tests for the AnalysisResult schema."""

    def test_valid_result(self) -> None:
        """Valid analysis result with all fields."""
        result = AnalysisResult(
            repo="owner/name",
            fit_score=7.5,
            reason="Good fit",
            contributions=["Fix bugs"],
        )
        assert result.repo == "owner/name"
        assert result.fit_score == 7.5
        assert result.reason == "Good fit"
        assert result.contributions == ["Fix bugs"]

        # Test round-trip via model_dump()
        dumped = result.model_dump()
        assert dumped["repo"] == "owner/name"
        assert dumped["fit_score"] == 7.5

    def test_fit_score_below_zero_rejected(self) -> None:
        """Fit score below zero is invalid."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                repo="owner/name",
                fit_score=-1,
                reason="Test",
                contributions=[],
            )

    def test_fit_score_above_ten_rejected(self) -> None:
        """Fit score above ten is invalid."""
        with pytest.raises(ValidationError):
            AnalysisResult(
                repo="owner/name",
                fit_score=11,
                reason="Test",
                contributions=[],
            )

    def test_boundary_scores_accepted(self) -> None:
        """Boundary scores (0.0 and 10.0) are valid."""
        result_zero = AnalysisResult(
            repo="owner/name",
            fit_score=0.0,
            reason="No fit",
            contributions=[],
        )
        assert result_zero.fit_score == 0.0

        result_ten = AnalysisResult(
            repo="owner/name",
            fit_score=10.0,
            reason="Perfect fit",
            contributions=["Contribute everywhere"],
        )
        assert result_ten.fit_score == 10.0

    def test_rejection_fields(self) -> None:
        """Test reject and reject_reason fields."""
        # GIVEN - analysis result marked for rejection
        result = AnalysisResult(
            repo="owner/name",
            fit_score=2.0,
            reason="Low fit",
            contributions=[],
            reject=True,
            reject_reason="Not enough beginner-friendly issues",
        )

        # THEN - rejection fields are set
        assert result.reject is True
        assert result.reject_reason == "Not enough beginner-friendly issues"

    def test_default_rejection_fields(self) -> None:
        """Test default values for reject and reject_reason."""
        # GIVEN - analysis result without rejection fields
        result = AnalysisResult(
            repo="owner/name",
            fit_score=7.0,
            reason="Good fit",
            contributions=["Add tests"],
        )

        # THEN - defaults are set
        assert result.reject is False
        assert result.reject_reason is None


class TestRepoMetadata:
    """Tests for the RepoMetadata schema."""

    def test_valid_metadata(self) -> None:
        """Valid metadata with all required fields."""
        metadata = RepoMetadata(
            github_id=123,
            owner="octocat",
            name="hello",
            url="https://github.com/octocat/hello",
            star_count=42,
        )
        assert metadata.github_id == 123
        assert metadata.owner == "octocat"
        assert metadata.name == "hello"
        assert metadata.url == "https://github.com/octocat/hello"
        assert metadata.star_count == 42

        # Check defaults for optional fields
        assert metadata.description is None
        assert metadata.primary_language is None
        assert metadata.fork_count == 0
        assert metadata.open_issue_count == 0
        assert metadata.languages == []
        assert metadata.topics == []
        assert metadata.license is None
        assert metadata.pushed_at is None
        assert metadata.created_at is None
        assert metadata.good_first_issue_count == 0
        assert metadata.help_wanted_count == 0

    def test_metadata_with_all_fields(self) -> None:
        """Valid metadata with all optional fields populated."""
        metadata = RepoMetadata(
            github_id=456,
            owner="facebook",
            name="react",
            url="https://github.com/facebook/react",
            description="A JavaScript library for building UIs",
            primary_language="JavaScript",
            languages=["JavaScript", "TypeScript"],
            star_count=250000,
            fork_count=50000,
            open_issue_count=1200,
            topics=["react", "frontend", "ui"],
            license="MIT",
            pushed_at="2025-01-15T12:00:00Z",
            created_at="2013-05-24T16:15:54Z",
            good_first_issue_count=15,
            help_wanted_count=8,
        )
        assert metadata.description == "A JavaScript library for building UIs"
        assert metadata.primary_language == "JavaScript"
        assert metadata.languages == ["JavaScript", "TypeScript"]
        assert metadata.topics == ["react", "frontend", "ui"]
        assert metadata.license == "MIT"
        assert metadata.pushed_at == "2025-01-15T12:00:00Z"
        assert metadata.created_at == "2013-05-24T16:15:54Z"
        assert metadata.good_first_issue_count == 15
        assert metadata.help_wanted_count == 8


class TestScoutStreamEvents:
    """Tests for streaming event schemas."""

    def test_status_event(self) -> None:
        """Status event serializes correctly."""
        event = ScoutStreamStatusEvent(message="Searching...")
        assert event.type == "status"
        assert event.message == "Searching..."
        assert event.phase is None

    @pytest.mark.parametrize(
        "phase",
        ["discovering", "filtering", "analyzing"],
    )
    def test_status_event_with_phases(
        self, phase: str
    ) -> None:
        """Status event with all valid phases."""
        typed_phase = cast(Literal["discovering", "filtering", "analyzing"], phase)
        event = ScoutStreamStatusEvent(
            message=f"Processing {phase}...",
            phase=typed_phase,
        )
        assert event.type == "status"
        assert event.phase == phase

    def test_complete_event(self) -> None:
        """Complete event contains scout search result data."""
        result_data = ScoutSearchResult(
            run_id="abc",
            status="completed",
        )
        event = ScoutStreamCompleteEvent(data=result_data)
        assert event.type == "complete"
        assert event.data.run_id == "abc"
        assert event.data.status == "completed"

    def test_error_event(self) -> None:
        """Error event contains message."""
        event = ScoutStreamErrorEvent(message="Failed")
        assert event.type == "error"
        assert event.message == "Failed"


class TestSearchRunResponse:
    """Tests for the SearchRunResponse schema."""

    @pytest.mark.parametrize(
        "status",
        ["running", "completed", "failed", "cancelled", "partial"],
    )
    def test_valid_statuses(
        self, status: str
    ) -> None:
        """All valid status values are accepted."""
        typed_status = cast(
            Literal["running", "completed", "failed", "cancelled", "partial"], status
        )
        response = SearchRunResponse(
            run_id="run_789",
            status=typed_status,
        )
        assert response.run_id == "run_789"
        assert response.status == status


class TestScoutSearchResult:
    """Tests for the ScoutSearchResult schema."""

    def test_valid_result(self) -> None:
        """Valid search result with required fields."""
        result = ScoutSearchResult(
            run_id="test",
            status="completed",
        )
        assert result.run_id == "test"
        assert result.status == "completed"

        # Check defaults
        assert result.total_discovered == 0
        assert result.total_filtered == 0
        assert result.total_analyzed == 0
        assert result.results == []
        assert result.repos == []
        assert result.warnings == []

    def test_complete_result_with_data(self) -> None:
        """Valid search result with all fields populated."""
        analysis = AnalysisResult(
            repo="owner/repo",
            fit_score=8.5,
            reason="Great fit",
            contributions=["Fix bugs", "Add tests"],
        )
        repo = RepoMetadata(
            github_id=789,
            owner="owner",
            name="repo",
            url="https://github.com/owner/repo",
            star_count=1000,
        )
        result = ScoutSearchResult(
            run_id="run_xyz",
            status="completed",
            total_discovered=100,
            total_filtered=50,
            total_analyzed=10,
            results=[analysis],
            repos=[repo],
            warnings=["Rate limit warning"],
        )
        assert result.run_id == "run_xyz"
        assert result.total_discovered == 100
        assert result.total_filtered == 50
        assert result.total_analyzed == 10
        assert len(result.results) == 1
        assert result.results[0].repo == "owner/repo"
        assert len(result.repos) == 1
        assert result.repos[0].owner == "owner"
        assert result.warnings == ["Rate limit warning"]
