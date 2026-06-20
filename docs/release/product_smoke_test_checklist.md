# Product Smoke Test Checklist (Phase 8 RC)

Use this checklist after deployment/update and before business demo.

## Access and Core Loading

- [ ] Login page loads.
- [ ] Valid user login works.
- [ ] Dashboard loads without crash.
- [ ] Projects page loads.

## Project / Item / Package Flow

- [ ] Open a project and list project items.
- [ ] Open project item details (including sub-items if decomposed).
- [ ] Package wizard opens.
- [ ] Package list renders and supports refresh.
- [ ] Coverage summary opens and shows data.

## Decision Lock Behavior

- [ ] Incomplete package coverage lock attempt fails with validation error.
- [ ] Complete package coverage lock attempt succeeds.
- [ ] Locked decision is visible in procurement plan.

## Procurement Plan Lifecycle

- [ ] Procurement can confirm delivery.
- [ ] PM can accept delivery.
- [ ] Delivery status transitions are correct.

## Finance and Payments

- [ ] Invoice entry works.
- [ ] Customer payment-in entry works.
- [ ] Supplier payment-out entry works.
- [ ] Decision/package/supplier traceability fields are visible in finance responses/UI where expected.

## Cashflow / Reporting

- [ ] Dashboard reflects new finance actions.
- [ ] Reports/analytics reflect inflow/outflow records.
- [ ] No obvious mismatch between decision state and payment status.

## Audit / Traceability

- [ ] Audit log page loads.
- [ ] At least one recent lifecycle/finance action is present in audit logs.

## Update and Data Safety

- [ ] Pre-update DB backup was created.
- [ ] Backup artifact is non-empty.
- [ ] Update script safety gate aborts on backup failure (verified in dry-run evidence).
- [ ] Update process did not use `docker compose down -v`.

## Infrastructure Health

- [ ] `docker compose ps` shows healthy backend/postgres.
- [ ] `GET /health` returns healthy.
- [ ] Backend tests pass.
- [ ] Frontend build succeeds.
