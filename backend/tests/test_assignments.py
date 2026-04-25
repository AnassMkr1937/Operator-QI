"""Tests for assignments endpoints."""


def _create_operator(client, emp_id: str, name: str) -> str:
    resp = client.post("/api/v1/operators", json={"employee_id": emp_id, "name": name})
    return resp.json()["id"]


def _create_operation(client, code: str, name: str) -> str:
    resp = client.post("/api/v1/operations", json={"code": code, "name": name})
    return resp.json()["id"]


def test_list_assignments_empty(client) -> None:
    resp = client.get("/api/v1/assignments")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_assignment(client) -> None:
    op_id = _create_operator(client, "A001", "Luc Dupont")
    oper_id = _create_operation(client, "C001", "Calibration")

    payload = {
        "operator_id": op_id,
        "operation_id": oper_id,
        "scheduled_date": "2025-06-01",
        "status": "pending",
    }
    resp = client.post("/api/v1/assignments", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["operator_id"] == op_id
    assert data["operation_id"] == oper_id
    assert data["status"] == "pending"


def test_get_assignment(client) -> None:
    op_id = _create_operator(client, "A002", "Marie Claude")
    oper_id = _create_operation(client, "C002", "Inspection")

    create_resp = client.post(
        "/api/v1/assignments",
        json={"operator_id": op_id, "operation_id": oper_id},
    )
    assign_id = create_resp.json()["id"]

    resp = client.get(f"/api/v1/assignments/{assign_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == assign_id


def test_get_assignment_not_found(client) -> None:
    resp = client.get("/api/v1/assignments/nonexistent")
    assert resp.status_code == 404


def test_update_assignment_status(client) -> None:
    op_id = _create_operator(client, "A003", "Jean Pierre")
    oper_id = _create_operation(client, "C003", "Montage")

    create_resp = client.post(
        "/api/v1/assignments",
        json={"operator_id": op_id, "operation_id": oper_id},
    )
    assign_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/assignments/{assign_id}", json={"status": "confirmed"}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "confirmed"


def test_filter_assignments_by_operator(client) -> None:
    op_id = _create_operator(client, "A004", "Sophie Moreau")
    oper_id = _create_operation(client, "C004", "Soudure")
    client.post("/api/v1/assignments", json={"operator_id": op_id, "operation_id": oper_id})

    resp = client.get(f"/api/v1/assignments?operator_id={op_id}")
    assert resp.status_code == 200
    assert len(resp.json()) >= 1
    for a in resp.json():
        assert a["operator_id"] == op_id


def test_delete_assignment(client) -> None:
    op_id = _create_operator(client, "A005", "Thomas Bernard")
    oper_id = _create_operation(client, "C005", "Reglage")

    create_resp = client.post(
        "/api/v1/assignments",
        json={"operator_id": op_id, "operation_id": oper_id},
    )
    assign_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/assignments/{assign_id}")
    assert del_resp.status_code == 204

    get_resp = client.get(f"/api/v1/assignments/{assign_id}")
    assert get_resp.status_code == 404
