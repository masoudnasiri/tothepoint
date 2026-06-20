# Phase 7 - Update Safety Hardening (Closed)

## Scope of this increment

Started the next post-Phase-6A phase by addressing the highest operational risk from `08_recommended_continuation_plan.md`:

- update scripts proceeding despite failed backups,
- inconsistent database service naming (`db` vs `postgres`) in distributed update artifacts.

## Changes implemented

### 1) Hardened packaged Linux update scripts

Updated both distributed updater copies to fail safely:

- `update_package/update-deployed-platform.sh`
- `pdss-update-v1.0.2-COMPLETE/update-deployed-platform.sh`

Applied improvements:

- `set -euo pipefail`
- database service auto-detection (`postgres` fallback to `db`)
- explicit DB readiness wait using `pg_isready`
- backup failure is blocking (update aborts)
- backup artifact non-empty validation
- safer copy behavior (`cp -a .../.`)
- rollback instructions include DB restore command with detected DB service

### 2) Hardened installer package generator backup template

Updated generated `scripts/backup.sh` template in:

- `installation_packages/create_linux_installer_package.sh`
- `installation_packages/create_linux_installer_package.ps1`

Template now:

- detects DB service (`postgres` or `db`),
- fails on backup errors,
- verifies backup file is not empty.

### 3) Reduced unsafe manual instructions in update package docs

Updated:

- `update_package/README.txt`
- `pdss-update-v1.0.2-COMPLETE/README.txt`

Changes:

- manual backup command now uses service detection snippet,
- troubleshooting "force complete rebuild" changed from destructive `docker-compose down -v` to non-destructive `docker-compose down`.

## Verification notes

- Changes are script/documentation hardening updates (no backend/frontend runtime behavior change).
- PowerShell parser compatibility remains unchanged (Windows update script already had service detection and backup-fail behavior from previous hardening).

## Dry-run validation on Linux server

Validation target:

- Host: `193.162.129.58`
- Active deploy: `/root/pdss`

### A) Real preflight backup validation (live environment, non-disruptive)

Executed dry-run preflight steps mirroring updater backup section:

1. Detect DB service from compose (`postgres`/`db`)
2. Verify DB container status and readiness (`pg_isready`)
3. Run `pg_dump` backup to `/root/pdss_backups/dryrun_backup.sql`
4. Verify backup artifact is non-empty

Observed evidence:

- `DB_SERVICE=postgres`
- postgres service healthy
- `pg_isready` accepted connections
- backup file created and non-empty (`247K`)

Result: **PASS** (backup preconditions and backup artifact checks work on real server).

### B) Simulated backup-failure abort test (isolated mocked environment)

To safely prove fail-fast behavior without impacting live services, ran updater in an isolated mocked runtime on the server:

- mocked `docker-compose` returned failure for `pg_dump`
- updater output contained:
  - `Database backup failed; update aborted.`
- process exit code was non-zero (`1`)
- updater did **not** reach apply stage (`APPLYING UPDATE` absent)

Result: **PASS** (hardened updater aborts before any apply action when backup fails).

## Staged apply rehearsal (cloned path)

### Rehearsal method

- Staging clone path: `/root/pdss_phase7_staging`
- Target server: `193.162.129.58`
- Safety isolation:
  - distinct compose project name: `pdss_phase7_staging`
  - staging host ports rewritten in staging compose:
    - backend `18000:8000`
    - frontend `13000:3000`
    - postgres `15432:5432`
  - live `/root/pdss` was not used for staged apply.
- Hardened updater executed against staging by isolated `HOME` mapping:
  - `HOME=/root/phase7_home`
  - `~/pdss` symlinked to `/root/pdss_phase7_staging`
  - `~/update_files` populated with staging marker files

### Commands (high level)

1. Clone and stage setup
   - `rsync -a --delete /root/pdss/ /root/pdss_phase7_staging/`
   - rewrite staging port bindings in `/root/pdss_phase7_staging/docker-compose.yml`
2. Baseline startup
   - `COMPOSE_PROJECT_NAME=pdss_phase7_staging docker-compose up -d`
   - health check: `curl http://127.0.0.1:18000/health`
3. Baseline DB value capture
   - user count before update (`SELECT COUNT(*) FROM users;`)
4. Run hardened updater on staging
   - `HOME=/root/phase7_home COMPOSE_PROJECT_NAME=pdss_phase7_staging bash /root/phase7_hardened_update.sh`
5. Post-update validation
   - staging health check
   - user count after update
   - fixture markers (`PH5%`) check
   - volume persistence check via `docker volume inspect`

### Staged apply evidence

- `STAGING_DB_SERVICE=postgres`
- `USER_COUNT_BEFORE=8`
- `USER_COUNT_AFTER=8`
- `DATA_PERSISTENCE_USERS=PASS`
- `PH5_PROJECTS_BEFORE=0`, `PH5_PROJECTS_AFTER=0`
- `PH5_OPTIONS_BEFORE=0`, `PH5_OPTIONS_AFTER=0`
- `VOLUME_NAME=pdss_phase7_staging_postgres_data`
- `VOLUME_CREATED_BEFORE=2026-06-20T08:50:32Z`
- `VOLUME_CREATED_AFTER=2026-06-20T08:50:32Z`
- `UPDATE_EXIT_CODE=0`
- `UPDATE_APPLY_STAGE=PASS`
- `STAGING_BACKUP_FILE=/root/phase7_home/pdss_backups/db_backup_20260620_085157.sql` (non-empty)
- `REHEARSAL_RESULT=PASS`

Result: **PASS** (full staged apply rehearsal succeeded with non-destructive behavior and preserved data/volume state).

## Rollback validation

- DB service detection for rollback command verified:
  - `ROLLBACK_DB_SERVICE_DETECTED=postgres`
- Backup format restorable by documented command verified:
  - restored backup into temporary DB `phase7_restore_check`
  - `RESTORE_USER_COUNT=8`
  - `ROLLBACK_RESTORE_FORMAT=PASS`
- Verified updater rollback guidance has no destructive volume deletion:
  - `ROLLBACK_NO_DOWNV=PASS`

Result: **PASS**

## Live deployment post-rehearsal verification

Live target: `/root/pdss`

1. `docker compose ps`
   - backend/frontend/postgres all healthy/up.
2. `curl -sS http://127.0.0.1:8000/health`
   - `{"status":"healthy","version":"1.0.0"}`
3. `docker compose run --rm backend python -m pytest tests -q`
   - `36 passed, 4 skipped, 37 warnings`
4. `docker compose run --rm frontend npm run build`
   - build succeeded (compiled with pre-existing eslint warnings).

Result: **PASS**

## Status after dry-run and staged apply

- Backup-fail hard stop behavior: **verified**
- DB service name auto-detection safety (`postgres`/`db`): **verified**
- Backup artifact integrity gate (non-empty): **verified**
- Full staged apply rehearsal on cloned path: **verified**
- Live environment health after rehearsal: **verified**

## Remaining limitations / risks

- Legacy docs/scripts outside the hardened set may still reference historical `db` examples; continue cleanup over time.
- Frontend build still reports large existing eslint warning set (non-blocking for Phase 7 safety objective).

## Phase 7 final status

- **Phase 7 status: CLOSED**
