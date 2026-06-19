# Rivar Restart Audit - Recommended Continuation Plan

## Objective

Resume development safely after pause, while protecting existing data and stabilizing the partially completed package/sub-item rollout.

## Guiding Constraints

- No destructive data operations in shared environments.
- Backup-first before update/migration.
- Feature-flagged rollout for behavior changes.
- Evidence-driven acceptance: tests + migration validation + rollback checks.

## Recommended Phased Plan

## Phase A - Stabilization (Immediate)

1. **Fix update safety scripts**
   - normalize DB service name usage (`postgres` vs `db`)
   - fail hard when backup fails
   - verify backup artifact integrity before update
2. **Create a migration runbook**
   - explicit order: phase 1 schema -> phase 2 data -> validation SQL
   - production-like dry run on clone database
3. **Lock test baseline**
   - repair `tests/test_crud_phase3.py` fixtures (`test_currency`)
   - resolve async DB context failures (`MissingGreenlet`)
   - keep tests deterministic for sqlite test mode

Exit criteria:

- one fully successful backend test run in container
- documented tested backup + restore drill
- no update script path that proceeds after failed backup

## Phase B - Policy Hardening (Package Mode Safety)

1. Define business rule for component coverage:
   - allow over-coverage vs block over-coverage
   - define decision-time minimum coverage threshold
2. Enforce server-side guardrails:
   - reject finalize/lock when coverage policy not met (if desired by PO)
   - unify package reference requirements under flags
3. Resolve frontend/backend flag contract:
   - remove/adjust frontend hard override in `useFeatureFlags.tsx`
   - ensure UI reflects backend rollout state

Exit criteria:

- policy signed off by product owner
- backend validations aligned with policy
- frontend flag behavior consistent with backend config

## Phase C - Optimization/FI Coupling Upgrade

1. Add package-native optimization mode behind `ENABLE_PACKAGE_BASED_OPTIMIZATION`
2. Ensure objective/constraints account for:
   - component coverage completeness
   - duplicate/overlap policy
   - package pricing and payment terms
3. Validate downstream:
   - decisions
   - cashflow/payment schedule effects
   - analytics consistency

Exit criteria:

- package-aware optimization run produces valid decisions in test scenarios
- no regression in legacy mode when fallback enabled

## Phase D - Test and Delivery Hardening

1. Replace placeholder API tests with real integration cases.
2. Add frontend smoke tests for package wizard and coverage modal.
3. Add CI checks:
   - backend tests
   - frontend build
   - lint/typecheck command with deterministic config
4. Add release checklist:
   - migration applied
   - backup verified
   - rollback command tested

Exit criteria:

- CI green on target branch
- release checklist completed for each deployment

---

## Top Technical Risks to Act On First

1. Update script backup path can fail silently (data safety risk).
2. Backend Phase 3 tests currently failing/errored.
3. Frontend package mode forced irrespective of backend flags.
4. Optimization is not yet fully package-native.
5. Frontend has no automated tests.

## Product-Owner Decisions Needed

1. Coverage policy for approval/finalization:
   - must be 100% component coverage or allow partial?
2. Overlap policy:
   - may multiple packages cover same component beyond required quantity?
3. Rollout strategy:
   - keep dual-mode fallback for one release or enforce package-only immediately?
4. Supplier assignment granularity:
   - do you need explicit component-level supplier offers, separate from package-level offers?
5. Optimization scope:
   - should optimizer prioritize package bundles as primary decision units in next milestone?

## Suggested First Development Sprint After Audit

- Sprint goal: "Safe package rollout foundation"
- Scope:
  1. update-script safety fixes + verified rollback drill
  2. backend test stabilization for Phase 3
  3. enforce agreed coverage validation at decision boundary
  4. remove frontend hardcoded flag override (or gate by environment policy)
