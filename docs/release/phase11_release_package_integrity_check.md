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
  - `update_package/update_files/VERSION`
  - `update_package/update_files/backend/VERSION`
  - `update_package/update_files/backend/app/app_metadata.py`
  - `update_package/update_files/backend/app/main.py`
  - `update_package/update-deployed-platform.sh`
  - `update_package/QUICK_UPDATE_COMPLETE.sh`
  - `update_package/README.txt`
  - `update_package/update_files/backend/app/crud.py`
  - `update_package/update_files/backend/app/schemas.py`
  - `update_package/update_files/frontend/public/index.html`
  - `update_package/update_files/frontend/public/manifest.json`
  - `update_package/update_files/frontend/public/rivar.png`
  - `update_package/update_files/frontend/src/App.tsx`
  - `update_package/update_files/frontend/src/components/Layout.tsx`
  - `update_package/update_files/frontend/src/pages/LoginPage.tsx`
  - `update_package/update_files/frontend/src/utils/appIdentity.ts`
  - `update_package/update_files/frontend/src/i18n/en.json`
  - `update_package/update_files/frontend/src/i18n/fa.json`
  - `update_package/update_files/frontend/src/responsive.css`
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

## Phase 11B Refresh Status

- Package was refreshed to include branding/version runtime files from `94a8a86` plus Phase 11B runtime deployment verification updates.
- Manifest now includes deployed environment verification metadata and backup evidence.

## Integrity Checksum Status

- `CHECKSUMS.sha256` exists and lists package files with SHA-256 digests.

## Final Status

`pass`
