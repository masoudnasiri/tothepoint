# Rivar Restart Audit - Phase 2 Local Docker Run Report

## Scope

Phase 2 validation on Windows Docker Desktop for local runtime reliability and data persistence.

## Commands Executed and Results

## 1) Start Stack

- Command: `docker compose up --build -d`
- Result: PASS
- Evidence:
  - images built: `cahs_flow_project-backend`, `cahs_flow_project-frontend`
  - services started: `postgres`, `backend`, `frontend`

## 2) Container Status

- Command: `docker compose ps`
- Result: PASS
- Observed:
  - `postgres`: Up (healthy), port `5432`
  - `backend`: Up (healthy), port `8000`
  - `frontend`: Up, port `3000`

## 3) Backend Health

- Attempt 1: `curl http://localhost:8000/health`
  - Result: timeout/reset in this environment (IPv6 `::1` path)
- Attempt 2: `curl http://127.0.0.1:8000/health`
  - Result: PASS
  - Response: `{"status":"healthy","version":"1.0.0"}`

## 4) Frontend URL

- Command: `curl -I http://127.0.0.1:3000`
- Result: PASS (after CRA warmup)
- Response: HTTP `200 OK`, `X-Powered-By: Express`

## 5) Service Logs

- Commands:
  - `docker compose logs backend --tail=100`
  - `docker compose logs frontend --tail=100`
  - `docker compose logs postgres --tail=100`
- Result: PASS with non-blocking warnings
- Notes:
  - backend startup completed, database init ran, existing seed data detected and preserved
  - frontend compiled with warning noise (unused vars), no hard crash
  - postgres healthy and accepting connections

## 6) Optional Backup

- Command:
  - `docker compose exec -T postgres pg_dump -U postgres procurement_dss > database_backups/phase2_backup_20260619_222305.sql`
- Result: PASS
- Backup file: `database_backups/phase2_backup_20260619_222305.sql`
- File size: `437646` bytes

## 7) Data Persistence Across Stop/Start

- Before restart check:
  - `docker compose exec -T postgres psql -U postgres -d procurement_dss -t -A -c "SELECT COUNT(*) FROM users;"`
  - Value: `9`
- Non-destructive restart:
  - `docker compose down`
  - `docker compose up -d`
- After restart check:
  - same SQL command
  - Value: `9`
- Result: PASS (data preserved across restart)

---

## Errors Found and Handling

1. `localhost:8000` health request timeout/reset:
   - likely host IPv6 path issue in this environment.
   - workaround/fix for runbook: validate with `127.0.0.1`.
2. Frontend first probe timeout:
   - CRA dev server needed warmup.
   - subsequent check returned HTTP 200.

No destructive command was used. No `docker compose down -v` was executed.

## Phase 2 Conclusion

- Local Docker run is reliable with safe commands.
- Backend health, frontend availability, and postgres health are validated.
- Data persistence across stop/start is confirmed.
- Runbook created for repeatable Windows workflow.
