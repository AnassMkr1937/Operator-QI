"""Tests for operations CRUD endpoints."""


def test_list_operations_empty(client) -> None:
    resp = client.get("/api/v1/operations")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_operation(client) -> None:
    payload = {
        "code": "OP001",
        "name": "Assemblage moteur",
        "required_skills": ["soudure", "mecanique"],
        "duration_minutes": 90,
    }
    resp = client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "OP001"
    assert data["required_skills"] == ["soudure", "mecanique"]
    assert data["duration_minutes"] == 90


def test_create_operation_duplicate(client) -> None:
    payload = {"code": "OP002", "name": "Test op"}
    client.post("/api/v1/operations", json=payload)
    resp = client.post("/api/v1/operations", json=payload)
    assert resp.status_code == 409


def test_get_operation(client) -> None:
    payload = {"code": "OP003", "name": "Controle qualite"}
    create_resp = client.post("/api/v1/operations", json=payload)
    op_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/operations/{op_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == op_id


def test_get_operation_not_found(client) -> None:
    resp = client.get("/api/v1/operations/nonexistent-id")
    assert resp.status_code == 404


def test_update_operation(client) -> None:
    payload = {"code": "OP004", "name": "Peinture"}
    create_resp = client.post("/api/v1/operations", json=payload)
    op_id = create_resp.json()["id"]

    patch_resp = client.patch(f"/api/v1/operations/{op_id}", json={"duration_minutes": 60})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["duration_minutes"] == 60


def test_delete_operation(client) -> None:
    payload = {"code": "OP005", "name": "Decoupe"}
    create_resp = client.post("/api/v1/operations", json=payload)
    op_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/operations/{op_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/operations/{op_id}")
    assert get_resp.status_code == 404
