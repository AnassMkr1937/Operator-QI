# ROADMAP — OPERATOR-QI

> Dernière mise à jour : 2026-04-28  
> État de référence : branche `main`

---

## 1. Vue d'ensemble rapide

| Étape | Titre | État |
|-------|-------|------|
| Step 1 | Monorepo skeleton + CI | ✅ Terminé & fusionné |
| CI fix | Packaging backend (ruff, pytest) | ✅ Terminé & fusionné |
| Step 3 | Moteur de matching v1 (stateless) | ✅ Terminé & fusionné |
| Docs | Alignement docs avec architecture réelle | ✅ Terminé & fusionné |
| Step 4 | Frontend métier (UI recommandation) | ✅ Terminé & fusionné |
| Step 5 | Sécurité, rôles, audit, persistance | 🔜 **Prochaine priorité** |
| Step 6 | Qualité finale + release v1 | 🔜 Après Step 5 |

**État actuel sur `main` :** 64 tests backend (pytest) + 28 tests frontend (Vitest) — CI verte.

---

## 2. Ce qui est terminé et fusionné ✅

### Step 1 — Monorepo skeleton (PR #4)
- Structure monorepo `backend/ / frontend/ / infra/ / docs/ / data/ / scripts/`
- `Makefile` avec commandes `up / down / build / test / lint / fmt`
- `docker-compose.yml` pour le développement local
- `.github/workflows/ci.yml` : lint + tests backend & frontend
- `.env.example`, `.editorconfig`, `.gitignore`
- ADR-001 (monorepo) et ADR-002 (FastAPI)

### CI fix — Packaging backend (PR #6)
- `pyproject.toml` : découverte setuptools restreinte à `app*` (exclusion `alembic*`, `tests*`)
- Passage à vert de tous les checks CI

### Step 3 — Moteur de matching v1 (PR #7)
- `backend/app/services/matching.py` : algorithme déterministe pondéré (stateless)
  - 40 % compétences · 30 % disponibilité · 20 % historique · 10 % expérience
  - Filtres durs : opérateur inactif, conflit horaire, compétence obligatoire manquante
- `backend/app/schemas/recommendation.py` : schémas Pydantic v2 complets
- `backend/app/routers/recommendations.py` :
  - `POST /api/v1/recommendations/operators` — ranking N candidats
  - `POST /api/v1/recommendations/preview` — score d'un seul opérateur
- 64 tests pytest : 36 unitaires matching + 27 API + 1 health

### Docs alignement (PR #8)
- `docs/architecture.md` : suppression des références stales (`models/`, `db.py`, PostgreSQL)
- `docs/deployment.md` : suppression des variables d'env inexistantes (`SECRET_KEY`, `POSTGRES_*`)
- Schéma d'architecture mis à jour (moteur stateless, sans BDD)

### Step 4 — Frontend métier (PR #9)
- `frontend/src/types/recommendation.ts` : types TypeScript complets
- `frontend/src/services/recommendationApi.ts` : client API (proxy Vite → FastAPI)
- `frontend/src/components/RecommendationForm.tsx` : formulaire opération + candidats JSON
- `frontend/src/components/CandidateCard.tsx` : carte candidat avec breakdown score
- `frontend/src/components/CandidateList.tsx` : liste classée + états vides/erreur
- `frontend/src/pages/RecommendationPage.tsx` : page principale
- 28 tests Vitest (form validation, rendering, empty/error states)
- `nginx.conf` pour le serving frontend en production

---

## 3. Ce qui est en cours / en attente (PRs ouvertes)

| PR | Titre | Recommandation |
|----|-------|----------------|
| #1 | Initialize ultra-professional architecture | ⛔ À fermer — supersédé par PR #4 |
| #2 | Verify completion of architecture | ⛔ À fermer — analyse stale |
| #3 | Confirm architecture status | ⛔ À fermer — analyse stale |
| #5 | Step 2 — CRUD + Alembic + CSV import | ⏸ En attente — Step 2 DB-backed non prioritaire en v1 stateless |

> **Note sur PR #5 :** Le projet a adopté une architecture stateless pour la v1 (matching sans BDD).
> La PR #5 (CRUD, Alembic, PostgreSQL) reste ouverte pour une future étape de persistance,
> mais elle n'est **pas bloquante** pour finir la roadmap v1.

---

## 4. Étapes restantes — ordre de priorité

### 🔴 Step 5 — Sécurité, authentification & persistance (priorité haute)

> Durée estimée : 1–2 sprints  
> Prérequis : Step 3 + Step 4 (✅ faits)

#### 5a — Authentification & RBAC
- [ ] Ajouter `python-jose` + `passlib` dans `pyproject.toml`
- [ ] Schéma `User` Pydantic (login, password_hash, role)
- [ ] `POST /api/v1/auth/login` → retourne JWT bearer
- [ ] Dépendance FastAPI `get_current_user` (middleware)
- [ ] Rôles : `admin`, `manager`, `viewer`
- [ ] Protection des endpoints `/recommendations/*` par rôle `manager+`
- [ ] Tests unitaires login/token + tests API avec et sans token

