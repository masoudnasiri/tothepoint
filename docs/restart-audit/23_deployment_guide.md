# Rivar Deployment Guide

## Scope

This guide describes practical deployment and update steps for the current Rivar codebase with a focus on zero-data-loss operations.

## Deployment Model

- Runtime is Docker Compose based (`docker-compose.yml`).
- Main services:
  - `postgres`
  - `backend`
  - `frontend`
- Persistent data:
  - PostgreSQL named volume (`postgres_data`)
  - uploads volume (`uploads_data`)

## Prerequisites

- Docker and Docker Compose installed on target host
- Access to project source/update bundle
- `.env` values prepared for target environment
- Network/firewall open for required ports

## First-Time Deployment (Safe Baseline)

1. Place code on server.
2. Review and set environment values (DB URL, secret key, origins, feature flags).
3. Start platform:
   - `docker compose up --build -d`
4. Verify:
   - `docker compose ps`
   - `curl http://127.0.0.1:8000/health`
5. Open frontend and verify login flow.

## Update Deployment (Recommended Safe Procedure)

1. Announce maintenance window.
2. Create and verify DB backup.
3. Apply updated files/bundle.
4. Restart/rebuild without deleting volumes:
   - `docker compose down`
   - `docker compose up --build -d`
5. Run post-update checks:
   - health endpoint
   - auth/login
   - procurement and finance smoke path
   - dashboard/report visibility

## Database Safety Rules

- Never use `docker compose down -v` in routine update.
- Ensure backup succeeds before any migration/update.
- Keep at least one verified rollback backup archive.

Recommended backup command pattern (service-name safe):

```bash
DB_SERVICE=$(docker compose config --services | grep -E "^(postgres|db)$" | head -1)
docker compose exec -T "$DB_SERVICE" pg_dump -U postgres procurement_dss > /path/to/backup.sql
test -s /path/to/backup.sql
```

## Migration Strategy

Current repository uses SQL-script migrations (phase scripts), not Alembic.

Typical script locations:

- `backend/execute_phase1_migrations.sh` / `.ps1`
- `backend/run_phase2_data_migration.sh` / `.ps1`
- phase SQL files in `backend/*.sql`

Apply migrations explicitly and validate outputs after execution.

## Production Validation Checklist

Minimum checks after deployment:

1. `docker compose ps` shows healthy backend/postgres
2. `GET /health` returns healthy response
3. decision list and procurement plan pages load
4. one invoice/payment create flow succeeds
5. one supplier payment flow succeeds
6. dashboard/report aggregates reflect new transactions

## Rollback Plan (Basic)

If critical regression appears:

1. stop user write activity,
2. preserve current state backup,
3. restore previous code bundle,
4. restore verified DB backup if needed,
5. restart services and re-run smoke checks.

## Known Operational Risks (Current Codebase)

- Script inconsistencies in some packaging/update paths (`db` vs `postgres` naming in historical scripts).
- Backup step may be non-fatal in some scripts; enforce fail-fast in your runbook.
- Mixed legacy/package paths require post-update compatibility checks.

## Suggested Automation Improvements

- Make backup failure blocking.
- Add backup checksum/restore-list validation step.
- Add post-deploy smoke script for critical endpoints.
- Standardize compose service naming across all scripts.

## Related Documents

- `docs/restart-audit/03_run_and_deployment.md`
- `docs/restart-audit/12_deployment_update_safety_report.md`
- `docs/restart-audit/16_phase5_end_to_end_completion_report.md`
- `docs/restart-audit/17_phase6a_operational_compatibility_hardening.md`
