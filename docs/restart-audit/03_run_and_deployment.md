# Rivar Restart Audit - Run and Deployment

## 1) How the System Runs (Verified)

## Runtime Source of Truth

- `docker-compose.yml` is the active runtime definition.
- Backend starts from `backend/app/main.py` and creates tables on startup (`init_db`).
- Seed flow executes on startup (`seed_sample_data`) and skips reseed when users already exist.

## Local Start/Stop Commands (Current Repo)

- Windows:
  - `start.bat` (safe mode, preserves data)
  - `stop.bat` (uses `docker-compose down`, preserves volumes)
  - `backup_database.bat` / `restore_database.bat`
- Linux/macOS:
  - `start.sh` (does `docker-compose down` then `docker-compose up --build -d`)
  - `stop.sh`

## Backend Start Mode

- Docker command in compose:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop asyncio`
- Local dev mode documented:
  - `uvicorn app.main:app --reload` (in `backend/`)

## Frontend Start/Build Mode

- Dev start: `npm start` (`react-scripts start`)
- Production build: `npm run build` (`react-scripts build`)

## Database Initialization and Seeding

- `backend/init.sql` is intentionally minimal; table creation is done by SQLAlchemy startup.
- `backend/app/database.py` calls `Base.metadata.create_all`.
- `backend/app/seed_data.py` creates default users/projects/items/etc only when DB has no users.

## Migrations

- No `alembic.ini` or `alembic/` folder found in this repo snapshot.
- Migration strategy is SQL-script based:
  - phase 1 schema scripts (`backend/create_procurement_packages_table.sql`, `backend/add_package_id_columns.sql`, etc.)
  - phase 2 data migration scripts (`backend/create_full_packages_for_project_items.sql`, `backend/populate_package_subitems.sql`, etc.)
  - execution wrappers (`backend/execute_phase1_migrations.sh`, `backend/run_phase2_data_migration.sh`, PowerShell variants)

## Required Environment Variables (Observed)

From `docker-compose.yml` and `backend/app/config.py`:

- `DATABASE_URL`
- `SECRET_KEY`
- `ENVIRONMENT`
- `DEBUG`
- `ALLOWED_ORIGINS`
- feature flags:
  - `ENABLE_PACKAGE_PROCUREMENT`
  - `LEGACY_PROJECT_ITEM_FALLBACK`
  - `SUPPLIER_NORMALIZATION_ENFORCED`
  - `ENABLE_PACKAGE_BASED_OPTIMIZATION`
  - `REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS`

## Default/Admin Users

Seeded in `backend/app/seed_data.py`:

- `admin / admin123`
- `pmo1 / pmo123`
- `pm1 / pm123`
- `proc1 / proc123`
- `finance1 / finance123`

## Safest Local Run Procedure (Recommended for Restart)

1. Verify Docker engine is running.
2. Confirm no destructive command is used (`docker-compose down -v` only when explicit reset is intended).
3. Run backup before risky testing:
   - Windows: `backup_database.bat`
4. Start using `start.bat` (Windows) to avoid accidental volume deletion and to keep restart behavior explicit.
5. Validate health:
   - `docker-compose ps`
   - backend health: `/health`
6. If phase migrations are required for package rollout, execute phase scripts in non-production clone first.

---

## Deployment and Update Mechanism: Data Safety Assessment

## Installation/Packaging Folders

- Installation package generators:
  - `installation_packages/create_deployment_package.bat`
  - `installation_packages/create_windows_installer_package.bat`
  - `installation_packages/create_linux_installer_package.sh`
- Prebuilt installer packages:
  - `installation_packages/pdss-linux-v1.0.0/`
  - `installation_packages/PDSS_Windows_v1.0.0_202511051521/`
- Update packages:
  - `update_package/`
  - `pdss-update-v1.0.2-COMPLETE/`

## How Updates Are Applied

- Update scripts (`update-deployed-platform.sh/.bat`) expect a deployed folder (`~/pdss` etc.).
- They copy changed files from sibling `update_files/backend` and `update_files/frontend` into deployment.
- They stop platform (`docker-compose down`), rebuild images (`docker-compose build --no-cache`), and start again (`docker-compose up -d`).

## Rebuild vs Pull

- Current update scripts rebuild local images; they do not primarily pull versioned app images from registry.
- Base images may be pulled by Docker as part of build.

## Database Volume Preservation

- Standard stop/update paths use `docker-compose down` (without `-v`), which preserves named DB volume.
- Explicit reset scripts (`reset.bat`, uninstall scripts) do use `down -v` and are destructive by design.

## Migration Execution During Update

- No automatic migration hook is wired into compose startup.
- Migration scripts are present but manual/explicit execution is required.

## Backup Behavior Before Update

- Update scripts attempt DB backup and code backup into `~/pdss_backups`.
- Critical issue: scripts use `docker-compose exec ... db ...` while compose service is named `postgres` in this repo and installation package compose files.
- Result: backup command can fail silently/warning and script continues.

## Data-Loss Risk Assessment

### High Risk

- **Backup false-positive risk:** update scripts may print backup warnings and proceed, leaving no verified DB backup.
- **Service-name mismatch risk (`db` vs `postgres`):** affects backup and staged startup steps in installer/update scripts.
- **Destructive troubleshooting guidance risk:** some docs suggest `docker-compose down -v` as fallback, which destroys persisted DB data.

### Medium Risk

- **No enforced pre-update backup verification:** update continues even if backup fails.
- **No automatic rollback orchestration:** rollback instructions exist but are manual.
- **No migration gate:** data and code version drift can happen if migration scripts are skipped.

### Lower Risk / Positive Controls

- `stop.bat` and normal update path avoid `-v`.
- Named Docker volume is used for PostgreSQL persistence.
- Dedicated backup and restore scripts exist in root for Windows operators.

## Files/Scripts Most Relevant to Zero-Data-Loss Behavior

Positive/intentional controls:

- `stop.bat` (non-destructive stop)
- `backup_database.bat`
- `restore_database.bat`
- `update-deployed-platform.sh`
- `update-deployed-platform.bat`
- `update_package/update-deployed-platform.sh`

Potentially destructive utilities (must be controlled):

- `reset.bat`
- `reset_data.sh`
- uninstall scripts in installer packages (`down -v`)

## Recommendations

1. Standardize compose DB service name across all scripts (`postgres` vs `db`) immediately.
2. Fail update if DB backup fails; do not continue on warning.
3. Add backup verification step (non-empty file, `pg_restore --list` or checksum).
4. Add mandatory preflight check for migration version and required SQL scripts.
5. Add explicit "safe mode" update script that disallows `down -v`.
6. Document a tested rollback procedure with timed recovery drill.
