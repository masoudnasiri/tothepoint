# Rivar Restart Audit - Architecture Map

## Runtime Architecture

## Container Topology (`docker-compose.yml`)

- `postgres`
  - image: `postgres:15-alpine`
  - persistent volume: `postgres_data`
  - init script mount: `./backend/init.sql`
- `backend`
  - build context: `./backend`
  - command: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop asyncio`
  - bind mount: `./backend:/app`
  - upload persistence volume: `uploads_data:/app/uploads`
- `frontend`
  - build context: `./frontend`
  - command: `npm start`
  - bind mount: `./frontend:/app`

Internal network: `procurement_network`.

## Backend Architecture

## Entry and Lifecycle

- App entrypoint: `backend/app/main.py`
- Startup lifecycle:
  1. `init_db()` creates tables from SQLAlchemy metadata
  2. `seed_sample_data()` runs and skips if users already exist

## API Layer (`backend/app/routers/`)

Router prefixes (selected):

- `/auth`, `/users`, `/projects`, `/items`, `/items-master`
- `/procurement`, `/delivery-options`, `/decisions`
- `/finance`, `/analytics`, `/dashboard`, `/reports`
- `/suppliers`, `/supplier-payments`
- `/packages` (Phase 3 package feature)
- `/config` (feature flags)
- `/audit-logs`

## Core Domain and Data Access

- Models: `backend/app/models.py`, `backend/app/models_invoice_payment.py`
- DTOs: `backend/app/schemas.py`
- CRUD orchestration: `backend/app/crud.py`
- Auth/JWT + role helpers: `backend/app/auth.py`

## Service and Validation Layer (Phase 3 relevant)

- `backend/app/services/package_service.py`
  - package lookup and coverage summary
  - reference normalization support
- `backend/app/validators/package_validators.py`
  - package/legacy reference validation
  - supplier normalization enforcement
  - optional package auto-resolution/creation
- `backend/app/services/audit_service.py`
  - feature-flag and phase-operation audit trail

## Optimization and Finance Layer

- `backend/app/optimization_engine.py` (legacy/main)
- `backend/app/optimization_engine_enhanced.py` (multi-mode enhanced)
- Finance router invokes these engines via `/finance/optimize` and `/finance/optimize-enhanced`

## Frontend Architecture

## App Shell and Routing

- Entry: `frontend/src/App.tsx`
- Auth + feature-flag providers wrap route tree
- Core routes:
  - `/dashboard`, `/projects`, `/projects/:projectId/items`
  - `/procurement`, `/procurement-plan`
  - `/finance`, `/optimization`, `/optimization-enhanced`
  - `/decisions`, `/analytics`, `/reports`, `/suppliers`, `/users`

## API Client and Data Contracts

- API gateway: `frontend/src/services/api.ts`
- Domain types:
  - shared core: `frontend/src/types/index.ts`
  - package-specific: `frontend/src/types/packages.ts`

## Package/Sub-item UI Subsystem

- Main entry page: `frontend/src/pages/ProcurementPage.tsx`
- Package wizard:
  - `frontend/src/components/PackageWizard/PackageWizard.tsx`
  - step components for metadata, composition, pricing/payment/delivery
- Package list + coverage:
  - `frontend/src/components/packages/PackageList.tsx`
  - `frontend/src/components/packages/CoverageSummaryModal.tsx`
- Coverage utility:
  - `frontend/src/utils/coverageCalculator.ts`

## Feature Flag Flow

- Backend source of flags: `backend/app/config.py`
- Backend exposure endpoint: `backend/app/routers/config.py`
- Frontend consumption: `frontend/src/hooks/useFeatureFlags.tsx`
- Important current behavior: frontend force-enables package mode (`enable_package_procurement: true`, `legacy_project_item_fallback: false`) regardless of fetched values.

## Cross-Cutting Technical Notes

- CORS driven by backend settings (`settings.get_allowed_origins()`)
- JWT bearer auth required across most routers (via `get_current_user`)
- Role helper functions exist in `backend/app/auth.py`, but most routers rely on authenticated user presence rather than strict role-specific dependencies.
- Database migrations are script-driven SQL phases rather than Alembic-managed revision history.
