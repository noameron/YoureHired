# Plan 4: GitHub GraphQL Client

**Branch:** `scout/04-github-client`
**Depends on:** plan_1 (schemas for `SearchFilters`, `RepoMetadata`; config for `github_token`)
**Blocks:** plan_7
**Parallel with:** plan_5, plan_6

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "New backend module for GitHub GraphQL API integration"
- Design: `openspec/changes/add-github-scout/design.md` — Decision 1 (GraphQL API), Decision 3 (fetch README after filtering), Decision 4 (1000-result cap warning)
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 4.1-4.4

## Production Files (1)

### 1. CREATE `backend/app/services/github_client.py`

```python
class GitHubGraphQLClient:
    GRAPHQL_URL = "https://api.github.com/graphql"
    RATE_LIMIT_THRESHOLD = 100   # abort if remaining points below this
    MAX_RETRIES = 3
    RETRY_DELAYS = [1.0, 2.0, 4.0]  # seconds, with added jitter
    README_BATCH_SIZE = 20
    README_MAX_CHARS = 16000     # ~4000 tokens

    def __init__(self, token: str) -> None
        # Raises ValueError if token is empty

    async def _execute_query(
        self, query: str, variables: dict[str, object] | None = None
    ) -> dict
        # Sends POST to GRAPHQL_URL with Bearer auth
        # Retries on 502/503/network errors with backoff + jitter
        # Raises immediately on 401 (bad token)
        # httpx timeout: 30s per request

    async def search_repositories(
        self, filters: SearchFilters
    ) -> tuple[list[RepoMetadata], list[str]]
        # Returns (repos, warnings)
        # Paginates with first:100 + after cursor
        # Stops when hasNextPage=false OR total > scout_max_repos * 2
        # Appends warning if repositoryCount >= 1000
        # Checks rateLimit.remaining after each page, stops if < threshold

    async def fetch_readmes(
        self, repos: list[tuple[str, str]]
    ) -> dict[str, str | None]
        # Batches up to 20 repos per GraphQL query using aliases
        # Returns {"owner/name": readme_text_or_none}
        # Truncates README text to README_MAX_CHARS


def _build_search_query_string(filters: SearchFilters) -> str
    # Module-level, pure function for testability
    # Constructs: "language:Python language:Go stars:10..5000
    #              pushed:>2025-08-01 archived:false fork:false
    #              topic:web-framework license:mit"
    # Multiple languages → separate language:X qualifiers (GitHub ORs them)
    # If min_activity_date is None → defaults to 6 months ago


def create_github_client() -> GitHubGraphQLClient
    # Factory using settings.github_token
```

**GraphQL search query:**

```graphql
query SearchRepos($query: String!, $first: Int!, $after: String) {
  search(query: $query, type: REPOSITORY, first: $first, after: $after) {
    repositoryCount
    pageInfo { hasNextPage endCursor }
    nodes {
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
  rateLimit { remaining resetAt }
}
```

**GraphQL README batch query (dynamic aliases):**

```python
def _build_readme_query(repos: list[tuple[str, str]]) -> str:
    parts = []
    for i, (owner, name) in enumerate(repos):
        # Sanitize: validate owner/name against ^[a-zA-Z0-9._-]+$
        alias = f"repo{i}"
        parts.append(
            f'{alias}: repository(owner: "{owner}", name: "{name}") '
            f'{{ object(expression: "HEAD:README.md") {{ ... on Blob {{ text }} }} }}'
        )
    return "query { " + " ".join(parts) + " rateLimit { remaining resetAt } }"
```

## Test Files

- `backend/tests/test_github_client.py`
  - `_build_search_query_string` with single language
  - `_build_search_query_string` with multiple languages (each gets own qualifier)
  - `_build_search_query_string` with all filter fields
  - `_build_search_query_string` with `min_activity_date=None` defaults to 6 months ago
  - `search_repositories` returns warning when `repositoryCount >= 1000`
  - `search_repositories` stops pagination when `rateLimit.remaining < 100`
  - `search_repositories` returns empty list for no results
  - Retry logic: mock httpx to fail with 502 then succeed
  - README truncation at 16000 chars
  - README missing (no `README.md`) → `None` in dict
  - Empty token → `ValueError`
  - GraphQL alias sanitization rejects invalid characters
  - All tests use mocked `httpx` responses (no real GitHub calls)

## Edge Cases

- Empty token → `ValueError("GITHUB_TOKEN is not configured")` in `__init__`
- 401 (bad token) → raise immediately, no retry
- 502/503 → retry up to 3x with `delay + random.uniform(0, delay * 0.5)` jitter
- Network timeout → `httpx.TimeoutException` after 30s
- `repositoryCount >= 1000` → append: "Results may be incomplete (GitHub caps at 1,000). Try narrowing your filters."
- `rateLimit.remaining < 100` → stop pagination, append: "GitHub rate limit approaching. Returning partial results."
- README not found → `None` for that repo key in the dict
- README > 16000 chars → truncated to 16000
- Empty search results → return `([], [])`
- Owner/name with special chars → reject with `ValueError` before interpolating into GraphQL

## Verification

```bash
cd backend && uv run pytest tests/test_github_client.py -v
```
