"""Tests for Scout profile API endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Async HTTP client for testing FastAPI app."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path, monkeypatch):
    """Ensure each test uses a fresh isolated database."""
    from app.services.github_repos_db import github_repos_db

    db_file = str(tmp_path / "test_scout.db")
    monkeypatch.setattr(github_repos_db, "db_path", db_file)
    github_repos_db._initialized = False
    yield
    github_repos_db._initialized = False


async def test_post_profile_returns_id(client: AsyncClient):
    # GIVEN - a valid developer profile payload
    profile_data = {
        "languages": ["Python", "TypeScript"],
        "topics": ["web", "api"],
        "skill_level": "intermediate",
        "goals": "Contribute to open-source Python projects"
    }

    # WHEN - posting the profile to the API
    response = await client.post("/api/scout/profile", json=profile_data)

    # THEN - returns 200 with id "default"
    assert response.status_code == 200
    assert response.json() == {"id": "default"}


async def test_get_profile_after_save(client: AsyncClient):
    # GIVEN - a saved developer profile
    profile_data = {
        "languages": ["Python", "TypeScript"],
        "topics": ["web", "api"],
        "skill_level": "intermediate",
        "goals": "Contribute to open-source Python projects"
    }
    await client.post("/api/scout/profile", json=profile_data)

    # WHEN - retrieving the profile
    response = await client.get("/api/scout/profile")

    # THEN - returns 200 with full profile including metadata
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "default"
    assert data["profile"]["languages"] == ["Python", "TypeScript"]
    assert data["profile"]["topics"] == ["web", "api"]
    assert data["profile"]["skill_level"] == "intermediate"
    assert data["profile"]["goals"] == "Contribute to open-source Python projects"
    assert "created_at" in data
    assert data["created_at"] is not None


async def test_get_profile_when_empty_returns_404(client: AsyncClient):
    # GIVEN - no profile has been saved

    # WHEN - attempting to retrieve a profile
    response = await client.get("/api/scout/profile")

    # THEN - returns 404 not found
    assert response.status_code == 404


async def test_post_profile_overwrites(client: AsyncClient):
    # GIVEN - an initially saved profile
    first_profile = {
        "languages": ["Python"],
        "topics": ["web"],
        "skill_level": "beginner",
        "goals": "Learn Python"
    }
    await client.post("/api/scout/profile", json=first_profile)

    # WHEN - posting a second different profile
    second_profile = {
        "languages": ["TypeScript", "Go"],
        "topics": ["api", "cloud"],
        "skill_level": "advanced",
        "goals": "Build scalable systems"
    }
    await client.post("/api/scout/profile", json=second_profile)

    # THEN - GET returns the second profile data
    response = await client.get("/api/scout/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["languages"] == ["TypeScript", "Go"]
    assert data["profile"]["topics"] == ["api", "cloud"]
    assert data["profile"]["skill_level"] == "advanced"
    assert data["profile"]["goals"] == "Build scalable systems"
    assert "updated_at" in data
    assert data["updated_at"] is not None


async def test_post_profile_empty_languages_returns_422(client: AsyncClient):
    # GIVEN - a profile with empty languages list (violates min_length=1)
    invalid_profile = {
        "languages": [],
        "topics": ["web"],
        "skill_level": "intermediate",
        "goals": "Test validation"
    }

    # WHEN - posting the invalid profile
    response = await client.post("/api/scout/profile", json=invalid_profile)

    # THEN - returns 422 validation error
    assert response.status_code == 422


async def test_post_profile_goals_too_long_returns_422(client: AsyncClient):
    # GIVEN - a profile with goals exceeding 500 character limit
    long_goals = "a" * 501
    invalid_profile = {
        "languages": ["Python"],
        "topics": ["web"],
        "skill_level": "intermediate",
        "goals": long_goals
    }

    # WHEN - posting the invalid profile
    response = await client.post("/api/scout/profile", json=invalid_profile)

    # THEN - returns 422 validation error
    assert response.status_code == 422


@pytest.mark.parametrize("invalid_skill", ["expert", "novice", "master", ""])
async def test_post_profile_invalid_skill_level_returns_422(
    client: AsyncClient, invalid_skill: str
):
    # GIVEN - a profile with invalid skill_level (not in Literal options)
    invalid_profile = {
        "languages": ["Python"],
        "topics": ["web"],
        "skill_level": invalid_skill,
        "goals": "Learn Python"
    }

    # WHEN - posting the invalid profile
    response = await client.post("/api/scout/profile", json=invalid_profile)

    # THEN - returns 422 validation error
    assert response.status_code == 422


async def test_post_profile_minimal_fields_succeeds(client: AsyncClient):
    # GIVEN - a profile with only required field (languages)
    minimal_profile = {
        "languages": ["Python"]
    }

    # WHEN - posting the minimal profile
    response = await client.post("/api/scout/profile", json=minimal_profile)

    # THEN - returns 200 with id
    assert response.status_code == 200
    assert response.json() == {"id": "default"}

    # AND - GET returns profile with defaults applied
    get_response = await client.get("/api/scout/profile")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["profile"]["languages"] == ["Python"]
    assert data["profile"]["topics"] == []
    assert data["profile"]["skill_level"] == "intermediate"
    assert data["profile"]["goals"] == ""
