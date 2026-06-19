# Root Housekeeping Archive (2026-06-19)

This folder stores files moved from the repository root to keep the project root focused on active runtime and development entrypoints.

## Why files were moved

- Reduce root-level clutter and improve discoverability of operational files.
- Preserve historical notes, ad-hoc diagnostics, and one-off test assets without deleting them.
- Keep Git history intact by moving with `git mv`.

## What was moved

- `root-markdown-notes/`
  - root-level implementation/status/fix summary markdown files that are not required as primary run/deploy entrypoints.
- `ad-hoc-tests-debug/`
  - one-off debug/test/demo files from root (e.g. `test_*`, `debug_*`, `diagnose_*`, ad-hoc SQL/HTML/ZIP artifacts).

## What was intentionally kept in root

- runtime and deployment entrypoints (for example: `docker-compose.yml`, `start.bat`, `stop.bat`, `backup_database.bat`, `restore_database.bat`, `update-deployed-platform.*`)
- primary user/developer docs (for example: `README.md`, `SETUP.md`, `USER_GUIDE.md`, `PLATFORM_UPDATE_GUIDE.md`)
- package/dependency manifests and active project folders

## Safety note

No files were deleted as part of this housekeeping step; files were only relocated inside the repository.
