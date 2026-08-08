# Server Reset and Fresh Reinstall Report

Date (UTC): 2026-08-08
Host: `193.162.129.58`
Requested action: controlled destructive reset for Rivar-only runtime and fresh reinstall

## 1) Incident Summary

- Reported issue: after some runtime duration, login fails and backend becomes unstable/unhealthy.
- Approved scope: destructive reset for Rivar-related deployments only, preserving evidence and backups.
- Non-goals: no deletion of unrelated server services, unrelated Docker resources, SSH keys, or system packages.

## 2) Pre-Reset Server State and Evidence

Evidence files created on server:

- `/root/rivar_reset_evidence/pre_reset_20260808_084145.log`
- `/root/rivar_reset_evidence/reset_actions_20260808_084705.log`
- `/root/rivar_reset_evidence/login_stability_probe.log`

Observed before reset:

- `/root/pdss` existed as a file (not a deployment directory).
- `/opt/rivar-demo` was the active Rivar runtime path.
- Active containers:
  - `rivar-demo-backend`
  - `rivar-demo-frontend`
  - `rivar-demo-postgres`
- Health before reset from localhost:
  - `GET /health` returned `{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}`

Disk/memory snapshot before reset:

- Disk: `/dev/sda2` usage `89G/197G` (`47%`).
- Memory: `32095 MB total`, `4781 MB used`, `24065 MB free`, `2047 MB swap` free.

Reset scope applied:

- Rivar runtime paths and Rivar-related compose resources only.

## 3) Release Package Preservation

- Expected package source under runtime paths was not found.
- RC1 package was uploaded from local workspace to server:
  - Source (local): `release_packages/corbit-rivar-rc1/`
  - Preserved path (server): `/root/rivar_install_sources/corbit-rivar-rc1`
- Integrity artifacts:
  - `manifest.json`: present
  - `CHECKSUMS.sha256`: present

## 4) Final Backup Before Destructive Reset

Backup path:

- `/root/rivar_final_backups/`

Database backup:

- `/root/pdss` DB backup skipped because `/root/pdss` was not a valid deployment directory.
- Successful SQL dump captured from active Rivar runtime:
  - `/root/rivar_final_backups/pre_reset_rivar_demo_20260808_084614.sql`

Config/log backup:

- Config archive directory kept at:
  - `/root/rivar_final_backups/config_and_logs/`

Notes:

- No backups or `.env` files were committed to git.

## 5) Destructive Cleanup Performed (Rivar-only)

Compose shutdown:

- `docker compose down --remove-orphans` executed for detected Rivar deployment at `/opt/rivar-demo`.

Removed deployment paths:

- `/root/pdss`
- `/opt/rivar-demo`

Removed Rivar Docker networks:

- `pdss_procurement_network`
- `rivar_demo_network`

Removed Rivar Docker volumes:

- `pdss_demo_uploads_data`
- `pdss_phase7_staging_postgres_data`
- `pdss_phase7_staging_uploads_data`
- `pdss_postgres_data`
- `pdss_uploads_data`
- `rivar-demo_postgres_data`
- `rivar-demo_uploads_data`
- `rivar_demo_postgres_data`

Protected paths preserved:

- `/root/rivar_install_sources`
- `/root/rivar_final_backups`
- `/root/rivar_reset_evidence`

## 6) Fresh Install Method and Source

### Installer Gap Found

- The RC1 package is update-oriented (`update_package`) and does not contain a complete first-time installer.
- A direct first-time overlay of RC1 `update_files` on baseline caused backend startup failure:
  - `ImportError: cannot import name 'log_audit' from 'app.crud'`

### Fallback Used (per deployment guide rule)

- Used canonical repository source at accepted commit:
  - `e8112387a32acabae6cf97aa1530bab1132bd6f5`
- Deployed fresh into:
  - `/root/pdss`
- Created fresh `.env` from `.env.example`, then set runtime identity metadata:
  - `APP_PRODUCT_NAME=Rivar`
  - `APP_VENDOR_NAME=Corbit`
  - `APP_VERSION=1.0.0-rc1`
  - `APP_RELEASE_TAG=v1.0.0-rc1`
  - `APP_RELEASE_CHANNEL=RC1 / Pilot`
  - `APP_RELEASE_POSTURE=APPROVED FOR PILOT`

Deployment command:

- `docker compose up --build -d`

## 7) Fresh Install Verification

Runtime status:

- `docker compose ps` shows all services up:
  - `pdss-postgres-1` healthy
  - `pdss-backend-1` healthy
  - `pdss-frontend-1` up

Health/API:

- `GET http://127.0.0.1:8000/health` -> `200`, body `{"status":"healthy","version":"1.0.0"}`
- Public checks:
  - `http://193.162.129.58:3000/` -> `200`
  - `http://193.162.129.58:8000/health` -> `200`

Seed login verification:

- `admin/admin123` -> `200`
- `finance1/finance123` -> `200`
- `proc1/proc123` -> `200`
- `pmo1/pmo123` -> `200`
- `pm1/pm123` -> `200`

## 8) Tests and Build Results

Backend full tests:

- Command: `docker compose run --rm backend python -m pytest tests -q`
- Result: PASS (`39 passed, 4 skipped`)

Phase 8 smoke:

- Command: `docker compose run --rm backend python -m pytest tests/test_phase8_release_candidate_smoke.py -q`
- Result: PASS (`3 passed`)

Frontend build:

- Command: `docker compose run --rm frontend npm run build`
- Result: PASS (compiled with warnings only)

## 9) Demo Dataset Fresh Install Test

Create command:

- `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode create`
- Result: PASS (demo projects, decisions, and finance records created)

Cleanup command:

- `docker compose run --rm -e PYTHONPATH=/app backend python scripts/create_demo_dataset.py --mode cleanup`
- Result: PASS (demo records removed)

Post-cleanup checks:

- `DEMO_RC8_` projects count: `0`
- `DEMO_RC8_` decisions count: `0`

## 10) Login Stability Probe

Probe output file:

- `/root/rivar_reset_evidence/login_stability_probe.log`

Execution:

- 5 iterations, every 2 minutes (short soak)
- Each iteration performed:
  - health check
  - admin login request
  - backend memory sample

Observed results:

- All 5 iterations:
  - `health_code=200`
  - `login_code=200`
  - `FAILURE_DETECTED=0`
- Backend memory remained stable around `164 MiB`.

## 11) Fresh DB Confirmation

- Confirmed yes: previous Rivar DB volumes were removed and new `pdss_*` volumes recreated during reinstall.

## 12) Remaining Risks

- RC1 package is not a full first-install bundle; it is update-oriented and direct fresh overlay produced backend import mismatch.
- Fresh health endpoint returns `version: 1.0.0` instead of `1.0.0-rc1`; runtime identity metadata likely needs explicit app-level wiring in this baseline.
- Demo create output field `fail_lock_error_contains_incomplete` returned `false`; business wording validation should be rechecked in a focused QA pass.
- Only short soak (5 iterations) was run; longer 20-30 minute probe remains recommended.

## 13) Recommended Next Action

1. Create a dedicated RC1 first-time installer package validated for clean bootstrap (not update-only).
2. Add/verify runtime metadata wiring so `/health` reflects RC1 identity consistently.
3. Run extended login soak (20-30+ minutes) and include authenticated endpoint verification with token parsing aligned to API response shape.
4. Proceed with focused QA on coverage-lock error messaging expectations.
