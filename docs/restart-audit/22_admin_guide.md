# Rivar Admin Guide

## Scope

This guide is for system administrators responsible for operating and safeguarding a Rivar deployment.

## Admin Responsibilities

- Manage platform uptime and service health
- Control environment configuration and secrets
- Protect database persistence and backups
- Manage users/roles and operational access
- Ensure safe updates with rollback readiness

## Environment and Configuration

Primary runtime settings are loaded from environment variables and `docker-compose.yml`.

Critical variables:

- `DATABASE_URL`
- `SECRET_KEY`
- `ALLOWED_ORIGINS`
- `ENVIRONMENT`
- package/optimization feature flags

Admin rule: treat `.env` and secret values as sensitive credentials.

## User and Role Administration

Role model is enforced through auth and router-level behavior:

- Admin
- PMO
- PM
- Procurement
- Finance

Default seed credentials may exist in initial environments; rotate all default passwords before production use.

## Daily Health Checklist

1. `docker compose ps`
2. backend health: `curl http://127.0.0.1:8000/health`
3. check backend logs for repeated exceptions
4. verify frontend responsiveness
5. verify DB container health

## Backup and Restore Operations

Use existing backup scripts and validate backup artifacts:

- Windows helpers:
  - `backup_database.bat`
  - `restore_database.bat`

Admin best practice:

- run backup before updates/migrations,
- verify backup file is created and non-empty,
- keep off-host backup copy for disaster recovery.

## Safe Update Procedure (Admin View)

1. Freeze active release window.
2. Take verified DB backup.
3. Apply update package/script in non-destructive mode.
4. Start services and run smoke checks.
5. Validate key business workflows (login, procurement plan, finance entries, dashboard).
6. Monitor logs for post-update regression.

Never run destructive volume deletion (`down -v`) in normal update operations.

## Feature Flag Operations

Admins should coordinate feature-flag changes with engineering and product owner, especially for:

- package procurement enablement,
- package-based optimization,
- lock coverage enforcement,
- legacy fallback behavior.

Incorrect flag combinations can create inconsistent behavior across legacy and package-aware flows.

## Audit and Traceability

Audit logs are available via `/audit-logs` UI/API and should be reviewed for:

- sensitive actions,
- unusual data lifecycle changes,
- finance and decision transitions.

## Incident Handling

When production behavior degrades:

1. capture logs and timestamps,
2. preserve DB state (backup first),
3. avoid ad-hoc destructive cleanup,
4. restart affected service(s) safely,
5. escalate with evidence to engineering.

## Security Baseline

- rotate default credentials,
- use strong secret keys,
- restrict network exposure and CORS origins,
- ensure HTTPS/SSL termination in production ingress,
- limit shell access to trusted operators only.

## Admin Acceptance Criteria After Changes

- health endpoint healthy,
- containers stable,
- login works,
- package decision flow works,
- finance entries reflected in reports,
- no critical errors in logs.

## References

- `docs/restart-audit/03_run_and_deployment.md`
- `docs/restart-audit/12_deployment_update_safety_report.md`
- `docs/restart-audit/14_existing_operational_modules_regression_audit.md`
