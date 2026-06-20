# Phase 11B - Pilot Branding Deployment Verification and RC1 Package Refresh

## Objective

Deploy the accepted branding baseline (`94a8a86`) to the pilot/demo environment, verify runtime identity (`Rivar by Corbit`, `1.0.0-rc1`), and refresh RC1 package artifacts.

## Deployment Target

- Target path: `/root/pdss_demo`
- Compose project: `pdss_demo`
- Backend host port: `18010`
- Frontend host port: `13010`

## Pre-Deploy Baseline and Backup

- Local branch: `restart/baseline-before-github-push`
- Local baseline commit used for deployment content: `94a8a86`
- Verified database backup created before apply:
  - `/root/pdss_backups/pdss_demo_pre_94a8a86_20260620_113854.sql`
  - size: `105K` (non-empty)
- Safety rule observed:
  - no volume deletion
  - no `docker compose down -v`

## Deployment Commands Executed

1. Build deployment archive from branding/version files.
2. Upload archive to target:
   - `/root/pdss_demo/phase11b_branding_94a8a86.tar.gz`
3. Apply files and restart services:
   - `cd /root/pdss_demo`
   - `tar -xzf phase11b_branding_94a8a86.tar.gz`
   - `COMPOSE_PROJECT_NAME=pdss_demo docker compose up --build -d`
4. Runtime correction applied after verification:
   - backend version file path was valid in code, but backend container could not read repo-root `VERSION` due backend-only Docker build context.
   - added `backend/VERSION` and deployed it.
   - rebuilt backend:
     - `COMPOSE_PROJECT_NAME=pdss_demo docker compose up --build -d backend`

## Runtime Identity Verification

## Backend

- Command:
  - `curl -sS http://127.0.0.1:18010/health`
- Result:
  - `{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}`
- Status: pass

## Frontend

- Root page title check: `Rivar | Corbit` (pass)
- Manifest check:
  - `name: Rivar | Corbit`
  - `short_name: Rivar`
  - icon source: `rivar.png`
- Logo endpoint check:
  - `http://193.162.129.58:13010/rivar.png` returned `200`, `image/png`
- Bundle identity check:
  - contains `Rivar by Corbit`
  - contains `Version` label text
- Status: pass

Post-verification UI feedback adjustment (same phase scope):

- Sidebar logo size reduced for cleaner layout.
- Sidebar identity text simplified to only `Rivar by Corbit` (version remains in footer to avoid duplication).
- Updated file: `frontend/src/components/Layout.tsx`

Note: Browser automation was not introduced in this phase; verification used deployed HTTP endpoint checks and runtime bundle/content inspection.

## Verification Commands and Results (Pilot/Demo Stack)

- `docker compose ps` (with `COMPOSE_PROJECT_NAME=pdss_demo`): pass, backend/frontend/postgres up and healthy
- `curl -sS http://127.0.0.1:18010/health`: pass
- `docker compose run --rm backend python -m pytest tests -q`: `39 passed, 4 skipped, 38 warnings`
- `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`: `3 passed, 20 warnings`
- `docker compose run --rm frontend npm run build`: success (`Compiled with warnings`)

## Demo Cleanup Verification

- Cleanup command executed:
  - `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode cleanup`
- Cleanup summary returned removal counts for demo-tagged entities.
- Post-cleanup DB checks:
  - `demo_projects=0`
  - `demo_packages=0`
  - `demo_decisions=0`
- Status: pass

## RC1 Package Refresh

Refreshed package path:

- `release_packages/corbit-rivar-rc1/`

Updated to include branding/version/runtime files:

- `update_package/update_files/VERSION`
- `update_package/update_files/backend/VERSION`
- `update_package/update_files/backend/app/app_metadata.py`
- `update_package/update_files/backend/app/main.py`
- `update_package/update_files/frontend/public/index.html`
- `update_package/update_files/frontend/public/manifest.json`
- `update_package/update_files/frontend/public/rivar.png`
- `update_package/update_files/frontend/src/App.tsx`
- `update_package/update_files/frontend/src/components/Layout.tsx`
- `update_package/update_files/frontend/src/pages/LoginPage.tsx`
- `update_package/update_files/frontend/src/utils/appIdentity.ts`
- `update_package/update_files/frontend/src/i18n/en.json`
- `update_package/update_files/frontend/src/i18n/fa.json`
- `update_package/update_files/frontend/src/responsive.css`

Also updated:

- `release_packages/corbit-rivar-rc1/manifest.json`
- `release_packages/corbit-rivar-rc1/README_RELEASE.md`
- `release_packages/corbit-rivar-rc1/RELEASE_NOTES.md`
- `release_packages/corbit-rivar-rc1/KNOWN_LIMITATIONS.md`
- `release_packages/corbit-rivar-rc1/POST_DEPLOY_SMOKE_CHECKLIST.md`
- `release_packages/corbit-rivar-rc1/CHECKSUMS.sha256`
- `docs/release/pr_summary_rc1.md`
- `docs/release/tagging_recommendation_rc1.md`
- `docs/release/phase11_release_package_integrity_check.md`

## Remaining Risks

1. Frontend eslint warnings remain in legacy areas.
2. Backend deprecation warnings remain.
3. Backend version value currently depends on `backend/VERSION` being kept in sync with root `VERSION` for Dockerized runtime.

## Phase 11B Status

`closed`
