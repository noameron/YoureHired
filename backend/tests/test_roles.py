import pytest
from httpx import ASGITransport, AsyncClient

from app.config import PREDEFINED_ROLES
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


class TestGetRolesEndpoint:
    """Tests for GET /api/roles endpoint."""

    async def test_returns_200_status_code(self, client: AsyncClient):
        # GIVEN a running API server

        # WHEN requesting the roles endpoint
        response = await client.get("/api/roles")

        # THEN the response status code is 200
        assert response.status_code == 200

    async def test_response_contains_roles_key(self, client: AsyncClient):
        # GIVEN a running API server

        # WHEN requesting the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # THEN the response contains a 'roles' key
        assert "roles" in data

    async def test_returns_all_predefined_roles(self, client: AsyncClient):
        # GIVEN the predefined roles from config

        # WHEN requesting the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # THEN the response contains exactly the predefined roles
        assert data["roles"] == PREDEFINED_ROLES


class TestRolesStructure:
    """Tests for the structure of returned roles."""

    async def test_each_role_has_id_field(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the roles

        # THEN every role has an 'id' field
        assert all("id" in role for role in data["roles"])

    async def test_each_role_has_label_field(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the roles

        # THEN every role has a 'label' field
        assert all("label" in role for role in data["roles"])

    async def test_all_role_ids_are_strings(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the role IDs

        # THEN all IDs are strings
        assert all(isinstance(role["id"], str) for role in data["roles"])

    async def test_all_role_labels_are_strings(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the role labels

        # THEN all labels are strings
        assert all(isinstance(role["label"], str) for role in data["roles"])


class TestRolesInvariants:
    """Tests for role data invariants that should always hold."""

    async def test_role_ids_are_unique(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()
        role_ids = [role["id"] for role in data["roles"]]

        # WHEN checking for duplicates

        # THEN all role IDs are unique
        assert len(role_ids) == len(set(role_ids))

    async def test_role_ids_are_not_empty(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the role IDs

        # THEN no role ID is empty
        assert all(role["id"].strip() != "" for role in data["roles"])

    async def test_role_labels_are_not_empty(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the role labels

        # THEN no role label is empty
        assert all(role["label"].strip() != "" for role in data["roles"])

    async def test_at_least_one_role_exists(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the number of roles

        # THEN at least one role exists
        assert len(data["roles"]) >= 1

    async def test_role_ids_use_snake_case(self, client: AsyncClient):
        # GIVEN a response from the roles endpoint
        response = await client.get("/api/roles")
        data = response.json()

        # WHEN checking the role ID format

        # THEN all role IDs use lowercase letters, numbers, and underscores only
        import re
        snake_case_pattern = re.compile(r"^[a-z][a-z0-9_]*$")
        assert all(
            snake_case_pattern.match(role["id"]) for role in data["roles"]
        )
