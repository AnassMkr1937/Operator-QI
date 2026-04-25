"""Tests for operators CRUD endpoints."""


def test_list_operators_empty(client) -> None:
    resp = client.get("/api/v1/operators")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_operator(client) -> None:
    payload = {"employee_id": "EMP001", "name": "Alice Martin", "department": "Production"}
    resp = client.post("/api/v1/operators", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["employee_id"] == "EMP001"
    assert data["name"] == "Alice Martin"
    assert "id" in data
    assert "created_at" in data


def test_create_operator_duplicate(client) -> None:
    payload = {"employee_id": "EMP002", "name": "Bob Dupont"}
    client.post("/api/v1/operators", json=payload)
    resp = client.post("/api/v1/operators", json=payload)
    assert resp.status_code == 409


def test_get_operator(client) -> None:
    payload = {"employee_id": "EMP003", "name": "Carol Durand"}
    create_resp = client.post("/api/v1/operators", json=payload)
    op_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/operators/{op_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == op_id


def test_get_operator_not_found(client) -> None:
    resp = client.get("/api/v1/operators/nonexistent-id")
    assert resp.status_code == 404


def test_update_operator(client) -> None:
    payload = {"employee_id": "EMP004", "name": "David Leclerc"}
    create_resp = client.post("/api/v1/operators", json=payload)
    op_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/api/v1/operators/{op_id}", json={"name": "David Leclerc-Updated"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "David Leclerc-Updated"


def test_delete_operator(client) -> None:
    payload = {"employee_id": "EMP005", "name": "Eva Renard"}
    create_resp = client.post("/api/v1/operators", json=payload)
    op_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/operators/{op_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/operators/{op_id}")
    assert get_resp.status_code == 404


def test_list_operators_active_filter(client) -> None:
    client.post("/api/v1/operators", json={"employee_id": "EMP006", "name": "Active Op", "is_active": True})
    client.post("/api/v1/operators", json={"employee_id": "EMP007", "name": "Inactive Op", "is_active": False})

    resp = client.get("/api/v1/operators?active_only=true")
    assert resp.status_code == 200
    names = [o["name"] for o in resp.json()]
    assert "Active Op" in names
    assert "Inactive Op" not in names
