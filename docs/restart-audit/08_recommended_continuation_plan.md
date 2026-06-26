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

---

## Standing Documentation Governance Rule (Mandatory)

Every sprint that changes product or software behavior must update `docs/restart-audit` as an in-scope deliverable.

Minimum required sprint documentation content:

1. sprint name and date
2. business/product purpose
3. changed behavior
4. changed API endpoints
5. changed data model/schema fields
6. changed backend services/routers
7. changed frontend behavior (or explicit no-change statement)
8. tests added/updated and result summary
9. deployment notes
10. known risks/technical debt
11. rollback notes (if relevant)
12. exact sprint status: `PASS`, `PASS WITH MINOR ISSUES`, or `FAIL`

If a sprint changes code but does not update `docs/restart-audit`, that sprint is treated as incomplete.

---

## Current Sprint Pointer

- Sprint 3C: Candidate Validation & Coverage Engine (`PASS WITH MINOR ISSUES` after QA)
- Sprint 3C-Fix: Release Hygiene Closure (`PASS`, no redeploy required; scope-clean artifact/runtime verified)
- Sprint 3D: Financial Projection Engine (`PASS WITH MINOR ISSUES` after QA)
- Sprint 3D-Fix: Projection Contract Hardening + Stable QA Dataset (`PASS`, no code redeploy required)
- Sprint 4A: Optimization Scenario Preview Engine (`PASS`, read-only scenario preview endpoints + tests + ADR-009)
- Sprint 4A-Clean Installer + Fresh Demo Reinstall (`PASS`, official demo path `/opt/rivar-demo`, installer-driven deployment/verification baseline)
- Sprint 4A-Workspace Organization (`PAUSED AFTER INITIAL PASS`, frozen until accepted UI inventory remains green)
- Sprint 4A-UI Regression Recovery (`PASS`, restored accepted Payment Methods visibility in Master Data and redeployed via clean installer flow)
- Sprint 3A-R1: Package Wizard Step 3 Recovery (`PASS WITH MINOR ISSUES`, layout recovered and redeployed; follow-up contract restoration required)
- Sprint 3A-R2: Payment and Cost Contract Restoration (`PASS WITH MINOR ISSUES`, payment terms/discount/base-price default restored; runtime deployment smoke required per sprint checklist)
- Sprint 3A-R3: Cost-Level Payment Schedule + Save/Verify Stability (`PASS`, original closure `23be386`; superseded as live baseline by hotfix chain `743a19b` + `6f9e944` + closure provenance in `53_sprint3a_r3_hotfix_closure_router_i18n_runtime.md`)
- Sprint 3A-R3 terminology follow-up (`743a19b`): schedule-oriented Step 3 labels; no enum/persistence/logic change
- Sprint 3A-R3 hotfix router registration (`6f9e944`): `procurement_financials.router` registered in `main.py`
- Sprint 3A-R3 hotfix closure (`PASS`, `53_*`): R3 `verify_runtime_r3.py`, installer `verify.sh` SPA Accept fix, `/opt/rivar-demo` runtime verify PASS; **accepted R3 baseline = `07b56f24` on `recovery/sprint3a-r3-cost-level-payment-schedule`**
- Sprint 4A Workspace Organization from R3 hotfix baseline (`PASS WITH MINOR ISSUES`, `54_*` / `55_*`): branch `restart/workspace-organization-after-sprint3a-r3-hotfix`; root `.tmp_*` scratch archived to gitignored `oldfiles/qa-temp/`; no product code changes
- Sprint 5A Access Control & Procurement Assignment Architecture (`PASS`, `56_*` / ADR-011): branch `restart/sprint5a-access-control-procurement-assignment-architecture`; docs-only; RBAC + assignment target model defined
- Sprint 5B Backend RBAC Foundation (`PASS WITH MINOR ISSUES`, `57_*`): branch `restart/sprint5b-backend-rbac-foundation` @ `445606edcfd9ec9d27be3e31ebdd2905966552a1`; RBAC tables, registry, APIs, `/auth/me` permissions, lockout protection; enforcement flag off; demo `verify.sh` blocked by missing `payment_metadata` on persisted Postgres volume
- Sprint 5B-R1 Demo DB Migration and Runtime Closure (`PASS WITH MINOR ISSUES`, `58_*`): branch `restart/sprint5b-r1-demo-runtime-closure` @ `fb9336e20d1d461e9db1e6f5ac5c151abf57340f`; applied canonical R3 `payment_metadata` migration on `/opt/rivar-demo`; installer `apply_r3_schema_migrations.sh` wired into install/verify; `verify.sh` PASS; R3 + RBAC runtime smoke PASS
- Sprint 5C Role Management Frontend (`PASS WITH MINOR ISSUES`, `59_*`): branch `restart/sprint5c-role-management-frontend`; Access Control page, permission helper, route guard, i18n; demo verify + RBAC/R3 smoke PASS
- Next planned work: Sprint 5D Procurement Assignment Backend
