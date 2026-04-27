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

## Moteur de matching (v1)

Le moteur de recommandation est un algorithme déterministe pondéré :

| Composant    | Poids | Description |
|--------------|-------|-------------|
| skills       | 0.40  | Couverture des compétences × ratio de maîtrise moyen. Bonus : certification (+0.10), récence ≤30j (+0.10), ≤90j (+0.05). |
| availability | 0.30  | 1.0 si aucun conflit de planning (conflit → filtre dur). |
| history      | 0.20  | +0.50 par affectation antérieure sur la même opération (max 1.0) + +0.25 par catégorie similaire (max 0.50). |
| experience   | 0.10  | (nb_compétences × maîtrise_moyenne) / 25, plafonné à 1.0. |

**Filtres durs** (avant le scoring) :
- Opérateur inactif
- Conflit d'affectation sur la même date + vacation
- Compétence obligatoire absente ou sous le seuil requis

Les ex-æquo sont départagés par `operator_id` (ordre lexicographique ascendant — résultat déterministe).

**Limitations connues (v1)** :
- Toutes les données (candidats, compétences, affectations) doivent être fournies dans le corps de la requête
- Similarité des compétences par correspondance exacte sur `skill_id`
- Signal historique sans décroissance temporelle
- Poids fixes (pas de personnalisation par opération)

Voir [docs/api.md](docs/api.md) pour les contrats d'endpoint complets.

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