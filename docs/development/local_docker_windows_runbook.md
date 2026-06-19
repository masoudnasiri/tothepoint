# Local Docker Windows Runbook (Rivar)

## Goal

Run Rivar reliably on Windows Docker Desktop with data preservation across restarts.

## Preconditions

- Docker Desktop is running.
- Open PowerShell/CMD in repository root: `C:\Old Laptop\D\Work\1404\140407\cahs_flow_project`.
- Do **not** use destructive volume commands unless you explicitly intend full reset.

## Safe Start Procedure

1. Optional backup (recommended before risky changes):
   - script (interactive): `backup_database.bat`
   - non-interactive equivalent:
     - `docker compose exec -T postgres pg_dump -U postgres procurement_dss > database_backups\backup_YYYYMMDD_HHMMSS.sql`
2. Start services:
   - script (interactive): `start.bat`
   - non-interactive equivalent (recommended for automation): `docker compose up --build -d`
3. Verify containers:
   - `docker compose ps`
4. Verify backend health:
   - Preferred on this environment: `curl http://127.0.0.1:8000/health`
   - Note: `http://localhost:8000/health` may route to IPv6 (`::1`) and can timeout depending on host networking.
5. Verify frontend:
   - Browser: `http://localhost:3000` (or `http://127.0.0.1:3000`)
   - CLI check: `curl -I http://127.0.0.1:3000`
6. Inspect logs:
   - `docker compose logs backend --tail=100`
   - `docker compose logs frontend --tail=100`
   - `docker compose logs postgres --tail=100`

## Safe Stop / Restart Procedure

- Stop while preserving data:
  - script (interactive): `stop.bat`
  - non-interactive equivalent: `docker compose down`
- Start again:
  - `docker compose up -d` (or `docker compose up --build -d` after code/dependency changes)

## Persistence Verification Checklist

1. Read a stable DB value before restart (example):
   - `docker compose exec -T postgres psql -U postgres -d procurement_dss -t -A -c "SELECT COUNT(*) FROM users;"`
2. Restart with non-destructive stop/start:
   - `docker compose down`
   - `docker compose up -d`
3. Re-check same value; counts should match.

## Common Issues and Fixes

- Backend health timeout on `localhost`:
  - use `127.0.0.1` for validation command.
- Frontend first response delay:
  - CRA dev server may need extra warmup; recheck after 20-30 seconds.
- Unauthorized responses in logs for `/config/feature-flags`:
  - expected if frontend probes endpoints without auth token; not startup failure by itself.

## What Not to Run (Data Safety)

- `docker compose down -v` (deletes volumes/data)
- any manual command that drops DB or deletes Docker volumes, unless explicitly approved for full reset.
