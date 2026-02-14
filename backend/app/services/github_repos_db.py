"""SQLite persistence layer for GitHub Scout feature."""

import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from functools import cache
from pathlib import Path
from typing import Literal

import aiosqlite

from app.config import settings
from app.schemas.scout import (
    AnalysisResult,
    DeveloperProfile,
    DeveloperProfileResponse,
    RepoMetadata,
    ScoutSearchResult,
    SearchFilters,
    SearchRunResponse,
)

_QUERIES_DIR = Path(__file__).parent / "queries"

_DDL_KEYS = [
    "create_developer_profiles",
    "create_search_runs",
    "create_repositories",
    "create_analysis_results",
]


@cache
def _sql(name: str) -> str:
    return (_QUERIES_DIR / f"{name}.sql").read_text().strip()


class GitHubReposDB:
    """Async SQLite persistence for GitHub Scout data."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._initialized = False

    @asynccontextmanager
    async def _connect(self) -> AsyncIterator[aiosqlite.Connection]:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL")
            await db.execute("PRAGMA foreign_keys=ON")
            yield db

    async def _ensure_init(self) -> None:
        if self._initialized:
            return
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        async with self._connect() as db:
            for key in _DDL_KEYS:
                await db.execute(_sql(key))
            await db.commit()
        self._initialized = True
        await self.prune_stale_repos()

    async def save_profile(
        self, profile: DeveloperProfile
<<<<<<< HEAD
    ) -> Literal["default"]:
        await self._ensure_init()
        now = datetime.now(tz=UTC).isoformat()
        async with self._connect() as db:
            cursor = await db.execute(
                _sql("check_profile_exists"),
                ("default",),
            )
            exists = await cursor.fetchone()
            if exists:
                await db.execute(
                    _sql("update_profile"),
                    (
                        json.dumps(profile.languages),
                        json.dumps(profile.topics),
                        profile.skill_level,
                        profile.goals,
                        now,
                        "default",
                    ),
                )
            else:
                await db.execute(
                    _sql("insert_profile"),
                    (
                        "default",
                        json.dumps(profile.languages),
                        json.dumps(profile.topics),
                        profile.skill_level,
                        profile.goals,
                        now,
                    ),
                )
            await db.commit()
        return "default"

    async def get_profile(
        self,
    ) -> DeveloperProfileResponse | None:
        await self._ensure_init()
        async with self._connect() as db:
            cursor = await db.execute(
                _sql("get_profile"),
                ("default",),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        profile = DeveloperProfile(
            languages=json.loads(row[1]),
            topics=json.loads(row[2]),
            skill_level=row[3],
            goals=row[4],
        )
        return DeveloperProfileResponse(
            id=row[0],
            profile=profile,
            created_at=row[5],
            updated_at=row[6],
        )

    async def create_search_run(
        self, filters: SearchFilters
    ) -> str:
        await self._ensure_init()
        run_id = str(uuid.uuid4())
        now = datetime.now(tz=UTC).isoformat()
        async with self._connect() as db:
            cursor = await db.execute(
                _sql("check_profile_for_run"),
                ("default",),
            )
            profile_row = await cursor.fetchone()
            profile_id = profile_row[0] if profile_row else None
            await db.execute(
                _sql("insert_search_run"),
                (
                    run_id,
                    profile_id,
                    json.dumps(filters.model_dump()),
                    "running",
                    now,
                ),
            )
            await db.commit()
        return run_id

    async def update_search_run(
        self,
        run_id: str,
        status: str,
        total_discovered: int = 0,
        total_filtered: int = 0,
        total_analyzed: int = 0,
    ) -> None:
        await self._ensure_init()
        now = datetime.now(tz=UTC).isoformat()
        async with self._connect() as db:
            await db.execute(
                _sql("update_search_run"),
                (
                    status,
                    now,
                    total_discovered,
                    total_filtered,
                    total_analyzed,
                    run_id,
                ),
            )
            await db.commit()

    async def get_search_run(
        self, run_id: str
    ) -> SearchRunResponse | None:
        await self._ensure_init()
        async with self._connect() as db:
            cursor = await db.execute(
                _sql("get_search_run"),
                (run_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return SearchRunResponse(run_id=row[0], status=row[1])

    async def get_search_run_filters(
        self, run_id: str
    ) -> SearchFilters | None:
        await self._ensure_init()
        async with self._connect() as db:
            cursor = await db.execute(
                _sql("get_search_run_filters"),
                (run_id,),
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return SearchFilters(**json.loads(row[0]))

    async def upsert_repositories(
        self, repos: list[RepoMetadata]
    ) -> None:
        await self._ensure_init()
        if not repos:
            return
        now = datetime.now(tz=UTC).isoformat()
        async with self._connect() as db:
            for repo in repos:
                await db.execute(
                    _sql("upsert_repository"),
                    (
                        repo.github_id,
                        repo.owner,
                        repo.name,
                        repo.url,
                        repo.description,
                        repo.primary_language,
                        json.dumps(repo.languages),
                        repo.star_count,
                        repo.fork_count,
                        repo.open_issue_count,
                        json.dumps(repo.topics),
                        repo.license,
                        repo.pushed_at,
                        repo.created_at,
                        repo.good_first_issue_count,
                        repo.help_wanted_count,
                        now,
                    ),
                )
            await db.commit()

    async def save_analysis_results(
        self, run_id: str, results: list[AnalysisResult]
    ) -> None:
        await self._ensure_init()
        if not results:
            return
        now = datetime.now(tz=UTC).isoformat()
        async with self._connect() as db:
            for result in results:
                owner, name = result.repo.split("/", 1)
                cursor = await db.execute(
                    _sql("find_repo_by_owner_name"),
                    (owner, name),
                )
                row = await cursor.fetchone()
                if row is None:
                    continue
                await db.execute(
                    _sql("insert_analysis_result"),
                    (
                        run_id,
                        row[0],
                        result.fit_score,
                        result.reason,
                        json.dumps(result.contributions),
                        1 if result.reject else 0,
                        result.reject_reason,
                        now,
                    ),
                )
            await db.commit()

    async def get_search_results(
        self, run_id: str
    ) -> ScoutSearchResult | None:
        await self._ensure_init()
        async with self._connect() as db:
            cursor = await db.execute(
                _sql("get_search_run_info"),
                (run_id,),
            )
            run_row = await cursor.fetchone()
            if run_row is None:
                return None
            cursor = await db.execute(
                _sql("get_analysis_with_repos"),
                (run_id,),
            )
            rows = await cursor.fetchall()
        results = []
        repos = []
        for row in rows:
            results.append(
                AnalysisResult(
                    repo=f"{row[6]}/{row[7]}",
                    fit_score=row[0],
                    reason=row[1],
                    contributions=(
                        json.loads(row[2]) if row[2] else []
                    ),
                    reject=bool(row[3]),
                    reject_reason=row[4],
                )
            )
            repos.append(
                RepoMetadata(
                    github_id=row[5],
                    owner=row[6],
                    name=row[7],
                    url=row[8],
                    description=row[9],
                    primary_language=row[10],
                    languages=(
                        json.loads(row[11]) if row[11] else []
                    ),
                    star_count=row[12],
                    fork_count=row[13],
                    open_issue_count=row[14],
                    topics=(
                        json.loads(row[15]) if row[15] else []
                    ),
                    license=row[16],
                    pushed_at=row[17],
                    created_at=row[18],
                    good_first_issue_count=row[19],
                    help_wanted_count=row[20],
                )
            )
        return ScoutSearchResult(
            run_id=run_row[0],
            status=run_row[1],
            total_discovered=run_row[2] or 0,
            total_filtered=run_row[3] or 0,
            total_analyzed=run_row[4] or 0,
            results=results,
            repos=repos,
        )

    async def prune_stale_repos(self, days: int = 30) -> int:
        await self._ensure_init()
        cutoff = (
            datetime.now(tz=UTC) - timedelta(days=days)
        ).isoformat()
        async with self._connect() as db:
            cursor = await db.execute(
                _sql("prune_stale_repos"),
                (cutoff,),
            )
            await db.commit()
            rowcount = cursor.rowcount
            return rowcount if rowcount is not None else 0


github_repos_db = GitHubReposDB(settings.scout_db_path)
