# Déploiement OPERATOR-QI

## Développement local

```bash
cp .env.example .env
make up
```

## Variables d'environnement requises

| Variable           | Description             | Défaut          |
|--------------------|-------------------------|-----------------|
| `APP_ENV`          | Environnement           | `development`   |
| `SECRET_KEY`       | Clé secrète JWT         | *(obligatoire)* |
| `POSTGRES_DB`      | Nom de la base          | `operatorqi`    |
| `POSTGRES_USER`    | Utilisateur DB          | `operatorqi`    |
| `POSTGRES_PASSWORD`| Mot de passe DB         | *(obligatoire)* |
| `DATABASE_URL`     | URL complète PostgreSQL | *(calculée)*    |

## Vérifications

- `GET /health` → `{"status": "ok"}`
- Frontend → `http://localhost:5173`
