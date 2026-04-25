# OPERATOR-QI

> Plateforme de matching opérateurs-missions basée sur la qualité d'intervention.

## Démarrage rapide

```bash
# 1. Copier les variables d'environnement
cp .env.example .env

# 2. Démarrer tous les services
make up

# 3. Accéder aux services
#   Frontend  → http://localhost:5173
#   Backend   → http://localhost:8000
#   API docs  → http://localhost:8000/docs
```

## Architecture

```
Operator-QI/
├── backend/       FastAPI · Python 3.12
├── frontend/      React 18 · Vite · TypeScript
├── infra/         docker-compose (Postgres 16)
├── docs/          Architecture, ADR
├── scripts/       Utilitaires de dev
├── .env.example   Variables d'environnement
├── Makefile       Commandes de dev
└── docker-compose.yml  Orchestration locale
```

## Commandes utiles

| Commande       | Description                     |
|----------------|---------------------------------|
| `make up`      | Démarrer tous les services      |
| `make down`    | Arrêter tous les services       |
| `make build`   | Reconstruire les images Docker  |
| `make test`    | Lancer tous les tests           |
| `make lint`    | Vérifier le code                |
| `make fmt`     | Formater le code                |
| `make logs`    | Afficher les logs               |

## Stack technique

- **Backend** : FastAPI, SQLAlchemy, Alembic, PostgreSQL
- **Frontend** : React 18, Vite, TypeScript, TailwindCSS
- **Infra** : Docker Compose, PostgreSQL 16
- **CI/CD** : GitHub Actions
- **Qualité** : ruff, black, mypy (Python) · ESLint, Prettier (TypeScript)

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