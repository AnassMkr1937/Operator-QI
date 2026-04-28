# Architecture OPERATOR-QI

## Vue d'ensemble

OPERATOR-QI est une plateforme de matching entre opérateurs et missions, basée sur une analyse de qualité d'intervention.

## Composants

```
┌────────────────────────────────────────────────┐
│                  Docker Compose                 │
│  ┌──────────┐    ┌──────────────────────────┐  │
│  │ Frontend │───▶│ Backend (FastAPI)         │  │
│  │ React/TS │    │ Stateless matching engine │  │
│  │  :5173   │    │          :8000            │  │
│  └──────────┘    └──────────────────────────┘  │
└────────────────────────────────────────────────┘
```

> **v1 — stateless** : aucune base de données n'est utilisée dans cette version.
> PostgreSQL sera ajouté à l'étape de persistance (Step 5+).

## Backend (FastAPI)

- **Framework** : FastAPI 0.111+
- **Moteur de matching** : algorithme déterministe pondéré (stateless, pas de BDD)
- **Validation** : Pydantic v2
- **Tests** : pytest + httpx (64 tests)

### Structure

```
backend/
├── app/
│   ├── main.py          Point d'entrée FastAPI
│   ├── routers/         Endpoints par domaine
│   │   └── recommendations.py  POST /api/v1/recommendations/*
│   ├── schemas/         Pydantic schemas (recommendation.py)
│   └── services/        Logique métier
│       └── matching.py  Moteur de scoring/ranking
└── tests/               Tests pytest (64 tests)
```

## Frontend (React/Vite/TypeScript)

- **Framework** : React 18 + Vite 5
- **Langage** : TypeScript strict
- **Tests** : Vitest + Testing Library

### Structure

```
frontend/
├── src/
│   ├── main.tsx         Point d'entrée React
│   ├── App.tsx          Composant racine
│   ├── components/      Composants réutilisables
│   ├── pages/           Pages de l'application
│   └── __tests__/       Tests Vitest
└── public/              Assets statiques
```

## Infrastructure

- **Docker Compose** : Orchestration locale
- **Nginx** : Serveur frontend (production)
- **PostgreSQL 16** : *(à venir — Step 5 persistance)*

## CI/CD

- **GitHub Actions** : Lint + tests sur chaque PR
- Branche protégée : `main` (merge uniquement via PR)
