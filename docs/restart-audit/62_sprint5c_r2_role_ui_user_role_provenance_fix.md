# Sprint 5C-R2 — Role UI Cleanup, User Role Simplification, and GitHub Provenance Closure

Date: 2026-06-26  
Status: **PASS WITH MINOR ISSUES**  
Sprint type: **UX cleanup / provenance closure** (no new RBAC enforcement scope)

## Baseline

| Item | Value |
|---|---|
| Starting branch | `restart/sprint5c-r1-fix-role-management-runtime-closure` |
| Starting commit | `65788fcb3a10d06f69cffe535160b87135aeb946` |
| New branch | `restart/sprint5c-r2-role-ui-user-role-provenance-fix` |

## User-reported issues

1. **Role Management layout broken** — role editor overlapped/hid role list in RTL/Persian.
2. **Dual role concepts in user create/edit** — legacy/base role + RBAC roles shown separately.
3. **GitHub provenance unclear** — user saw no commits on default branch for 5 days.

## Role Management layout fix

| Change | Detail |
|---|---|
| Layout approach | Replaced CSS grid with responsive flex two-panel layout |
| Desktop | Role list ~38% width (scrollable, sticky header); editor ~62% (scrollable Paper) |
| Mobile/tablet | Stacked: role list first, editor below |
| Permission matrix | Wrapped in dedicated `overflow: auto` container inside editor panel |
| RTL | Verified via layout test with `dir=rtl`; list remains visible alongside editor |

## User role simplification strategy

| Item | Detail |
|---|---|
| Visible UI | Single **Roles** / **نقش‌ها** multi-select in create/edit dialogs |
| Hidden | Legacy `users.role` enum selector removed from UI |
| Role source | All active roles from `GET /access-control/roles` (system + custom) |
| User table | Shows assigned role display names (loaded via `getUserRoles`) |
| Wording | Removed user-facing "RBAC", "legacy", "base", "compatibility" labels |

## Compatibility role strategy (Fallback B)

`frontend/src/utils/legacyRoleDerivation.ts` derives hidden `users.role` on create/update:

| Selected system role code | Hidden legacy value |
|---|---|
| `system_admin` | `admin` |
| `pmo` | `pmo` |
| `project_manager` | `pm` |
| `procurement_specialist` | `procurement` |
| `finance_analyst` | `finance` |

- Multiple system roles: highest precedence per backend `LEGACY_ROLE_PRECEDENCE` (`admin` > `pmo` > `finance` > `procurement` > `pm`).
- Custom-only selection: defaults to `pm` (least-privilege legacy slot); effective access remains RBAC-driven.
- `PUT /access-control/users/{id}/roles` still calls backend `sync_legacy_role_for_user` after assignment.

No new `viewer` enum added (avoided schema/Pydantic risk).

## GitHub provenance findings

| Item | Value |
|---|---|
| `origin` remote | `https://github.com/masoudnasiri/tothepoint.git` |
| Secondary remote | `corbit-rivar` → `https://github.com/masoudnasiri/corbit-rivar.git` (not used for 5C pushes) |
| GitHub default branch | `main` @ `b6d9b6c` — **stale** (pre-restart audit work) |
| Latest 5C code branch | `restart/sprint5c-r1-fix-role-management-runtime-closure` @ `65788fc` |
| 5C-R2 branch | `restart/sprint5c-r2-role-ui-user-role-provenance-fix` (this sprint) |
| Why user saw no recent commits | Work landed on `restart/sprint5c*` feature branches, not `main` |
| Branch to inspect on GitHub | `restart/sprint5c-r2-role-ui-user-role-provenance-fix` (after push) |
| Merge to main | **Not performed** (out of scope unless explicitly requested) |

## Tests run

```text
npm test -- --watchAll=false --testPathPattern="(AccessControl|UsersPage.rbac|legacyRoleDerivation|Layout.usersAccessControl|ItemsMaster.*pilot|PackageWizard)"
→ 41 passed (10 suites)

CI=false npm run build → PASS
```

New/updated tests:

- `AccessControlPage.layout.test.tsx` — list + editor coexist, scroll regions, RTL
- `UsersPage.rbac.test.tsx` — single role selector, legacy derivation, lockout/partial failure
- `legacyRoleDerivation.test.ts` — compatibility mapping

Backend unchanged — no backend test rerun required.

## Runtime smoke on `/opt/rivar-demo`

See sprint closure commit for deploy timestamp. Checks:

- `verify.sh` PASS
- `run_sprint5c_r1_smoke.sh` PASS (restricted + permissioned roles)
- `/health`, `/openapi.json`, `/users-access` 200
- Unified Users & Access Control menu unchanged
- Role layout + single role selector verified post-deploy

Path: `/opt/rivar-demo` (not `/root/pdss_demo`).

## Files changed

| File | Change |
|---|---|
| `frontend/src/pages/AccessControlPage.tsx` | Two-panel responsive layout, scrollable matrix |
| `frontend/src/pages/UsersPage.tsx` | Single role selector, hidden legacy derivation, table labels |
| `frontend/src/utils/legacyRoleDerivation.ts` | Compatibility role mapping |
| `frontend/src/utils/legacyRoleDerivation.test.ts` | Unit tests |
| `frontend/src/pages/AccessControlPage.layout.test.tsx` | Layout tests |
| `frontend/src/pages/UsersPage.rbac.test.tsx` | Updated role assignment tests |
| `frontend/src/i18n/en.json`, `fa.json` | Roles labels, removed RBAC/legacy wording |
| `docs/restart-audit/62_*`, `08_*` | Sprint documentation |

## Known risks

- Demo frontend uses dev `npm start` image — layout fix verified via source + tests.
- Custom-only users get `pm` legacy slot for API compatibility; permissions still RBAC-only.
- `access_control_admin` has no legacy mirror — hidden role stays `pm` until backend sync runs on mixed assignments.
- Default branch `main` remains behind restart feature branches.

## Out of scope (confirmed)

- Sprint 5D Procurement Assignment
- Broad RBAC beyond Items/Suppliers pilot
- Package Wizard, Payment Methods, Cost Components changes
- JWT / optimization / cashflow / decision changes
- Merge to `main`

## Git provenance

Branch: `restart/sprint5c-r2-role-ui-user-role-provenance-fix`  
Commit: see closure commit hash in final report.

## Recommendation

**Proceed to Sprint 5D Procurement Assignment Backend** after accepting 5C-R2 UX cleanup.
