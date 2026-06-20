# Corbit Rivar RC1 Release Notes

Release candidate: `RC1`  
Branch: `restart/baseline-before-github-push`

## Product Summary

This release candidate provides a stabilized procurement decision-support flow with package/sub-item coverage controls, procurement execution tracking, operational finance compatibility, cashflow visibility, audit traceability, and hardened update safety procedures.

## Major Completed Capabilities

1. Package/Sub-item procurement flow:
   - master item decomposition to sub-items
   - package-level coverage computation
   - lock rejection for incomplete required coverage
   - lock success for complete required coverage
2. Procurement execution tracking:
   - locked decisions visible in procurement plan
   - delivery confirmation and PM acceptance lifecycle
3. Operational finance compatibility:
   - invoice and payment-in flows
   - supplier payment-out by decision flow
   - package/supplier context carried into operational responses
4. Cashflow/dashboard/report visibility:
   - inflow/outflow events reflected in reporting paths
5. Audit coverage:
   - key decision and lifecycle actions tracked
6. Update safety hardening:
   - backup success gate
   - backup failure abort behavior
   - service-name-safe DB handling (`postgres` / `db`)
7. Demo dataset tooling:
   - deterministic `DEMO_RC8_` create/cleanup script
   - repeatable UAT and demo readiness path

## Upgrade Notes

- Prepare backup before any apply (`pg_dump` via validated update path).
- Use hardened update scripts only:
  - `scripts/linux/deployment/update-deployed-platform.sh`
  - `scripts/windows/deployment/update-deployed-platform.bat`
- Avoid destructive update commands that remove volumes.
- Validate post-update with health/tests/build smoke gates.

## Rollback Notes

- If apply fails after backup creation:
  1. restore code from code backup archive
  2. rebuild/restart containers without volume deletion
  3. restore DB from backup SQL if needed
- Do not use `docker compose down -v` for rollback.

## Known Limitations

- Frontend still contains pre-existing eslint warnings outside release-blocking scope.
- Backend test output still includes deprecation warnings.
- Some legacy docs/scripts may still contain historical examples; use hardened paths in release package.

## Recommended Release Posture

Current sign-off target for this RC: `APPROVED FOR PILOT` after Phase 10 verification and controlled package preparation.
