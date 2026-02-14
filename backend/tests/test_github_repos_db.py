"""
Test suite for GitHubReposDB persistence layer.

These tests cover:
- Database initialization and table creation
- Developer profile CRUD operations
- Search run lifecycle management
- Repository upsert and deduplication
- Analysis result storage and retrieval
- Stale repository pruning logic

All tests use temporary SQLite databases via pytest's tmp_path fixture.
"""

from datetime import UTC, datetime, timedelta

import aiosqlite

from app.schemas.scout import (
    AnalysisResult,
    DeveloperProfile,
    DeveloperProfileResponse,
    RepoMetadata,
    ScoutSearchResult,
    SearchFilters,
    SearchRunResponse,
)
from app.services.github_repos_db import GitHubReposDB


class TestGitHubReposDBInit:
    """Test database initialization and setup."""

    async def test_init_creates_tables(self, tmp_path):
        """
        GIVEN a fresh GitHubReposDB instance
        WHEN _ensure_init is called
        THEN all 4 tables should exist in sqlite_master
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        await db._ensure_init()

        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "ORDER BY name"
            )
            tables = [row[0] for row in await cursor.fetchall()]

        expected = [
            "analysis_results",
            "developer_profiles",
            "repositories",
            "search_runs",
        ]
        assert tables == expected

    async def test_wal_mode_activated(self, tmp_path):
        """
        GIVEN a fresh GitHubReposDB instance
        WHEN _ensure_init is called
        THEN WAL journal mode should be active
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        await db._ensure_init()

        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute("PRAGMA journal_mode")
            mode = (await cursor.fetchone())[0]

        assert mode.lower() == "wal"


class TestProfileOperations:
    """Test developer profile save and retrieve operations."""

    async def test_save_profile_returns_default(self, tmp_path):
        """
        GIVEN a valid DeveloperProfile
        WHEN save_profile is called
        THEN it should return the string "default"
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        profile = DeveloperProfile(
            languages=["Python", "TypeScript"],
            topics=["web", "api"],
            skill_level="intermediate",
            goals="Build full-stack applications",
        )

        result = await db.save_profile(profile)

        assert result == "default"

    async def test_get_profile_returns_saved(self, tmp_path):
        """
        GIVEN a saved developer profile
        WHEN get_profile is called
        THEN it should return DeveloperProfileResponse with matching fields
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        profile = DeveloperProfile(
            languages=["Python", "TypeScript"],
            topics=["web", "api"],
            skill_level="advanced",
            goals="Contribute to open source",
        )

        await db.save_profile(profile)
        result = await db.get_profile()

        assert result is not None
        assert isinstance(result, DeveloperProfileResponse)
        assert result.id == "default"
        assert result.profile.languages == ["Python", "TypeScript"]
        assert result.profile.topics == ["web", "api"]
        assert result.profile.skill_level == "advanced"
        assert result.profile.goals == "Contribute to open source"
        assert result.created_at is not None
        assert result.updated_at is None  # First save has no update timestamp

    async def test_save_overwrites_previous(self, tmp_path):
        """
        GIVEN two different developer profiles
        WHEN both are saved sequentially
        THEN get_profile should return the second profile (single-profile mode)
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))

        profile_a = DeveloperProfile(
            languages=["Java"],
            topics=["backend"],
            skill_level="beginner",
            goals="Learn Java",
        )
        profile_b = DeveloperProfile(
            languages=["Rust", "Go"],
            topics=["systems", "performance"],
            skill_level="advanced",
            goals="Build high-performance systems",
        )

        await db.save_profile(profile_a)
        await db.save_profile(profile_b)
        result = await db.get_profile()

        assert result is not None
        assert result.profile.languages == ["Rust", "Go"]
        assert result.profile.topics == ["systems", "performance"]
        assert result.profile.skill_level == "advanced"
        assert result.updated_at is not None  # Second save creates update timestamp

    async def test_get_profile_empty_returns_none(self, tmp_path):
        """
        GIVEN a fresh database with no profiles
        WHEN get_profile is called
        THEN it should return None
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))

        result = await db.get_profile()

        assert result is None


