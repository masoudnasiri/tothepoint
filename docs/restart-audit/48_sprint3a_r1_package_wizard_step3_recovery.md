# Sprint 3A-R1 - Package Wizard Step 3 Recovery

Date: 2026-06-25

## Sprint Name

Sprint 3A-R1 — Recover, Commit, and Deploy Package Wizard Step 3 Simplification

## Root Cause

- Prior frontend artifact packaging was partial and excluded `frontend/src/components/PackageWizard/PackageWizardStep3.tsx`.
- This produced a mixed/stale deployed wizard experience, even though backend readiness endpoints remained current.
- Forensic evidence indicated intended Step 3 simplification existed in working tree but was not safely captured as a clean, scoped recovery commit/deploy chain.

## Recovery Action

- Preserved pre-recovery working-tree evidence snapshots under `oldfiles/recovery/sprint3a_r1/`.
- Recovered and committed the intended Step 3 simplified structure with the three user-facing sections:
  1. Pricing and Costs
  2. Delivery
  3. Payment
- Removed legacy Step 3 header markers (`Metadata`, `Quantities`, `Pricing & Delivery`) from the active Step 3 view to align runtime UX with recovery acceptance criteria.
- Ensured recovery artifact manifest explicitly includes `PackageWizardStep3.tsx` and related scoped frontend files.

## QA Evidence Required Before Acceptance

1. Focused Package Wizard tests pass.
2. Frontend test suite passes (or pre-existing failures are clearly separated).
3. Build succeeds for frontend recovery scope.
4. Artifact manifest proves inclusion of:
   - `frontend/src/components/PackageWizard/PackageWizardStep3.tsx`
   - `frontend/src/components/PackageWizard/PackageWizard.tsx`
   - any other changed scoped frontend files
5. Deployed UI smoke confirms Step 3 shows:
   - Pricing and Costs
   - Delivery
   - Payment
6. Deployed Step 3 no longer renders old Step 3 layout sections:
   - Metadata
   - Quantities
   - Pricing & Delivery
7. Save flow still persists:
   - `payment_method_id`
   - `planned_supplier_payment_date`
   - `supplier_actual_delivery_date`
8. Backend readiness endpoint remains available post-deploy.

## Deployment Hygiene Reminder

Future deployment artifacts must include all directly affected component files, not only parent/container files. Incomplete frontend component inclusion is treated as release-blocking.
