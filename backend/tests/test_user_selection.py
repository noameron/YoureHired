import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestUserSelectionValidRequest:
    """Tests for valid POST /api/user-selection requests."""

    async def test_valid_selection_returns_success(self, client: AsyncClient):
        """Valid request returns success with session_id."""
        # GIVEN a valid company name and role

        # WHEN submitting a user selection request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": "backend_developer",
            },
        )

        # THEN the response indicates success with expected data
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["company_name"] == "Google"
        assert data["data"]["role"] == "Backend Developer"
        assert "session_id" in data["data"]
        assert data["next_step"] == "/api/generate-tasks"

    async def test_valid_selection_with_description(self, client: AsyncClient):
        """Valid request with role_description is accepted."""
        # GIVEN a valid request with an optional role description
        description = (
            "I am applying for a senior backend role focusing on "
            "distributed systems and microservices architecture."
        )

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Meta",
                "role": "backend_developer",
                "role_description": description,
            },
        )

        # THEN the response includes the role description
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["role_description"] is not None

    async def test_session_id_is_valid_uuid(self, client: AsyncClient):
        """Session ID is a valid UUID format."""
        # GIVEN a valid user selection request

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": "backend_developer",
            },
        )

        # THEN the session_id is a valid UUID
        assert response.status_code == 200
        data = response.json()
        session_id = data["data"]["session_id"]
        uuid.UUID(session_id)  # Should not raise


class TestCompanyNameValidation:
    """Tests for company_name field validation."""

    async def test_missing_company_name_returns_error(self, client: AsyncClient):
        """Missing company_name returns validation error."""
        # GIVEN a request without company_name field

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "role": "backend_developer",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_empty_company_name_returns_error(self, client: AsyncClient):
        """Empty company_name returns validation error."""
        # GIVEN a request with an empty company_name

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "",
                "role": "backend_developer",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_whitespace_only_company_name_returns_error(self, client: AsyncClient):
        """Whitespace-only company_name returns validation error."""
        # GIVEN a request with a whitespace-only company_name

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "   ",
                "role": "backend_developer",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_company_name_too_short_returns_error(self, client: AsyncClient):
        """Company name with less than 2 characters returns error."""
        # GIVEN a company name with only 1 character

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "A",
                "role": "backend_developer",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_company_name_too_long_returns_error(self, client: AsyncClient):
        """Company name exceeding 100 characters returns error."""
        # GIVEN a company name with 101 characters

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "A" * 101,
                "role": "backend_developer",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_company_name_with_emoji_returns_error(self, client: AsyncClient):
        """Company name containing emoji returns validation error."""
        # GIVEN a company name containing an emoji

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google Inc",
                "role": "backend_developer",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_company_name_with_numbers_accepted(self, client: AsyncClient):
        """Company name with numbers is valid."""
        # GIVEN a company name containing numbers

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google123",
                "role": "backend_developer",
            },
        )

        # THEN the request is accepted
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["company_name"] == "Google123"

    async def test_company_name_with_special_characters_accepted(self, client: AsyncClient):
        """Company name with dots, hyphens, and other non-emoji characters is valid."""
        # GIVEN a company name with special characters

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Company-Name Inc.",
                "role": "backend_developer",
            },
        )

        # THEN the request is accepted
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["company_name"] == "Company-Name Inc."


class TestRoleValidation:
    """Tests for role field validation."""

    async def test_missing_role_returns_error(self, client: AsyncClient):
        """Missing role returns validation error."""
        # GIVEN a request without a role field

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_invalid_role_returns_error(self, client: AsyncClient):
        """Invalid role value returns error."""
        # GIVEN a request with an invalid role

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": "invalid_role",
            },
        )

        # THEN a 400 error with validation details is returned
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VALIDATION_ERROR"
        assert "role" in data["error"]["details"]

    @pytest.mark.parametrize(
        "role_id",
        [
            "frontend_developer",
            "backend_developer",
            "fullstack_developer",
            "devops_engineer",
            "qa_engineer",
            "data_engineer",
        ],
    )
    async def test_all_valid_roles_accepted(self, client: AsyncClient, role_id: str):
        """All predefined roles are accepted."""
        # GIVEN a valid predefined role ID

        # WHEN submitting a request with that role
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": role_id,
            },
        )

        # THEN the request is accepted
        assert response.status_code == 200, f"Role {role_id} should be accepted"


class TestRoleDescriptionValidation:
    """Tests for role_description field validation."""

    async def test_role_description_too_short_returns_error(self, client: AsyncClient):
        """Role description shorter than 30 characters returns error."""
        # GIVEN a role description that is too short

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": "backend_developer",
                "role_description": "Too short",
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_role_description_too_long_returns_error(self, client: AsyncClient):
        """Role description exceeding 8000 characters returns error."""
        # GIVEN a role description that exceeds the maximum length

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": "backend_developer",
                "role_description": "A" * 8001,
            },
        )

        # THEN a 422 validation error is returned
        assert response.status_code == 422

    async def test_empty_role_description_treated_as_null(self, client: AsyncClient):
        """Empty string role_description is treated as null."""
        # GIVEN a request with an empty role_description

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": "backend_developer",
                "role_description": "",
            },
        )

        # THEN the request succeeds and role_description is null
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role_description"] is None

    async def test_whitespace_role_description_treated_as_null(self, client: AsyncClient):
        """Whitespace-only role_description is treated as null."""
        # GIVEN a request with a whitespace-only role_description

        # WHEN submitting the request
        response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Google",
                "role": "backend_developer",
                "role_description": "   ",
            },
        )

        # THEN the request succeeds and role_description is null
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["role_description"] is None
