"""GitHub GraphQL API client for repository search and README fetching."""

import asyncio
import random
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from app.config import settings
from app.schemas.scout import RepoMetadata, SearchFilters

_VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9._-]+$")

GRAPHQL_URL = "https://api.github.com/graphql"
RATE_LIMIT_THRESHOLD = 100
MAX_RETRIES = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]
README_BATCH_SIZE = 20
README_MAX_CHARS = 16000

SEARCH_QUERY = """
query SearchRepos($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo { hasNextPage endCursor }
    edges {
      node {
        ... on Repository {
          databaseId
          owner { login }
          name
          url
          description
          primaryLanguage { name }
          languages(first: 10) { nodes { name } }
          stargazerCount
          forkCount
          issues(states: OPEN) { totalCount }
          repositoryTopics(first: 20) { nodes { topic { name } } }
          licenseInfo { spdxId }
          pushedAt
          createdAt
          goodFirstIssues: issues(labels: ["good first issue"], states: OPEN) { totalCount }
          helpWantedIssues: issues(labels: ["help wanted"], states: OPEN) { totalCount }
        }
      }
    }
  }
  rateLimit { remaining resetAt }
}
"""


class GitHubGraphQLClient:
    GRAPHQL_URL = GRAPHQL_URL
    RATE_LIMIT_THRESHOLD = RATE_LIMIT_THRESHOLD
    MAX_RETRIES = MAX_RETRIES
    RETRY_DELAYS = RETRY_DELAYS
    README_BATCH_SIZE = README_BATCH_SIZE
    README_MAX_CHARS = README_MAX_CHARS

    def __init__(self, token: str) -> None:
        if not token:
            raise ValueError("GITHUB_TOKEN is not configured — token is required")
        self.token = token

    async def _execute_query(
        self, query: str, variables: dict[str, object] | None = None
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload: dict[str, object] = {"query": query}
        if variables:
            payload["variables"] = variables

        response = await self._retry_request(payload, headers)
        data = response.json()
        result: dict[str, Any] = data.get("data", data)
        return result

    async def _retry_request(
        self,
        payload: dict[str, object],
        headers: dict[str, str],
    ) -> httpx.Response:
        """Execute an HTTP POST with retry for 502/503 errors."""
        last_exc: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            async with httpx.AsyncClient(timeout=30.0) as http:
                response = await http.post(
                    self.GRAPHQL_URL, json=payload, headers=headers
                )

            if response.status_code == 401:
                response.raise_for_status()

            if response.status_code in (502, 503):
                last_exc = httpx.HTTPStatusError(
                    f"Server error {response.status_code}",
                    request=response.request,
                    response=response,
                )
                if attempt < self.MAX_RETRIES - 1:
                    await _sleep_with_jitter(self.RETRY_DELAYS[attempt])
                    continue
                raise last_exc

            response.raise_for_status()
            return response

        assert last_exc is not None, "Retry loop completed without setting exception"
        raise last_exc

    async def search_repositories(
        self, filters: SearchFilters
    ) -> tuple[list[RepoMetadata], list[str]]:
        query_string = _build_search_query_string(filters)
        repos: list[RepoMetadata] = []
        warnings: list[str] = []
        cursor: str | None = None
        max_total = settings.scout_max_repos * 2

        while True:
            variables: dict[str, object] = {
                "query": query_string,
                "first": 100,
                "after": cursor,
            }
            data = await self._execute_query(SEARCH_QUERY, variables)
            cursor = self._process_search_page(data, repos, warnings, max_total)
            if cursor is None:
                break

        return repos, warnings

    def _process_search_page(
        self,
        data: dict[str, Any],
        repos: list[RepoMetadata],
        warnings: list[str],
        max_total: int,
    ) -> str | None:
        search = data["search"]

        if search["repositoryCount"] >= 1000 and not any(
            "incomplete" in w.lower() for w in warnings
        ):
            warnings.append(
                "Results may be incomplete (GitHub caps at 1,000). "
                "Try narrowing your filters."
            )

        for edge in search["edges"]:
            repos.append(_parse_repo_node(edge["node"]))

        rate_remaining = data.get("rateLimit", {}).get("remaining", 5000)
        if rate_remaining < self.RATE_LIMIT_THRESHOLD:
            warnings.append(
                "GitHub rate limit approaching. Returning partial results."
            )
            return None

        page_info = search["pageInfo"]
        if not page_info["hasNextPage"] or len(repos) >= max_total:
            return None

        end_cursor: str = page_info["endCursor"]
        return end_cursor

    async def fetch_readmes(
        self, repos: list[tuple[str, str]]
    ) -> dict[str, str | None]:
        for owner, name in repos:
            if not _VALID_NAME_RE.match(owner) or not _VALID_NAME_RE.match(name):
                raise ValueError(
                    f"Repository '{owner}/{name}' contains invalid characters"
                )

        result: dict[str, str | None] = {}
        for batch_start in range(0, len(repos), self.README_BATCH_SIZE):
            batch = repos[batch_start : batch_start + self.README_BATCH_SIZE]
            query = _build_readme_query(batch, batch_start)
            data = await self._execute_query(query)

            for i, (owner, name) in enumerate(batch):
                alias = f"repo_{batch_start + i}"
                repo_data = data.get(alias)
                if repo_data and repo_data.get("object"):
                    text = repo_data["object"].get("text")
                    if text and len(text) > self.README_MAX_CHARS:
                        text = text[: self.README_MAX_CHARS]
                    result[f"{owner}/{name}"] = text
                else:
                    result[f"{owner}/{name}"] = None

        return result


def _parse_repo_node(node: dict[str, Any]) -> RepoMetadata:
    return RepoMetadata(
        github_id=node["databaseId"],
        owner=node["owner"]["login"],
        name=node["name"],
        url=node["url"],
        description=node.get("description"),
        primary_language=(node.get("primaryLanguage") or {}).get("name"),
        languages=[n["name"] for n in (node.get("languages", {}).get("nodes") or [])],
        star_count=node.get("stargazerCount", 0),
        fork_count=node.get("forkCount", 0),
        open_issue_count=(node.get("issues") or {}).get("totalCount", 0),
        topics=[
            n["topic"]["name"]
            for n in (node.get("repositoryTopics", {}).get("nodes") or [])
        ],
        license=(node.get("licenseInfo") or {}).get("spdxId"),
        pushed_at=node.get("pushedAt"),
        created_at=node.get("createdAt"),
        good_first_issue_count=(node.get("goodFirstIssues") or {}).get(
            "totalCount", 0
        ),
        help_wanted_count=(node.get("helpWantedIssues") or {}).get("totalCount", 0),
    )


def _build_search_query_string(filters: SearchFilters) -> str:
    parts: list[str] = []

    for lang in filters.languages:
        parts.append(f"language:{lang}")

    parts.append(f"stars:{filters.min_stars}..{filters.max_stars}")

    if filters.min_activity_date:
        parts.append(f"pushed:>={filters.min_activity_date}")
    else:
        six_months_ago = (datetime.now(tz=UTC) - timedelta(days=180)).strftime("%Y-%m-%d")
        parts.append(f"pushed:>={six_months_ago}")

    for topic in filters.topics:
        parts.append(f"topic:{topic}")

    if filters.license:
        parts.append(f"license:{filters.license}")

    parts.append("archived:false")
    parts.append("fork:false")

    return " ".join(parts)


def _build_readme_query(repos: list[tuple[str, str]], offset: int = 0) -> str:
    parts: list[str] = []
    for i, (owner, name) in enumerate(repos):
        alias = f"repo_{offset + i}"
        parts.append(
            f'{alias}: repository(owner: "{owner}", name: "{name}") '
            f'{{ object(expression: "HEAD:README.md") {{ ... on Blob {{ text }} }} }}'
        )
    return "query { " + " ".join(parts) + " rateLimit { remaining resetAt } }"


async def _sleep_with_jitter(delay: float) -> None:
    jitter = random.uniform(0, delay * 0.5)
    await asyncio.sleep(delay + jitter)


def create_github_client() -> GitHubGraphQLClient:
    return GitHubGraphQLClient(settings.github_token)
