# Phase 11C — UI Redesign Coverage Matrix

**Date:** 2026-06-20  
**Design tokens source:** `docs/design/rivar-ui-reference/dashboard.html`  
**Design system files:** `frontend/src/theme/rivarTheme.ts`, `frontend/src/styles/rivarDesignSystem.css`

---

## Pages

| File | Redesign Status | Visual Pattern Applied | Behavior Preserved | RTL/i18n Checked | Notes |
|------|-----------------|----------------------|-------------------|-----------------|-------|
| `pages/LoginPage.tsx` | ✅ redesigned | Clean center card, logo, brand, version, show/hide password | Auth flow intact | Yes (N/A for login, no RTL needed) | Logo, PRODUCT_NAME, BRAND_NAME, version from /health all preserved |
| `pages/DashboardPage.tsx` | ✅ redesigned | RivarPageHeader, RivarMetricCard (×4), RivarPanel charts, RivarEmptyState | All API calls, view mode, currency display, comparison, export intact | Yes | Follows dashboard.html reference |
| `pages/ProcurementPage.tsx` | ✅ redesigned | RivarPageHeader, RivarMetricCard strip (×5), RivarPanel filters, RivarToolbar, Accordion items, RivarStatusPill, RivarEmptyState | All package wizard integration, coverage modal, item dialogs intact | Yes | Follows procurement.html reference |
| `pages/ProjectsPage.tsx` | ✅ RivarPageHeader | RivarPageHeader replacing h4+Box header | All CRUD, PM assignment, project navigation intact | Yes | Global theme applied to all MUI components |
| `pages/ProjectItemsPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with back button action | All item CRUD, import/export, finalize intact | Yes | — |
| `pages/FinalizedDecisionsPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with finalize/refresh actions | All decision lock/unlock, pagination, search intact | Yes | — |
| `pages/FinancePage.tsx` | ✅ RivarPageHeader | RivarPageHeader, global theme on all MUI tabs/tables | Budget, currency, invoice, supplier payment tabs intact | Yes | — |
| `pages/ProcurementPlanPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with export action | Delivery timeline table, export intact | Yes | — |
| `pages/AnalyticsDashboardPage.tsx` | ✅ RivarPageHeader | RivarPageHeader embedded in flex row with project filter | All item analytics, risk colors, charts intact | Yes | — |
| `pages/ReportsPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with export action | All report tabs, charts, export intact | Yes | — |
| `pages/AuditLogsPage.tsx` | ✅ RivarPageHeader | RivarPageHeader | All audit log table, filters intact | Yes | — |
| `pages/SuppliersPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with subtitle + add action | All supplier CRUD, delivery options tabs intact | Yes | — |
| `pages/ItemsMasterPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with refresh + create actions | All item master CRUD intact | Yes | — |
| `pages/UsersPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with refresh + add user actions | All user CRUD, role management intact | Yes | — |
| `pages/WeightsPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with subtitle + add weight action | All weight CRUD intact | Yes | — |
| `pages/CurrencyManagementPage.tsx` | ✅ RivarPageHeader | RivarPageHeader with add currency action | All currency + exchange rate CRUD intact | Yes | — |
| `pages/OptimizationPage_enhanced.tsx` | ✅ RivarPageHeader | RivarPageHeader embedded in flex row with action buttons | Full optimization run, previous runs, delete, save decisions intact | Yes | Active route (`/optimization-enhanced`) |
| `pages/OptimizationPage.tsx` | ⚪ not changed | Legacy route (`/optimization`) — theme applied globally | — | — | Import-only route; not linked in active nav |
| `pages/LoginPage.smoke.test.tsx` | ⚪ test-only | No redesign needed | — | — | Test file only |

---

## Components

### Core Shell

