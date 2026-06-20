# Rivar Developer Manual

## Scope

This document is for backend/frontend engineers continuing development in the current Rivar codebase.

## Tech Stack

- Backend: FastAPI + SQLAlchemy async (`backend/app/`)
- Frontend: React + TypeScript + MUI (`frontend/src/`)
- Database: PostgreSQL (runtime), SQLite (tests)
- Orchestration: Docker Compose (`docker-compose.yml`)
- Migrations: SQL-script based (no Alembic revision chain in this repo)

## Repository Map

- `backend/app/main.py`: app entrypoint and router registration.
- `backend/app/models.py`, `models_invoice_payment.py`: ORM domain models.
- `backend/app/schemas.py`: Pydantic request/response contracts.
- `backend/app/routers/`: API routes by domain.
- `backend/app/crud.py`: shared DB operations and audit helper.
- `backend/app/services/`: service logic (package service, audit service, etc.).
- `backend/app/validators/`: package reference and validation logic.
- `backend/tests/`: pytest suite (mixed completeness; some placeholders).
- `frontend/src/pages/`: top-level screens.
- `frontend/src/components/`: feature components (including package wizard).
- `frontend/src/services/api.ts`: frontend API client layer.

## Local Development Workflow

### Preferred (Docker)

1. `docker compose up --build -d`
2. Backend health: `curl http://127.0.0.1:8000/health`
3. Frontend: open `http://localhost:3000`

### Backend-only local

- From `backend/`: `uvicorn app.main:app --reload`

### Frontend-only local

- From `frontend/`: `npm install`, then `npm start`

## Feature Flags

Runtime flags are controlled in backend settings and exposed by `/config/feature-flags`:

- `ENABLE_PACKAGE_PROCUREMENT`
- `LEGACY_PROJECT_ITEM_FALLBACK`
- `SUPPLIER_NORMALIZATION_ENFORCED`
- `ENABLE_PACKAGE_BASED_OPTIMIZATION`
- `REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS`
- `ENFORCE_PACKAGE_COVERAGE_ON_LOCK`

Important: frontend flag consumption exists in `frontend/src/hooks/useFeatureFlags.tsx`; verify actual behavior before assuming backend-only control.

## Data Model Conventions

- Package-aware path uses `package_id` where available.
- Legacy compatibility path still supports item-level fields in multiple flows.
- New development should keep backward compatibility unless intentionally deprecating legacy mode.

## Current Operational Coupling (Must Preserve)

- Decisions -> procurement plan tracking
- Decisions -> invoice/payment and supplier payment flows
- Finance writes -> cashflow events
- Key lifecycle actions -> audit logs

Do not break these integrations when changing package logic.

## API Development Guidelines

- Always use ORM models in SQLAlchemy queries (`select(Model)`), not schema classes.
- Keep response payloads traceable: include package/supplier metadata when relevant.
- For dual paths (legacy + package), preserve existing behavior and add safe fallbacks.
- Add role-aware checks where domain logic depends on actor context.

## Testing Guidance

Primary backend tests live in `backend/tests/`:

- `test_crud_phase3.py`
- `test_validators.py`
- `test_phase5_package_optimization_boundary.py`
- `test_phase5_decision_lock_coverage.py`
- `test_phase6a_operational_compat.py`
- `test_phase8_release_candidate_smoke.py`

Run:

- `docker compose run --rm backend python -m pytest tests -q`
- `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`

If local Docker is unhealthy, validate syntax as minimum guard:

- `python -m compileall app tests`

## Documentation and Change Discipline

- Update relevant docs in `docs/restart-audit/` for every non-trivial phase.
- Keep release/demo docs in sync (`docs/release/`) when user-facing demo flow changes.
- Keep changes small and phase-focused.
- Avoid introducing new modules when compatibility patching existing ones is sufficient.

## Demo Dataset (Phase 8 RC)

- Script: `backend/scripts/create_demo_dataset.py`
- Create/recreate:
  - `python scripts/create_demo_dataset.py --mode create`
- Cleanup:
  - `python scripts/create_demo_dataset.py --mode cleanup`

## Common Pitfalls

- Mixing schema and model types in query code.
- Assuming invoice/payment tables are the only source of truth (legacy decision fields still used).
- Returning item-level-only payloads in package-aware flows.
- Skipping audit writes for lifecycle transitions.

## Recommended PR Checklist

1. Models/schemas updated consistently.
2. Router output includes required metadata.
3. Audit writes added for create/update/delete/status actions.
4. Regression tests added/updated.
5. Backend compile/tests pass in Docker.
6. Docs updated in `docs/restart-audit/`.

## Related References

- `docs/restart-audit/02_architecture_map.md`
- `docs/restart-audit/03_run_and_deployment.md`
- `docs/restart-audit/14_existing_operational_modules_regression_audit.md`
- `docs/restart-audit/17_phase6a_operational_compatibility_hardening.md`
