# Phase 9 - RC UAT and Release Sign-off

## Environment Tested

- Host: `193.162.129.58` (Ubuntu)
- UAT stack path: `/root/pdss_demo`
- Compose project: `pdss_demo`
- Frontend URL: `http://193.162.129.58:13010`
- Backend URL: `http://193.162.129.58:18010`
- Branch baseline: `restart/baseline-before-github-push`
- Baseline commit under test: `ed6e5d2`

## UAT Environment Preparation Result

- Docker services healthy: pass
- Backend health endpoint healthy: pass
- Demo dataset create command executed: pass
- Demo records confirmed (`DEMO_RC8_`): pass
- Old `PH5` fixtures in UAT DB: none found (`ph5_projects_count=0`)
- Active UAT logins validated:
  - `admin/admin123`
  - `finance1/finance123`
  - `proc1/proc123`
  - `pmo1/pmo123`
  - `pm1/pm123`

## Manual Walkthrough Result

Walkthrough source: `docs/release/demo_script_phase8.md`  
Execution style: API-driven UAT probe in active demo environment.

1. Login - PASS  
2. Dashboard - PASS  
3. Projects - PASS  
4. Project item and sub-item breakdown - PASS  
5. Supplier packages - PASS  
6. Package coverage - PASS  
7. Incomplete coverage lock rejection - PASS  
8. Complete coverage lock success - PASS  
9. Procurement plan visibility - PASS  
10. Delivery confirmation - PASS  
11. PM acceptance - PASS  
12. Invoice/payment entry - PASS  
13. Supplier payment entry - PASS  
14. Cashflow/report/dashboard impact - PASS  
15. Audit log traceability - PASS

Screenshots: not captured in this run (N/A).

## Product Smoke Checklist Result

Checklist source: `docs/release/product_smoke_test_checklist.md`

- login: PASS
- dashboard load: PASS
- projects load: PASS
- project item creation/view: PASS
- package wizard: NOT TESTED
- coverage summary: PASS
- decision lock fail/pass: PASS
- procurement plan visibility: PASS
- delivery confirm: PASS
- PM acceptance: PASS
- invoice/payment entry: PASS
- supplier payment entry: PASS
- cashflow/report visibility: PASS
- audit log entries: PASS
- backup before update: PASS (Phase 7 accepted evidence)
- update safety gate: PASS (Phase 7 accepted evidence)

## Defects Found / Fixed / Deferred

Defect log: `docs/release/uat_defect_log_phase9.md`

- Found during Phase 9: 2
  - 1 product defect (`UAT-05`, major)
  - 1 UAT harness path issue (`UAT-12`, non-product)
- Fixed in Phase 9: 2 (including harness correction)
- Deferred: 0
- Open blockers: 0
- Open majors: 0

### Phase 9 code fix applied

- `backend/app/routers/projects.py`
  - `list_packages_by_project` now eager-loads `supplier` and `subitems` to prevent async lazy-load serialization failure (`MissingGreenlet`).

## Final Verification Commands and Results

Executed in `/root/pdss_demo` (`COMPOSE_PROJECT_NAME=pdss_demo`):

1. Docker status  
   - Command: `docker compose ps`  
   - Result: backend healthy, postgres healthy, frontend up

2. Backend health  
   - Command: `curl -sS http://127.0.0.1:18010/health`  
   - Result: `{"status":"healthy","version":"1.0.0"}`

3. Backend full tests  
   - Command: `docker compose run --rm backend python -m pytest tests -q`  
   - Result: `39 passed, 4 skipped, 38 warnings`

4. Phase 8 smoke tests  
   - Command: `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`  
   - Result: `3 passed, 20 warnings`

5. Frontend build  
   - Command: `docker compose run --rm frontend npm run build`  
   - Result: success (`Compiled with warnings`)

## Demo Cleanup Verification

1. Cleanup executed  
   - Command: `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode cleanup`  
   - Result: demo-tagged rows removed

2. Post-cleanup validation  
   - `demo_projects_count=0`
   - `demo_decisions_count=0`
   - `ph5_projects_count=0`

## Release Decision

Decision: **GO WITH KNOWN LIMITATIONS**

Known limitations:

- Frontend build still has existing eslint warnings (non-blocking).
- Backend pytest output still has existing deprecation warnings (non-blocking).
- Package wizard was not directly UI-click-tested in this run (API-backed flow validated end-to-end).

## Recommended Next Action

- Proceed to controlled release rollout and production sign-off packaging (Phase 10), with a short live UI witness session (product owner/business lead) focused on package wizard UX confirmation.