#### 5b — Persistance opérateurs (optionnelle en v1)
- [ ] Modèles SQLAlchemy `Operator`, `Skill`, `Assignment` (depuis PR #5 en attente)
- [ ] Alembic migration initiale
- [ ] Endpoints CRUD `/api/v1/operators` (liste, créer, modifier, supprimer)
- [ ] CSV import endpoint ou script `scripts/import_data.py`
- [ ] Mise à jour de `docker-compose.yml` pour ajouter le service PostgreSQL
- [ ] Variables d'env `DATABASE_URL`, `POSTGRES_*` dans `.env.example`

#### 5c — Audit & hardening API
- [ ] Table `AuditLog` (qui, quoi, quand, IP)
- [ ] Middleware FastAPI pour logger chaque appel recommendations
- [ ] `GET /api/v1/audit/logs` (admin only)
- [ ] Rate limiting (`slowapi` ou middleware personnalisé)
- [ ] En-têtes CORS restreints aux origines connues
- [ ] `HTTPS_ONLY` flag dans la config

#### 5d — Frontend auth
- [ ] Page login React (formulaire email + mot de passe)
- [ ] Stockage token JWT (`localStorage` / `sessionStorage`)
- [ ] Intercepteur Axios/fetch pour ajouter `Authorization: Bearer …`
- [ ] Redirection vers `/login` si 401
- [ ] Gestion des rôles côté UI (boutons admin visibles/cachés)

---

### 🟡 Step 6 — Qualité finale + release v1 (priorité moyenne)

> Durée estimée : 1 sprint  
> Prérequis : Step 5a au minimum

#### 6a — Tests end-to-end
- [ ] Installer Playwright (`npm install --save-dev @playwright/test`)
- [ ] Test E2E scénario principal : remplir formulaire → soumettre → vérifier ranking
- [ ] Test E2E état vide (aucun candidat éligible)
- [ ] Test E2E erreur API (backend arrêté / 422)
- [ ] Ajouter job `e2e` dans `.github/workflows/ci.yml`

#### 6b — Performance basique
- [ ] Mesurer temps de réponse `POST /recommendations/operators` pour 100 candidats
- [ ] Documenter les seuils cibles (ex. < 200 ms p99 pour 100 candidats)
- [ ] Profiler `matching.py` si > seuil (optimisation si besoin)

#### 6c — Documentation finale
- [ ] Compléter `docs/deployment.md` : procédure de déploiement production complète
  - Build images Docker, push registry
  - Variables d'env production
  - Health checks, rollback
- [ ] `CHANGELOG.md` (format [Keep a Changelog](https://keepachangelog.com/))
  - Section `[0.1.0]` avec toutes les features Step 1–4
- [ ] Compléter section "Authentification" dans `docs/api.md`
- [ ] ADR-003 : décision architecture stateless v1 vs DB-backed

#### 6d — Release v1
- [ ] Bump version dans `backend/pyproject.toml` → `1.0.0`
- [ ] Bump version dans `frontend/package.json` → `1.0.0`
- [ ] Tag Git `v1.0.0` sur `main`
- [ ] GitHub Release avec notes de version et assets (docker images si applicable)
- [ ] Mettre à jour `README.md` badge de version

---

## 5. Synthèse — chemin critique vers v1

```
[FAIT] Step 1 (monorepo) → [FAIT] CI fix → [FAIT] Step 3 (matching)
  → [FAIT] Step 4 (frontend)
    → Step 5a (auth JWT + RBAC)        ← PROCHAIN
      → Step 5c (audit + hardening)
        → Step 5b (persistance DB)     ← peut être parallèle à 5c
          → Step 6a (E2E tests)
            → Step 6c (docs + changelog)
              → Step 6d (release v1)   ← OBJECTIF FINAL
```

**Minimum viable pour "v1 production-ready" :**  
Step 5a (auth) + Step 6c (docs) + Step 6d (release) — soit environ **2–3 sprints**.

**Version complète avec persistance + audit :**  
Steps 5a + 5b + 5c + 5d + 6a + 6b + 6c + 6d — soit environ **4–5 sprints**.

---

## 6. Décisions d'architecture à documenter (ADR)

| ADR | Sujet | Statut |
|-----|-------|--------|
| ADR-001 | Monorepo | ✅ Documenté |
| ADR-002 | FastAPI | ✅ Documenté |
| ADR-003 | Stateless v1 (sans DB) | 🔜 À créer |
| ADR-004 | Auth strategy (JWT vs session) | 🔜 À créer (Step 5) |
| ADR-005 | Persistence strategy (PostgreSQL + SQLAlchemy) | 🔜 À créer (Step 5b) |

---

## 7. Stack technique cible v1

| Couche | Technologie | État |
|--------|-------------|------|
| Backend | FastAPI 0.111+ · Python 3.12 | ✅ En place |
| Matching | Algorithme déterministe pondéré (stateless) | ✅ En place |
| Auth | JWT (python-jose) + RBAC | 🔜 Step 5a |
| Persistance | PostgreSQL 16 + SQLAlchemy 2 + Alembic | 🔜 Step 5b |
| Frontend | React 18 + Vite 5 + TypeScript | ✅ En place |
| Frontend Auth | JWT localStorage + intercepteur fetch | 🔜 Step 5d |
| Tests backend | pytest (64 tests) | ✅ En place |
| Tests frontend | Vitest (28 tests) | ✅ En place |
| Tests E2E | Playwright | 🔜 Step 6a |
| CI/CD | GitHub Actions | ✅ En place |
| Infra | Docker Compose + Nginx | ✅ En place |
| Monitoring | *(hors scope v1)* | — |
