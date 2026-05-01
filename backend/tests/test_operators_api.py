from __future__ import annotations


def test_create_and_list_operator(client, manager_headers) -> None:
    payload = {
        "operator_id": "OP-100",
        "name": "Op Test",
        "is_active": True,
        "skills": [
            {"skill_id": "welding", "proficiency": 4, "certified": True}
        ],
        "assignments": [
            {
                "operation_id": "OP-001",
                "assignment_date": "2024-06-15",
                "shift": "morning",
                "category": "assembly",
            }
        ],
    }
    resp = client.post("/api/v1/operators", json=payload, headers=manager_headers)
    assert resp.status_code == 201

    list_resp = client.get("/api/v1/operators", headers=manager_headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 1
    assert data["items"][0]["operator_id"] == "OP-100"


def test_update_operator(client, manager_headers) -> None:
    payload = {"operator_id": "OP-200", "name": "Op Old", "skills": []}
    client.post("/api/v1/operators", json=payload, headers=manager_headers)

    update = {"name": "Op New", "is_active": False}
    resp = client.put("/api/v1/operators/OP-200", json=update, headers=manager_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Op New"
    assert resp.json()["is_active"] is False


def test_delete_operator_requires_admin(client, manager_headers, admin_headers) -> None:
    payload = {"operator_id": "OP-300", "name": "Op Delete", "skills": []}
    client.post("/api/v1/operators", json=payload, headers=manager_headers)

    forbidden = client.delete("/api/v1/operators/OP-300", headers=manager_headers)
    assert forbidden.status_code == 403

    resp = client.delete("/api/v1/operators/OP-300", headers=admin_headers)
    assert resp.status_code == 204
