# Scripts Directory Layout

This directory contains scripts that were moved from the project root and organized by platform and purpose.

## Structure

- `scripts/linux/operations/`
  - service lifecycle scripts (`start`, `stop`)
- `scripts/linux/deployment/`
  - Linux deployment/update scripts
- `scripts/linux/maintenance/`
  - Linux reset/maintenance scripts
- `scripts/linux/tooling/`
  - Linux tooling/install helper scripts

- `scripts/windows/migrations/`
  - Windows migration scripts
- `scripts/windows/deployment/`
  - Windows backup/restore/deployment scripts
- `scripts/windows/operations/`
  - Windows runtime operation scripts (`start`, `stop`, logs, checks)
- `scripts/windows/maintenance/`
  - Windows maintenance/reset/reseed scripts
- `scripts/windows/tooling/`
  - Windows tooling/install helper scripts
- `scripts/windows/seeding/`
  - Data seeding scripts
- `scripts/windows/testing/`
  - Manual test helper scripts

- `scripts/python/data-helpers/`
  - Python helper scripts used for data setup/update

- `scripts/sql/migrations/`
  - Root-level SQL migration scripts

## Notes

- Only script files from the repository root were moved.
- Existing scripts already under `backend/`, `frontend/`, `installation_packages/`, and other subdirectories were left unchanged.
