# Phase 11C — UI Inventory

**Date:** 2026-06-20  
**Scope:** `frontend/src/pages` and `frontend/src/components` (all sub-folders)  
**Purpose:** Complete inventory of every page and component before redesign begins.

---

## Pages (`frontend/src/pages`)

| File | Classification | Notes |
|------|----------------|-------|
| `AnalyticsDashboardPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel, RivarMetricCard; keep recharts |
| `AuditLogsPage.tsx` | redesigned | Apply RivarPageHeader, ResponsiveTable pattern |
| `CurrencyManagementPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `DashboardPage.tsx` | redesigned | Core reference page — follows `dashboard.html` |
| `FinalizedDecisionsPage.tsx` | redesigned | Apply RivarPageHeader, RivarStatusPill |
| `FinancePage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel, RivarStatusPill |
| `ItemsMasterPage.tsx` | redesigned | Apply RivarPageHeader, ResponsiveTable pattern |
| `LoginPage.tsx` | redesigned | Clean centered card, logo, brand identity |
| `OptimizationPage.tsx` | wrapped in new layout | Logic-heavy; uses RivarPageHeader wrapper only |
| `OptimizationPage_enhanced.tsx` | redesigned | Apply RivarPageHeader; this is the active route |
| `ProcurementPage.tsx` | redesigned | Core reference page — follows `procurement.html` |
| `ProcurementPlanPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `ProjectItemsPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `ProjectsPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `ReportsPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `SuppliersPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `UsersPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `WeightsPage.tsx` | redesigned | Apply RivarPageHeader, RivarPanel |
| `LoginPage.smoke.test.tsx` | test-only | Not a UI page; no redesign needed |

**Total pages inventoried: 18** (19 files; 1 is test-only)

---

## Components (`frontend/src/components`)

### Root-level components

| File | Classification | Notes |
|------|----------------|-------|
| `BudgetAnalysis.tsx` | redesigned | Apply RivarPanel, RivarMetricCard |
| `CurrencySelector.tsx` | wrapped | Logic-only form; apply consistent MUI field style |
| `DeliveryOptionsManager.tsx` | redesigned | Apply RivarPanel, RivarSection |
| `FeatureFlagsDebugPanel.tsx` | logic-only / no visual redesign needed | Dev/debug tool; no user-facing design changes |
| `InvoicePaymentManagement.tsx` | redesigned | Active page component; apply RivarPageHeader, RivarPanel, RivarStatusPill |
| `InvoicePaymentManagement_Old.tsx` | deprecated but still present | Still present in repo; confirmed not imported by live pages; safe to leave |
| `InvoicePaymentManagement_Simple.tsx` | deprecated but still present | Confirmed present; check import status — leave if not imported |
| `LanguageSwitcher.tsx` | wrapped | Logic-only; apply consistent icon-button style |
| `Layout.tsx` | redesigned | **Core shell** — follows sidebar/topbar reference design |
| `LocalizedDateProvider.tsx` | logic-only / no visual redesign needed | No visual output; pure provider |
| `ProjectFilter.tsx` | wrapped | Logic-only form control; apply consistent MUI field style |
| `ProjectPhases.tsx` | redesigned | Apply RivarPanel, RivarStatusPill |
| `ProtectedRoute.tsx` | logic-only / no visual redesign needed | No visual output; pure auth guard |
| `ResponsivePageHeader.tsx` | redesigned | Replaced by `RivarPageHeader`; updated to delegate |
| `ResponsiveTable.tsx` | redesigned | Apply Rivar table styling tokens |

### Sub-folder: `packages/`

| File | Classification | Notes |
|------|----------------|-------|
| `packages/CoverageSummaryModal.tsx` | redesigned | Core reference component; follows package-wizard.html coverage rail |
| `packages/PackageList.tsx` | redesigned | Core reference component; follows procurement.html package cards |

### Sub-folder: `PackageWizard/`

| File | Classification | Notes |
|------|----------------|-------|
| `PackageWizard/PackageWizard.tsx` | redesigned | Core reference — drawer-based, stepper, follows `package-wizard.html` |
| `PackageWizard/PackageWizardStep1.tsx` | redesigned | Metadata step; apply RivarSection, RivarPanel |
| `PackageWizard/PackageWizardStep2.tsx` | redesigned | Quantity cards; apply RivarPanel, quantity card pattern |
| `PackageWizard/PackageWizardStep3.tsx` | redesigned | Pricing & Delivery; apply RivarPanel, RivarSection |
| `PackageWizard/PackageWizard.smoke.test.tsx` | test-only | Not a UI component; no redesign needed |

**Total components inventoried: 22** (23 files; 1 is test-only)

---

## Summary

| Category | Count |
|----------|-------|
| Pages inventoried | 18 |
| Pages test-only | 1 |
| Pages to be redesigned | 17 |
| Pages logic-only / no visual redesign | 1 |
| Components inventoried | 22 |
| Components test-only | 1 |
| Components to be redesigned | 13 |
| Components wrapped / logic-only | 5 |
| Components deprecated but present | 2 |
| Components logic-only / no visual redesign | 2 |

---

## New Files to Be Created

### Theme
- `frontend/src/theme/rivarTheme.ts`

### Styles
- `frontend/src/styles/rivarDesignSystem.css`

### UI Primitives
- `frontend/src/components/ui/RivarPageHeader.tsx`
- `frontend/src/components/ui/RivarMetricCard.tsx`
- `frontend/src/components/ui/RivarPanel.tsx`
- `frontend/src/components/ui/RivarStatusPill.tsx`
- `frontend/src/components/ui/RivarCoverageRing.tsx`
- `frontend/src/components/ui/RivarToolbar.tsx`
- `frontend/src/components/ui/RivarEmptyState.tsx`
- `frontend/src/components/ui/RivarSection.tsx`

---

## Deprecated File Status

| File | Status | Action |
|------|--------|--------|
| `InvoicePaymentManagement_Old.tsx` | deprecated — not imported by live routes | Leave in repo; document as safe-to-leave |
| `InvoicePaymentManagement_Simple.tsx` | deprecated — needs import check | Leave in repo pending import verification |

---

*Inventory created: 2026-06-20*  
*Phase 11C — Full UI Redesign System Migration*
