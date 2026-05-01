from __future__ import annotations

def test_audit_logs_created(client, manager_headers, admin_headers) -> None:
    payload = {
        "operation": {
            "operation_id": "OP-001",
            "name": "Assembly Line A",
            "required_skills": [{"skill_id": "welding", "min_proficiency": 3, "mandatory": True}],
            "assignment_date": "2024-06-15",
            "shift": "morning",
            "category": "assembly",
        },
        "candidates": [
            {
                "operator_id": "OP-A",
                "name": "Alice",
                "is_active": True,
                "skills": [{"skill_id": "welding", "proficiency": 4}],
                "assignments": [],
            }
        ],
    }
    client.post("/api/v1/recommendations/operators", json=payload, headers=manager_headers)

    resp = client.get("/api/v1/audit/logs", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(item["action"] == "recommendations" for item in data["items"])