class TestSearchRunOperations:
    """Test search run creation, retrieval, and updates."""

    async def test_create_and_get_search_run(self, tmp_path):
        """
        GIVEN a SearchFilters object
        WHEN create_search_run is called
        THEN get_search_run should return SearchRunResponse with status="running"
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        filters = SearchFilters(
            languages=["Python"],
            min_stars=50,
            max_stars=1000,
            topics=["fastapi", "web"],
        )

        run_id = await db.create_search_run(filters)
        result = await db.get_search_run(run_id)

        assert result is not None
        assert isinstance(result, SearchRunResponse)
        assert result.run_id == run_id
        assert result.status == "running"

    async def test_get_search_run_nonexistent_returns_none(self, tmp_path):
        """
        GIVEN a nonexistent run_id
        WHEN get_search_run is called
        THEN it should return None
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))

        result = await db.get_search_run("nonexistent-run-id")

        assert result is None

    async def test_update_search_run_status_and_totals(self, tmp_path):
        """
        GIVEN an existing search run
        WHEN update_search_run is called with new status and totals
        THEN get_search_run should reflect the updates
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        filters = SearchFilters(languages=["TypeScript"])

        run_id = await db.create_search_run(filters)
        await db.update_search_run(
            run_id=run_id,
            status="completed",
            total_discovered=50,
            total_filtered=20,
            total_analyzed=10,
        )
        result = await db.get_search_run(run_id)

        assert result is not None
        assert result.status == "completed"
        # Note: SearchRunResponse doesn't expose totals directly in your schema
        # but the DB should store them for get_search_results

    async def test_get_search_run_filters(self, tmp_path):
        """
        GIVEN a search run created with specific filters
        WHEN get_search_run_filters is called
        THEN it should return SearchFilters matching the input
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        original_filters = SearchFilters(
            languages=["Rust", "Go"],
            min_stars=100,
            max_stars=5000,
            topics=["cli", "performance"],
            license="MIT",
        )

        run_id = await db.create_search_run(original_filters)
        retrieved_filters = await db.get_search_run_filters(run_id)

        assert retrieved_filters is not None
        assert isinstance(retrieved_filters, SearchFilters)
        assert retrieved_filters.languages == ["Rust", "Go"]
        assert retrieved_filters.min_stars == 100
        assert retrieved_filters.max_stars == 5000
        assert retrieved_filters.topics == ["cli", "performance"]
        assert retrieved_filters.license == "MIT"

    async def test_get_search_run_filters_nonexistent_returns_none(self, tmp_path):
        """
        GIVEN a nonexistent run_id
        WHEN get_search_run_filters is called
        THEN it should return None
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))

        result = await db.get_search_run_filters("nonexistent-run-id")

        assert result is None


class TestRepoOperations:
    """Test repository upsert and deduplication logic."""

    async def test_upsert_deduplicates_by_github_id(self, tmp_path):
        """
        GIVEN a repository metadata record
        WHEN the same github_id is upserted twice with different star_count
        THEN only one row should exist with the updated values
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        await db._ensure_init()

        repo_v1 = RepoMetadata(
            github_id=123456,
            owner="test-owner",
            name="test-repo",
            url="https://github.com/test-owner/test-repo",
            star_count=100,
            primary_language="Python",
        )
        repo_v2 = RepoMetadata(
            github_id=123456,
            owner="test-owner",
            name="test-repo",
            url="https://github.com/test-owner/test-repo",
            star_count=200,  # Updated
            primary_language="Python",
        )

        await db.upsert_repositories([repo_v1])
        await db.upsert_repositories([repo_v2])

        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*), star_count FROM repositories WHERE github_id = ?",
                (123456,),
            )
            row = await cursor.fetchone()

        assert row[0] == 1  # Only one row
        assert row[1] == 200  # Updated star count

    async def test_upsert_empty_list_does_nothing(self, tmp_path):
        """
        GIVEN an empty repository list
        WHEN upsert_repositories is called
        THEN it should complete without error
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))

        await db.upsert_repositories([])

        # Should not raise an exception


class TestAnalysisResults:
    """Test analysis result storage and retrieval with repo joins."""

    async def test_save_and_retrieve_results(self, tmp_path):
        """
        GIVEN a search run with upserted repos and saved analysis results
        WHEN get_search_results is called
        THEN it should return ScoutSearchResult with results sorted by fit_score desc
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        filters = SearchFilters(languages=["Python"])
        run_id = await db.create_search_run(filters)

        # Create repos
        repos = [
            RepoMetadata(
                github_id=1,
                owner="owner1",
                name="repo1",
                url="https://github.com/owner1/repo1",
                star_count=500,
                primary_language="Python",
            ),
            RepoMetadata(
                github_id=2,
                owner="owner2",
                name="repo2",
                url="https://github.com/owner2/repo2",
                star_count=300,
                primary_language="Python",
            ),
            RepoMetadata(
                github_id=3,
                owner="owner3",
                name="repo3",
                url="https://github.com/owner3/repo3",
                star_count=800,
                primary_language="Python",
            ),
        ]
        await db.upsert_repositories(repos)

        # Save analysis results with different fit scores
        analyses = [
            AnalysisResult(
                repo="owner1/repo1",
                fit_score=7.5,
                reason="Good beginner-friendly issues",
                contributions=["Fix typos", "Add tests"],
            ),
            AnalysisResult(
                repo="owner2/repo2",
                fit_score=9.2,
                reason="Perfect match for skill level",
                contributions=["Implement feature X"],
            ),
            AnalysisResult(
                repo="owner3/repo3",
                fit_score=5.0,
                reason="Limited documentation",
                contributions=["Update README"],
            ),
        ]
        await db.save_analysis_results(run_id, analyses)

        result = await db.get_search_results(run_id)

        assert result is not None
        assert isinstance(result, ScoutSearchResult)
        assert result.run_id == run_id
        assert len(result.results) == 3
        # Verify sorted by fit_score descending
        assert result.results[0].fit_score == 9.2
        assert result.results[0].repo == "owner2/repo2"
        assert result.results[1].fit_score == 7.5
        assert result.results[2].fit_score == 5.0
        # Verify repos are included
        assert len(result.repos) == 3

    async def test_get_search_results_unknown_run(self, tmp_path):
        """
        GIVEN a nonexistent run_id
        WHEN get_search_results is called
        THEN it should return None
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))

        result = await db.get_search_results("nonexistent-run-id")

        assert result is None

    async def test_get_search_results_no_results(self, tmp_path):
        """
        GIVEN a search run with no saved analysis results
        WHEN get_search_results is called
        THEN it should return ScoutSearchResult with empty results list
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        filters = SearchFilters(languages=["Python"])
        run_id = await db.create_search_run(filters)

        result = await db.get_search_results(run_id)

        assert result is not None
        assert isinstance(result, ScoutSearchResult)
        assert result.run_id == run_id
        assert result.results == []
        assert result.repos == []

    async def test_save_analysis_results_empty_list_does_nothing(self, tmp_path):
        """
        GIVEN an empty analysis results list
        WHEN save_analysis_results is called
        THEN it should complete without error
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        filters = SearchFilters(languages=["Python"])
        run_id = await db.create_search_run(filters)

        await db.save_analysis_results(run_id, [])

        # Should not raise an exception

    async def test_save_analysis_results_skips_unknown_repos(self, tmp_path):
        """
        GIVEN an analysis result for a repo not in the repositories table
        WHEN save_analysis_results is called
        THEN it should skip that result without error
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        filters = SearchFilters(languages=["Python"])
        run_id = await db.create_search_run(filters)

        # Try to save analysis for a repo that doesn't exist
        analyses = [
            AnalysisResult(
                repo="nonexistent/repo",
                fit_score=5.0,
                reason="Test",
            )
        ]
        await db.save_analysis_results(run_id, analyses)

        # Should not raise an exception, and get_search_results should be empty
        result = await db.get_search_results(run_id)
        assert result is not None
        assert result.results == []
        assert result.repos == []


