# Déploiement OPERATOR-QI

## Développement local

```bash
cp .env.example .env
make up
```

## Variables d'environnement requises

| Variable  | Description   | Défaut        |
|-----------|---------------|---------------|
| `APP_ENV` | Environnement | `development` |

> **Note v1** : le moteur de matching est entièrement stateless.
> Aucune base de données n'est requise pour les endpoints `/api/v1/recommendations/*`.
> PostgreSQL, JWT et autres variables seront ajoutés aux étapes suivantes (auth, persistence).

## Vérifications

- `GET /health` → `{"status": "ok", "version": "0.1.0"}`
- `POST /api/v1/recommendations/operators` → liste de candidats classés
- `POST /api/v1/recommendations/preview` → score détaillé d'un opérateur
- Frontend → `http://localhost:5173`
