# Sprint 5C-R4 — Full RBAC Inventory Matrix

**Sprint:** Sprint 5C-R4 Full Application RBAC Inventory and End-to-End Access Audit  
**Date:** 2026-06-26  
**Parent branch:** `restart/sprint5c-r3-role-management-usability-delete` @ `10fc427`  
**Working branch:** `restart/sprint5c-r4-full-rbac-inventory-e2e-audit`  
**Extraction method:** Code-driven (`backend/scripts/sprint5c_r4_extract_rbac_inventory.py`) — no manual page selection.

## Inventory counts (code extraction)

| Artifact | Count |
|----------|------:|
| Frontend routes (App.tsx) | 19 |
| Page components (`frontend/src/pages/*.tsx`, excl. tests) | 20 |
| Layout navigation items | 16 |
| Backend routers (`backend/app/routers/*.py`) | 27 |
| Backend endpoints (extracted) | 267 |
| Permission registry keys | 67 |

## Enforcement legend

| Status | Meaning |
|--------|---------|
| **pilot enforced** | Backend `require_pilot_permission`; frontend permission helpers |
| **enforced** | Backend always-on RBAC guard; frontend permission helpers |
| **legacy role** | Backend `require_role` / `require_admin` / `require_finance` etc. |
| **auth-only** | `get_current_user` only |
| **frontend-only** | Permission UI gating without matching backend |
| **legacy-only (nav)** | Layout `roles[]` array only |
| **future** | Registered permission; not enforced |
| **not protected** | No auth dependency |

---

## Master RBAC matrix (feature areas)

| Feature area | Page / route | Frontend component | Menu (i18n) | Primary backend endpoints | Permission key(s) | Frontend gating | Backend enforcement | Runtime tested | Test role | Result | Gap severity | Recommended action |
|--------------|--------------|-------------------|-------------|---------------------------|-------------------|-----------------|---------------------|----------------|-----------|--------|--------------|-------------------|
| Login | `/login` | LoginPage | — | `POST /auth/login` | — | login only | auth-only | yes | — | PASS | Low | — |
| Dashboard | `/dashboard` | DashboardPage | navigation.dashboard | `GET /dashboard/*` | — (future: none) | legacy role nav | auth-only | partial | admin | PASS | Medium | Add permission keys in future sprint |
| Project analytics | `/analytics` | AnalyticsDashboardPage | navigation.projectAnalytics | `GET /analytics/*` | reports.view (partial) | legacy role nav | auth-only / require_analytics_access on some | partial | admin | PASS | Medium | Map to reports/analytics permissions |
| Reports | `/reports` | ReportsPage | navigation.reports | `GET /reports/*` | reports.view, reports.export | legacy role nav | auth-only | partial | admin | PASS | Medium | Enforce reports.* when flag on |
| Projects | `/projects` | ProjectsPage | navigation.projects | `GET/POST/PUT/DELETE /projects/*` | projects.* | legacy role nav | legacy role / auth-only | partial | admin | PASS | High | Enforce projects.* (future) |
| Project items | `/projects/:id/items` | ProjectItemsPage | (via Projects) | `GET/POST /items/*`, `/projects/*` | project_items.* | legacy role (ProtectedRoute only) | legacy role / auth-only | partial | admin | PASS | High | Enforce project_items.* |
| Procurement | `/procurement` | ProcurementPage | navigation.procurement | `GET/POST /procurement/*`, `/packages/*` | procurement.* | legacy role nav | auth-only / mixed legacy | partial | admin | PASS | High | Enforce procurement.* |
| Procurement plan | `/procurement-plan` | ProcurementPlanPage | navigation.procurementPlan | `GET/POST /procurement-plan/*` | procurement.* | legacy role nav | legacy role on mutations | partial | admin | PASS | High | Enforce procurement.* |
| Finance | `/finance` | FinancePage | navigation.finance | `GET/POST /finance/*`, `/payment-methods` | finance.*, master_data.payment_methods.* | legacy role nav | require_finance on writes | partial | admin | PASS | High | Permission-based finance enforcement |
| Optimization (legacy) | `/optimization` | OptimizationPage | — (hidden) | — | optimization.* | none (direct route) | — | no | — | Future | Low | Legacy route; enhanced used |
| Optimization | `/optimization-enhanced` | OptimizationPageEnhanced | navigation.optimization | `POST /decisions/*`, solver endpoints | optimization.* | legacy role nav | auth-only / legacy | partial | admin | PASS | High | Enforce optimization.* |
| Decisions | `/decisions` | FinalizedDecisionsPage | navigation.decisions | `GET/POST /decisions/*` | decisions.* | legacy role nav | legacy / auth-only | partial | admin | PASS | High | Enforce decisions.* |
| Items Master | `/items-master` | ItemsMasterPage | navigation.itemsMaster | `GET/POST/PUT/DELETE /items-master/*` | master_data.items.* | permission pilot (`canViewItemsMaster` etc.) | **pilot enforced** | yes | sprint5c_r4_masterdata_denied | PASS | — | Keep pilot |
| Suppliers | `/suppliers` | SuppliersPage | navigation.suppliers | `GET/POST/PUT/DELETE /suppliers/*` | master_data.suppliers.* | permission pilot | **pilot enforced** | yes | sprint5c_r4_masterdata_denied | PASS | — | Keep pilot |
| Weights | `/weights` | WeightsPage | navigation.weights | `GET/POST /weights/*` | — | legacy role nav (admin) | auth-only | partial | admin | PASS | Medium | Register/enforce weights permissions |
| Audit logs | `/audit-logs` | AuditLogsPage | navigation.auditLogs | `GET /audit/*` | audit_logs.view | legacy role nav (admin) | legacy admin | partial | admin | PASS | Medium | Enforce audit_logs.view |
| Users & Access Control | `/users-access` | UsersAccessControlPage | navigation.usersAccessControl | `/users/*`, `/access-control/*` | users.*, access_control.* | permission-based route + tabs | access_control: enforced; users: **fixed in 5C-R4** | yes | sprint5c_r4_users_view_only | FIXED | **Critical (was)** | Backend users.* enforcement added |
| Users tab | `/users-access?tab=users` | UsersPage | navigation.users | `GET/POST/PUT/DELETE /users/*` | users.view/create/edit/delete | `canViewUsersSection` etc. | **enforced (5C-R4)** | yes | sprint5c_r4_users_view_only | FIXED | Critical | Deploy fix |
| Roles tab | `/users-access?tab=roles` | AccessControlPage | accessControl.rolesTab | `/access-control/roles/*` | access_control.roles.manage | `canManageAccessControl` | require_access_control_manager | yes | sprint5c_r4_users_view_only | PASS | — | Correctly restricted |
| User roles tab | `/users-access?tab=userRoles` | AccessControlPage | accessControl.userRolesTab | `/access-control/users/{id}/roles` | access_control.user_roles.view/edit | `canViewUserRoleAssignment` | require_access_control_manager | yes | — | PASS | Medium | Split AC manager vs user_roles viewer (future) |
| Redirects | `/users`, `/access-control` | Navigate | — | — | — | redirect | — | yes | — | PASS | Low | — |
| Hidden pages | CurrencyManagementPage | (not routed in App.tsx) | — | `/currencies/*` | — | — | mixed | no | — | Future | Low | Dead page file |

