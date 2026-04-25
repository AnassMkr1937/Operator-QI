# OPERATOR-QI

> Plateforme de matching opérateurs-missions basée sur la qualité d'intervention.

## Démarrage rapide

```bash
# 1. Copier les variables d'environnement
cp .env.example .env

# 2. Démarrer tous les services (DB + migrate + backend + frontend)
make up

# 3. Accéder aux services
#   Frontend  → http://localhost:5173
#   Backend   → http://localhost:8000
#   API docs  → http://localhost:8000/docs
```

## Développement local (sans Docker)

```bash
# Backend
cd backend
pip install -e ".[dev]"

# Appliquer les migrations (SQLite par défaut)
alembic upgrade head

# Lancer le serveur
uvicorn app.main:app --reload --port 8000
```

## Migrations

```bash
# Appliquer toutes les migrations
make migrate

# Créer une nouvelle migration (après modification des modèles)
cd backend && alembic revision --autogenerate -m "description"
```

## Import de données CSV

```bash
# Importer les données de démonstration (nécessite le backend en cours d'exécution)
make import-data

# Ou manuellement
curl -X POST http://localhost:8000/api/v1/import/operators \
  -F "file=@data/operators.csv;type=text/csv"
```

## Architecture

```
Operator-QI/
├── backend/       FastAPI · Python 3.12 · SQLAlchemy · Alembic
│   ├── app/
│   │   ├── main.py          Point d'entrée FastAPI
│   │   ├── config.py        Pydantic Settings (env vars)
│   │   ├── db.py            Session SQLAlchemy
│   │   ├── models/          ORM models (Operator, Operation, Skill, Assignment)
│   │   ├── schemas/         Pydantic schemas (CRUD)
│   │   ├── routers/         Endpoints REST v1
│   │   └── services/        Logique métier (import CSV...)
│   ├── alembic/             Migrations
│   └── tests/               Tests pytest
├── frontend/      React 18 · Vite · TypeScript
├── data/          Fichiers CSV de démonstration
├── infra/         docker-compose (Postgres 16)
├── docs/          Architecture, API, ADR
├── .env.example   Variables d'environnement
├── Makefile       Commandes de dev
└── docker-compose.yml  Orchestration locale
```

## Commandes utiles

| Commande            | Description                              |
|---------------------|------------------------------------------|
| `make up`           | Démarrer tous les services               |
| `make down`         | Arrêter tous les services                |
| `make build`        | Reconstruire les images Docker           |
| `make migrate`      | Appliquer les migrations Alembic         |
| `make import-data`  | Importer les CSV de démonstration        |
| `make test`         | Lancer tous les tests                    |
| `make lint`         | Vérifier le code                         |
| `make fmt`          | Formater le code                         |
| `make logs`         | Afficher les logs                        |

## Stack technique

- **Backend** : FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16, pydantic-settings
- **Frontend** : React 18, Vite, TypeScript, TailwindCSS
- **Infra** : Docker Compose, PostgreSQL 16
- **CI/CD** : GitHub Actions
- **Qualité** : ruff, mypy (Python) · ESLint, Prettier (TypeScript)

## Conventions

- Branches : `feat/<ticket>`, `fix/<ticket>`, `chore/<ticket>`
- Commits : [Conventional Commits](https://www.conventionalcommits.org/)
- PR : description obligatoire + 1 reviewer
- Tests : coverage ≥ 80 % (backend), tests unitaires (frontend)

## Documentation

- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Déploiement](docs/deployment.md)
- [ADR](docs/adr/)