"""API-level tests for POST /api/v1/recommendations/operators and /preview."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

OP_DATE = "2024-06-15"
OPERATION_PAYLOAD = {
    "operation_id": "OP-001",
    "name": "Assembly Line A",
    "required_skills": [
        {"skill_id": "welding", "min_proficiency": 3, "mandatory": True}
    ],
    "assignment_date": OP_DATE,
    "shift": "morning",
    "category": "assembly",
}

GOOD_CANDIDATE = {
    "operator_id": "OP-A",
    "name": "Alice Martin",
    "is_active": True,
    "skills": [{"skill_id": "welding", "proficiency": 4, "certified": True}],
    "assignments": [],
}

POOR_CANDIDATE = {
    "operator_id": "OP-B",
    "name": "Bob Dupont",
    "is_active": True,
    "skills": [{"skill_id": "welding", "proficiency": 3}],
    "assignments": [],
}

INACTIVE_CANDIDATE = {
    "operator_id": "OP-C",
    "name": "Charlie Durand",
    "is_active": False,
    "skills": [{"skill_id": "welding", "proficiency": 5}],
    "assignments": [],
}

CONFLICTING_CANDIDATE = {
    "operator_id": "OP-D",
    "name": "Diana Lefevre",
    "is_active": True,
    "skills": [{"skill_id": "welding", "proficiency": 5}],
    "assignments": [{"operation_id": "OTHER", "assignment_date": OP_DATE, "shift": "morning"}],
}

MISSING_SKILL_CANDIDATE = {
    "operator_id": "OP-E",
    "name": "Eric Bernard",
    "is_active": True,
    "skills": [],
    "assignments": [],
}


# ---------------------------------------------------------------------------
# POST /api/v1/recommendations/operators — happy path
# ---------------------------------------------------------------------------


class TestRecommendOperatorsHappyPath:
    def test_returns_200(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE, POOR_CANDIDATE],
                "top_n": 5,
            },
        )
        assert resp.status_code == 200

    def test_response_schema_fields(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE],
                "top_n": 5,
            },
        )
        data = resp.json()
        assert "recommendations" in data
        assert "total_eligible" in data
        assert "total_candidates" in data
        assert "operation_id" in data
        assert "filtered_out" in data

    def test_operation_id_echoed(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE],
            },
        )
        assert resp.json()["operation_id"] == "OP-001"

    def test_total_candidates_count(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE, POOR_CANDIDATE, INACTIVE_CANDIDATE],
            },
        )
        assert resp.json()["total_candidates"] == 3

    def test_good_candidate_ranked_above_poor(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [POOR_CANDIDATE, GOOD_CANDIDATE],
            },
        )
        recs = resp.json()["recommendations"]
        assert recs[0]["operator_id"] == "OP-A"
        assert recs[1]["operator_id"] == "OP-B"

    def test_ranks_are_1_based_sequential(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE, POOR_CANDIDATE],
            },
        )
        recs = resp.json()["recommendations"]
        for i, rec in enumerate(recs):
            assert rec["rank"] == i + 1

    def test_score_breakdown_present(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE],
            },
        )
        bd = resp.json()["recommendations"][0]["breakdown"]
        for key in ("skills_score", "availability_score", "history_score", "experience_score"):
            assert key in bd

    def test_inactive_candidate_in_filtered_out(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE, INACTIVE_CANDIDATE],
            },
        )
        data = resp.json()
        assert "OP-C" in data["filtered_out"]
        ids = [r["operator_id"] for r in data["recommendations"]]
        assert "OP-C" not in ids

    def test_conflicting_candidate_filtered(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE, CONFLICTING_CANDIDATE],
            },
        )
        data = resp.json()
        assert "OP-D" in data["filtered_out"]

    def test_missing_mandatory_skill_filtered(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [MISSING_SKILL_CANDIDATE],
            },
        )
        data = resp.json()
        assert "OP-E" in data["filtered_out"]
        assert data["recommendations"] == []

    def test_no_eligible_candidates(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [INACTIVE_CANDIDATE, MISSING_SKILL_CANDIDATE],
            },
        )
        data = resp.json()
        assert data["recommendations"] == []
        assert len(data["filtered_out"]) == 2

    def test_top_n_respected(self) -> None:
        candidates = [
            {
                "operator_id": f"OP-{i}",
                "name": f"Op {i}",
                "is_active": True,
                "skills": [{"skill_id": "welding", "proficiency": 3}],
                "assignments": [],
            }
            for i in range(10)
        ]
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": candidates,
                "top_n": 3,
            },
        )
        assert len(resp.json()["recommendations"]) <= 3

    def test_explanation_non_empty(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE],
            },
        )
        explanation = resp.json()["recommendations"][0]["explanation"]
        assert isinstance(explanation, str) and len(explanation) > 0

    def test_deterministic_results(self) -> None:
        """Same input must always produce same output."""
        payload = {
            "operation": OPERATION_PAYLOAD,
            "candidates": [GOOD_CANDIDATE, POOR_CANDIDATE],
        }
        resp1 = client.post("/api/v1/recommendations/operators", json=payload)
        resp2 = client.post("/api/v1/recommendations/operators", json=payload)
        assert resp1.json() == resp2.json()


# ---------------------------------------------------------------------------
# POST /api/v1/recommendations/operators — validation failures
# ---------------------------------------------------------------------------


class TestRecommendOperatorsValidation:
    def test_empty_candidates_list_rejected(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [],
            },
        )
        assert resp.status_code == 422

    def test_missing_operation_field_rejected(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={"candidates": [GOOD_CANDIDATE]},
        )
        assert resp.status_code == 422

    def test_invalid_shift_value_rejected(self) -> None:
        bad_op = {**OPERATION_PAYLOAD, "shift": "noon"}
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={"operation": bad_op, "candidates": [GOOD_CANDIDATE]},
        )
        assert resp.status_code == 422

    def test_invalid_proficiency_too_high_rejected(self) -> None:
        bad_candidate = {
            **GOOD_CANDIDATE,
            "skills": [{"skill_id": "welding", "proficiency": 10}],
        }
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={"operation": OPERATION_PAYLOAD, "candidates": [bad_candidate]},
        )
        assert resp.status_code == 422

    def test_invalid_proficiency_zero_rejected(self) -> None:
        bad_candidate = {
            **GOOD_CANDIDATE,
            "skills": [{"skill_id": "welding", "proficiency": 0}],
        }
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={"operation": OPERATION_PAYLOAD, "candidates": [bad_candidate]},
        )
        assert resp.status_code == 422

    def test_top_n_zero_rejected(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE],
                "top_n": 0,
            },
        )
        assert resp.status_code == 422

    def test_top_n_above_100_rejected(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={
                "operation": OPERATION_PAYLOAD,
                "candidates": [GOOD_CANDIDATE],
                "top_n": 101,
            },
        )
        assert resp.status_code == 422

    def test_missing_date_rejected(self) -> None:
        bad_op = {k: v for k, v in OPERATION_PAYLOAD.items() if k != "assignment_date"}
        resp = client.post(
            "/api/v1/recommendations/operators",
            json={"operation": bad_op, "candidates": [GOOD_CANDIDATE]},
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/v1/recommendations/preview
# ---------------------------------------------------------------------------


class TestPreviewScore:
    def test_eligible_candidate_returns_score(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/preview",
            json={"operation": OPERATION_PAYLOAD, "candidate": GOOD_CANDIDATE},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is True
        assert data["total_score"] is not None
        assert data["breakdown"] is not None

    def test_inactive_candidate_not_eligible(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/preview",
            json={"operation": OPERATION_PAYLOAD, "candidate": INACTIVE_CANDIDATE},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["eligible"] is False
        assert data["filter_reason"] is not None
        assert data["total_score"] is None

    def test_conflicting_candidate_not_eligible(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/preview",
            json={"operation": OPERATION_PAYLOAD, "candidate": CONFLICTING_CANDIDATE},
        )
        data = resp.json()
        assert data["eligible"] is False
        assert "conflicting" in data["filter_reason"]

    def test_preview_schema_fields(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/preview",
            json={"operation": OPERATION_PAYLOAD, "candidate": GOOD_CANDIDATE},
        )
        data = resp.json()
        for key in ("operator_id", "eligible", "filter_reason", "total_score", "breakdown"):
            assert key in data

    def test_preview_missing_candidate_rejected(self) -> None:
        resp = client.post(
            "/api/v1/recommendations/preview",
            json={"operation": OPERATION_PAYLOAD},
        )
        assert resp.status_code == 422
