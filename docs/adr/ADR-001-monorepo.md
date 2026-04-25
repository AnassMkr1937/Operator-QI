# ADR-001 — Choix de l'architecture monorepo

**Date** : 2026-04-25  
**Statut** : Accepté

## Contexte

Le projet OPERATOR-QI nécessite un backend API, un frontend web et une infrastructure partagée. Nous devons décider de l'organisation du code.

## Décision

Utiliser un **monorepo** avec `backend/`, `frontend/`, `infra/`, `docs/` dans un seul dépôt GitHub.

## Justification

- Facilite la cohérence des versions et des changements inter-couches
- Simplifie la CI/CD (un seul pipeline)
- Réduit la friction pour les nouveaux contributeurs (un seul `git clone`)

## Conséquences

- Le dépôt grossira avec le temps (acceptable pour ce projet)
- Les builds CI doivent être divisés en jobs indépendants
