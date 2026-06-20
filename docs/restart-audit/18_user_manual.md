# Rivar User Manual

## Purpose

This guide is for daily end users of Rivar (PMO, Project Manager, Procurement, Finance, and Management viewers).  
It explains how to use the existing workflows in the current codebase without technical setup steps.

## Access and Login

1. Open the frontend URL in your browser (example: `http://localhost:3000` in local mode).
2. Login with your assigned username/password.
3. Based on your role, available pages and actions are different.

## Main Navigation

- `Dashboard`: high-level metrics and recent status.
- `Projects`: create/manage projects and open project item lists.
- `Project Items`: define item requirements for each project.
- `Procurement`: manage supplier options and package procurement.
- `Procurement Plan`: track delivery confirmation and PM acceptance.
- `Finance`: invoice/payment entry and optimization actions.
- `Decisions`: proposed/locked/reverted decisions.
- `Reports` and `Analytics`: cashflow and summary views.
- `Suppliers`: supplier registry and management.
- `Audit Logs`: trace key logged actions.

## Core Workflow (Recommended Order)

1. Define or update `Projects`.
2. Add `Project Items`.
3. (Package mode) define sub-items/components and supplier packages.
4. Add procurement options and delivery options.
5. Run optimization / select proposal.
6. Save decisions, then finalize (lock) approved decisions.
7. Track delivery in `Procurement Plan`.
8. Enter invoices and payments in `Finance`.
9. Verify outcomes in dashboard/reports.

## Package/Sub-item Workflow

### Step 1: Build item breakdown

- Go to `Project Items`.
- Add parent item and required sub-items (quantities and requirements).

### Step 2: Define supplier packages

- Go to `Procurement`.
- Use package wizard to create:
  - full package (covers all sub-items), or
  - partial package (covers subset).

### Step 3: Validate coverage before lock

- If required components are not fully covered, decision lock is rejected.
- Complete coverage allows decision finalization.

## Procurement Plan Operations

For locked decisions:

- Procurement confirms delivery (`confirm-delivery` action).
- PM accepts delivery (`accept-delivery` action).
- Status updates through:
  - `AWAITING_DELIVERY`
  - `CONFIRMED_BY_PROCUREMENT`
  - `DELIVERY_COMPLETE`

## Finance Operations

- Invoice entry uses existing invoice/payment simple flow.
- Supplier payments can be recorded from supplier payment screens.
- Customer payment-in and supplier payment-out affect cashflow reporting.
- Package/supplier traceability fields are now available in operational responses (Phase 6A hardening).

## Status Meanings

- Decision status:
  - `PROPOSED`: generated/saved, not locked.
  - `LOCKED`: finalized and execution-tracked.
  - `REVERTED`: reverted by finance flow.
- Payment status in procurement plan:
  - `not_paid`, `partially_paid`, `fully_paid`.

## Common User Checks

- Confirm decision is `LOCKED` before execution tracking.
- Confirm package coverage is complete before lock.
- Confirm invoice/payment entries appear in dashboard/reports.
- Confirm supplier and package context appears in finance-related records.

## Troubleshooting (User Level)

- If you cannot see expected actions, check your role permissions.
- If a record does not appear, refresh filters (project, status, date ranges).
- If lock fails, inspect package coverage completeness.
- If finance status looks stale, verify invoice/payment was submitted successfully.

## Do and Don't

- Do keep decision notes meaningful for audit traceability.
- Do use package mode consistently for package-based projects.
- Do verify project selection before creating options/payments.
- Don't create duplicate supplier/payment records for same transaction.
- Don't finalize decisions before coverage validation passes.

## Related Technical References

- `docs/restart-audit/06_api_frontend_flow_map.md`
- `docs/restart-audit/14_existing_operational_modules_regression_audit.md`
- `docs/restart-audit/17_phase6a_operational_compatibility_hardening.md`
