# Procurement UI Package-Centric Implementation

## Overview

This document describes the package-centric procurement UI implementation. **Legacy procurement option workflows have been completely removed.** The system now operates exclusively in package mode.

## Architecture

### Feature Flags

The system maintains feature flags for future extensibility, but package mode is **always enabled**:
- `ENABLE_PACKAGE_PROCUREMENT`: Always `true` (legacy removed)
- `LEGACY_PROJECT_ITEM_FALLBACK`: Always `false` (legacy removed)
- `REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS`: Requires package_id for new procurement options
- `ENABLE_PACKAGE_BASED_OPTIMIZATION`: Enables optimizer to use packages
- `SUPPLIER_NORMALIZATION_ENFORCED`: Enforces supplier_id usage

Flags are managed via:
- Backend: `/api/config/feature-flags` endpoint
- Frontend: `useFeatureFlags()` hook with QA override support (non-production only)

**Note**: The frontend always operates in package mode regardless of backend flag values. Legacy option creation/editing UI has been removed.

### Components

#### PackageWizard (`components/PackageWizard/`)
3-step wizard for creating packages:
1. **Step 1 - Metadata**: Package name, supplier, type (FULL/PARTIAL/CUSTOM), description
2. **Step 2 - Quantity Composition**: 
   - Main item quantity (with coverage display)
   - Subitem quantities (sliders/inputs with validation)
   - Real-time coverage summary
   - "Analyze Coverage & Remaining Demand" button
3. **Step 3 - Pricing & Delivery**: Base cost, currency, shipping, delivery options, payment terms

#### PackageList (`components/packages/PackageList.tsx`)
Displays packages in a table format with:
- Package name, type, supplier
- Coverage percentage
- Subitem count
- Procurement option count
- Actions: Analyze, Send to Optimizer, Edit, Delete

#### CoverageSummaryModal (`components/packages/CoverageSummaryModal.tsx`)
Modal showing:
- Overall coverage statistics
- Per-item coverage breakdown
- Subitem coverage details
- "Create for Remaining Demand" actions

### Pages

#### ProcurementPage (`pages/ProcurementPage.tsx`)
**Package-only implementation.** Always renders:
- `PackageList` component for each project item
- "Create Package" button to open PackageWizard
- "Analyze Coverage" button in header
- Empty state when no items/packages exist

Features:
- Package wizard integration
- Coverage analysis modal
- Optimizer integration (via packages)
- Lazy-loaded package data for performance
- Memoized filtering and search

**Legacy procurement option UI has been completely removed.**

## Workflows

### Creating a Package

1. User clicks "Create Package" button on a project item
2. Package Wizard opens with project item context
3. Step 1: Enter package metadata (name, supplier, type, description)
4. Step 2: Set quantities (main item + subitems), view real-time coverage summary
5. Step 3: Set pricing and delivery details (base cost, currency, shipping, delivery options, payment terms)
6. Submit creates:
   - Package record
   - Associated procurement option (linked via `package_id`)
   - Package subitems (if any)

### Analyzing Coverage

1. Click "Analyze Coverage" button in header
2. CoverageSummaryModal opens showing:
   - Overall coverage statistics
   - Per-item breakdown
   - Remaining demand
3. Can create packages for remaining demand from modal

### Optimizer Integration

1. Select packages from PackageList
2. Click "Send to Optimizer" action
3. Optimizer preview runs with selected package IDs
4. Review optimizer suggestion
5. Finalize selection (creates finalized decisions)

## API Endpoints

### Packages
- `GET /api/packages/by-project-item/:projectItemId` - List packages for item
- `GET /api/projects/:projectId/packages` - List packages for project
- `GET /api/packages/:id` - Get package details
- `POST /api/packages/` - Create package
- `PUT /api/packages/:id` - Update package
- `DELETE /api/packages/:id` - Delete package
- `POST /api/packages/subitems/` - Create package subitem
- `PUT /api/packages/subitems/:id` - Update package subitem
- `DELETE /api/packages/subitems/:id` - Delete package subitem

### Coverage
- `GET /api/packages/coverage/:projectItemId` - Get coverage for item
- `GET /api/projects/:projectId/coverage-summary` - Get project coverage summary

### Optimizer
- `POST /api/projects/:projectId/optimizer/preview` - Preview optimization with packages

## QA Overrides

In non-production environments, QA can override feature flags via:
- `FeatureFlagsDebugPanel` component (accessible via drawer)
- Overrides stored in localStorage
- Persistent banner when overrides active
- Toast notifications on toggle

## Testing

### Unit Tests
- `__tests__/components/PackageWizard.test.tsx` - Wizard validation, step navigation
- `__tests__/hooks/useFeatureFlags.test.tsx` - Flag merging, override handling

### E2E Tests (Cypress/Playwright)
- Enable package mode via QA drawer
- Create package with main + subitem quantities
- Run optimizer with packages
- Finalize and verify coverage

## Migration Notes

**Legacy procurement option workflows have been completely removed from the frontend:**
- No legacy option creation/editing dialogs
- No legacy options table
- No legacy API calls (`/procurement-options`)
- Package mode is the only path

**Backend compatibility:**
- Backend still supports legacy procurement options (for backward compatibility)
- All new procurement must go through packages
- Existing legacy options may be visible in backend but are not accessible via UI

**Data requirements:**
- All new procurement options must be created via packages
- Packages require `supplier_id` (normalized supplier reference)
- Package subitems are optional but recommended for accurate coverage tracking
