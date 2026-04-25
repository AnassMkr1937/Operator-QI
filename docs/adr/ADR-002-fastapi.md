# ADR-002 — Choix de FastAPI pour le backend

**Date** : 2026-04-25  
**Statut** : Accepté

## Contexte

Choisir un framework Python pour l'API REST.

## Décision

Utiliser **FastAPI** avec Python 3.12.

## Justification

- Documentation automatique (OpenAPI/Swagger)
- Performances élevées (ASGI)
- Typage fort avec Pydantic v2
- Ecosystème mature (SQLAlchemy, Alembic, pytest)

## Conséquences

- Nécessite Python 3.12+
- Apprentissage de Pydantic v2 pour l'équipe
