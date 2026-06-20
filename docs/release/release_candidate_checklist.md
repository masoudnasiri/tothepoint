# Release Candidate Checklist (Phase 8)

## Release Identification

- Branch: `restart/baseline-before-github-push`
- Baseline commit before Phase 8: `751bb1f`
- Candidate commit: _(updated at commit time)_

## Required Command Gates

### Docker / Health

- Command: `docker compose ps`
- Result: pass (`backend` healthy, `postgres` healthy, `frontend` up)

- Command: `curl -sS http://127.0.0.1:8000/health`
- Result: pass (`{"status":"healthy","version":"1.0.0"}`)

### Backend Tests

- Command: `docker compose run --rm backend python -m pytest tests -q`
- Result: pass (`39 passed, 4 skipped, 38 warnings`)

### Phase 8 Smoke Test

- Command: `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`
- Result: pass (`3 passed, 20 warnings`)

### Frontend Build

- Command: `docker compose run --rm frontend npm run build`
- Result: pass (`Compiled with warnings`)

## Update/Backup Safety Gates

- [x] Backup preflight success verified
- [x] Backup failure abort behavior verified
- [x] Staged apply rehearsal on cloned path verified
- [x] Rollback commands validated

## Demo Readiness

- Demo dataset creation command:
  - `python scripts/create_demo_dataset.py --mode create`
- Demo dataset creation result: pass (`DEMO_RC8_` data created; lock fail/pass validation true)
- Demo cleanup command:
  - `python scripts/create_demo_dataset.py --mode cleanup`
- Demo cleanup result: pass (tagged rows removed; DB check counts returned 0)

- Demo runbook present:
  - `docs/release/demo_script_phase8.md`
- Product smoke checklist present:
  - `docs/release/product_smoke_test_checklist.md`

## Manual Smoke Test Summary

- Manual run date: 2026-06-20
- Scope used: `docs/release/product_smoke_test_checklist.md`
- Outcome: partial (automated/infra gates passed; full business UI walkthrough remains for product reviewers)

## Known Limitations

- Existing frontend eslint warnings remain (build is green).
- Existing backend deprecation warnings remain in pytest output.
- Legacy docs/scripts may still contain historical examples outside hardened paths.

## Release Decision

- [x] Ready for RC demonstration
- [ ] Not ready (blocking issues documented)
