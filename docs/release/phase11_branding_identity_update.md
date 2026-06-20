# Phase 11A Branding, Identity, and Version Visibility Update

## Scope

Focused product identity pass only (no business feature development):

- Official producer/company: `Corbit`
- Official product/software name: `Rivar`
- Display version for current release candidate: `1.0.0-rc1`

## Files Changed

- Version source:
  - `VERSION`
  - `backend/VERSION`
  - `backend/app/app_metadata.py`
  - `backend/app/main.py`
- Browser identity:
  - `frontend/public/index.html`
  - `frontend/public/manifest.json`
  - `frontend/public/rivar.png` (included as tracked canonical logo asset)
- In-app identity:
  - `frontend/src/utils/appIdentity.ts`
  - `frontend/src/App.tsx`
  - `frontend/src/pages/LoginPage.tsx`
  - `frontend/src/components/Layout.tsx`
- Naming consistency touch-up:
  - `frontend/src/i18n/en.json`
  - `frontend/src/i18n/fa.json`
  - `frontend/src/responsive.css`

## Branding Decisions

1. Canonical product naming:
   - Product: `Rivar`
   - Attribution: `Rivar by Corbit`
2. Canonical logo asset:
   - `frontend/public/rivar.png`
3. Browser identity:
   - title: `Rivar | Corbit`
   - favicon/apple icon: `rivar.png`
4. In-app identity:
   - login: logo + `Rivar` + `Rivar by Corbit` + version
   - main shell/sidebar: logo + name + attribution + version
   - footer: `Rivar by Corbit | Version <runtime-version>`

## Logo Usage

- Browser icon via `index.html` (`rel="icon"` and `apple-touch-icon`)
- Login page hero logo
- Main shell/sidebar logo

## Favicon and Title Update

- `frontend/public/index.html` now points favicon to `rivar.png`.
- Browser title set to `Rivar | Corbit` in:
  - static HTML title
  - runtime reinforcement in `frontend/src/App.tsx`

## Version Storage and Source-of-Truth

Version source of truth:

- `VERSION` file at repository root (`1.0.0-rc1`)

Runtime container copy for current backend build context:

- `backend/VERSION` (`1.0.0-rc1`)

Runtime wiring:

- Backend loads version from `VERSION` via `backend/app/app_metadata.py`.
- Backend runtime in Docker currently reads `backend/VERSION` (mirrors root `VERSION`) due backend-only build context.
- `/health` and root API info now expose this runtime version and identity fields.
- Frontend reads runtime version from backend `/health` through `getRuntimeVersion()`.

## Where Version Is Displayed

- Login page (`Version <value>`)
- Sidebar identity block (`Version <value>`)
- Footer identity bar (`Rivar by Corbit | Version <value>`)
- Backend health response (`/health`)

## Future Version Bump Procedure

For the next release:

1. update `VERSION` file value
2. run backend tests and frontend build
3. verify UI footer/login version and `/health` version
4. prepare tag using naming convention `v<version>` (example: `v1.0.0-rc1`)

## Suggested Tag Convention

- Release tag format: `v<semver-or-rc>`
- Current recommended tag: `v1.0.0-rc1`

## Remaining Limitations

- Existing frontend eslint warnings remain (non-blocking for this branding scope).
- Existing backend deprecation warnings remain in test output.
- Active server runtime still reports previous deployed version until this commit is deployed to the target environment.
- Manual business-owner live click-through remains required for final production approval posture.
