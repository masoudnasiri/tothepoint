# Corbit Rivar RC1 Release Notes

## Summary

RC1 delivers a stabilized package-aware procurement flow with operational finance compatibility, audit traceability, demo tooling, and hardened update safety.

## Included Capabilities

- package/sub-item procurement with coverage validation
- decision lock fail/pass controls based on required coverage
- procurement execution lifecycle visibility (delivery + PM acceptance)
- invoice/payment-in and supplier payment-out compatibility with decision context
- cashflow/report/dashboard visibility for finance events
- audit log coverage for key lifecycle actions
- deterministic demo dataset create/cleanup tooling
- validated backup/update safety gates from Phase 7

## Verification Snapshot

- Docker/health: pass
- Backend tests: `39 passed, 4 skipped, 38 warnings`
- Phase 8 smoke: `3 passed, 20 warnings`
- Frontend build: success (`Compiled with warnings`)
- Demo cleanup verification: pass (`DEMO_RC8_` rows removed)

## Upgrade Notes

- use hardened update scripts only
- verify backup artifact is non-empty before apply
- avoid destructive volume deletion during rollout

## Rollback Notes

- restore code backup
- restart services without `down -v`
- restore DB backup when required

## Known Limitations

See `KNOWN_LIMITATIONS.md`.