class TestPruning:
    """Test stale repository pruning logic."""

    async def test_prune_deletes_stale_unreferenced_repos(self, tmp_path):
        """
        GIVEN repos with last_seen_at > 30 days ago
        WHEN prune_stale_repos is called
        THEN those repos should be deleted
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        await db._ensure_init()

        stale_date = datetime.now(tz=UTC) - timedelta(days=31)
        stale_date_str = stale_date.isoformat()

        # Insert stale repo directly
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO repositories
                (github_id, owner, name, url, star_count, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    999, "old-owner", "old-repo",
                    "https://github.com/old-owner/old-repo",
                    100, stale_date_str,
                ),
            )
            await conn.commit()

        await db.prune_stale_repos()

        # Verify deletion
        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM repositories "
                "WHERE github_id = ?",
                (999,),
            )
            count = (await cursor.fetchone())[0]

        assert count == 0

    async def test_prune_keeps_referenced_repos(self, tmp_path):
        """
        GIVEN old repos attached to analysis results
        WHEN prune_stale_repos is called
        THEN those repos should NOT be deleted
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        await db._ensure_init()

        stale_date = datetime.now(tz=UTC) - timedelta(days=31)
        stale_date_str = stale_date.isoformat()

        # Insert stale repo
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO repositories
                (github_id, owner, name, url, star_count, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    777, "kept-owner", "kept-repo",
                    "https://github.com/kept-owner/kept-repo",
                    200, stale_date_str,
                ),
            )
            await conn.commit()

        # Create search run and analysis result referencing this repo
        filters = SearchFilters(languages=["Python"])
        run_id = await db.create_search_run(filters)
        analyses = [
            AnalysisResult(
                repo="kept-owner/kept-repo",
                fit_score=8.0,
                reason="Referenced repo",
            )
        ]
        await db.save_analysis_results(run_id, analyses)

        await db.prune_stale_repos()

        # Verify repo still exists
        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM repositories "
                "WHERE github_id = ?",
                (777,),
            )
            count = (await cursor.fetchone())[0]

        assert count == 1

    async def test_prune_keeps_recent_repos(self, tmp_path):
        """
        GIVEN repos with last_seen_at < 30 days ago
        WHEN prune_stale_repos is called
        THEN those repos should NOT be deleted
        """
        db = GitHubReposDB(str(tmp_path / "scout.db"))
        await db._ensure_init()

        recent_date = datetime.now(tz=UTC) - timedelta(days=10)
        recent_date_str = recent_date.isoformat()

        # Insert recent repo
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute(
                """
                INSERT INTO repositories
                (github_id, owner, name, url, star_count, last_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    888, "recent-owner", "recent-repo",
                    "https://github.com/recent-owner/recent-repo",
                    150, recent_date_str,
                ),
            )
            await conn.commit()

        await db.prune_stale_repos()

        # Verify repo still exists
        async with aiosqlite.connect(db.db_path) as conn:
            cursor = await conn.execute(
                "SELECT COUNT(*) FROM repositories "
                "WHERE github_id = ?",
                (888,),
            )
            count = (await cursor.fetchone())[0]

        assert count == 1
