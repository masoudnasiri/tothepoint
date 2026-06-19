# Rivar Restart Audit - Phase 4 Deployment/Update Safety Report

## Scope

Phase 4 focused on deployment/update safety hardening before server packaging, with two explicit goals:

1. Fix database service-name mismatch in update scripts.
2. Enforce backup verification so updates cannot continue without a valid backup.

## Findings (Before Fix)

- `docker-compose.yml` defines database service as `postgres`.
- Update scripts used `docker-compose exec -T db ...` for backups.
- If backup failed, scripts only printed warnings and continued update flow.
- This created a data-loss risk: platform update could proceed without a usable backup.

## Implemented Fixes

### 1) Service-name mismatch fixed

Updated scripts now auto-detect DB service from compose config:

- prefer `postgres`
- fallback to `db`
- abort if neither exists

Files updated:

- `update-deployed-platform.sh`
- `update-deployed-platform.bat`

### 2) Backup verification enforcement

Both update scripts now fail fast before applying updates unless backup is verified:

- ensure Docker is running
- ensure DB service is running
- wait for DB readiness (`pg_isready`)
- run `pg_dump`
- verify DB backup file exists and is non-empty
- create code backup archive
- verify code backup file exists and is non-empty
- abort update if any backup check fails

### 3) Documentation alignment

Updated guide examples to use correct service name and reflect safer behavior:

- `PLATFORM_UPDATE_GUIDE.md`
  - replaced `db` service examples with `postgres`
  - added note that scripts auto-detect DB service and verify backups

## Non-Destructive Validation

Commands run:

- `bash -n update-deployed-platform.sh`
  - result: PASS (syntax valid)
- `docker-compose config --services`
  - result: PASS
  - output includes: `postgres`, `backend`, `frontend`

Manual static checks:

- no hardcoded `exec -T db` remains in `update-deployed-platform.sh`
- no hardcoded `exec -T db` remains in `update-deployed-platform.bat`

## Outcome

Phase 4 deployment/update safety hardening is complete for the primary root update scripts:

- service mismatch risk removed
- update now blocked unless backups are actually valid
- rollback guidance includes explicit optional DB restore command

This materially reduces accidental zero-backup updates and aligns with the zero-data-loss update requirement.
