"""
Tests for the Operators REST API endpoints.

Uses the TestClient fixture from conftest.py which overrides the DB dependency
with an in-memory SQLite session.
"""

import pytest


class TestListOperators:
    def test_requires_auth(self, client):
        """Unauthenticated requests should be rejected with 401."""
        response = client.get("/api/v1/operators")
        assert response.status_code == 401

    def test_returns_empty_list(self, client, auth_headers):
        """With no operators in the DB the response should be an empty paginated list."""
        response = client.get("/api/v1/operators", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_pagination_params(self, client, auth_headers):
        """Page and page_size query params should be reflected in the response."""
        response = client.get("/api/v1/operators?page=2&page_size=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 5


class TestCreateOperator:
    def test_create_requires_admin(self, client, auth_headers):
        """Non-admin tokens should be rejected with 403."""
        from app.core.security import create_access_token

        non_admin_token = create_access_token(subject="regular_user")
        headers = {"Authorization": f"Bearer {non_admin_token}"}
        payload = {
            "matricule": "OP-X01",
            "full_name": "Test User",
            "team": "A",
            "shift": "matin",
            "status": "present",
        }
        response = client.post("/api/v1/operators", json=payload, headers=headers)
        assert response.status_code == 403

    def test_create_operator_success(self, client, auth_headers):
        """Admin users should be able to create operators."""
        payload = {
            "matricule": "OP-C01",
            "full_name": "Created Operator",
            "team": "B",
            "shift": "nuit",
            "status": "present",
        }
        response = client.post("/api/v1/operators", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["matricule"] == "OP-C01"
        assert data["id"] > 0

    def test_duplicate_matricule_returns_409(self, client, auth_headers):
        """Creating an operator with a duplicate matricule should return 409 Conflict."""
        payload = {
            "matricule": "OP-DUP01",
            "full_name": "Duplicate",
            "team": "A",
            "shift": "matin",
            "status": "present",
        }
        client.post("/api/v1/operators", json=payload, headers=auth_headers)
        response = client.post("/api/v1/operators", json=payload, headers=auth_headers)
        assert response.status_code == 409

    def test_create_missing_required_field_returns_422(self, client, auth_headers):
        """Missing required fields should return HTTP 422."""
        payload = {"matricule": "OP-INC01"}  # Missing full_name, team, shift
        response = client.post("/api/v1/operators", json=payload, headers=auth_headers)
        assert response.status_code == 422


class TestGetOperator:
    def test_get_existing_operator(self, client, auth_headers):
        """Should return operator details for a valid ID."""
        create_payload = {
            "matricule": "OP-G01",
            "full_name": "Get Me",
            "team": "C",
            "shift": "matin",
            "status": "present",
        }
        create_response = client.post("/api/v1/operators", json=create_payload, headers=auth_headers)
        operator_id = create_response.json()["id"]

        response = client.get(f"/api/v1/operators/{operator_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["matricule"] == "OP-G01"

    def test_get_nonexistent_operator_returns_404(self, client, auth_headers):
        """Requesting an operator that doesn't exist should return 404."""
        response = client.get("/api/v1/operators/999999", headers=auth_headers)
        assert response.status_code == 404


class TestUpdateOperator:
    def test_update_operator_partial(self, client, auth_headers):
        """PUT should apply partial updates."""
        create_payload = {
            "matricule": "OP-U01",
            "full_name": "Before Update",
            "team": "A",
            "shift": "matin",
            "status": "present",
        }
        op_id = client.post(
            "/api/v1/operators", json=create_payload, headers=auth_headers
        ).json()["id"]

        response = client.put(
            f"/api/v1/operators/{op_id}",
            json={"full_name": "After Update", "status": "absent"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "After Update"
        assert data["status"] == "absent"
        assert data["team"] == "A"  # unchanged

    def test_update_nonexistent_returns_404(self, client, auth_headers):
        response = client.put(
            "/api/v1/operators/999999",
            json={"full_name": "Ghost"},
            headers=auth_headers,
        )
        assert response.status_code == 404


class TestDeleteOperator:
    def test_delete_operator(self, client, auth_headers):
        """Deleting an existing operator should return 204."""
        create_payload = {
            "matricule": "OP-DEL01",
            "full_name": "Delete Me",
            "team": "D",
            "shift": "nuit",
            "status": "present",
        }
        op_id = client.post(
            "/api/v1/operators", json=create_payload, headers=auth_headers
        ).json()["id"]

        response = client.delete(f"/api/v1/operators/{op_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(f"/api/v1/operators/{op_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_returns_404(self, client, auth_headers):
        response = client.delete("/api/v1/operators/999999", headers=auth_headers)
        assert response.status_code == 404


class TestFilterOperators:
    def test_filter_by_team(self, client, auth_headers):
        """Filtering by team should return only operators from that team."""
        for matricule, team in [("FILT-T01", "TeamX"), ("FILT-T02", "TeamY")]:
            client.post(
                "/api/v1/operators",
                json={
                    "matricule": matricule,
                    "full_name": matricule,
                    "team": team,
                    "shift": "matin",
                    "status": "present",
                },
                headers=auth_headers,
            )

        response = client.get("/api/v1/operators?team=TeamX", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["team"] == "TeamX"
