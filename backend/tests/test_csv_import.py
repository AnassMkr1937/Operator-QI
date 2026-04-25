"""Tests for CSV import endpoints."""
import io

OPERATORS_CSV_VALID = b"""employee_id,name,department,hire_date,is_active
EMP_CSV001,Alice Dupont,Production,2023-01-15,true
EMP_CSV002,Bob Martin,Qualite,2022-06-01,true
"""

OPERATORS_CSV_MALFORMED = b"""employee_id,name
EMP_CSV003,Charlie
,Missing Employee ID
EMP_CSV004,
"""

OPERATIONS_CSV_VALID = b"""code,name,description,required_skills,duration_minutes,is_active
OPR_CSV001,Assemblage,Description assemblage,soudure|mecanique,90,true
OPR_CSV002,Controle qualite,,inspection,60,true
"""

ASSIGNMENTS_CSV_VALID = b"""operator_employee_id,operation_code,scheduled_date,status,notes
EMP_CSV001,OPR_CSV001,2025-06-01,pending,First assignment
EMP_CSV002,OPR_CSV002,2025-06-15,confirmed,
"""

ASSIGNMENTS_CSV_INVALID_REF = b"""operator_employee_id,operation_code
DOES_NOT_EXIST,ALSO_MISSING
"""


def test_import_operators_happy_path(client) -> None:
    resp = client.post(
        "/api/v1/import/operators",
        files={"file": ("operators.csv", io.BytesIO(OPERATORS_CSV_VALID), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] == 2
    assert data["updated"] == 0
    assert data["total_errors"] == 0


def test_import_operators_malformed_rows(client) -> None:
    resp = client.post(
        "/api/v1/import/operators",
        files={"file": ("operators.csv", io.BytesIO(OPERATORS_CSV_MALFORMED), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    # EMP_CSV003 should succeed; rows with blank employee_id or name should error
    assert data["inserted"] >= 1
    assert data["total_errors"] >= 2


def test_import_operators_missing_header(client) -> None:
    bad_csv = b"name,department\nAlice,Prod\n"
    resp = client.post(
        "/api/v1/import/operators",
        files={"file": ("operators.csv", io.BytesIO(bad_csv), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_errors"] >= 1
    assert any("Missing required columns" in e for e in data["errors"])


def test_import_operations_happy_path(client) -> None:
    resp = client.post(
        "/api/v1/import/operations",
        files={"file": ("operations.csv", io.BytesIO(OPERATIONS_CSV_VALID), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] == 2
    assert data["total_errors"] == 0


def test_import_assignments_happy_path(client) -> None:
    # First seed operators and operations
    client.post(
        "/api/v1/import/operators",
        files={"file": ("operators.csv", io.BytesIO(OPERATORS_CSV_VALID), "text/csv")},
    )
    client.post(
        "/api/v1/import/operations",
        files={"file": ("operations.csv", io.BytesIO(OPERATIONS_CSV_VALID), "text/csv")},
    )

    resp = client.post(
        "/api/v1/import/assignments",
        files={"file": ("assignments.csv", io.BytesIO(ASSIGNMENTS_CSV_VALID), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["inserted"] == 2
    assert data["total_errors"] == 0


def test_import_assignments_invalid_references(client) -> None:
    resp = client.post(
        "/api/v1/import/assignments",
        files={
            "file": ("assignments.csv", io.BytesIO(ASSIGNMENTS_CSV_INVALID_REF), "text/csv")
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_errors"] >= 1
