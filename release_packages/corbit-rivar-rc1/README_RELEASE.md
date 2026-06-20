# Corbit Rivar RC1 Controlled Release Package

This package is prepared for controlled rollout and pilot sign-off.

## Package Contents

- `manifest.json`: release metadata and included artifact list
- `RELEASE_NOTES.md`: business + technical release summary
- `KNOWN_LIMITATIONS.md`: accepted limitations for RC1
- `POST_DEPLOY_SMOKE_CHECKLIST.md`: required post-deploy checks
- `CHECKSUMS.sha256`: hashes for package integrity checks
- `update_package/`: update package snapshot including update files
- `deployment_scripts/`: deployment, backup, and restore scripts

## Pre-Deployment Requirements

1. Take a database backup before applying updates.
2. Confirm Docker is healthy and compose services are running.
3. Confirm target environment branch/commit matches approved baseline.

## Deployment (Linux)

Use:

- `deployment_scripts/linux/update-deployed-platform.sh`

Expected behavior:

- detects DB service (`postgres` or `db`)
- requires backup success before apply
- aborts on backup failure
- applies update files and restarts services

## Deployment (Windows)

Use:

- `deployment_scripts/windows/update-deployed-platform.bat`

Backup/restore helpers:

- `deployment_scripts/windows/backup_database.bat`
- `deployment_scripts/windows/restore_database.bat`

## Backup/Restore Instructions

### Backup

- Linux: run hardened update script backup step or manually use `pg_dump` in compose DB service.
- Windows: run `backup_database.bat`.

### Restore

- Windows: run `restore_database.bat`.
- Linux (manual): `docker compose exec -T <db_service> psql -U postgres -d procurement_dss < <backup.sql>`

## Rollback Instructions

1. Stop services without deleting volumes.
2. Restore code from code backup archive.
3. Rebuild/start services.
4. Restore DB from backup SQL only if required.
5. Re-run post-deploy smoke checklist.

Important: do not use `docker compose down -v` for rollback in controlled rollout.
