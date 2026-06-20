# Phase 11C — UI Smoke Checklist

**Date prepared:** 2026-06-20  
**Target environment:** `/root/pdss_demo` · `193.162.129.58:13010` (frontend) · `193.162.129.58:18010` (backend)  
**COMPOSE_PROJECT_NAME:** `pdss_demo`  
**Verification method:** Manual browser walkthrough after Phase 11C frontend deploy + rebuild

> Status key: **PASS** | **FAIL** | **NOT TESTED**  
> This checklist must be executed manually via a browser after the Phase 11C deploy.  
> Backend API behaviors are unchanged and verified by the backend pytest gate.

---

## 1. Identity / Shell

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 1.1 | Login page loads | Rivar logo, "Rivar" title, "by Corbit" subtitle, version, clean white card on surface bg | NOT TESTED |
| 1.2 | Login page — product name | `Rivar` displayed prominently | NOT TESTED |
| 1.3 | Login page — producer name | `by Corbit` displayed | NOT TESTED |
| 1.4 | Login page — version | Version from `/health` shown (e.g. `1.0.0-rc1`) | NOT TESTED |
| 1.5 | Login succeeds (admin / admin123) | Redirects to Dashboard | NOT TESTED |
| 1.6 | Sidebar — brand area | Rivar logo image + "Rivar" text + "Corbit" monospace | NOT TESTED |
| 1.7 | Sidebar — background | White (`#FFFFFF`), no dark background | NOT TESTED |
| 1.8 | Sidebar — active nav item | Accent-tint background (`#EEF1FD`) + accent-600 text (`#2C44B8`) | NOT TESTED |
| 1.9 | Sidebar — nav items compact | Items at 8px/10px padding, 216px wide sidebar | NOT TESTED |
| 1.10 | Topbar — background | White, 56px height, sticky | NOT TESTED |
| 1.11 | Topbar — user avatar | Dark circle with user initials (not profile icon) | NOT TESTED |
| 1.12 | Topbar — language switcher | Globe icon, EN / فارسی options | NOT TESTED |
| 1.13 | Page background | Surface color (`#F6F7F9`) not white | NOT TESTED |
| 1.14 | User role display | User menu shows username + role on click | NOT TESTED |
| 1.15 | Logout | Works from user menu | NOT TESTED |

---

## 2. Dashboard

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 2.1 | Dashboard loads | Page title "Dashboard", subtitle | NOT TESTED |
| 2.2 | Metric cards row | 4 white bordered metric cards (Inflow, Outflow, Net, Balance) | NOT TESTED |
| 2.3 | Metric card values | Monospace-style numeric values | NOT TESTED |
| 2.4 | View mode toggle | Forecast / Actual / Comparison toggle buttons | NOT TESTED |
| 2.5 | Currency toggle | Unified / Original Currencies toggle | NOT TESTED |
| 2.6 | Cash flow chart | Composed chart in white panel with Rivar line/bar colors | NOT TESTED |
| 2.7 | Cumulative balance chart | Line chart in white panel | NOT TESTED |
| 2.8 | Data table | Compact table in white panel with paginator | NOT TESTED |
| 2.9 | Export button | Present in header and table panel | NOT TESTED |
| 2.10 | Empty state (no data) | RivarEmptyState with icon, title, description | NOT TESTED |
| 2.11 | PM role — restricted view | Only revenue inflow card visible | NOT TESTED |
| 2.12 | Procurement role — restricted view | Only payment outflow card visible | NOT TESTED |

---

## 3. Procurement

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 3.1 | Procurement page loads | RivarPageHeader with refresh + coverage buttons | NOT TESTED |
| 3.2 | Summary metric strip | 5 metric tiles: Items, Packages, Active, w/Pkg, Suppliers | NOT TESTED |
| 3.3 | Filter panel | Search input + project multi-select + Clear button | NOT TESTED |
| 3.4 | Item accordion | White-bordered accordion items, compact font | NOT TESTED |
| 3.5 | Item accordion — code display | Item code bold, name/project/description subtle | NOT TESTED |
| 3.6 | Item accordion — Qty pill | Status pill showing quantity | NOT TESTED |
| 3.7 | View item button | Opens item detail dialog | NOT TESTED |
| 3.8 | Item detail dialog | Rivar-styled: icon header, grid layout, delivery options | NOT TESTED |
| 3.9 | Create Package button | Visible in accordion for procurement/admin | NOT TESTED |
| 3.10 | Empty state | Shows when no finalized items | NOT TESTED |
| 3.11 | Pagination | Shows count, first/prev/next/last | NOT TESTED |