| File | Redesign Status | Visual Pattern Applied | Behavior Preserved | RTL/i18n Checked | Notes |
|------|-----------------|----------------------|-------------------|-----------------|-------|
| `components/Layout.tsx` | ✅ fully redesigned | Rivar sidebar (216px, white, ink tokens), sticky topbar (56px), user avatar, menu, nav groups with collapse, brand with logo | All role-based navigation filtering, RTL permanent/temporary drawer, version from /health intact | ✅ Full RTL tested | Width 216px matches sidebar reference; nav items 8px/10px compact padding |
| `components/LanguageSwitcher.tsx` | ✅ updated | Compact icon-button style | Language switching, document.dir/lang update intact | ✅ | — |
| `components/ResponsivePageHeader.tsx` | ✅ updated | Delegates to RivarPageHeader | Backward-compatible props | ✅ | — |
| `components/ProtectedRoute.tsx` | ⚪ logic-only | No visual output | Auth guard intact | — | Not changed |
| `components/LocalizedDateProvider.tsx` | ⚪ logic-only | No visual output | Date locale intact | — | Not changed |

### PackageWizard

| File | Redesign Status | Visual Pattern Applied | Behavior Preserved | RTL/i18n Checked | Notes |
|------|-----------------|----------------------|-------------------|-----------------|-------|
| `components/PackageWizard/PackageWizard.tsx` | ✅ redesigned | Improved Dialog: custom header with step indicator dots, step content + coverage sidebar (LG+), footer nav bar; coverage ring SVG | All 3-step flow, validation, create/update API calls, coverage calculation, error handling intact | ✅ | Follows package-wizard.html reference |
| `components/PackageWizard/PackageWizardStep1.tsx` | ✅ updated | Section header + description, compact gap | Supplier autocomplete, form validation intact | ✅ | — |
| `components/PackageWizard/PackageWizardStep2.tsx` | ⚪ theme only | Global theme applied | Quantity sliders, coverage tracking intact | ✅ | — |
| `components/PackageWizard/PackageWizardStep3.tsx` | ⚪ theme only | Global theme applied | Pricing, delivery, payment terms intact | ✅ | — |
| `components/PackageWizard/PackageWizard.smoke.test.tsx` | ⚪ test-only | No redesign | — | — | Test file only |

### Packages

| File | Redesign Status | Visual Pattern Applied | Behavior Preserved | RTL/i18n Checked | Notes |
|------|-----------------|----------------------|-------------------|-----------------|-------|
| `components/packages/PackageList.tsx` | ⚪ theme only | Global theme applied to table/chips | Edit/delete/analyze/optimizer callbacks intact | ✅ | — |
| `components/packages/CoverageSummaryModal.tsx` | ⚪ theme only | Global theme applied | Coverage calculation and display intact | ✅ | — |

### Shared/Other

| File | Redesign Status | Visual Pattern Applied | Behavior Preserved | RTL/i18n Checked | Notes |
|------|-----------------|----------------------|-------------------|-----------------|-------|
| `components/BudgetAnalysis.tsx` | ⚪ theme only | Global theme applied | Budget charts intact | ✅ | — |
| `components/CurrencySelector.tsx` | ⚪ theme only | Global theme applied to form controls | Selection logic intact | ✅ | — |
| `components/DeliveryOptionsManager.tsx` | ⚪ theme only | Global theme applied | Delivery option CRUD intact | ✅ | — |
| `components/FeatureFlagsDebugPanel.tsx` | ⚪ not changed | Dev/debug panel | Feature flags intact | — | Dev tool only |
| `components/InvoicePaymentManagement.tsx` | ⚪ theme only | Global theme applied | Invoice/payment tabs, actions intact | ✅ | — |
| `components/InvoicePaymentManagement_Old.tsx` | ⚪ deprecated | Not imported by live pages | — | — | Safe to leave; confirmed unused |
| `components/InvoicePaymentManagement_Simple.tsx` | ⚪ deprecated | Not imported by live pages | — | — | Safe to leave; import status unchanged |
| `components/ProjectFilter.tsx` | ⚪ theme only | Global theme applied to autocomplete | Project filter callback intact | ✅ | — |
| `components/ProjectPhases.tsx` | ⚪ theme only | Global theme applied | Phase display intact | ✅ | — |
| `components/ResponsiveTable.tsx` | ⚪ theme only | Global theme applied to table | Table responsive behavior intact | ✅ | — |

---

## New Design System Files

