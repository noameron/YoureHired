"""Tests for GitHub GraphQL API client — RED phase."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.schemas.scout import SearchFilters
from app.services.github_client import (
    GitHubGraphQLClient,
    _build_search_query_string,
    create_github_client,
)


@pytest.mark.anyio
class TestGitHubGraphQLClient:
    """Test suite for GitHubGraphQLClient class."""

    async def test_empty_token_raises_value_error(self):
        """GIVEN an empty token string
        WHEN GitHubGraphQLClient is instantiated
        THEN ValueError is raised
        """
        # GIVEN
        empty_token = ""

        # WHEN / THEN
        with pytest.raises(ValueError, match="token.*empty|required"):
            GitHubGraphQLClient(empty_token)

    async def test_retry_on_502_then_success(self):
        """GIVEN httpx returns 502 on first call, then 200 with valid data
        WHEN _execute_query is called
        THEN it retries and succeeds on second attempt
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        query = "{ viewer { login } }"

        success_response = httpx.Response(
            status_code=200,
            json={"data": {"viewer": {"login": "testuser"}}},
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )
        error_response = httpx.Response(
            status_code=502,
            text="Bad Gateway",
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(side_effect=[error_response, success_response])

        # WHEN
        with patch("httpx.AsyncClient.post", mock_post):
            result = await client._execute_query(query)

        # THEN
        assert result == {"viewer": {"login": "testuser"}}
        assert mock_post.call_count == 2

    async def test_401_raises_immediately_no_retry(self):
        """GIVEN httpx returns 401 Unauthorized
        WHEN _execute_query is called
        THEN it raises immediately without retrying
        """
        # GIVEN
        client = GitHubGraphQLClient("invalid_token")
        query = "{ viewer { login } }"

        error_response = httpx.Response(
            status_code=401,
            json={"message": "Bad credentials"},
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(return_value=error_response)

        # WHEN / THEN
        with patch("httpx.AsyncClient.post", mock_post):
            with pytest.raises(httpx.HTTPStatusError):
                await client._execute_query(query)

        # Verify only one call was made (no retries)
        assert mock_post.call_count == 1

    async def test_retry_exhaustion_raises_exception(self):
        """GIVEN httpx returns 502 on all retry attempts
        WHEN _execute_query is called
        THEN it raises HTTPStatusError after MAX_RETRIES attempts
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        query = "{ viewer { login } }"

        error_response = httpx.Response(
            status_code=502,
            text="Bad Gateway",
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(return_value=error_response)

        # WHEN / THEN
        with patch("httpx.AsyncClient.post", mock_post):
            with pytest.raises(httpx.HTTPStatusError):
                await client._execute_query(query)

        # Verify MAX_RETRIES (3) attempts were made
        assert mock_post.call_count == 3

    async def test_search_repositories_empty_results(self):
        """GIVEN GitHub API returns empty search results
        WHEN search_repositories is called
        THEN empty lists are returned
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        filters = SearchFilters(languages=["Python"])

        mock_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "search": {
                        "repositoryCount": 0,
                        "edges": [],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                    "rateLimit": {"remaining": 5000},
                }
            },
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(return_value=mock_response)

        # WHEN
        with patch("httpx.AsyncClient.post", mock_post):
            repos, warnings = await client.search_repositories(filters)

        # THEN
        assert repos == []
        assert warnings == []

    async def test_search_repositories_1000_result_warning(self):
        """GIVEN GitHub API returns exactly 1000 results
        WHEN search_repositories is called
        THEN warning message about incomplete results is included
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        filters = SearchFilters(languages=["JavaScript"])

        mock_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "search": {
                        "repositoryCount": 1000,
                        "edges": [
                            {
                                "node": {
                                    "databaseId": 123,
                                    "owner": {"login": "test"},
                                    "name": "repo",
                                    "url": "https://github.com/test/repo",
                                    "description": "Test",
                                    "primaryLanguage": {"name": "JavaScript"},
                                    "languages": {"nodes": [{"name": "JavaScript"}]},
                                    "stargazerCount": 100,
                                    "forkCount": 10,
                                    "issues": {"totalCount": 5},
                                    "repositoryTopics": {"nodes": []},
                                    "licenseInfo": None,
                                    "pushedAt": "2024-01-01T00:00:00Z",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "goodFirstIssues": {"totalCount": 0},
                                    "helpWantedIssues": {"totalCount": 0},
                                }
                            }
                        ],
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                    },
                    "rateLimit": {"remaining": 5000},
                }
            },
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(return_value=mock_response)

        # WHEN
        with patch("httpx.AsyncClient.post", mock_post):
            repos, warnings = await client.search_repositories(filters)

        # THEN
        assert len(warnings) > 0
        assert any("incomplete" in w.lower() or "1000" in w for w in warnings)

    async def test_search_repositories_rate_limit_stop(self):
        """GIVEN GitHub API response shows rate limit below threshold
        WHEN search_repositories is called with pagination
        THEN pagination stops and rate limit warning is included
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        filters = SearchFilters(languages=["Python"])

        # First page with hasNextPage=True but low rate limit
        mock_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "search": {
                        "repositoryCount": 200,
                        "edges": [
                            {
                                "node": {
                                    "databaseId": 123,
                                    "owner": {"login": "test"},
                                    "name": "repo",
                                    "url": "https://github.com/test/repo",
                                    "description": "Test",
                                    "primaryLanguage": {"name": "Python"},
                                    "languages": {"nodes": [{"name": "Python"}]},
                                    "stargazerCount": 100,
                                    "forkCount": 10,
                                    "issues": {"totalCount": 5},
                                    "repositoryTopics": {"nodes": []},
                                    "licenseInfo": None,
                                    "pushedAt": "2024-01-01T00:00:00Z",
                                    "createdAt": "2023-01-01T00:00:00Z",
                                    "goodFirstIssues": {"totalCount": 0},
                                    "helpWantedIssues": {"totalCount": 0},
                                }
                            }
                        ],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                    },
                    "rateLimit": {"remaining": 50},  # Below threshold of 100
                }
            },
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(return_value=mock_response)

        # WHEN
        with patch("httpx.AsyncClient.post", mock_post):
            repos, warnings = await client.search_repositories(filters)

        # THEN
        assert len(warnings) > 0
        assert any("rate limit" in w.lower() for w in warnings)
        # Should not paginate further
        assert mock_post.call_count == 1

    async def test_readme_truncation(self):
        """GIVEN a README with more than 16000 characters
        WHEN fetch_readmes is called
        THEN README is truncated to exactly 16000 characters
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        repos = [("owner", "repo")]
        long_text = "x" * 20000  # Exceeds 16000 limit

        mock_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "repo_0": {
                        "object": {
                            "text": long_text
                        }
                    }
                }
            },
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(return_value=mock_response)

        # WHEN
        with patch("httpx.AsyncClient.post", mock_post):
            readmes = await client.fetch_readmes(repos)

        # THEN
        assert "owner/repo" in readmes
        assert len(readmes["owner/repo"]) == 16000

    async def test_readme_missing_returns_none(self):
        """GIVEN GitHub API returns null for README object
        WHEN fetch_readmes is called
        THEN None is returned in the dictionary
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        repos = [("owner", "repo")]

        mock_response = httpx.Response(
            status_code=200,
            json={
                "data": {
                    "repo_0": {
                        "object": None  # README not found
                    }
                }
            },
            request=httpx.Request("POST", GitHubGraphQLClient.GRAPHQL_URL),
        )

        mock_post = AsyncMock(return_value=mock_response)

        # WHEN
        with patch("httpx.AsyncClient.post", mock_post):
            readmes = await client.fetch_readmes(repos)

        # THEN
        assert "owner/repo" in readmes
        assert readmes["owner/repo"] is None

    async def test_graphql_alias_sanitization(self):
        """GIVEN repository owner/name with special characters
        WHEN fetch_readmes is called
        THEN ValueError is raised to prevent GraphQL injection
        """
        # GIVEN
        client = GitHubGraphQLClient("valid_token")
        malicious_repos = [("../../evil", "repo"), ("owner", "repo{malicious}")]

        # WHEN / THEN
        with pytest.raises(ValueError, match="invalid.*characters"):
            await client.fetch_readmes(malicious_repos)