---

## 4. Package Wizard

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 4.1 | Package Wizard opens (Dialog) | Large MD dialog with custom header, no generic DialogTitle | NOT TESTED |
| 4.2 | Wizard header | Step indicator (1→2→3 with checkmarks for completed) | NOT TESTED |
| 4.3 | Wizard header — item name | Item code + name shown below title | NOT TESTED |
| 4.4 | Step 1 — Metadata | Package name, type selector, supplier autocomplete, description | NOT TESTED |
| 4.5 | Step 2 — Quantities | Main item quantity + sub-item fields | NOT TESTED |
| 4.6 | Step 2 — Coverage sidebar | Right panel shows coverage ring + per-item progress bars | NOT TESTED |
| 4.7 | Coverage ring | SVG ring, color changes: green ≥100%, amber 70–99%, red <70% | NOT TESTED |
| 4.8 | Coverage sidebar — incomplete warning | Amber warning box when coverage <100% | NOT TESTED |
| 4.9 | Step 3 — Pricing & Delivery | Base cost, currency, shipping, delivery date, payment terms | NOT TESTED |
| 4.10 | Wizard footer | Cancel (left) + Back/Next (right) buttons in clean footer bar | NOT TESTED |
| 4.11 | Create Package submits | Package created, procurement plan updated | NOT TESTED |
| 4.12 | Edit Package opens with data | Step 1 pre-filled with package data | NOT TESTED |

---

## 5. Coverage Summary

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 5.1 | Coverage modal opens | Opens from "Analyze Coverage" button | NOT TESTED |
| 5.2 | Coverage per-item breakdown | Shows coverage for each project item | NOT TESTED |
| 5.3 | Create for remaining demand | Button to open wizard with remaining demand | NOT TESTED |

---

## 6. Finalized Decisions

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 6.1 | Decisions page loads | RivarPageHeader with finalize + refresh actions | NOT TESTED |
| 6.2 | Decision table | Compact table with status pills | NOT TESTED |
| 6.3 | Status pills | PROPOSED / FINALIZED / LOCKED status pills styled correctly | NOT TESTED |

---

## 7. Procurement Plan

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 7.1 | Procurement plan loads | RivarPageHeader with export button | NOT TESTED |
| 7.2 | Plan table | Delivery timeline visible | NOT TESTED |
| 7.3 | Export to Excel | Works | NOT TESTED |

---

## 8. Finance

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 8.1 | Finance page loads | RivarPageHeader + tabs | NOT TESTED |
| 8.2 | Invoice/payment tab | InvoicePaymentManagement renders with Rivar theme | NOT TESTED |
| 8.3 | Supplier payment tab | Supplier payment flows accessible | NOT TESTED |
| 8.4 | Budget management tab | Budget table renders | NOT TESTED |
| 8.5 | Currency management tab | Currency and exchange rate table renders | NOT TESTED |

---

## 9. Reports & Analytics

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 9.1 | Reports page loads | RivarPageHeader with export button | NOT TESTED |
| 9.2 | Analytics page loads | RivarPageHeader + project filter | NOT TESTED |
| 9.3 | Charts render | Recharts in white panels with Rivar colors | NOT TESTED |

---

## 10. Audit Logs

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 10.1 | Audit logs page loads | RivarPageHeader "Audit Logs" | NOT TESTED |
| 10.2 | Audit log table | Compact table, filter panel | NOT TESTED |

---

