# Rivar Restart Audit - Project Overview

## Scope and Evidence

This audit is based on direct inspection of the active codebase in:

- `backend/`
- `frontend/`
- top-level deployment/runtime scripts
- `installation_packages/`, `update_package/`, and `pdss-update-v1.0.2-COMPLETE/`
- Git history and working tree state

No business refactoring or schema mutation was performed during this phase.

## Product and Technical Identity

Rivar (PDSS naming also appears in scripts/docs) is a project-based procurement decision support platform with:

- supplier option comparison
- package/bundle-style procurement flows
- optimization-driven decisioning
- finance and cashflow projection
- role-based access and audit logging
- Persian/English UI localization

## Repository Orientation

### Primary Stack

- **Backend framework:** FastAPI (`backend/app/main.py`)
- **Frontend framework:** React + TypeScript + Material UI (`frontend/src/App.tsx`, `frontend/package.json`)
- **Database:** PostgreSQL in runtime (`docker-compose.yml`), SQLite in tests (`backend/tests/conftest.py`)
- **ORM:** SQLAlchemy async models/sessions (`backend/app/models.py`, `backend/app/database.py`)
- **Migration style:** raw SQL migration scripts + execution wrappers, no Alembic config found (`backend/*.sql`, `backend/execute_phase1_migrations.sh`, `backend/run_phase2_data_migration.sh`)
- **Optimization libraries:** OR-Tools + PuLP (`backend/requirements.txt`, `backend/app/optimization_engine*.py`)

### Build and Runtime System

- **Container orchestration:** Docker Compose (`docker-compose.yml`)
- **Backend startup:** `uvicorn app.main:app` from Docker command and local dev instructions
- **Frontend startup:** CRA `react-scripts start` (`frontend/package.json`, `frontend/Dockerfile`)
- **Frontend production build:** `react-scripts build`

### Configuration System

- Backend uses `pydantic-settings` with `.env` support (`backend/app/config.py`)
- Docker Compose injects key runtime env vars (`docker-compose.yml`)
- Feature flags exposed by API (`backend/app/routers/config.py`) and consumed in frontend (`frontend/src/hooks/useFeatureFlags.tsx`)

## High-Level Repository Map

- `backend/app/`
  - `main.py` application entrypoint and router registration
  - `models.py`, `models_invoice_payment.py` domain models
  - `schemas.py` API DTOs
  - `crud.py` core data operations
  - `routers/` feature modules (`projects`, `items`, `procurement`, `packages`, `finance`, `decisions`, etc.)
  - `services/` package/audit services
  - `validators/` package-aware validation layer
- `backend/tests/`
  - Phase 3 package/validator/audit CRUD tests
- `frontend/src/`
  - `App.tsx` route map
  - `pages/` workflow pages
  - `components/PackageWizard/` package authoring flow
  - `components/packages/` package list + coverage analysis
  - `services/api.ts` HTTP client endpoint map
  - `hooks/useFeatureFlags.tsx` feature-flag context
- Deployment/runtime top-level
  - `docker-compose.yml`
  - `start.bat`, `stop.bat`, `start.sh`, `stop.sh`
  - backup/restore scripts (`backup_database.bat`, `restore_database.bat`)
- Packaging/update artifacts
  - `installation_packages/`
  - `update_package/`
  - `pdss-update-v1.0.2-COMPLETE/`

## Git State Snapshot (Audit Time)

- Branch: `main` tracking `origin/main`
- Working tree: heavily dirty (many modified/untracked files in active app and many deleted archive/package files)
- Recent commit theme includes procurement/sub-item/package work:
  - `3b3eede` "after adding subitem"
  - `b28dcff` "after adding subitem"
  - newer commits around delivery option fixes and debugging

## Initial Conclusion

The codebase is an active, partially stabilized continuation of an existing product, not a clean release branch. The procurement package/sub-item capability is materially present across backend models, APIs, services, validators, and frontend UI, with rollout controls and migration scripts indicating a transition from legacy item-centric references to package-centric references.