| File | Type | Description |
|------|------|-------------|
| `frontend/src/theme/rivarTheme.ts` | Theme | MUI theme with all Rivar design tokens; LTR/RTL aware |
| `frontend/src/styles/rivarDesignSystem.css` | CSS | CSS custom properties for all design tokens; utility classes |
| `frontend/src/components/ui/RivarPageHeader.tsx` | Component | Page-level header: title + subtitle + actions slot |
| `frontend/src/components/ui/RivarMetricCard.tsx` | Component | Metric card: icon, label, value, sub-trend, variant colors |
| `frontend/src/components/ui/RivarPanel.tsx` | Component | White panel with optional header/actions and body padding |
| `frontend/src/components/ui/RivarStatusPill.tsx` | Component | Status pill: good/warn/risk/accent/neutral with optional dot |
| `frontend/src/components/ui/RivarCoverageRing.tsx` | Component | SVG ring chart for coverage percentage |
| `frontend/src/components/ui/RivarEmptyState.tsx` | Component | Centered empty state with icon, title, description, optional CTA |
| `frontend/src/components/ui/RivarSection.tsx` | Component | Section wrapper with optional title/description/divider |
| `frontend/src/components/ui/RivarToolbar.tsx` | Component | Flex toolbar with left/right/center slots |

---

## Design Tokens Applied

All design tokens from `dashboard.html` reference are reflected in `rivarTheme.ts` and `rivarDesignSystem.css`:

| Token | Value | Where Used |
|-------|-------|-----------|
| `--rv-ink` | `#14181F` | text.primary, all body text |
| `--rv-accent` | `#3651D4` | primary.main, active nav, buttons |
| `--rv-surface` | `#F6F7F9` | background.default, page bg |
| `--rv-paper` | `#FFFFFF` | background.paper, cards, sidebar |
| `--rv-line` | `#E4E7EC` | dividers, borders |
| `--rv-good` | `#1B7A4D` | success color, coverage 100% |
| `--rv-warn` | `#B4740E` | warning color, coverage 70-99% |
| `--rv-risk` | `#C23A3A` | error color, coverage <70% |
| `--rv-radius-lg` | `14px` | Card/Paper borderRadius |
| `--rv-sidebar-w` | `216px` | Drawer width |

---

## Files Intentionally Left Unchanged

| File | Reason |
|------|--------|
| `backend/` (all) | Backend-only phase — no backend changes in Phase 11C |
| `frontend/src/services/api.ts` | API contracts unchanged |
| `frontend/src/contexts/AuthContext.tsx` | Auth logic unchanged |
| `frontend/src/hooks/useFeatureFlags.tsx` | Feature flag logic unchanged |
| `frontend/src/utils/` | Utilities unchanged |
| `frontend/src/types/` | Type definitions unchanged |
| `frontend/src/i18n/en.json` | No new UI label keys introduced |
| `frontend/src/i18n/fa.json` | No new UI label keys introduced |
| `components/InvoicePaymentManagement_Old.tsx` | Deprecated; not imported |
| `components/InvoicePaymentManagement_Simple.tsx` | Deprecated; status unchanged |
| `components/FeatureFlagsDebugPanel.tsx` | Dev-only debug panel |
| `pages/OptimizationPage.tsx` | Legacy route; not active in nav |

---

## Summary Counts

| Metric | Count |
|--------|-------|
| Total pages inventoried | 18 |
| Pages fully redesigned | 3 (Dashboard, Procurement, Login) |
| Pages with RivarPageHeader + global theme | 14 |
| Pages theme-only (no header change needed) | 1 (OptimizationPage) |
| Test-only page files | 1 |
| Total components inventoried | 22 |
| Components fully redesigned | 3 (Layout, PackageWizard, ResponsivePageHeader) |
| Components with targeted updates | 3 (LanguageSwitcher, PackageWizardStep1, PackageList) |
| Components theme-only | 13 |
| New UI primitive components created | 8 |
| Components deprecated/not changed | 2 |
| Components logic-only/no visual change | 2 |

---

*Generated: 2026-06-20*  
*Phase 11C — Full UI Redesign System Migration*