## 11. Admin Pages

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 11.1 | Users page loads | RivarPageHeader, user table | NOT TESTED |
| 11.2 | Add user dialog | Opens, role select works | NOT TESTED |
| 11.3 | Suppliers page loads | RivarPageHeader with subtitle + add button | NOT TESTED |
| 11.4 | Items master loads | RivarPageHeader, item table | NOT TESTED |
| 11.5 | Weights page loads | RivarPageHeader with subtitle | NOT TESTED |
| 11.6 | Currency management loads | RivarPageHeader, currency table | NOT TESTED |

---

## 12. Projects

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 12.1 | Projects page loads | RivarPageHeader + stat cards | NOT TESTED |
| 12.2 | Create project dialog | Opens with form | NOT TESTED |
| 12.3 | Project items page | RivarPageHeader with back button | NOT TESTED |

---

## 13. RTL / Persian Check

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 13.1 | Switch to Persian | Language switcher → فارسی, page direction flips to RTL | NOT TESTED |
| 13.2 | Sidebar RTL | Sidebar anchor switches to right side | NOT TESTED |
| 13.3 | Nav items RTL | Icon + text direction correct in RTL | NOT TESTED |
| 13.4 | Forms RTL | Inputs align right, labels correct | NOT TESTED |
| 13.5 | Tables RTL | Header and cell alignment correct | NOT TESTED |
| 13.6 | Topbar RTL | Actions align correctly | NOT TESTED |
| 13.7 | Persian font | Yekan Bakh FaNum used for Persian text | NOT TESTED |

---

## 14. Responsive / Desktop Check

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 14.1 | Desktop (1280px+) | Sidebar visible, all content in main area | NOT TESTED |
| 14.2 | Laptop (960-1280px) | Sidebar visible, metric cards 2-col | NOT TESTED |
| 14.3 | Tablet (600-960px) | Sidebar collapses to hamburger | NOT TESTED |
| 14.4 | Mobile (< 600px) | Full hamburger, stacked cards | NOT TESTED |

---

## 15. Optimization

| # | Check | Expected | Status |
|---|-------|----------|--------|
| 15.1 | Optimization page loads | RivarPageHeader + run button | NOT TESTED |
| 15.2 | Run optimization (if data) | Optimization flow intact | NOT TESTED |

---

## Server Quality Gates (to be run on `/root/pdss_demo`)

```bash
# 1. Container health
COMPOSE_PROJECT_NAME=pdss_demo docker compose -f /root/pdss_demo/docker-compose.yml ps

# 2. Backend health identity
curl -sS http://127.0.0.1:18010/health

# 3. Backend full test suite
COMPOSE_PROJECT_NAME=pdss_demo docker compose -f /root/pdss_demo/docker-compose.yml run --rm backend \
  python -m pytest tests -q

# 4. Phase 8 smoke tests
COMPOSE_PROJECT_NAME=pdss_demo docker compose -f /root/pdss_demo/docker-compose.yml run --rm backend \
  python -m pytest tests/test_phase8_release_candidate_smoke.py -q

# 5. Frontend build
COMPOSE_PROJECT_NAME=pdss_demo docker compose -f /root/pdss_demo/docker-compose.yml run --rm frontend \
  npm run build

# 6. Frontend tests (if runner stable)
COMPOSE_PROJECT_NAME=pdss_demo docker compose -f /root/pdss_demo/docker-compose.yml run --rm frontend \
  npm test -- --watchAll=false
```

### Expected Results (from previous phase baseline)

| Gate | Expected |
|------|----------|
| docker compose ps | backend, frontend, postgres all Up/healthy |
| curl /health | `{"status":"healthy","version":"1.0.0-rc1","product":"Rivar","producer":"Corbit"}` |
| backend pytest full | `39 passed, 4 skipped, N warnings` |
| phase 8 smoke | `3 passed, N warnings` |
| frontend build | success (`Compiled with warnings` — pre-existing eslint warnings acceptable) |
| frontend tests | pass (or documented as `NO STABLE RUNNER`) |

---

*Prepared: 2026-06-20*  
*Phase 11C — Full UI Redesign System Migration*  
*Manual browser verification required after server deployment.*
