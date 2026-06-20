# Post-Deploy Smoke Checklist (RC1)

Run immediately after deployment.

## Infrastructure

- [ ] `docker compose ps` shows backend and postgres healthy.
- [ ] `curl -sS http://127.0.0.1:8000/health` returns healthy.

## Core Product

- [ ] Login works.
- [ ] Dashboard loads.
- [ ] Projects and project items load.
- [ ] Procurement page and package list load.
- [ ] Coverage summary renders.

## Decision and Execution

- [ ] Incomplete coverage lock attempt fails correctly.
- [ ] Complete coverage lock succeeds.
- [ ] Locked decision appears in procurement plan.
- [ ] Delivery confirm + PM acceptance path works.

## Finance and Visibility

- [ ] Invoice entry works.
- [ ] Payment-in entry works.
- [ ] Supplier payment entry works.
- [ ] Cashflow/report reflects recent finance events.
- [ ] Audit log contains lifecycle/finance actions.

## Build and Tests

- [ ] `docker compose run --rm backend python -m pytest tests -q` passes.
- [ ] `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q` passes.
- [ ] `docker compose run --rm frontend npm run build` succeeds.

## Data Safety

- [ ] Backup artifact exists and non-empty before update.
- [ ] Rollback command path is available and validated.
