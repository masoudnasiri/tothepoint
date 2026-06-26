# Rivar Clean Installer

This installer provides a repeatable clean deployment baseline for accepted Sprint 3A-4A scope.

## Scope

- Production-like Docker Compose stack:
  - `postgres`
  - `backend`
  - `frontend` (static React build served by nginx)
- Deterministic QA fixture seeding for read-only Sprint 3A-4A runtime checks
- Backup-first cleanup flow for legacy `pdss`/`rivar` demo deployments

## Files

- `install.sh` - install and upgrade entrypoint with backup/wipe controls
- `uninstall.sh` - stop/remove services (optional data wipe)
- `verify.sh` - frontend/backend/runtime verification orchestration
- `backend/scripts/verify_runtime.py` - in-container backend endpoint + side-effect smoke checker
- `docker-compose.rivar-demo.yml` - compose stack definition
- `.env.example` - environment template

## Quick Start (Demo Server)

1. Extract clean installer artifact on server.
2. Copy `.env.example` to `.env` and adjust values if needed.
3. Run:

```bash
bash deployment/rivar-installer/install.sh \
  --fresh \
  --backup-existing \
  --wipe-existing-after-backup \
  --seed-demo-data
```

4. Verify:

```bash
bash deployment/rivar-installer/verify.sh
```

`verify.sh` reseeds the deterministic fixture (`RIVAR_DEMO_ACCEPTED_BASELINE`) by default
before runtime checks, and the verifier discovers fixture IDs dynamically from seeded data.
The runtime verification report includes discovered identifiers for:

- `project_id`
- `project_item_id`
- `package_id`
- `procurement_option_id`
- `candidate_id` (when candidate builder returns rows)

## Uninstall

```bash
bash deployment/rivar-installer/uninstall.sh
```

To remove Postgres volume too:

```bash
bash deployment/rivar-installer/uninstall.sh --wipe-data
```

Backups are never deleted by uninstall.
