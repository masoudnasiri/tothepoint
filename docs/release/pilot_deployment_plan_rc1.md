# Pilot Deployment Plan - RC1

## Pilot Environment Assumptions

- Target is a controlled non-production or pilot-designated environment.
- Docker Compose deployment model is available.
- Backup storage location is writable and monitored.
- Pilot user group is limited and pre-briefed.

## Pre-Deploy Backup Steps

1. Confirm compose services and DB container health.
2. Run DB backup (`pg_dump`) and verify backup file is non-empty.
3. Save code snapshot/archive before apply.
4. Record deployment baseline:
   - branch/commit
   - timestamp
   - service status

## Deployment / Update Steps

1. Place approved release package artifacts on target host.
2. Use hardened update script from package:
   - Linux: `deployment_scripts/linux/update-deployed-platform.sh`
   - Windows: `deployment_scripts/windows/update-deployed-platform.bat`
3. Ensure update does not use destructive volume deletion.
4. Start/restart services and verify health endpoint.

## Post-Deploy Smoke Checklist

Use: `release_packages/corbit-rivar-rc1/POST_DEPLOY_SMOKE_CHECKLIST.md`

Minimum must-pass gates:

- backend health
- login/dashboard/projects/procurement
- lock fail/pass behavior
- procurement plan visibility
- invoice/payment/supplier payment flow
- audit visibility

## Rollback Plan

1. Stop services without deleting volumes.
2. Restore code backup.
3. Rebuild/restart services.
4. Restore DB backup if data rollback is required.
5. Re-run smoke checks to confirm recovery.

## Pilot User Roles

- Admin (system-level checks)
- Procurement user (package/decision lifecycle)
- Finance user (invoice/payment/supplier payment)
- PM user (delivery acceptance)
- Business owner (final acceptance viewpoint)

## Monitoring Window

- Suggested minimum: 5-10 business days.
- Monitor:
  - availability/health checks
  - critical workflow completion
  - pilot user defect log
  - rollback trigger indicators

## Success Criteria

- No blocker defects in pilot-critical flows.
- End-to-end package-aware procurement flow works for pilot scenarios.
- Finance/cashflow/audit visibility remains consistent.
- No data-loss incidents during update/operation.

## Go / No-Go Criteria After Pilot

- Go to production approval when:
  - pilot state is `PILOT PASSED` or `PILOT PASSED WITH LIMITATIONS` with accepted limitations.
- No-go / rollback when:
  - pilot state is `PILOT FAILED / ROLLBACK REQUIRED`.

## Pilot Decision States

- `PILOT STARTED`
- `PILOT PASSED`
- `PILOT PASSED WITH LIMITATIONS`
- `PILOT FAILED / ROLLBACK REQUIRED`