class TestBuildSearchQueryString:
    """Test suite for _build_search_query_string function."""

    def test_build_search_query_string_single_language(self):
        """GIVEN SearchFilters with single language
        WHEN _build_search_query_string is called
        THEN query contains language qualifier
        """
        # GIVEN
        filters = SearchFilters(languages=["Python"])

        # WHEN
        query = _build_search_query_string(filters)

        # THEN
        assert "language:Python" in query

    def test_build_search_query_string_multiple_languages(self):
        """GIVEN SearchFilters with multiple languages
        WHEN _build_search_query_string is called
        THEN query contains separate language qualifiers for each
        """
        # GIVEN
        filters = SearchFilters(languages=["Python", "Go"])

        # WHEN
        query = _build_search_query_string(filters)

        # THEN
        assert "language:Python" in query
        assert "language:Go" in query

    def test_build_search_query_string_all_fields(self):
        """GIVEN SearchFilters with all fields populated
        WHEN _build_search_query_string is called
        THEN query contains stars range, pushed date, topics, license, archived, fork qualifiers
        """
        # GIVEN
        filters = SearchFilters(
            languages=["Rust"],
            min_stars=100,
            max_stars=1000,
            topics=["cli", "tools"],
            min_activity_date="2024-01-01",
            license="mit",
        )

        # WHEN
        query = _build_search_query_string(filters)

        # THEN
        assert "stars:100..1000" in query
        assert "pushed:>=2024-01-01" in query
        assert "topic:cli" in query
        assert "topic:tools" in query
        assert "license:mit" in query
        assert "archived:false" in query
        assert "fork:false" in query

    def test_build_search_query_string_default_activity_date(self):
        """GIVEN SearchFilters with min_activity_date=None
        WHEN _build_search_query_string is called
        THEN query defaults to 6 months ago from today
        """
        # GIVEN
        filters = SearchFilters(languages=["TypeScript"], min_activity_date=None)
        six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")

        # WHEN
        query = _build_search_query_string(filters)

        # THEN
        assert f"pushed:>={six_months_ago}" in query


class TestCreateGitHubClient:
    """Test suite for create_github_client factory function."""

    def test_create_github_client_uses_settings(self):
        """GIVEN app.config.settings.github_token is set
        WHEN create_github_client is called
        THEN GitHubGraphQLClient is created with that token
        """
        # GIVEN
        test_token = "ghp_test_token_123"

        # WHEN
        with patch("app.config.settings.github_token", test_token):
            client = create_github_client()

        # THEN
        assert isinstance(client, GitHubGraphQLClient)
        assert client.token == test_token
