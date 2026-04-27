# API OPERATOR-QI

Base URL : `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

## Endpoints

### System

| Méthode | Path      | Description        |
|---------|-----------|--------------------|
| GET     | `/health` | Health check       |

### Recommendations (v1)

| Méthode | Path                                    | Description                                |
|---------|-----------------------------------------|--------------------------------------------|
| POST    | `/api/v1/recommendations/operators`    | Rank operator candidates for an operation  |
| POST    | `/api/v1/recommendations/preview`      | Preview score for a single operator        |

---

## POST /api/v1/recommendations/operators

Accepts an operation context and a pool of candidate operators.
Applies hard filters then returns the top-N ranked candidates with a full score breakdown.

### Request body

```json
{
  "operation": {
    "operation_id": "OP-001",
    "name": "Assembly Line A",
    "required_skills": [
      { "skill_id": "welding", "min_proficiency": 3, "mandatory": true }
    ],
    "assignment_date": "2024-06-15",
    "shift": "morning",
    "category": "assembly"
  },
  "candidates": [
    {
      "operator_id": "OP-A",
      "name": "Alice Martin",
      "is_active": true,
      "skills": [
        {
          "skill_id": "welding",
          "proficiency": 4,
          "certified": true,
          "last_used_date": "2024-06-01"
        }
      ],
      "assignments": []
    }
  ],
  "top_n": 5
}
```

### Response body

```json
{
  "recommendations": [
    {
      "operator_id": "OP-A",
      "name": "Alice Martin",
      "rank": 1,
      "total_score": 0.826,
      "breakdown": {
        "skills_score": 0.346,
        "availability_score": 0.3,
        "history_score": 0.0,
        "experience_score": 0.032,
        "raw_skills": 0.865,
        "raw_availability": 1.0,
        "raw_history": 0.0,
        "raw_experience": 0.32
      },
      "unmet_requirements": [],
      "explanation": "covers 1/1 required skill(s) (skills contribution 0.35/0.40). no assignment history on this operation."
    }
  ],
  "total_eligible": 1,
  "total_candidates": 1,
  "operation_id": "OP-001",
  "filtered_out": []
}
```

### Hard filter rules (candidates excluded before scoring)

| Rule | Condition |
|------|-----------|
| Inactive | `is_active == false` |
| Conflicting assignment | operator has an assignment on the same `assignment_date` + `shift` |
| Missing mandatory skill | operator lacks a skill where `mandatory == true` |
| Below mandatory threshold | operator's proficiency < `min_proficiency` for a mandatory skill |

---

## POST /api/v1/recommendations/preview

Evaluates a **single** operator against an operation context and returns
the full score breakdown without persisting anything.

### Request body

```json
{
  "operation": { ... },
  "candidate": { ... }
}
```

### Response body (eligible)

```json
{
  "operator_id": "OP-A",
  "eligible": true,
  "filter_reason": null,
  "total_score": 0.826,
  "breakdown": { ... },
  "unmet_requirements": [],
  "explanation": "..."
}
```

### Response body (filtered out)

```json
{
  "operator_id": "OP-C",
  "eligible": false,
  "filter_reason": "operator is inactive",
  "total_score": null,
  "breakdown": null,
  "unmet_requirements": [],
  "explanation": null
}
```

---

## Matching algorithm (v1)

### Scoring weights

| Component    | Weight | Description |
|--------------|--------|-------------|
| skills       | 0.40   | Skill coverage × average proficiency ratio. Bonuses: certification (+0.10), recency ≤30 days (+0.10), ≤90 days (+0.05). |
| availability | 0.30   | 1.0 when no conflict detected (conflict → hard filter). |
| history      | 0.20   | +0.50 per previous assignment on the same operation (capped 1.0); +0.25 per similar-category assignment (capped 0.50). |
| experience   | 0.10   | Normalised: (total_skills × avg_proficiency) / 25 (capped 1.0). |

### Tie-breaking

Equal total scores are broken by `operator_id` lexicographic ascending (deterministic).

### Known limitations (v1)

- All input data (candidates, skills, assignments) must be provided in the request body;
  no database lookup is performed by the recommendation engine.
- Skill similarity is exact-match on `skill_id`; no semantic skill grouping.
- History signal counts raw assignment occurrences; no time-decay applied.
- No ML model; purely deterministic weighted scoring.
- Weights are hard-coded; no per-operation weight customisation in v1.

---

## Format des réponses (erreurs)

```json
{
  "detail": [
    {
      "loc": ["body", "candidates"],
      "msg": "List should have at least 1 item after validation, not 0",
      "type": "too_short"
    }
  ]
}
```

## Authentification

*(à implémenter dans une prochaine étape)*
