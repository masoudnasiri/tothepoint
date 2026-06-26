# Sprint 3A-R3 - Cost-Level Payment Schedule and Save/Verify Stability

- Status: PASS
- Date: 2026-06-26
- Branch: `recovery/sprint3a-r3-cost-level-payment-schedule`

## Product Purpose

Close the Sprint 3A recovery gap by:

1. stabilizing save/reopen on procurement option update (`MissingGreenlet` regression),
2. introducing safe component-level payment schedule overrides,
3. preserving Sprint 3A-4A read-only model compatibility,
4. hardening installer verification to remove stale fixture-ID assumptions.

## Changed Behavior

- Procurement option update/create paths no longer rely on lazy access after audit writes; save/reopen is stable.
- Each active cost component can now inherit the option-level schedule or override it with payee-specific metadata.
- Step 3 now distinguishes:
  - default option-level schedule (Payment section),
  - per-component payment overrides (inside each cost-component panel).
- Financial projection avoids double-counting when custom component schedules are present.

## API / Contract Changes

- `procurement_cost_components` API now supports `payment_metadata`.
- New schema contract fields:
  - `inherit_option_payment_schedule`
  - `payee_type`, `payee_label`
  - `payment_method_id`, `payment_type`
  - `planned_payment_date`
  - `payment_schedule[]` rows
- Readiness response includes `component_payment_diagnostics`.

## Data Model / Schema Changes

- Added `procurement_cost_components.payment_metadata` JSON column.
- Added migration script:
  - `backend/add_procurement_cost_component_payment_metadata.sql`
- Added ADR:
  - `docs/architecture/ADR-010-cost-level-payment-schedule-contract.md`

## Backend Services / Routers Updated

- `backend/app/routers/procurement.py`
- `backend/app/routers/procurement_financials.py`
- `backend/app/services/procurement_financials_service.py`
- `backend/app/services/atomic_optimization_candidate_service.py`
- `backend/app/services/financial_projection_service.py`
- `backend/app/crud.py`

## Frontend Changes

- `frontend/src/components/PackageWizard/PackageWizardStep3.tsx`
  - added per-component payment metadata controls
  - added custom installment schedule rows per component
  - added default-vs-custom payment summary in Payment section
- `frontend/src/components/PackageWizard/PackageWizard.tsx`
- `frontend/src/components/PackageWizard/costComponentValidation.ts`
- `frontend/src/types/index.ts`
- `frontend/src/i18n/en.json`, `frontend/src/i18n/fa.json`

## Installer / Verification Changes

- Added clean-installer baseline files under `deployment/rivar-installer/`.
- `deployment/rivar-installer/verify.sh` now reseeds deterministic fixture by default before runtime checks.
- Added runtime scripts:
  - `backend/scripts/create_sprint4a_demo_fixture.py`
  - `backend/scripts/verify_runtime.py`
- Runtime verifier report now includes discovered IDs:
  - `project_id`, `project_item_id`, `package_id`, `procurement_option_id`, `candidate_id` (when present).

## Tests and Build Evidence

Backend:

- `python -m pytest tests/test_phase13a_payment_methods_and_cost_components.py -q` -> PASS
- `python -m pytest tests/test_phase13c_procurement_option_persistence_readiness.py -q` -> PASS
- `python -m pytest tests/test_phase13f_financial_projection_engine.py -q` -> PASS

Frontend:

- `npm test -- --runInBand --watch=false PackageWizardStep3.test.tsx PackageWizard.saveBoundary.test.tsx` -> PASS
- `npm run build` -> PASS (pre-existing eslint warnings outside R3 scope)

Installer scripts:

- `bash -n deployment/rivar-installer/install.sh` -> PASS
- `bash -n deployment/rivar-installer/verify.sh` -> PASS
- `bash -n deployment/rivar-installer/uninstall.sh` -> PASS

## Deployment Notes

- Artifact used: `rivar_sprint3a_r3_cost_level_payment_schedule_20260626_000243.tar.gz`
- Server: `193.162.129.58`, path `/opt/rivar-demo`
- Deployment sequence executed:
  - services rebuilt with `docker compose ... up -d --build`
  - DB migration applied (`payment_metadata` column add-if-not-exists)
  - deterministic fixture reseed + runtime verify
- Runtime verification result: `PASS` with discovered IDs:
  - `project_id=13`
  - `project_item_id=103`
  - `package_id=5`
  - `procurement_option_id=4`
  - `candidate_id=candidate:13:103:5:4`

## Closure Provenance (Commit/Push/Verify)

- Final Sprint 3A-R3 closure commit:
  - `cd9f7ca26a72a0a1e49e745169bb6c352d7cfcf9`
  - message: `fix: add cost-level payment schedule contract`
- Push result:
  - pushed to `origin/recovery/sprint3a-r3-cost-level-payment-schedule` successfully
  - remote branch confirmed contains closure commit via `git branch -r --contains HEAD` and `git ls-remote --heads`
- FK violation review:
  - observed during closure verification: fixture cleanup failed with FK on `procurement_options_supplier_id_fkey`
  - root cause: cleanup selector missed procurement options linked by fixture supplier/payment-method IDs
  - fix applied in `backend/scripts/create_sprint4a_demo_fixture.py`:
    - include supplier-linked and payment-method-linked procurement options in cleanup option-id set before deleting suppliers/payment methods
  - post-fix verification: `deployment/rivar-installer/verify.sh` passes without FK errors
- Final installer/runtime verification (post-fix):
  - `verify.sh` PASS on `/opt/rivar-demo`
  - fixture recreate cleanup evidence:
    - `procurement_options=6`, `delivery_options=1`, `suppliers=1`, `payment_methods=1`
  - runtime verifier PASS with discovered IDs:
    - `project_id=14`
    - `project_item_id=104`
    - `package_id=10`
    - `procurement_option_id=10`
    - `candidate_id=candidate:14:104:10:10`
- Save/reopen stability smoke (post-commit):
  - `GET /procurement/option/10` -> `200`
  - `PUT /procurement/option/10` -> `200`
  - `POST /procurement/options` -> `200` (created option id `12`)

## Risks / Debt

- Existing repo has broad unrelated local modifications; release artifact must be strict scope-clean.
- Frontend build warnings remain from pre-existing files outside Sprint 3A-R3 scope.

## Continuation Gate

- Sprint 3A-R3 closure is accepted PASS with committed provenance.
- Recommendation: resume Workspace Organization only after this closure record is treated as the active accepted baseline.

## Terminology Refinement Follow-up (UI Labels Only)

- Scope: user-facing payment schedule wording refinement in Package Wizard Step 3.
- Updated visible terminology:
  - EN: `Payment schedule type`, `Single-stage`, `Multi-stage`, `Default payment schedule`, `Custom payment schedule for this cost`
  - FA: `نوع زمان‌بندی پرداخت`, `تک‌مرحله‌ای`, `چندمرحله‌ای`, `برنامه پرداخت پیش‌فرض`, `برنامه پرداخت اختصاصی این هزینه`
- Explicitly unchanged:
  - backend enum/internal contract values (`cash` / `installments`)
  - persistence schema and stored payload structure
  - payment schedule logic and component metadata behavior
  - financial projection and optimization/scenario calculations