---

## Frontend route inventory (extracted)

| Path | Component / behavior | In nav | Frontend guard |
|------|---------------------|--------|----------------|
| `/login` | LoginPage | No | Public |
| `/` | Redirect → `/dashboard` | — | ProtectedRoute (auth) |
| `/dashboard` | DashboardPage | Yes | Legacy nav roles |
| `/decisions` | FinalizedDecisionsPage | Yes | Legacy nav |
| `/projects` | ProjectsPage | Yes | Legacy nav |
| `/items-master` | ItemsMasterPage | Yes | Pilot permissions + legacy nav |
| `/projects/:projectId/items` | ProjectItemsPage | Via projects | ProtectedRoute only |
| `/procurement` | ProcurementPage | Yes | Legacy nav |
| `/procurement-plan` | ProcurementPlanPage | Yes | Legacy nav |
| `/finance` | FinancePage | Yes | Legacy nav |
| `/optimization` | OptimizationPage | No | ProtectedRoute only |
| `/optimization-enhanced` | OptimizationPageEnhanced | Yes | Legacy nav |
| `/analytics` | AnalyticsDashboardPage | Yes (Insights) | Legacy nav |
| `/reports` | ReportsPage | Yes (Insights) | Legacy nav |
| `/users` | Redirect → users tab | — | — |
| `/users-access` | UsersAccessControlPage | Yes | `UsersAccessControlRoute` (permission) |
| `/access-control` | Redirect → roles tab | — | — |
| `/weights` | WeightsPage | Yes (Base info) | Legacy nav |
| `/suppliers` | SuppliersPage | Yes (Base info) | Pilot permissions + legacy nav |
| `/audit-logs` | AuditLogsPage | Yes | Legacy nav (admin) |

