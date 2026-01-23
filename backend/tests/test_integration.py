"""Integration tests for the complete user selection flow."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


class TestRoleSelectionFlow:
    """End-to-end tests for the role selection user flow."""

    async def test_complete_flow_fetch_roles_and_submit_selection(self, client: AsyncClient):
        """Test the complete flow: fetch roles, submit selection, verify response."""
        # Step 1: Fetch available roles
        roles_response = await client.get("/api/roles")
        assert roles_response.status_code == 200
        roles_data = roles_response.json()
        assert "roles" in roles_data
        assert len(roles_data["roles"]) > 0

        # Step 2: Select a role from the available options
        selected_role = roles_data["roles"][0]
        assert "id" in selected_role
        assert "label" in selected_role

        # Step 3: Submit user selection
        selection_payload = {
            "company_name": "Integration Test Corp",
            "role": selected_role["id"],
        }
        selection_response = await client.post("/api/user-selection", json=selection_payload)

        # Step 4: Verify response format
        assert selection_response.status_code == 200
        selection_data = selection_response.json()

        # Verify success structure
        assert selection_data["success"] is True
        assert "data" in selection_data
        assert "next_step" in selection_data

        # Verify data fields
        data = selection_data["data"]
        assert data["company_name"] == "Integration Test Corp"
        assert data["role"] == selected_role["label"]
        assert data["role_description"] is None
        assert "session_id" in data

        # Verify session_id is valid UUID
        uuid.UUID(data["session_id"])

        # Verify next_step points to task generation
        assert selection_data["next_step"] == "/api/generate-tasks"

    async def test_flow_with_role_description(self, client: AsyncClient):
        """Test the flow with an optional role description."""
        # Step 1: Fetch roles
        roles_response = await client.get("/api/roles")
        assert roles_response.status_code == 200
        selected_role_id = roles_response.json()["roles"][0]["id"]

        # Step 2: Submit with role description
        description = (
            "I am preparing for a senior engineering position "
            "focusing on distributed systems and cloud architecture."
        )
        selection_response = await client.post(
            "/api/user-selection",
            json={
                "company_name": "Tech Giant Inc",
                "role": selected_role_id,
                "role_description": description,
            },
        )

        # Step 3: Verify response
        assert selection_response.status_code == 200
        data = selection_response.json()["data"]
        assert data["role_description"] is not None
        assert "distributed systems" in data["role_description"]

    async def test_flow_with_all_available_roles(self, client: AsyncClient):
        """Test that all roles from GET /roles work with POST /user-selection."""
        # Fetch all roles
        roles_response = await client.get("/api/roles")
        assert roles_response.status_code == 200
        roles = roles_response.json()["roles"]

        # Submit selection for each role
        for role in roles:
            response = await client.post(
                "/api/user-selection",
                json={
                    "company_name": f"Company for {role['label']}",
                    "role": role["id"],
                },
            )
            assert response.status_code == 200, f"Failed for role: {role['id']}"
            assert response.json()["data"]["role"] == role["label"]


class TestApiRootAndHealth:
    """Integration tests for API root and health endpoints."""

    async def test_api_root_accessible(self, client: AsyncClient):
        """Verify API root returns expected response."""
        response = await client.get("/api/")
        assert response.status_code == 200
        assert response.json()["message"] == "YoureHired API"

    async def test_health_endpoint(self, client: AsyncClient):
        """Verify health check endpoint works."""
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
