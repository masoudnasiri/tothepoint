# Phase 11 Release Package Integrity Check

## Target Package

- `release_packages/corbit-rivar-rc1/`

## Required Content Verification

Confirmed present:

- `manifest.json`
- `RELEASE_NOTES.md`
- `KNOWN_LIMITATIONS.md`
- `POST_DEPLOY_SMOKE_CHECKLIST.md`
- `README_RELEASE.md`
- `CHECKSUMS.sha256`
- update package snapshot:
  - `update_package/update-deployed-platform.sh`
  - `update_package/QUICK_UPDATE_COMPLETE.sh`
  - `update_package/README.txt`
  - `update_package/update_files/backend/app/crud.py`
  - `update_package/update_files/backend/app/schemas.py`
  - `update_package/update_files/frontend/src/pages/LoginPage.tsx`
- deployment/update scripts:
  - `deployment_scripts/linux/update-deployed-platform.sh`
  - `deployment_scripts/windows/update-deployed-platform.bat`
  - `deployment_scripts/windows/backup_database.bat`
  - `deployment_scripts/windows/restore_database.bat`

## Prohibited Content Verification

Verified absent from release package:

- `.env`
- real secrets/private keys
- DB backups / SQL dumps
- Docker volumes
- `node_modules`
- Python virtualenv directories
- uploaded files

Note: secret-pattern scan returned only non-secret matches (`.env` in manifest exclusion text and `password` symbol usage in copied backend code). No credential leakage found.

## Integrity Checksum Status

- `CHECKSUMS.sha256` exists and lists package files with SHA-256 digests.

## Final Status

`pass`