**Route guards:** `ProtectedRoute` = JWT auth only. `UsersAccessControlRoute` = `canAccessUsersAccessControlSection` (users.view OR access_control manage OR user_roles view/edit).

---

## Backend router inventory (summary)

| Router file | Prefix (typical) | Endpoints | Dominant guard |
|-------------|------------------|----------:|----------------|
| auth.py | `/auth` | 4 | get_current_user |
| access_control.py | `/access-control` | 11 | require_access_control_manager |
| users.py | `/users` | 6 | **require_users_permission (5C-R4)** |
| items_master.py | `/items-master` | 12+ | require_pilot_permission |
| suppliers.py | `/suppliers` | 18+ | require_pilot_permission |
| projects.py | `/projects` | many | get_current_user / legacy |
| items.py | `/items` | many | get_current_user / legacy |
| procurement.py | `/procurement` | many | get_current_user |
| packages.py | `/packages` | many | get_current_user |
| procurement_plan.py | `/procurement-plan` | many | mixed legacy |
| finance.py | `/finance` | many | require_finance / auth |
| decisions.py | `/decisions` | many | legacy / auth |
| dashboard.py | `/dashboard` | 4 | get_current_user |
| analytics.py | `/analytics` | many | require_analytics_access / auth |
| reports.py | `/reports` | many | auth-only |
| weights.py | `/weights` | many | auth-only |
| audit.py | `/audit` | many | require_admin |
| currencies.py | `/currencies` | many | require_finance / auth |
| files.py | `/files` | 4 | require_role |
| config.py | `/config` | few | auth |
| brs_api.py | `/brs` | many | auth |
| delivery_options.py | `/delivery-options` | 6 | get_current_user |
| excel.py | `/excel` | few | auth |
| phases.py | `/phases` | few | auth |
| invoice_payment_simple.py | various | many | auth |
| supplier_payments.py | various | many | auth |
| procurement_financials.py | various | many | auth |

Full endpoint list: run `python backend/scripts/sprint5c_r4_extract_rbac_inventory.py` (267 rows).

---

## Permission registry (67 keys)

| Feature group | Keys | Backend enforced | Frontend gating | Matrix badge |
|---------------|------|------------------|-----------------|--------------|
| access_control.* | 9 | Yes (AC router) | Yes | Enforced |
| users.* | 4 | Yes (5C-R4) | Yes | Enforced |
| master_data.items.* | 4 | Pilot | Yes | Pilot enforced |
| master_data.suppliers.* | 4 | Pilot | Yes | Pilot enforced |
| master_data.payment_methods.* | 4 | No | No (Finance UI) | Future |
| master_data.cost_components.* | 4 | No | Partial | Future |
| projects.* | 4 | No | Legacy nav | Future |
| project_items.* | 5 | No | No | Future |
| procurement.* / packages / options | 16 | No | Legacy nav | Future |
| finance.* / cashflow.* | 4 | Partial legacy | Legacy nav | Future |
| optimization.* | 4 | No | Legacy nav | Future |
| reports.* | 2 | No | Legacy nav | Future |
| decisions.* | 4 | No | Legacy nav | Future |
| audit_logs.view | 1 | Legacy admin | Legacy nav | Future |

---

## Documentation cross-check

| Doc | Finding |
|-----|---------|
| ADR-011 | Defines RBAC model; procurement assignment not implemented (correct) |
| 56–63 restart-audit | Sprint chain through 5C-R3; pilot scope = Items/Suppliers |
| 08 continuation plan | Updated with 5C-R4 pointer |

**Gaps vs docs:** Most registered permissions are intentionally future; global `ENABLE_PERMISSION_ENFORCEMENT` remains off except pilot + users (5C-R4).

---

## Severity rollup

| Severity | Count | Examples |
|----------|------:|---------|
| Critical | 1 (fixed) | users.view blocked by require_admin on backend |
| High | 8+ | Projects, procurement, finance modules legacy-only |
| Medium | 10+ | Nav legacy vs permission mismatch |
| Low | 5+ | Hidden routes, wording |
| Future | 40+ | Registered permissions not yet enforced |

---

## Phase B fixes in this sprint

1. Backend `require_users_permission` on all `/users/*` CRUD endpoints.
2. Permission matrix badges: pilot only on Items/Suppliers; enforced on users/access_control.
3. Tests: `test_phase15c_r4_users_permission_enforcement.py`, `permissionLabels.test.ts`.

**Deploy note:** Demo runtime before deploy confirmed `users.view` → GET `/users/` returns **403**. Fix requires redeploy to `/opt/rivar-demo`.
