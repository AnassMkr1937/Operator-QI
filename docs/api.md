# API OPERATOR-QI

Base URL : `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

## Endpoints

### System

| Méthode | Path         | Description                    |
|---------|--------------|--------------------------------|
| GET     | `/health`    | Health check                   |
| GET     | `/readiness` | Readiness probe (vérifie la DB)|

### Opérateurs (`/api/v1/operators`)

| Méthode | Path                    | Description                          |
|---------|-------------------------|--------------------------------------|
| GET     | `/api/v1/operators`     | Lister les opérateurs (+ filtre active_only) |
| POST    | `/api/v1/operators`     | Créer un opérateur                   |
| GET     | `/api/v1/operators/{id}`| Récupérer un opérateur               |
| PATCH   | `/api/v1/operators/{id}`| Mettre à jour un opérateur           |
| DELETE  | `/api/v1/operators/{id}`| Supprimer un opérateur               |

### Opérations (`/api/v1/operations`)

| Méthode | Path                      | Description                            |
|---------|---------------------------|----------------------------------------|
| GET     | `/api/v1/operations`      | Lister les opérations (+ filtre active_only) |
| POST    | `/api/v1/operations`      | Créer une opération                    |
| GET     | `/api/v1/operations/{id}` | Récupérer une opération                |
| PATCH   | `/api/v1/operations/{id}` | Mettre à jour une opération            |
| DELETE  | `/api/v1/operations/{id}` | Supprimer une opération                |

### Compétences (`/api/v1/skills`)

| Méthode | Path                   | Description                          |
|---------|------------------------|--------------------------------------|
| GET     | `/api/v1/skills`       | Lister les compétences (+ filtre operator_id) |
| POST    | `/api/v1/skills`       | Créer une compétence                 |
| GET     | `/api/v1/skills/{id}`  | Récupérer une compétence             |
| PATCH   | `/api/v1/skills/{id}`  | Mettre à jour une compétence         |
| DELETE  | `/api/v1/skills/{id}`  | Supprimer une compétence             |

### Assignations (`/api/v1/assignments`)

| Méthode | Path                         | Description                           |
|---------|------------------------------|---------------------------------------|
| GET     | `/api/v1/assignments`        | Lister les assignations (filtres : operator_id, operation_id, status) |
| POST    | `/api/v1/assignments`        | Créer une assignation                 |
| GET     | `/api/v1/assignments/{id}`   | Récupérer une assignation             |
| PATCH   | `/api/v1/assignments/{id}`   | Mettre à jour une assignation         |
| DELETE  | `/api/v1/assignments/{id}`   | Supprimer une assignation             |

### Import CSV (`/api/v1/import`)

| Méthode | Path                           | Description                              |
|---------|--------------------------------|------------------------------------------|
| POST    | `/api/v1/import/operators`     | Importer des opérateurs depuis un fichier CSV |
| POST    | `/api/v1/import/operations`    | Importer des opérations depuis un fichier CSV |
| POST    | `/api/v1/import/assignments`   | Importer des assignations depuis un fichier CSV |

#### Format de retour d'import

```json
{
  "inserted": 5,
  "updated": 2,
  "errors": [],
  "total_errors": 0
}
```

#### Colonnes requises pour l'import CSV

- **operators** : `employee_id`, `name` (opt : email, department, hire_date, is_active)
- **operations** : `code`, `name` (opt : description, required_skills, duration_minutes, is_active)
- **assignments** : `operator_employee_id`, `operation_code` (opt : scheduled_date, status, notes)

## Format des réponses

```json
{
  "status": "ok",
  "version": "0.2.0"
}
```

## Authentification

*(à implémenter dans une prochaine étape)*
