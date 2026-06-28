# Sprint 5F-Fix-2 - Runtime Deployment and Live UI Closure

## Sprint metadata

- Sprint: `Sprint 5F-Fix-2 — Runtime Deployment and Live UI Closure`
- Source branch: `restart/sprint5f-fix-assignment-table-display-closure`
- Source commit: `ab7f7131ef67714036cf2cf88a722e78179d2d1c`
- Closure branch: `restart/sprint5f-fix2-runtime-ui-closure`
- Official server: `193.162.129.58`
- Official path: `/opt/rivar-demo`
- Forbidden path used: **No** (`/root/pdss_demo` not used)

## User-reported continuing issue

- User still observed old assignment-table behavior in live runtime.
- Prior QA had code/test pass but deployment provenance was not fully closed.
- This sprint verifies runtime identity, replaces stale frontend artifacts, and confirms live security/regression behavior.

## Server access gate

- SSH method used successfully:
  - `ssh -i ~/.ssh/id_rivar_deploy_temp root@193.162.129.58`
  - fallback key also valid: `~/.ssh/id_rivar_deploy`
- Access to `/opt/rivar-demo` confirmed.

## Before-deploy evidence

### Deployment markers (before)

- `/opt/rivar-demo/DEPLOYED_COMMIT.txt`:
  - `branch=restart/sprint5f-procurement-assignment-scope-enforcement`
  - `commit=c1e90b2c32035055e98bba90d0312fa8c98d353e`
  - `sprint=5F`
- `/opt/rivar-demo/docs/restart-audit/DEPLOYED_COMMIT.txt` matched same stale marker.

### Containers (before)

- frontend id: `cfd4786ee4858bb0a495e6e6e66c7a7b3c68e6fcea53aa0d46e43565822424c3`
  - created: `2026-06-28T17:19:25.420271352Z`
- backend id: `917caab1c22cf71879ae9868da2dbefb828c573deca252f7501abc719493caad`
  - created: `2026-06-28T17:19:23.510612182Z`

### Frontend asset/cache state (before)

- Frontend served `JS_ASSETS: /static/js/bundle.js` (non-hashed dev-style path).
- Pre-deploy bundle header:
  - `ETag: W/"b2d62d-GZ46PNSKZM3PBc4rs7Rkm8iAhwY"`
  - length: `11640703`
- `service-worker.js`: `404`

### Deployed source signatures (before)

- Project view source in `/opt/rivar-demo` still reflected pre-fix structure:
  - no explicit project-table `procurement.actions` header signature
  - inline remove handler signature present in project row rendering
- Item view lacked new tooltip signature (`Tooltip` not present).

Conclusion: accepted fix commit `ab7f713...` was not deployed before this sprint.

## Deployment actions executed

1. Built exact archive from source commit `ab7f7131ef67714036cf2cf88a722e78179d2d1c`.
2. Uploaded archive to `/opt/rivar-demo` via deploy key.
3. Extracted into `/opt/rivar-demo`.
4. Rebuilt frontend image with compose:
   - `docker compose ... build --no-cache frontend`
5. Recreated frontend container:
   - `docker compose ... up -d --force-recreate frontend`
6. Updated runtime markers:
   - `/opt/rivar-demo/DEPLOYED_COMMIT.txt`
   - `/opt/rivar-demo/docs/restart-audit/DEPLOYED_COMMIT.txt`
7. Corrected script line endings and reran installer verification.

## Deployment identity (after)

- Marker files now state:
  - `branch=restart/sprint5f-fix-assignment-table-display-closure`
  - `commit=ab7f7131ef67714036cf2cf88a722e78179d2d1c`
  - `sprint=5F-Fix-2`
- frontend id after deploy:
  - `2f620e461336ed5c174d0d50335a3855ac6677df75e907e3cdd49773d09069d4`
  - created: `2026-06-28T18:52:30.045098778Z`
- backend id unchanged (backend not rebuilt):
  - `917caab1c22cf71879ae9868da2dbefb828c573deca252f7501abc719493caad`

## Frontend bundle/cache closure evidence

- Asset path remains `/static/js/bundle.js`, but runtime content changed after deploy:
  - pre: `ETag W/"b2d62d-GZ46PNSKZM3PBc4rs7Rkm8iAhwY"`, len `11640703`
  - post: `ETag W/"b30337-yj2tOaZaegtxTACSwvaYcLxt3gM"`, len `11652229`
- `service-worker.js` remains `404` (no service-worker cache layer).
- `Cache-Control` headers are not forcing immutable static cache.

Conclusion: stale frontend bundle was replaced on server; browser hard refresh remains recommended for clients that cached old bundle.

## Live UI structure verification

Deployed frontend source hash on server matches local accepted source for key files:

- `ProcurementAssignmentProjectView.tsx`
- `ProcurementAssignmentItemView.tsx`
- `ProcurementAssignmentManagementPanel.tsx`

Verified deployed table structure signatures include:

- explicit actions column header (`procurement.actions`)
- assigned users header (`assignedProcurementUsers`)
- tooltip/selection clarity signatures in item/project views
- generated remove-key signature (`remove-${assignment.id}`) for action column rows

This confirms runtime source now contains the 5F-fix table separation implementation.

## Runtime/regression smoke

- `/health`: `200`
- `/openapi.json`: `200`
- frontend root: `200`
- `/#/procurement`: `200`
- `python backend/scripts/sprint5e_r4_runtime_smoke.py`: `PASS`
  - finalized-only visibility checks pass
  - direct Project Items deny for procurement view-only pass
  - bulk remove path pass
  - Payment Methods RBAC pass
  - Package Wizard Step 3 readiness endpoint pass
- `bash deployment/rivar-installer/verify.sh`: `PASS`

## Browser hard-refresh guidance

To ensure users do not see stale runtime UI from local browser cache:

1. Open Procurement page.
2. Use hard reload (`Ctrl+F5` / `Cmd+Shift+R`).
3. If needed, clear site data for `193.162.129.58:3000` and reload.

## Scope control check

- No Sprint 5G work started.
- No backend scope/security logic changed in this sprint.
- No Package Wizard behavior change.
- No Master Data RBAC change.
- No optimization/cashflow/decision logic change.

## Git provenance

- Closure branch: `restart/sprint5f-fix2-runtime-ui-closure`
- Source deployed commit: `ab7f7131ef67714036cf2cf88a722e78179d2d1c`
- Commit/push evidence: recorded in this sprint closure chat commands.

## Remaining risks

- Live visual confirmation from user browser is still needed after hard refresh, because this environment cannot attach an authenticated browser screenshot from the running app session.

## Recommendation

- If user confirms table is now visually correct after hard refresh, proceed to Sprint 5G.
- If user still sees mixed columns, create `Sprint 5F-Fix-3` focused on client/browser cache and authenticated UI capture evidence.
