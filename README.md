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

## Interface de recommandation (Step 4)

### Lancer le frontend en local

```bash
cd frontend
npm install
npm run dev          # → http://localhost:5173
```

Le frontend utilise le proxy Vite (configuré dans `vite.config.ts`) pour
rediriger les appels `/api/*` vers le backend FastAPI sur `http://backend:8000`.
Pour un développement local sans Docker, assurez-vous que le backend tourne sur
le port 8000 ou modifiez la cible dans `vite.config.ts`.

### Utiliser l'interface de recommandation

1. **Ouvrir** `http://localhost:5173` dans votre navigateur.
2. **Remplir** le formulaire "Recommandation d'opérateurs" :
   - **Identifiant** et **nom** de l'opération (ex. `OP-001`, `Ligne d'assemblage A`)
   - **Date d'affectation** (ex. `2024-06-15`) et **vacation** (`Matin / Après-midi / Nuit`)
   - Ajouter les **compétences requises** (identifiant, niveau minimum, obligatoire ou non)
   - Coller un **tableau JSON de candidats** (ou cliquer "Charger l'exemple")
   - Régler **Top-N** (nombre de recommandations souhaitées, entre 1 et 100)
3. **Soumettre** → les candidats éligibles apparaissent classés par score.
4. **Cliquer "Détails ▼"** sur un candidat pour voir la décomposition complète du score.

### Exemple de requête / réponse

**Candidats JSON (à coller dans le formulaire) :**
```json
[
  {
    "operator_id": "OP-A",
    "name": "Alice Martin",
    "is_active": true,
    "skills": [
      { "skill_id": "welding", "proficiency": 4, "certified": true, "last_used_date": "2024-06-01" }
    ],
    "assignments": []
  },
  {
    "operator_id": "OP-B",
    "name": "Bob Dupont",
    "is_active": true,
    "skills": [
      { "skill_id": "welding", "proficiency": 2, "certified": false }
    ],
    "assignments": []
  }
]
```

**Réponse attendue (extraite) :**
```json
{
  "recommendations": [
    {
      "operator_id": "OP-A",
      "name": "Alice Martin",
      "rank": 1,
      "total_score": 0.826,
      "breakdown": {
        "skills_score": 0.346, "availability_score": 0.3,
        "history_score": 0.0,  "experience_score": 0.032
      },
      "unmet_requirements": [],
      "explanation": "covers 1/1 required skill(s) ..."
    }
  ],
  "total_eligible": 2,
  "total_candidates": 2,
  "operation_id": "OP-001",
  "filtered_out": []
}
```

### Tests frontend

```bash
cd frontend
npx vitest run          # 28 tests (form validation, results rendering, empty/error states)
npx eslint src/ --max-warnings 0
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

- **Backend** : FastAPI 0.111+ · Python 3.12 · moteur de matching stateless (v1)
- **Frontend** : React 18, Vite 5, TypeScript strict
- **Infra** : Docker Compose · Nginx (production)
- **CI/CD** : GitHub Actions (lint + tests sur chaque PR)
- **Qualité** : ruff, pytest (backend) · ESLint, Vitest (frontend)

## Conventions

- Branches : `feat/<ticket>`, `fix/<ticket>`, `chore/<ticket>`
- Commits : [Conventional Commits](https://www.conventionalcommits.org/)
- PR : description obligatoire + 1 reviewer
- Tests : coverage ≥ 80 % (backend), tests unitaires (frontend)

## Documentation

- [Roadmap & plan d'action](ROADMAP.md)
- [Architecture](docs/architecture.md)
- [API](docs/api.md)
- [Déploiement](docs/deployment.md)
- [ADR](docs/adr/)