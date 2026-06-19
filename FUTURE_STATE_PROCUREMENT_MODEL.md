# Future-State Procurement Data Model Design

## Executive Summary

This document proposes a **package-based procurement data model** that extends the current item-level model to support both entire project-item sourcing and granular sub-item/package sourcing. The design maintains backward compatibility while enabling procurement teams to assign suppliers at the sub-item level and track execution accordingly.

---

## Proposed Entity-Relationship Specification

### Core Package Tables

| Entity | Key Columns | Primary Relationships | Purpose |
|--------|-------------|----------------------|---------|
| **procurement_packages** | `id` (PK), `project_item_id` (FK), `package_name`, `package_type` (ENUM: 'FULL', 'PARTIAL', 'CUSTOM'), `supplier_id` (FK, nullable), `is_active`, `created_at` | → `project_items` (N:1), → `suppliers` (N:1), → `package_subitems` (1:N), → `procurement_options` (1:N), → `finalized_decisions` (1:N) | Groups sub-items into procurement units (packages) |
| **package_subitems** | `id` (PK), `package_id` (FK), `project_item_subitem_id` (FK), `quantity_covered` (INT), `is_fully_covered` (BOOL), `coverage_percentage` (NUMERIC) | → `procurement_packages` (N:1), → `project_item_subitems` (N:1) | Maps sub-items to packages with coverage details |
| **procurement_options** (MODIFIED) | `id` (PK), `package_id` (FK, nullable), `project_item_id` (FK, nullable, legacy), `item_code` (nullable, legacy), `supplier_id` (FK, **NOT NULL**), `supplier_name` (removed in future), `cost_amount`, `cost_currency`, `delivery_option_id` (FK), `is_active`, `is_finalized` | → `procurement_packages` (N:1), → `suppliers` (N:1), → `delivery_options` (N:1), → `finalized_decisions` (1:N) | Procurement quotes/options for packages (primary) or legacy project items (transitional) |
| **finalized_decisions** (MODIFIED) | `id` (PK), `package_id` (FK, nullable), `project_item_id` (FK, **NOT NULL**), `procurement_option_id` (FK), `quantity`, `final_cost_amount`, `final_cost_currency`, `status`, `delivery_status` | → `procurement_packages` (N:1), → `project_items` (N:1), → `procurement_options` (N:1), → `package_payments` (1:N) | Final procurement decisions tracking package-level execution |
| **package_payments** (NEW) | `id` (PK), `decision_id` (FK), `package_id` (FK), `supplier_id` (FK, **NOT NULL**), `payment_amount`, `currency`, `payment_date`, `status` | → `finalized_decisions` (N:1), → `procurement_packages` (N:1), → `suppliers` (N:1) | Payment tracking at package level (replaces/additional to supplier_payments) |
| **delivery_options** (MODIFIED) | `id` (PK), `project_item_id` (FK, nullable, legacy), `package_id` (FK, nullable), `delivery_date`, `invoice_amount_per_unit`, `invoice_timing_type` | → `project_items` (N:1, legacy), → `procurement_packages` (N:1, new) | Delivery timing configurable at package or project item level |
| **invoices** (MODIFIED) | `id` (PK), `decision_id` (FK), `package_id` (FK, nullable), `invoice_number`, `invoice_amount`, `currency`, `status`, `invoice_date`, `due_date` | → `finalized_decisions` (N:1), → `procurement_packages` (N:1, new), → `payments` (1:N) | Invoices for packages (buyer receipts) or legacy decisions |
| **payments** (MODIFIED) | `id` (PK), `invoice_id` (FK), `decision_id` (FK), `package_id` (FK, nullable), `payment_amount`, `currency`, `payment_date`, `status` | → `invoices` (N:1), → `finalized_decisions` (N:1), → `procurement_packages` (N:1, new) | Buyer receipts (customer payments) at package or decision level |
| **supplier_payments** (MODIFIED) | `id` (PK), `decision_id` (FK), `package_id` (FK, nullable), `supplier_id` (FK, nullable, **required for new records**), `supplier_name` (legacy, deprecated), `payment_amount`, `currency`, `payment_date`, `status` | → `finalized_decisions` (N:1), → `procurement_packages` (N:1, new), → `suppliers` (N:1, new) | Supplier payment tracking (legacy and package-level). supplier_id required for new records, nullable during transition. |

### Legacy/Transitional Fields

| Table | Legacy Field | New Field | Migration Strategy |
|-------|--------------|-----------|-------------------|
| **procurement_options** | `supplier_name` (TEXT) | `supplier_id` (FK, NOT NULL) | Mark `supplier_name` as deprecated, require `supplier_id`, migrate existing data |
| **procurement_options** | `project_item_id` (nullable) | `package_id` (nullable) | Allow both during transition, prefer `package_id` |
| **procurement_options** | `item_code` (nullable) | `package_id` (nullable) | Migrate to packages, deprecate `item_code` |
| **finalized_decisions** | (none) | `package_id` (nullable) | Add nullable field, existing decisions remain without package |
| **delivery_options** | `project_item_id` (NOT NULL) | `package_id` (nullable) | Make `project_item_id` nullable, add `package_id`, migrate existing |
| **invoices** (MODIFIED) | (none) | `package_id` (nullable) | Add nullable field, link invoices to packages for granular tracking |
| **payments** (MODIFIED) | (none) | `package_id` (nullable) | Add nullable field, track buyer receipts at package level |
| **supplier_payments** (MODIFIED) | `supplier_name` (string) | `supplier_id` (FK, nullable, **required for new records**), `package_id` (nullable) | Add FK and package_id. supplier_id is nullable during transition but required for all new records. Migrate supplier_name to supplier_id. |

---

## Detailed Table Specifications

### 1. procurement_packages

**Purpose:** Represents a group of sub-items that can be procured together from a supplier.

**Key Columns:**
- `id` (PK, SERIAL)
- `project_item_id` (FK to `project_items.id`, NOT NULL, indexed)
- `package_name` (TEXT, nullable) - Human-readable name like "Network Package", "Full Package"
- `package_type` (ENUM: 'FULL', 'PARTIAL', 'CUSTOM', NOT NULL)
  - `FULL`: Covers all sub-items of the project item (backward compatibility)
  - `PARTIAL`: Covers a subset of sub-items
  - `CUSTOM`: User-defined package with specific sub-item mix
- `supplier_id` (FK to `suppliers.id`, nullable) - Optional pre-assigned supplier
- `description` (TEXT, nullable)
- `is_active` (BOOLEAN, default TRUE)
- `created_at`, `updated_at` (TIMESTAMP)
- `created_by_id` (FK to `users.id`, nullable)

**Constraints:**
- At least one `FULL` package must exist per project item (for backward compatibility)
- `package_name` must be unique within a `project_item_id` (or allow NULL with auto-generation)

**Relationships:**
- **N:1** with `project_items` (every package belongs to one project item)
- **N:1** with `suppliers` (optional pre-assignment)
- **1:N** with `package_subitems` (package contains multiple sub-items)
- **1:N** with `procurement_options` (multiple quotes/options per package)
- **1:N** with `finalized_decisions` (multiple decisions per package over time)

---

### 2. package_subitems

**Purpose:** Maps sub-items to packages with coverage details (quantities, percentages).

**Key Columns:**
- `id` (PK, SERIAL)
- `package_id` (FK to `procurement_packages.id`, NOT NULL, indexed)
- `project_item_subitem_id` (FK to `project_item_subitems.id`, NOT NULL, indexed)
- `quantity_covered` (INTEGER, NOT NULL) - How many units of this sub-item are covered by this package
- `is_fully_covered` (BOOLEAN, default FALSE) - Whether this package fully satisfies the sub-item requirement
- `coverage_percentage` (NUMERIC(5,2), nullable) - Percentage of required quantity covered (0-100)
- `created_at` (TIMESTAMP)

**Constraints:**
- `quantity_covered >= 0`
- `coverage_percentage >= 0 AND coverage_percentage <= 100`
- UNIQUE constraint on (`package_id`, `project_item_subitem_id`) - prevent duplicate mappings
- `quantity_covered` cannot exceed the quantity required in `project_item_subitems.quantity`

**Relationships:**
- **N:1** with `procurement_packages` (many sub-items per package)
- **N:1** with `project_item_subitems` (each sub-item can be in multiple packages)

**Business Logic:**
- For a `FULL` package: All sub-items of the project item must be included with `is_fully_covered = TRUE`
- For a `PARTIAL` package: At least one sub-item must be included, but not all
- A sub-item can be covered by multiple packages (e.g., "Router from Package A" and "Router from Package B" as alternatives)

---

### 3. procurement_options (MODIFIED)

**Purpose:** Procurement quotes/options for packages (primary) or legacy project items (transitional).

**Key Columns:**
- `id` (PK, SERIAL)
- `package_id` (FK to `procurement_packages.id`, nullable, indexed) - **PRIMARY** link
- `project_item_id` (FK to `project_items.id`, nullable, legacy, indexed) - **DEPRECATED** for new records
- `item_code` (TEXT, nullable, legacy) - **DEPRECATED** for new records
- `supplier_id` (FK to `suppliers.id`, **NOT NULL**, indexed) - **REQUIRED** (no more nullable)
- `supplier_name` (TEXT, nullable, legacy) - **DEPRECATED**, kept for migration only
- `cost_amount` (NUMERIC(15,2), NOT NULL)
- `cost_currency` (VARCHAR(3), NOT NULL)
- `shipping_cost` (NUMERIC(15,2), nullable)
- `delivery_option_id` (FK to `delivery_options.id`, nullable)
- `expected_delivery_date` (DATE, nullable)
- `payment_terms` (JSON, nullable)
- `is_active` (BOOLEAN, default TRUE)
- `is_finalized` (BOOLEAN, default FALSE)
- `created_at`, `updated_at` (TIMESTAMP)

**Constraints:**
- **EXACTLY ONE** of `package_id` OR `project_item_id` OR `item_code` must be non-null (CHECK constraint)
- `supplier_id` is NOT NULL (enforced)
- `cost_amount > 0`

**Relationships:**
- **N:1** with `procurement_packages` (primary, new records)
- **N:1** with `project_items` (legacy, transitional)
- **N:1** with `suppliers` (required, non-nullable)
- **N:1** with `delivery_options` (optional)
- **1:N** with `finalized_decisions` (multiple decisions per option)

**Migration Notes:**
- Existing records: Keep `project_item_id` or `item_code`, set `supplier_id` from `supplier_name` mapping
- New records: Require `package_id` and `supplier_id`, do not allow `supplier_name`
- Transition period: Allow both patterns, but prefer `package_id`

---

### 4. finalized_decisions (MODIFIED)

**Purpose:** Final procurement decisions tracking package-level execution (or legacy item-level).

**Key Columns:**
- `id` (PK, SERIAL)
- `package_id` (FK to `procurement_packages.id`, nullable, indexed) - **NEW** field
- `project_item_id` (FK to `project_items.id`, **NOT NULL**, indexed) - **REQUIRED** (for aggregation)
- `procurement_option_id` (FK to `procurement_options.id`, NOT NULL)
- `quantity` (INTEGER, NOT NULL) - Quantity of packages procured (or legacy: quantity of project item)
- `final_cost_amount` (NUMERIC(15,2), NOT NULL)
- `final_cost_currency` (VARCHAR(3), NOT NULL)
- `status` (ENUM: 'PROPOSED', 'LOCKED', 'REVERTED', NOT NULL)
- `delivery_status` (VARCHAR(50), default 'AWAITING_DELIVERY')
- `purchase_date`, `delivery_date` (DATE, nullable)
- `decision_maker_id` (FK to `users.id`, NOT NULL)
- `finalized_at`, `finalized_by_id` (timestamp/user FK)
- (all existing fields remain: invoice tracking, payment tracking, etc.)

**Constraints:**
- `package_id` OR legacy pattern (check constraint: if `package_id` is NULL, must have valid `procurement_option_id` with `project_item_id`)
- `quantity > 0`

**Relationships:**
- **N:1** with `procurement_packages` (new, nullable)
- **N:1** with `project_items` (required, always present)
- **N:1** with `procurement_options` (required)
- **1:N** with `package_payments` (new, package-level payments)
- **1:N** with `supplier_payments` (legacy, kept for backward compatibility)

**Business Logic:**
- If `package_id` is NULL: Legacy decision (entire project item from one supplier)
- If `package_id` is NOT NULL: Package-level decision (specific sub-items from one supplier)
- Multiple decisions can exist for the same `project_item_id` (different packages)

---

### 5. package_payments (NEW)

**Purpose:** Payment tracking at package level (more granular than supplier_payments).

**Key Columns:**
- `id` (PK, SERIAL)
- `decision_id` (FK to `finalized_decisions.id`, NOT NULL, indexed)
- `package_id` (FK to `procurement_packages.id`, NOT NULL, indexed)
- `supplier_id` (FK to `suppliers.id`, **NOT NULL**, indexed) - **REQUIRED** (no string names)
- `payment_amount` (NUMERIC(12,2), NOT NULL)
- `currency` (VARCHAR(10), NOT NULL)
- `payment_date` (DATE, NOT NULL)
- `payment_method` (VARCHAR(50), NOT NULL)
- `reference_number` (TEXT, nullable)
- `status` (ENUM: 'pending', 'completed', 'failed', 'cancelled', NOT NULL)
- `notes` (TEXT, nullable)
- `created_at`, `updated_at` (TIMESTAMP)
- `created_by_id` (FK to `users.id`, nullable)

**Constraints:**
- `payment_amount > 0`
- `supplier_id` is NOT NULL (enforced FK)

**Relationships:**
- **N:1** with `finalized_decisions` (multiple payments per decision)
- **N:1** with `procurement_packages` (payments for specific packages)
- **N:1** with `suppliers` (required, non-nullable)

**Business Logic:**
- One decision can have multiple package payments (if decision covers multiple packages)
- Payment can be split across multiple installments (separate records)
- Aggregates to project item level for reporting

---

### 6. delivery_options (MODIFIED)

**Purpose:** Delivery timing configurable at package or project item level.

**Key Columns:**
- `id` (PK, SERIAL)
- `project_item_id` (FK to `project_items.id`, nullable, indexed) - **MADE NULLABLE** (legacy)
- `package_id` (FK to `procurement_packages.id`, nullable, indexed) - **NEW** field
- `delivery_date` (DATE, NOT NULL)
- `invoice_amount_per_unit` (NUMERIC(18,2), NOT NULL) - Supports values up to 999,999,999,999,999,999.99 (precision increased from NUMERIC(12,2))
- `invoice_timing_type` (VARCHAR(20), default 'RELATIVE')
- `invoice_issue_date`, `invoice_days_after_delivery` (existing fields)
- `preference_rank` (INTEGER, nullable)
- `is_active` (BOOLEAN, default TRUE)
- `created_at`, `updated_at` (TIMESTAMP)

**Constraints:**
- **EXACTLY ONE** of `project_item_id` OR `package_id` must be non-null (CHECK constraint)
- `delivery_date` must be in the future (or allow past for historical data)

**Relationships:**
- **N:1** with `project_items` (legacy, nullable)
- **N:1** with `procurement_packages` (new, nullable)
- **1:N** with `procurement_options` (options reference delivery options)

**Migration Notes:**
- Existing records: Keep `project_item_id`, set `package_id` to NULL
- New records: Prefer `package_id`, but allow `project_item_id` for backward compatibility
- For full packages: Delivery option can be at package level (all sub-items delivered together)
- **Precision update**: `invoice_amount_per_unit` precision increased from NUMERIC(12,2) to NUMERIC(18,2) to support larger invoice amounts (max: 999,999,999,999,999,999.99). Migration applied via `increase_invoice_amount_precision.sql`.

---

### 7. invoices (MODIFIED)

**Purpose:** Invoices issued to customers (buyer receipts) for packages or legacy decisions. Supports both consolidated invoicing (entire project item) and split invoicing (package-level).

**Key Columns:**
- `id` (PK, SERIAL)
- `decision_id` (FK to `finalized_decisions.id`, NOT NULL, indexed)
- `package_id` (FK to `procurement_packages.id`, nullable, indexed) - **NEW** field
- `invoice_number` (VARCHAR(100), UNIQUE, NOT NULL)
- `invoice_date` (TIMESTAMP WITH TIME ZONE, NOT NULL)
- `invoice_amount` (NUMERIC(15,2), NOT NULL)
- `currency` (VARCHAR(3), NOT NULL, default 'IRR')
- `due_date` (TIMESTAMP WITH TIME ZONE, NOT NULL)
- `status` (ENUM: 'draft', 'sent', 'paid', 'overdue', 'cancelled', NOT NULL, default 'draft')
- `payment_terms` (VARCHAR(100), nullable)
- `notes` (TEXT, nullable)
- `created_at` (TIMESTAMP WITH TIME ZONE, server default NOW())
- `updated_at` (TIMESTAMP WITH TIME ZONE, on update)

**Constraints:**
- `invoice_amount > 0` (CHECK constraint)
- `invoice_number` must be UNIQUE
- `package_id` is nullable (supports both consolidated and split invoicing)
- `invoice_date <= due_date` (application-level validation recommended)

**Relationships:**
- **N:1** with `finalized_decisions` (required, always present - every invoice links to a decision)
- **N:1** with `procurement_packages` (new, nullable - for package-level invoices)
- **1:N** with `payments` (multiple payments can pay one invoice - installments, partial payments)

**Business Logic:**
- **Consolidated Invoice**: If `package_id` is NULL, invoice covers entire decision (legacy behavior, single invoice for all packages)
- **Split Invoice**: If `package_id` is NOT NULL, invoice covers specific package within the decision (package-level invoicing)
- Multiple invoices can exist for the same decision:
  - Split invoices: One invoice per package (`package_id` set for each)
  - Consolidated invoice: One invoice covering all (`package_id = NULL`)
  - Hybrid: Mix of consolidated and split invoices
- Invoice amount validation:
  - If `package_id` present: Invoice amount should match the package cost (from procurement_option)
  - If `package_id` NULL: Invoice amount should match decision total (sum of all package costs)
- Invoice status lifecycle: draft → sent → paid/overdue → cancelled

**Index Considerations:**
- `idx_invoices_decision_id` (existing) - Fast lookup of invoices by decision
- `idx_invoices_package_id` (new) - Fast lookup of invoices by package
- `idx_invoices_status` (existing) - Filter invoices by status
- `idx_invoices_invoice_date` (existing) - Date range queries
- `idx_invoices_due_date` (existing) - Overdue invoice detection
- Composite index on `(decision_id, package_id)` may be useful for package-specific invoice queries

**Migration Notes:**
- Existing records: Keep `package_id = NULL` (legacy consolidated invoices)
- New records: Can set `package_id` for split invoicing or leave NULL for consolidated
- Migration Phase 2 (Line 945-1004): Scripts link existing invoices to FULL packages where applicable
- No breaking changes: Existing invoices continue to work with `package_id = NULL`

---

### 8. payments (MODIFIED)

**Purpose:** Buyer receipts (customer payments) for invoices, trackable at package or decision level. Supports both consolidated payments (covering entire invoice) and split payments (package-specific).

**Key Columns:**
- `id` (PK, SERIAL)
- `invoice_id` (FK to `invoices.id`, NOT NULL, indexed) - Required: payment always pays an invoice
- `decision_id` (FK to `finalized_decisions.id`, NOT NULL, indexed) - Required: payment is for a decision
- `package_id` (FK to `procurement_packages.id`, nullable, indexed) - **NEW** field
- `payment_date` (TIMESTAMP WITH TIME ZONE, NOT NULL)
- `payment_amount` (NUMERIC(15,2), NOT NULL)
- `currency` (VARCHAR(3), NOT NULL, default 'IRR')
- `payment_method` (ENUM: 'cash', 'bank_transfer', 'check', 'credit_card', NOT NULL)
- `reference_number` (VARCHAR(100), nullable) - Transaction reference, check number, etc.
- `status` (ENUM: 'pending', 'completed', 'failed', 'cancelled', NOT NULL, default 'pending')
- `notes` (TEXT, nullable)
- `created_at` (TIMESTAMP WITH TIME ZONE, server default NOW())
- `updated_at` (TIMESTAMP WITH TIME ZONE, on update)

**Constraints:**
- `payment_amount > 0` (CHECK constraint)
- `package_id` should match the invoice's `package_id` if invoice has one (application-level validation for consistency)
- `payment_date` should be <= current date (application-level validation)
- `payment_amount` cannot exceed invoice amount (application-level validation)

**Relationships:**
- **N:1** with `invoices` (required - payment always pays an invoice)
- **N:1** with `finalized_decisions` (required - payment is for a decision)
- **N:1** with `procurement_packages` (new, nullable - for package-level payments)

**Business Logic:**
- **Payment-Invoice Consistency**: 
  - If invoice has `package_id`, payment should also have `package_id` (matches invoice package)
  - If invoice has `package_id = NULL` (consolidated), payment should have `package_id = NULL` (consolidated payment)
- **Multiple Payments per Invoice**:
  - Installments: Multiple payments can pay one invoice over time
  - Partial payments: Customer can pay invoice in multiple transactions
  - Payment reconciliation: Sum of payments should not exceed invoice amount
- **Payment Status**:
  - `pending`: Payment initiated but not yet confirmed
  - `completed`: Payment successfully processed
  - `failed`: Payment attempt failed
  - `cancelled`: Payment cancelled/refunded
- **Aggregation**: Payments aggregate to project item level for cash flow reporting (via `decision_id` → `project_item_id`)

**Index Considerations:**
- `idx_payments_invoice_id` (existing) - Fast lookup of payments for an invoice
- `idx_payments_decision_id` (existing) - Fast lookup of payments for a decision
- `idx_payments_package_id` (new) - Fast lookup of payments by package
- `idx_payments_status` (existing) - Filter payments by status
- `idx_payments_payment_date` (existing) - Date range queries
- Composite index on `(invoice_id, package_id)` may be useful for package-specific payment reconciliation

**Migration Notes:**
- Existing records: Keep `package_id = NULL` (legacy consolidated payments)
- New records: Set `package_id` to match invoice's `package_id` for consistency
- Migration Phase 2 (Line 945-1004): Scripts link existing payments to invoices' packages where applicable
- No breaking changes: Existing payments continue to work with `package_id = NULL`

---

### 9. supplier_payments (MODIFIED)

**Purpose:** Payments made to suppliers for packages or legacy decisions (outflow tracking). Supports both consolidated payments (entire decision) and split payments (package-level). Tracks supplier payments with normalized FK references.

**Key Columns:**
- `id` (PK, SERIAL)
- `decision_id` (FK to `finalized_decisions.id`, NOT NULL, indexed)
- `package_id` (FK to `procurement_packages.id`, nullable, indexed) - **NEW** field
- `supplier_id` (FK to `suppliers.id`, nullable, indexed) - **NEW** field (preferred over supplier_name)
- `supplier_name` (VARCHAR(200), nullable, legacy) - **DEPRECATED** (kept for migration only)
- `item_code` (VARCHAR(100), NOT NULL, indexed) - Legacy field for backward compatibility
- `project_id` (FK to `projects.id`, NOT NULL, indexed)
- `payment_date` (DATE, NOT NULL)
- `payment_amount` (NUMERIC(12,2), NOT NULL)
- `currency` (VARCHAR(10), NOT NULL, default 'IRR')
- `payment_method` (VARCHAR(50), NOT NULL)
- `reference_number` (VARCHAR(100), nullable)
- `status` (ENUM: 'pending', 'completed', 'failed', 'cancelled', NOT NULL, default 'completed')
- `notes` (TEXT, nullable)
- `created_at` (TIMESTAMP WITH TIME ZONE, server default NOW())
- `updated_at` (TIMESTAMP WITH TIME ZONE, on update)
- `created_by_id` (FK to `users.id`, nullable)

**Constraints:**
- `payment_amount > 0` (CHECK constraint)
- **EXACTLY ONE** of `supplier_id` OR `supplier_name` must be non-null (CHECK constraint) - **Transitional requirement**
- `package_id` is nullable (supports legacy payments without packages)
- `payment_method` must be in ('cash', 'bank_transfer', 'check', 'credit_card')
- `status` must be in ('pending', 'completed', 'failed', 'cancelled')

**Relationships:**
- **N:1** with `finalized_decisions` (required - payment is for a decision)
- **N:1** with `procurement_packages` (new, nullable - for package-level payments)
- **N:1** with `suppliers` (new, preferred over supplier_name - normalized supplier reference)
- **N:1** with `projects` (required - payment is for a project)
- **N:1** with `users` (created_by - audit trail)

**Business Logic:**
- **Supplier Reference**:
  - **NEW RECORDS**: `supplier_id` is **REQUIRED** (NOT NULL) - use FK to suppliers table
  - **LEGACY RECORDS**: `supplier_name` is allowed during transition period
  - **MIGRATION**: Existing records are migrated from `supplier_name` to `supplier_id` via name matching
  - **FUTURE**: After Phase 4, `supplier_name` will be removed and `supplier_id` will be NOT NULL
- **Package-Level Payments**:
  - If `package_id` is NULL: Legacy payment (entire decision, consolidated payment)
  - If `package_id` is NOT NULL: Payment for specific package (split payment)
- **Multiple Payments per Decision**:
  - Installments: Multiple payments can exist for one decision (staged payments)
  - Split by package: One payment per package (different suppliers for different packages)
  - Payment aggregation: All payments aggregate to project item level for financial reporting
- **Payment Status**: Tracks payment lifecycle: pending → completed/failed/cancelled

**Index Considerations:**
- `idx_supplier_payments_decision_id` (existing) - Fast lookup of payments by decision
- `idx_supplier_payments_package_id` (new) - Fast lookup of payments by package
- `idx_supplier_payments_supplier_id` (new) - Fast lookup of payments by supplier (FK)
- `idx_supplier_payments_supplier_name` (existing, legacy) - Keep for migration queries
- `idx_supplier_payments_project_id` (existing) - Fast lookup by project
- `idx_supplier_payments_payment_date` (existing) - Date range queries
- `idx_supplier_payments_status` (existing) - Filter by status
- Composite index on `(decision_id, package_id)` may be useful for package-specific payment queries
- Composite index on `(supplier_id, payment_date)` may be useful for supplier payment history

**Migration Notes:**
- **Phase 1** (Line 892): Add `package_id` and `supplier_id` columns as nullable
- **Phase 2** (Line 945-1004): 
  - Link existing supplier_payments to packages (via decision → FULL package)
  - Migrate `supplier_name` to `supplier_id` by matching to suppliers table
  - Existing records: Keep `supplier_name` if `supplier_id` cannot be matched (manual review)
- **Transition Period** (Phase 3):
  - **NEW RECORDS**: Require `supplier_id` (NOT NULL), do not allow `supplier_name`
  - **LEGACY RECORDS**: Keep `supplier_name` until migration completes
  - CHECK constraint ensures at least one is present: `(supplier_id IS NOT NULL) OR (supplier_name IS NOT NULL)`
- **Phase 4** (Line 965): After migration completes:
  - Enforce `supplier_id` NOT NULL (remove CHECK constraint, add NOT NULL constraint)
  - Remove `supplier_name` column
- **No Breaking Changes**: Existing records continue to work with `supplier_name` during transition

---

## Workflow Narrative

### 1. Package Creation and Representation

#### Full Package (Entire Project Item)

When a project item is created (or migrated), a **default FULL package** is automatically created:

```python
# Pseudocode
package = ProcurementPackage(
    project_item_id=project_item.id,
    package_name=f"{project_item.item_code} - Full Package",
    package_type='FULL',
    supplier_id=None  # No pre-assignment
)

# Create package_subitems entries for all sub-items
for sub_item in project_item.sub_items:
    PackageSubItem(
        package_id=package.id,
        project_item_subitem_id=sub_item.id,
        quantity_covered=sub_item.quantity,  # Full coverage
        is_fully_covered=True,
        coverage_percentage=100.0
    )
```

**Purpose:** This maintains backward compatibility. Existing procurement workflows that operate at project item level continue to work by referencing the FULL package.

#### Partial Package (Subset of Sub-Items)

Users can create **PARTIAL packages** to group specific sub-items:

```python
# Example: Network components package
partial_package = ProcurementPackage(
    project_item_id=server_rack.id,
    package_name="Network Components Package",
    package_type='PARTIAL'
)

# Only include Router and Switch, not the Server
PackageSubItem(package_id=partial_package.id, project_item_subitem_id=router.id, quantity_covered=1, is_fully_covered=True)
PackageSubItem(package_id=partial_package.id, project_item_subitem_id=switch.id, quantity_covered=1, is_fully_covered=True)
# Server is NOT included
```

**Coexistence:** Multiple packages (FULL and PARTIAL) can exist simultaneously for the same project item. This allows:
- **FULL package**: "All components from Supplier A" (one quote)
- **PARTIAL packages**: "Router from Supplier B", "Switch from Supplier C" (separate quotes)
- Procurement team can compare: "Full package from A" vs "Router from B + Switch from C + Server from D"

#### Coverage Validation

The system must ensure that sub-item requirements are satisfied:

```python
# Validation logic
def validate_subitem_coverage(project_item_id):
    required = get_subitem_requirements(project_item_id)
    coverage = calculate_package_coverage(project_item_id)
    
    for sub_item in required:
        total_covered = sum(coverage[sub_item.id])
        if total_covered < sub_item.quantity:
            raise ValidationError(f"Sub-item {sub_item.name} not fully covered")
```

**Rules:**
- A sub-item can be covered by multiple packages (alternatives)
- Total coverage across all packages must meet or exceed required quantity
- Optimization engine can select the best combination of packages

---

### 2. Procurement Options and Quotes

#### Creating Options for Packages

Procurement team creates quotes/options by linking to packages:

```python
# Option 1: Quote for FULL package
option_full = ProcurementOption(
    package_id=full_package.id,
    supplier_id=supplier_a.id,  # REQUIRED, no supplier_name
    cost_amount=50000,
    cost_currency='USD',
    delivery_option_id=delivery_opt.id
)

# Option 2: Quote for PARTIAL package (Router only)
option_router = ProcurementOption(
    package_id=router_package.id,
    supplier_id=supplier_b.id,
    cost_amount=15000,
    cost_currency='USD'
)

# Option 3: Quote for another PARTIAL package (Switch only)
option_switch = ProcurementOption(
    package_id=switch_package.id,
    supplier_id=supplier_c.id,
    cost_amount=8000,
    cost_currency='USD'
)
```

**Key Points:**
- `supplier_id` is **required** (no more `supplier_name` strings)
- Options link to packages, not directly to project items
- Multiple options can exist for the same package (different suppliers, prices, terms)

#### Legacy Options (Backward Compatibility)

Existing procurement options that reference `project_item_id` or `item_code` continue to work:

```python
# Legacy option (migrated or created during transition)
legacy_option = ProcurementOption(
    project_item_id=project_item.id,  # Legacy link
    supplier_id=supplier_a.id,  # Migrated from supplier_name
    cost_amount=50000,
    cost_currency='USD'
)
```

**Migration Strategy:**
- Existing options: Create a FULL package automatically and link option to it
- Or: Allow `project_item_id` during transition, but prefer `package_id` for new records

---

### 3. Optimization Engine Integration

#### Reading Package-Based Options

The optimizer reads procurement options grouped by packages:

```python
def get_procurement_options_for_item(project_item_id):
    # Get all packages for this project item
    packages = get_packages(project_item_id)
    
    # Get all options for these packages
    options = []
    for package in packages:
        package_options = get_options_for_package(package.id)
        for option in package_options:
            option.package = package
            option.covered_subitems = get_package_subitems(package.id)
            options.append(option)
    
    return options
```

#### Cost Calculation

The optimizer calculates costs at package level:

```python
def calculate_package_cost(option):
    # Base cost from option
    cost = option.cost_amount
    
    # Add shipping if applicable
    if option.shipping_cost:
        cost += option.shipping_cost
    
    # Cost is for the entire package (all covered sub-items)
    return (cost, option.cost_currency)
```

#### Decision Variables

The optimizer creates decision variables for packages, not individual sub-items:

```python
# Variable: Should we select this package option?
var_select_package_A = solver.IntVar(0, 1, "select_package_A")
var_select_package_B = solver.IntVar(0, 1, "select_package_B")
var_select_package_C = solver.IntVar(0, 1, "select_package_C")

# Constraint: All sub-items must be covered
for sub_item in required_subitems:
    total_coverage = 0
    for package in packages_covering_subitem(sub_item):
        if package.type == 'FULL':
            total_coverage += var_select_package_FULL * sub_item.quantity
        else:
            total_coverage += var_select_package_PARTIAL * package.quantity_covered
    
    solver.Add(total_coverage >= sub_item.quantity)
```

#### Output: Finalized Decisions

The optimizer creates `finalized_decisions` records:

```python
# Decision for FULL package
decision = FinalizedDecision(
    package_id=full_package.id,
    project_item_id=project_item.id,  # Always present for aggregation
    procurement_option_id=option_full.id,
    quantity=1,  # One package
    final_cost_amount=50000,
    final_cost_currency='USD'
)

# OR: Decision for PARTIAL package combination
decision_router = FinalizedDecision(
    package_id=router_package.id,
    project_item_id=project_item.id,
    procurement_option_id=option_router.id,
    quantity=1
)

decision_switch = FinalizedDecision(
    package_id=switch_package.id,
    project_item_id=project_item.id,
    procurement_option_id=option_switch.id,
    quantity=1
)
```

**Aggregation:** All decisions for the same `project_item_id` are aggregated for reporting, but tracked separately for execution.

---

### 4. Execution and Payment Workflows

#### Delivery Tracking

Delivery options can be at package level:

```python
# Delivery option for FULL package (all sub-items together)
delivery_full = DeliveryOption(
    package_id=full_package.id,
    delivery_date=date(2025, 2, 15),
    invoice_amount_per_unit=50000
)

# Delivery option for PARTIAL package (Router only)
delivery_router = DeliveryOption(
    package_id=router_package.id,
    delivery_date=date(2025, 2, 10),  # Earlier delivery
    invoice_amount_per_unit=15000
)
```

**Tracking:** When delivery is confirmed, the system updates `finalized_decisions.delivery_status` at package level.

#### Payment Processing

Payments are tracked at package level:

```python
# Payment for FULL package
payment = PackagePayment(
    decision_id=decision.id,
    package_id=full_package.id,
    supplier_id=supplier_a.id,  # REQUIRED FK, no string
    payment_amount=50000,
    currency='USD',
    payment_date=date(2025, 2, 20),
    status='completed'
)

# Payment for PARTIAL package (Router)
payment_router = PackagePayment(
    decision_id=decision_router.id,
    package_id=router_package.id,
    supplier_id=supplier_b.id,
    payment_amount=15000,
    currency='USD',
    payment_date=date(2025, 2, 12)
)
```

**Aggregation:** Payments are aggregated to project item level for financial reporting:

```sql
-- Total payments for a project item
SELECT 
    pi.id,
    SUM(pp.payment_amount) as total_paid,
    COUNT(DISTINCT pp.supplier_id) as supplier_count
FROM project_items pi
JOIN finalized_decisions fd ON fd.project_item_id = pi.id
JOIN package_payments pp ON pp.decision_id = fd.id
WHERE pi.id = ?
GROUP BY pi.id
```

#### Supplier Payments (Legacy Compatibility)

The existing `supplier_payments` table remains for backward compatibility:

```python
# Legacy payment (if decision has no package_id)
legacy_payment = SupplierPayment(
    decision_id=legacy_decision.id,
    supplier_name="Supplier A",  # Legacy string
    payment_amount=50000,
    currency='USD'
)
```

**Migration:** Existing `supplier_payments` records continue to work. New records should use `package_payments` or enhanced `supplier_payments` with `package_id`.

---

### 5. Finance Workflows: Invoicing, Supplier Payments, and Buyer Receipts

#### Invoicing at Package and Project Item Levels

Finance team can create invoices at different granularities:

**Scenario 1: Consolidated Invoice (Entire Project Item)**

```python
# One invoice for entire decision (legacy behavior)
consolidated_invoice = Invoice(
    decision_id=decision.id,
    package_id=None,  # No package = consolidated
    invoice_number="INV-2025-001",
    invoice_date=date(2025, 2, 15),
    invoice_amount=50000,  # Total for all packages
    currency='USD',
    due_date=date(2025, 3, 15),
    status='sent'
)
```

**Purpose:** Single invoice covering all packages in the decision. Useful for customers who prefer consolidated billing.

**Scenario 2: Split Invoices (One Per Package)**

```python
# Invoice for Router package
invoice_router = Invoice(
    decision_id=decision.id,
    package_id=router_package.id,  # Package-specific
    invoice_number="INV-2025-002",
    invoice_date=date(2025, 2, 10),
    invoice_amount=15000,  # Router package cost
    currency='USD',
    due_date=date(2025, 3, 10),
    status='sent'
)

# Invoice for Switch package
invoice_switch = Invoice(
    decision_id=decision.id,
    package_id=switch_package.id,  # Package-specific
    invoice_number="INV-2025-003",
    invoice_date=date(2025, 2, 12),
    invoice_amount=8000,  # Switch package cost
    currency='USD',
    due_date=date(2025, 3, 12),
    status='sent'
)
```

**Purpose:** Separate invoices for each package. Useful when:
- Different payment terms per package
- Staggered deliveries require separate invoicing
- Customer accounting requires package-level tracking

**Business Rules:**
- Finance team chooses: consolidated or split invoices
- Can mix: Some packages consolidated, others split
- Invoice amount must match package cost (if `package_id` present) or decision total (if consolidated)
- Multiple invoices can exist for one decision (split invoices) or one invoice can cover multiple decisions (consolidated)

#### Buyer Receipts (Customer Payments) at Package Level

Customer payments are tracked via the `payments` table:

**Scenario 1: Payment Against Consolidated Invoice**

```python
# Customer pays consolidated invoice
payment = Payment(
    invoice_id=consolidated_invoice.id,
    decision_id=decision.id,
    package_id=None,  # Matches invoice (no package = consolidated)
    payment_date=date(2025, 3, 10),
    payment_amount=50000,
    currency='USD',
    payment_method='bank_transfer',
    status='completed'
)
```

**Scenario 2: Split Payments Against Package Invoices**

```python
# Customer pays Router invoice
payment_router = Payment(
    invoice_id=invoice_router.id,
    decision_id=decision.id,
    package_id=router_package.id,  # Matches invoice package
    payment_date=date(2025, 3, 5),
    payment_amount=15000,
    currency='USD',
    payment_method='bank_transfer',
    status='completed'
)

# Customer pays Switch invoice (partial payment)
payment_switch_partial = Payment(
    invoice_id=invoice_switch.id,
    decision_id=decision.id,
    package_id=switch_package.id,
    payment_date=date(2025, 3, 12),
    payment_amount=4000,  # Partial payment
    currency='USD',
    payment_method='check',
    status='completed'
)

# Second payment for Switch invoice
payment_switch_remaining = Payment(
    invoice_id=invoice_switch.id,
    decision_id=decision.id,
    package_id=switch_package.id,
    payment_date=date(2025, 3, 20),
    payment_amount=4000,  # Remaining amount
    currency='USD',
    payment_method='bank_transfer',
    status='completed'
)
```

**Business Rules:**
- Payment `package_id` should match invoice `package_id` (application-level validation)
- Multiple payments can pay one invoice (installments, partial payments)
- Payment status tracks: pending, completed, failed, cancelled
- Payments aggregate to project item for cash flow reporting

#### Supplier Payments (Outflow) at Package Level

Payments to suppliers are tracked via `supplier_payments` (enhanced) or `package_payments`:

**Scenario 1: Consolidated Payment to Supplier (FULL Package)**

```python
# Single payment for FULL package
supplier_payment = SupplierPayment(
    decision_id=decision.id,
    package_id=full_package.id,  # Package-specific
    supplier_id=supplier_a.id,  # REQUIRED FK
    supplier_name=None,  # Deprecated, use supplier_id
    item_code="SERVER-RACK-001",
    project_id=project.id,
    payment_date=date(2025, 2, 25),
    payment_amount=50000,
    currency='USD',
    payment_method='bank_transfer',
    status='completed'
)
```

**Scenario 2: Split Payments to Multiple Suppliers (PARTIAL Packages)**

```python
# Payment to Supplier B for Router package
payment_router_supplier = SupplierPayment(
    decision_id=decision_router.id,
    package_id=router_package.id,
    supplier_id=supplier_b.id,  # REQUIRED FK
    item_code="ROUTER-001",
    project_id=project.id,
    payment_date=date(2025, 2, 18),
    payment_amount=15000,
    currency='USD',
    payment_method='bank_transfer',
    status='completed'
)

# Payment to Supplier C for Switch package
payment_switch_supplier = SupplierPayment(
    decision_id=decision_switch.id,
    package_id=switch_package.id,
    supplier_id=supplier_c.id,  # REQUIRED FK
    item_code="SWITCH-001",
    project_id=project.id,
    payment_date=date(2025, 2, 20),
    payment_amount=8000,
    currency='USD',
    payment_method='check',
    status='completed'
)
```

**Business Rules:**
- **supplier_id requirement**: `supplier_id` is **REQUIRED for all new records** (FK to suppliers table, NOT NULL for new records)
- **Transition period**: `supplier_id` is nullable during migration phase to allow legacy records with `supplier_name`
- **Legacy support**: `supplier_name` is deprecated but kept for migration of existing records
- **CHECK constraint**: At least one of `supplier_id` OR `supplier_name` must be present (ensures data integrity during transition)
- **package_id**: Enables split payments (one payment per package) when set
- **Multiple payments**: Multiple payments can exist for one decision (installments, split by package)
- **Aggregation**: Payments aggregate to project item for financial reporting

#### Financial Aggregation and Reporting

**Project Item Level Aggregation:**

All financial records aggregate to project item level for reporting:

```sql
-- Total invoices for a project item (consolidated + split)
SELECT 
    pi.id,
    pi.item_code,
    COUNT(DISTINCT i.id) as invoice_count,
    SUM(CASE WHEN i.package_id IS NULL THEN i.invoice_amount ELSE 0 END) as consolidated_invoice_total,
    SUM(CASE WHEN i.package_id IS NOT NULL THEN i.invoice_amount ELSE 0 END) as split_invoice_total,
    SUM(i.invoice_amount) as total_invoiced
FROM project_items pi
JOIN finalized_decisions fd ON fd.project_item_id = pi.id
LEFT JOIN invoices i ON i.decision_id = fd.id
WHERE pi.id = ?
GROUP BY pi.id, pi.item_code;

-- Total buyer receipts (customer payments) for a project item
SELECT 
    pi.id,
    SUM(p.payment_amount) as total_received,
    COUNT(DISTINCT p.supplier_id) as payment_count
FROM project_items pi
JOIN finalized_decisions fd ON fd.project_item_id = pi.id
JOIN payments p ON p.decision_id = fd.id
WHERE pi.id = ?
GROUP BY pi.id;

-- Total supplier payments (outflow) for a project item
SELECT 
    pi.id,
    SUM(sp.payment_amount) as total_paid_to_suppliers,
    COUNT(DISTINCT sp.supplier_id) as supplier_count,
    COUNT(DISTINCT sp.package_id) as package_count
FROM project_items pi
JOIN finalized_decisions fd ON fd.project_item_id = pi.id
JOIN supplier_payments sp ON sp.decision_id = fd.id
WHERE pi.id = ?
GROUP BY pi.id;
```

**Package Level Reporting:**

Financial records can also be queried at package level:

```sql
-- Invoice and payment summary by package
SELECT 
    pp.id as package_id,
    pp.package_name,
    pp.package_type,
    SUM(i.invoice_amount) as total_invoiced,
    SUM(p.payment_amount) as total_received,
    SUM(sp.payment_amount) as total_paid_to_supplier
FROM procurement_packages pp
LEFT JOIN invoices i ON i.package_id = pp.id
LEFT JOIN payments p ON p.package_id = pp.id
LEFT JOIN supplier_payments sp ON sp.package_id = pp.id
WHERE pp.project_item_id = ?
GROUP BY pp.id, pp.package_name, pp.package_type;
```

**Split vs Consolidated Transaction Support:**

The model supports both patterns:

1. **Split Transactions:**
   - Multiple invoices (one per package)
   - Multiple buyer receipts (one per invoice/package)
   - Multiple supplier payments (one per package/supplier)

2. **Consolidated Transactions:**
   - Single invoice (package_id = NULL, covers all packages)
   - Single buyer receipt (package_id = NULL, pays consolidated invoice)
   - Single supplier payment (package_id = NULL, if one supplier for all)

3. **Hybrid Transactions:**
   - Consolidated invoice, split payments
   - Split invoices, consolidated payment
   - Any combination based on business needs

**Financial Reconciliation:**

The system ensures financial integrity:

```python
# Validation: Invoice amounts match package/decision costs
def validate_invoice_amounts(decision_id):
    decision = get_decision(decision_id)
    invoices = get_invoices(decision_id)
    
    total_invoiced = sum(inv.invoice_amount for inv in invoices)
    
    if decision.package_id:
        # Package-level: Invoice should match package cost
        package_cost = get_package_cost(decision.package_id)
        if total_invoiced != package_cost:
            raise ValidationError("Invoice amount mismatch")
    else:
        # Legacy: Invoice should match decision cost
        if total_invoiced != decision.final_cost_amount:
            raise ValidationError("Invoice amount mismatch")

# Validation: Payments match invoices
def validate_payment_reconciliation(invoice_id):
    invoice = get_invoice(invoice_id)
    payments = get_payments_for_invoice(invoice_id)
    
    total_paid = sum(p.payment_amount for p in payments)
    
    if total_paid > invoice.invoice_amount:
        raise ValidationError("Overpayment detected")
    
    if total_paid == invoice.invoice_amount:
        invoice.status = 'paid'
    elif total_paid > 0:
        invoice.status = 'partially_paid'
```

---

## Migration Considerations

### Backward Compatibility Strategy

#### Phase 1: Additive Changes (No Breaking Changes)

1. **Create `procurement_packages` table** (new table, no impact on existing)
2. **Add `package_id` columns** (nullable) to:
   - `procurement_options`
   - `finalized_decisions`
   - `delivery_options`
   - `invoices` (new - financial table)
   - `payments` (new - financial table)
   - `supplier_payments` (new - financial table)
3. **Add `supplier_id` column** (nullable) to `supplier_payments` (new - financial table)
4. **Make `supplier_id` NOT NULL** in `procurement_options` (migrate existing data first)
5. **Create `package_subitems` and `package_payments` tables** (new tables)
6. **Make `project_item_id` nullable** in `delivery_options` (to allow package-only links)
7. **Increase `invoice_amount_per_unit` precision** in `delivery_options` from NUMERIC(12,2) to NUMERIC(18,2) to support larger invoice amounts (max: 999,999,999,999,999,999.99). Migration applied via `increase_invoice_amount_precision.sql`.

#### Phase 2: Data Migration

1. **Create FULL packages for existing project items:**
   ```sql
   -- For each project_item with sub-items, create a FULL package
   INSERT INTO procurement_packages (project_item_id, package_name, package_type)
   SELECT id, item_code || ' - Full Package', 'FULL'
   FROM project_items
   WHERE id IN (SELECT DISTINCT project_item_id FROM project_item_subitems);
   ```

2. **Migrate existing procurement_options:**
   ```sql
   -- Link existing options to FULL packages
   UPDATE procurement_options po
   SET package_id = (
       SELECT pp.id
       FROM procurement_packages pp
       WHERE pp.project_item_id = po.project_item_id
       AND pp.package_type = 'FULL'
       LIMIT 1
   )
   WHERE po.project_item_id IS NOT NULL
   AND po.package_id IS NULL;
   ```

5. **Migrate supplier_name to supplier_id in procurement_options:**
   ```sql
   -- Match supplier_name to suppliers table
   UPDATE procurement_options
   SET supplier_id = (
       SELECT id FROM suppliers
       WHERE LOWER(TRIM(company_name)) = LOWER(TRIM(supplier_name))
       LIMIT 1
   )
   WHERE supplier_id IS NULL
   AND supplier_name IS NOT NULL;
   ```

6. **Create package_subitems for FULL packages:**
   ```sql
   -- Link all sub-items to FULL packages
   INSERT INTO package_subitems (package_id, project_item_subitem_id, quantity_covered, is_fully_covered, coverage_percentage)
   SELECT pp.id, pis.id, pis.quantity, TRUE, 100.0
   FROM procurement_packages pp
   JOIN project_items pi ON pi.id = pp.project_item_id
   JOIN project_item_subitems pis ON pis.project_item_id = pi.id
   WHERE pp.package_type = 'FULL';
   ```

#### Phase 3: Transition Period

**Dual-Mode Operation:**
- Allow both `package_id` and `project_item_id` in `procurement_options` (CHECK constraint ensures one is present)
- UI/API accepts both patterns
- Prefer `package_id` for new records, but allow `project_item_id` for compatibility

**Flags:**
- Add `migration_complete` flag to `procurement_options` (default FALSE)
- When option is migrated, set flag to TRUE
- After migration period, require `package_id` for new records

#### Phase 4: Deprecation (Future)

1. **Remove `supplier_name` field** from `procurement_options` and `supplier_payments` (after all records have `supplier_id`)
2. **Remove `item_code` field** from `procurement_options` (after migration)
3. **Make `package_id` required** in `procurement_options` (remove `project_item_id` option)
4. **Make `project_item_id` nullable** in `delivery_options` (require `package_id`)
5. **Enforce `supplier_id` NOT NULL** in `supplier_payments` (after migration from `supplier_name`)
6. **Optional: Make `package_id` required** in `invoices`, `payments`, `supplier_payments` (after full migration)

### Nullable Fields and Transitional Flags

| Field | Table | Nullable | Purpose | Migration Strategy |
|-------|-------|----------|---------|-------------------|
| `package_id` | `procurement_options` | YES (transitional) | Allow legacy options during migration | Migrate existing, require for new after transition |
| `package_id` | `finalized_decisions` | YES | Legacy decisions have no package | Keep nullable, prefer package_id for new |
| `package_id` | `delivery_options` | YES | Legacy delivery options | Migrate existing, prefer package_id for new |
| `project_item_id` | `procurement_options` | YES (legacy) | Backward compatibility | Deprecate after migration |
| `project_item_id` | `delivery_options` | YES (made nullable) | Backward compatibility | Keep nullable, prefer package_id |
| `supplier_id` | `procurement_options` | NO (enforced) | Required FK | Migrate from supplier_name before enforcing |
| `supplier_name` | `procurement_options` | YES (deprecated) | Legacy field | Keep for migration, remove later |
| `item_code` | `procurement_options` | YES (deprecated) | Legacy field | Keep for migration, remove later |
| `package_id` | `invoices` | YES (new) | Package-level invoicing | Add nullable field, link to packages |
| `package_id` | `payments` | YES (new) | Package-level buyer receipts | Add nullable field, link to packages |
| `package_id` | `supplier_payments` | YES (new) | Package-level supplier payments | Add nullable field, link to packages |
| `supplier_id` | `supplier_payments` | YES (transitional), **NO (new records)** | Required FK for new records | Add nullable field during transition. Required (NOT NULL) for all new records. Migrate from supplier_name in Phase 2. |
| `supplier_name` | `supplier_payments` | YES (deprecated) | Legacy field | Keep for migration only. Required during transition for legacy records. Remove in Phase 4. |

### Data Integrity Constraints

1. **CHECK constraint on procurement_options:**
   ```sql
   CHECK (
       (package_id IS NOT NULL) OR
       (project_item_id IS NOT NULL) OR
       (item_code IS NOT NULL)
   )
   ```

2. **CHECK constraint on delivery_options:**
   ```sql
   CHECK (
       (package_id IS NOT NULL) OR
       (project_item_id IS NOT NULL)
   )
   ```

3. **UNIQUE constraint on package_subitems:**
   ```sql
   UNIQUE (package_id, project_item_subitem_id)
   ```

4. **Coverage validation (application-level):**
   - Ensure sum of `quantity_covered` across packages for a sub-item does not exceed required quantity
   - Ensure at least one FULL package exists per project item (for backward compatibility)

5. **CHECK constraint on supplier_payments:**
   ```sql
   CHECK (
       (supplier_id IS NOT NULL) OR
       (supplier_name IS NOT NULL)
   )
   ```

6. **Financial validation (application-level):**
   - Invoice amounts must match package costs (if `package_id` present) or decision costs (if legacy)
   - Payment amounts cannot exceed invoice amounts
   - Supplier payment amounts should match package costs (if `package_id` present)

---

## Summary

This future-state model extends the current procurement system to support **package-level procurement** while maintaining **backward compatibility** through:

1. **Package abstraction** - Groups sub-items into procurement units (FULL, PARTIAL, CUSTOM)
2. **Dual-mode operation** - Supports both package-based and legacy item-based workflows
3. **Supplier normalization** - Requires FK relationships, removes legacy string fields
4. **Granular tracking** - Package-level decisions, deliveries, and payments
5. **Aggregation** - All data aggregates to project item level for reporting

The design enables procurement teams to:
- Source entire project items from one supplier (FULL package)
- Source subsets of sub-items from different suppliers (PARTIAL packages)
- Compare full vs. partial sourcing strategies
- Track execution and payments at the appropriate granularity

---

## Prompt 3 — Migration & Rollout Plan

This section provides an executable migration and rollout blueprint for engineering teams implementing the future-state procurement data model. All SQL migrations are production-ready and include transaction management, error handling, and rollback capabilities.

---

### Migration Phases → SQL Tasks

#### Phase 1: Additive Changes (No Breaking Changes)

**Strategy:** Online migration, no downtime required. All changes are additive (new columns nullable, new tables).

**Dependencies:** None (can run independently)

**Transaction Strategy:** Each migration script uses `BEGIN;` / `COMMIT;` for atomicity. Can run in parallel with application, but recommend running during low-traffic period.

##### 1.1 Create `procurement_packages` Table

**File:** `backend/migrations/001_create_procurement_packages.sql`

```sql
-- Migration: Create procurement_packages table
-- Phase: 1.1 - Additive Changes
-- Strategy: Online (no downtime)

BEGIN;

CREATE TABLE IF NOT EXISTS procurement_packages (
    id SERIAL PRIMARY KEY,
    project_item_id INTEGER NOT NULL REFERENCES project_items(id) ON DELETE CASCADE,
    package_name TEXT,
    package_type VARCHAR(20) NOT NULL CHECK (package_type IN ('FULL', 'PARTIAL', 'CUSTOM')),
    supplier_id INTEGER REFERENCES suppliers(id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT check_package_type CHECK (package_type IN ('FULL', 'PARTIAL', 'CUSTOM'))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_procurement_packages_project_item_id 
    ON procurement_packages(project_item_id);
CREATE INDEX IF NOT EXISTS idx_procurement_packages_supplier_id 
    ON procurement_packages(supplier_id);
CREATE INDEX IF NOT EXISTS idx_procurement_packages_package_type 
    ON procurement_packages(package_type);
CREATE INDEX IF NOT EXISTS idx_procurement_packages_is_active 
    ON procurement_packages(is_active);

-- Unique constraint: package_name per project_item (or allow NULL)
CREATE UNIQUE INDEX IF NOT EXISTS idx_procurement_packages_unique_name 
    ON procurement_packages(project_item_id, package_name) 
    WHERE package_name IS NOT NULL;

COMMENT ON TABLE procurement_packages IS 'Groups sub-items into procurement units (packages)';
COMMENT ON COLUMN procurement_packages.package_type IS 'FULL: all sub-items, PARTIAL: subset, CUSTOM: user-defined';

COMMIT;
```

##### 1.2 Create `package_subitems` Table

**File:** `backend/migrations/002_create_package_subitems.sql`

```sql
-- Migration: Create package_subitems table
-- Phase: 1.2 - Additive Changes

BEGIN;

CREATE TABLE IF NOT EXISTS package_subitems (
    id SERIAL PRIMARY KEY,
    package_id INTEGER NOT NULL REFERENCES procurement_packages(id) ON DELETE CASCADE,
    project_item_subitem_id INTEGER NOT NULL REFERENCES project_item_subitems(id) ON DELETE CASCADE,
    quantity_covered INTEGER NOT NULL CHECK (quantity_covered >= 0),
    is_fully_covered BOOLEAN DEFAULT FALSE,
    coverage_percentage NUMERIC(5,2) CHECK (coverage_percentage >= 0 AND coverage_percentage <= 100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Prevent duplicate mappings
    CONSTRAINT unique_package_subitem UNIQUE (package_id, project_item_subitem_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_package_subitems_package_id 
    ON package_subitems(package_id);
CREATE INDEX IF NOT EXISTS idx_package_subitems_subitem_id 
    ON package_subitems(project_item_subitem_id);

COMMENT ON TABLE package_subitems IS 'Maps sub-items to packages with coverage details';

COMMIT;
```

##### 1.3 Create `package_payments` Table

**File:** `backend/migrations/003_create_package_payments.sql`

```sql
-- Migration: Create package_payments table
-- Phase: 1.3 - Additive Changes

BEGIN;

CREATE TABLE IF NOT EXISTS package_payments (
    id SERIAL PRIMARY KEY,
    decision_id INTEGER NOT NULL REFERENCES finalized_decisions(id) ON DELETE CASCADE,
    package_id INTEGER NOT NULL REFERENCES procurement_packages(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id),
    payment_amount NUMERIC(12,2) NOT NULL CHECK (payment_amount > 0),
    currency VARCHAR(10) NOT NULL DEFAULT 'IRR',
    payment_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL CHECK (payment_method IN ('cash', 'bank_transfer', 'check', 'credit_card')),
    reference_number TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed', 'cancelled')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by_id INTEGER REFERENCES users(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_package_payments_decision_id 
    ON package_payments(decision_id);
CREATE INDEX IF NOT EXISTS idx_package_payments_package_id 
    ON package_payments(package_id);
CREATE INDEX IF NOT EXISTS idx_package_payments_supplier_id 
    ON package_payments(supplier_id);
CREATE INDEX IF NOT EXISTS idx_package_payments_payment_date 
    ON package_payments(payment_date);
CREATE INDEX IF NOT EXISTS idx_package_payments_status 
    ON package_payments(status);

COMMENT ON TABLE package_payments IS 'Payment tracking at package level';

COMMIT;
```

##### 1.4 Add `package_id` Columns (Nullable)

**File:** `backend/migrations/004_add_package_id_columns.sql`

```sql
-- Migration: Add package_id columns to existing tables
-- Phase: 1.4 - Additive Changes
-- Strategy: Online (no downtime, columns nullable)

BEGIN;

-- Add package_id to procurement_options
ALTER TABLE procurement_options 
ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_procurement_options_package_id 
    ON procurement_options(package_id);

-- Add package_id to finalized_decisions
ALTER TABLE finalized_decisions 
ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_finalized_decisions_package_id 
    ON finalized_decisions(package_id);

-- Add package_id to delivery_options
ALTER TABLE delivery_options 
ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_delivery_options_package_id 
    ON delivery_options(package_id);

-- Add package_id to invoices (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'invoices') THEN
        ALTER TABLE invoices 
        ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;
        
        CREATE INDEX IF NOT EXISTS idx_invoices_package_id 
            ON invoices(package_id);
    END IF;
END $$;

-- Add package_id to payments (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        ALTER TABLE payments 
        ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;
        
        CREATE INDEX IF NOT EXISTS idx_payments_package_id 
            ON payments(package_id);
    END IF;
END $$;

-- Add package_id to supplier_payments (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'supplier_payments') THEN
        ALTER TABLE supplier_payments 
        ADD COLUMN IF NOT EXISTS package_id INTEGER REFERENCES procurement_packages(id) ON DELETE SET NULL;
        
        CREATE INDEX IF NOT EXISTS idx_supplier_payments_package_id 
            ON supplier_payments(package_id);
    END IF;
END $$;

COMMIT;
```

##### 1.5 Make `project_item_id` Nullable in `delivery_options`

**File:** `backend/migrations/005_make_delivery_options_project_item_nullable.sql`

```sql
-- Migration: Make project_item_id nullable in delivery_options
-- Phase: 1.5 - Additive Changes
-- Strategy: Online (requires CHECK constraint update)

BEGIN;

-- First, add CHECK constraint to ensure at least one of project_item_id OR package_id is present
ALTER TABLE delivery_options 
ADD CONSTRAINT IF NOT EXISTS check_delivery_option_reference 
    CHECK (project_item_id IS NOT NULL OR package_id IS NOT NULL);

-- Then make project_item_id nullable
ALTER TABLE delivery_options 
ALTER COLUMN project_item_id DROP NOT NULL;

COMMENT ON CONSTRAINT check_delivery_option_reference ON delivery_options IS 
    'Ensures delivery option references either project_item_id (legacy) or package_id (new)';

COMMIT;
```

##### 1.6 Add `supplier_id` to `supplier_payments`

**File:** `backend/migrations/006_add_supplier_id_to_supplier_payments.sql`

```sql
-- Migration: Add supplier_id FK to supplier_payments
-- Phase: 1.6 - Additive Changes

BEGIN;

-- Add supplier_id column (nullable during transition)
ALTER TABLE supplier_payments 
ADD COLUMN IF NOT EXISTS supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_supplier_payments_supplier_id 
    ON supplier_payments(supplier_id);

-- Add CHECK constraint: at least one of supplier_id OR supplier_name must be present
ALTER TABLE supplier_payments 
ADD CONSTRAINT IF NOT EXISTS check_supplier_reference 
    CHECK (supplier_id IS NOT NULL OR supplier_name IS NOT NULL);

COMMENT ON COLUMN supplier_payments.supplier_id IS 
    'FK to suppliers table. Required for new records, nullable during transition.';

COMMIT;
```

##### 1.7 Increase `invoice_amount_per_unit` Precision

**File:** `backend/migrations/007_increase_invoice_amount_precision.sql`

```sql
-- Migration: Increase invoice_amount_per_unit precision
-- Phase: 1.7 - Additive Changes
-- Reference: backend/increase_invoice_amount_precision.sql

BEGIN;

ALTER TABLE delivery_options 
ALTER COLUMN invoice_amount_per_unit TYPE NUMERIC(18, 2);

COMMENT ON COLUMN delivery_options.invoice_amount_per_unit IS 
    'Invoice amount per unit. Precision increased from Numeric(12,2) to Numeric(18,2) to support larger values (max: 999,999,999,999,999,999.99)';

COMMIT;
```

##### 1.8 Add CHECK Constraints for `procurement_options`

**File:** `backend/migrations/008_add_procurement_options_check_constraint.sql`

```sql
-- Migration: Add CHECK constraint to procurement_options
-- Phase: 1.8 - Additive Changes
-- Ensures at least one of package_id, project_item_id, or item_code is present

BEGIN;

ALTER TABLE procurement_options 
ADD CONSTRAINT IF NOT EXISTS check_procurement_option_reference 
    CHECK (
        (package_id IS NOT NULL) OR 
        (project_item_id IS NOT NULL) OR 
        (item_code IS NOT NULL)
    );

COMMENT ON CONSTRAINT check_procurement_option_reference ON procurement_options IS 
    'Ensures procurement option references package_id (new), project_item_id (legacy), or item_code (legacy)';

COMMIT;
```

**Phase 1 Summary:**
- **Downtime Required:** None (online migration)
- **Rollback Strategy:** Drop new tables/columns, remove constraints
- **Validation:** Run data validation queries (see Testing section)
- **Dependencies:** None (independent phase)

---

#### Phase 2: Data Migration

**Strategy:** Online migration with data backfill. Can run in batches. Requires application-level feature flags to handle both legacy and new data.

**Dependencies:** Phase 1 must be complete

**Transaction Strategy:** Use batched transactions for large datasets. Each batch is atomic. Can pause/resume migration.

##### 2.1 Create FULL Packages for Existing Project Items

**File:** `backend/migrations/009_create_full_packages.sql`

```sql
-- Migration: Create FULL packages for existing project items
-- Phase: 2.1 - Data Migration
-- Strategy: Batch processing, online migration

BEGIN;

-- Create FULL packages for project items that have sub-items
INSERT INTO procurement_packages (project_item_id, package_name, package_type, created_at)
SELECT 
    pi.id,
    COALESCE(pi.item_code, 'ITEM-' || pi.id::text) || ' - Full Package',
    'FULL',
    NOW()
FROM project_items pi
WHERE pi.id IN (
    SELECT DISTINCT project_item_id 
    FROM project_item_subitems
)
AND NOT EXISTS (
    SELECT 1 
    FROM procurement_packages pp 
    WHERE pp.project_item_id = pi.id 
    AND pp.package_type = 'FULL'
);

-- Log created packages
DO $$
DECLARE
    packages_created INTEGER;
BEGIN
    SELECT COUNT(*) INTO packages_created 
    FROM procurement_packages 
    WHERE package_type = 'FULL';
    
    RAISE NOTICE 'Created % FULL packages', packages_created;
END $$;

COMMIT;
```

##### 2.2 Create `package_subitems` for FULL Packages

**File:** `backend/migrations/010_create_package_subitems_for_full_packages.sql`

```sql
-- Migration: Create package_subitems for FULL packages
-- Phase: 2.2 - Data Migration

BEGIN;

-- Link all sub-items to FULL packages
INSERT INTO package_subitems (
    package_id, 
    project_item_subitem_id, 
    quantity_covered, 
    is_fully_covered, 
    coverage_percentage,
    created_at
)
SELECT 
    pp.id,
    pis.id,
    pis.quantity,
    TRUE,
    100.0,
    NOW()
FROM procurement_packages pp
JOIN project_items pi ON pi.id = pp.project_item_id
JOIN project_item_subitems pis ON pis.project_item_id = pi.id
WHERE pp.package_type = 'FULL'
AND NOT EXISTS (
    SELECT 1 
    FROM package_subitems psi 
    WHERE psi.package_id = pp.id 
    AND psi.project_item_subitem_id = pis.id
);

-- Validate coverage
DO $$
DECLARE
    missing_coverage INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_coverage
    FROM project_item_subitems pis
    WHERE NOT EXISTS (
        SELECT 1 
        FROM package_subitems psi
        JOIN procurement_packages pp ON pp.id = psi.package_id
        WHERE psi.project_item_subitem_id = pis.id
        AND pp.package_type = 'FULL'
    );
    
    IF missing_coverage > 0 THEN
        RAISE WARNING 'Found % sub-items without FULL package coverage. Review required.', missing_coverage;
    END IF;
END $$;

COMMIT;
```

##### 2.3 Link Existing `procurement_options` to FULL Packages

**File:** `backend/migrations/011_link_procurement_options_to_packages.sql`

```sql
-- Migration: Link existing procurement_options to FULL packages
-- Phase: 2.3 - Data Migration

BEGIN;

-- Link options that have project_item_id
UPDATE procurement_options po
SET package_id = (
    SELECT pp.id
    FROM procurement_packages pp
    WHERE pp.project_item_id = po.project_item_id
    AND pp.package_type = 'FULL'
    LIMIT 1
)
WHERE po.project_item_id IS NOT NULL
AND po.package_id IS NULL;

-- Log migration results
DO $$
DECLARE
    options_linked INTEGER;
    options_unlinked INTEGER;
BEGIN
    SELECT COUNT(*) INTO options_linked
    FROM procurement_options
    WHERE package_id IS NOT NULL;
    
    SELECT COUNT(*) INTO options_unlinked
    FROM procurement_options
    WHERE package_id IS NULL
    AND project_item_id IS NULL
    AND item_code IS NULL;
    
    RAISE NOTICE 'Linked % procurement options to packages', options_linked;
    
    IF options_unlinked > 0 THEN
        RAISE WARNING 'Found % procurement options without any reference. Review required.', options_unlinked;
    END IF;
END $$;

COMMIT;
```

##### 2.4 Migrate `supplier_name` to `supplier_id` in `procurement_options`

**File:** `backend/migrations/012_migrate_supplier_name_to_supplier_id.sql`

```sql
-- Migration: Migrate supplier_name to supplier_id in procurement_options
-- Phase: 2.4 - Data Migration
-- Strategy: Fuzzy matching with reconciliation report

BEGIN;

-- Step 1: Match exact supplier names (case-insensitive, trimmed)
UPDATE procurement_options po
SET supplier_id = (
    SELECT s.id
    FROM suppliers s
    WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(po.supplier_name))
    LIMIT 1
)
WHERE po.supplier_id IS NULL
AND po.supplier_name IS NOT NULL
AND EXISTS (
    SELECT 1
    FROM suppliers s
    WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(po.supplier_name))
);

-- Step 2: Create reconciliation report for unmatched suppliers
CREATE TEMP TABLE IF NOT EXISTS unmatched_suppliers AS
SELECT DISTINCT
    po.id as option_id,
    po.supplier_name,
    po.item_code,
    po.project_item_id
FROM procurement_options po
WHERE po.supplier_id IS NULL
AND po.supplier_name IS NOT NULL;

-- Log unmatched suppliers
DO $$
DECLARE
    unmatched_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO unmatched_count FROM unmatched_suppliers;
    
    IF unmatched_count > 0 THEN
        RAISE WARNING 'Found % procurement options with unmatched supplier names. Review required.', unmatched_count;
        
        -- Export unmatched suppliers for manual review
        RAISE NOTICE 'Unmatched suppliers saved to temp table: unmatched_suppliers';
    END IF;
END $$;

-- Step 3: Enforce supplier_id for new records (application-level, not DB constraint yet)
-- This will be done in Phase 3

COMMIT;
```

##### 2.5 Migrate `supplier_name` to `supplier_id` in `supplier_payments`

**File:** `backend/migrations/013_migrate_supplier_payments_supplier_id.sql`

```sql
-- Migration: Migrate supplier_name to supplier_id in supplier_payments
-- Phase: 2.5 - Data Migration

BEGIN;

-- Match supplier names to supplier_id
UPDATE supplier_payments sp
SET supplier_id = (
    SELECT s.id
    FROM suppliers s
    WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(sp.supplier_name))
    LIMIT 1
)
WHERE sp.supplier_id IS NULL
AND sp.supplier_name IS NOT NULL
AND EXISTS (
    SELECT 1
    FROM suppliers s
    WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(sp.supplier_name))
);

-- Log results
DO $$
DECLARE
    payments_linked INTEGER;
    payments_unlinked INTEGER;
BEGIN
    SELECT COUNT(*) INTO payments_linked
    FROM supplier_payments
    WHERE supplier_id IS NOT NULL;
    
    SELECT COUNT(*) INTO payments_unlinked
    FROM supplier_payments
    WHERE supplier_id IS NULL
    AND supplier_name IS NULL;
    
    RAISE NOTICE 'Linked % supplier payments to supplier FK', payments_linked;
    
    IF payments_unlinked > 0 THEN
        RAISE WARNING 'Found % supplier payments without supplier reference. Review required.', payments_unlinked;
    END IF;
END $$;

COMMIT;
```

##### 2.6 Link Financial Records to Packages

**File:** `backend/migrations/014_link_financial_records_to_packages.sql`

```sql
-- Migration: Link financial records (invoices, payments, supplier_payments) to packages
-- Phase: 2.6 - Data Migration

BEGIN;

-- Link invoices to packages (via decision → FULL package)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'invoices') THEN
        UPDATE invoices i
        SET package_id = (
            SELECT pp.id
            FROM finalized_decisions fd
            JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
            WHERE fd.id = i.decision_id
            AND pp.package_type = 'FULL'
            LIMIT 1
        )
        WHERE i.package_id IS NULL
        AND EXISTS (
            SELECT 1
            FROM finalized_decisions fd
            JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
            WHERE fd.id = i.decision_id
            AND pp.package_type = 'FULL'
        );
        
        RAISE NOTICE 'Linked invoices to packages';
    END IF;
END $$;

-- Link payments to packages (via invoice or decision)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'payments') THEN
        UPDATE payments p
        SET package_id = COALESCE(
            -- Try via invoice first
            (SELECT i.package_id FROM invoices i WHERE i.id = p.invoice_id),
            -- Fallback to decision
            (SELECT pp.id
             FROM finalized_decisions fd
             JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
             WHERE fd.id = p.decision_id
             AND pp.package_type = 'FULL'
             LIMIT 1)
        )
        WHERE p.package_id IS NULL;
        
        RAISE NOTICE 'Linked payments to packages';
    END IF;
END $$;

-- Link supplier_payments to packages (via decision)
UPDATE supplier_payments sp
SET package_id = (
    SELECT pp.id
    FROM finalized_decisions fd
    JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
    WHERE fd.id = sp.decision_id
    AND pp.package_type = 'FULL'
    LIMIT 1
)
WHERE sp.package_id IS NULL
AND EXISTS (
    SELECT 1
    FROM finalized_decisions fd
    JOIN procurement_packages pp ON pp.project_item_id = fd.project_item_id
    WHERE fd.id = sp.decision_id
    AND pp.package_type = 'FULL'
);

RAISE NOTICE 'Linked supplier_payments to packages';

COMMIT;
```

**Phase 2 Summary:**
- **Downtime Required:** None (online migration, batched)
- **Rollback Strategy:** Set `package_id = NULL`, remove `package_subitems` entries, delete FULL packages
- **Validation:** Run reconciliation queries (see Testing section)
- **Dependencies:** Phase 1 complete

---

#### Phase 3: Transition Period

**Strategy:** Dual-mode operation. Application code handles both legacy and package-aware logic. Feature flags control behavior.

**Dependencies:** Phase 2 complete

**Transaction Strategy:** No database changes. Application-level feature flags.

##### 3.1 Add `migration_complete` Flag (Optional)

**File:** `backend/migrations/015_add_migration_complete_flag.sql`

```sql
-- Migration: Add migration_complete flag to procurement_options
-- Phase: 3.1 - Transition Period (Optional)
-- Purpose: Track which options have been migrated to package-aware logic

BEGIN;

ALTER TABLE procurement_options 
ADD COLUMN IF NOT EXISTS migration_complete BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_procurement_options_migration_complete 
    ON procurement_options(migration_complete);

-- Mark options with package_id as migrated
UPDATE procurement_options 
SET migration_complete = TRUE 
WHERE package_id IS NOT NULL;

COMMENT ON COLUMN procurement_options.migration_complete IS 
    'Flag indicating option has been migrated to package-aware logic';

COMMIT;
```

**Phase 3 Summary:**
- **Downtime Required:** None (application changes only)
- **Rollback Strategy:** Disable feature flags, revert to legacy logic
- **Validation:** A/B testing, monitoring
- **Dependencies:** Phase 2 complete

---

#### Phase 4: Deprecation (Future)

**Strategy:** Requires downtime for constraint changes. Remove legacy fields after migration validation.

**Dependencies:** Phase 3 complete, all data migrated

**Transaction Strategy:** Maintenance window required. Full backup before execution.

##### 4.1 Enforce `supplier_id` NOT NULL in `supplier_payments`

**File:** `backend/migrations/016_enforce_supplier_id_not_null.sql`

```sql
-- Migration: Enforce supplier_id NOT NULL in supplier_payments
-- Phase: 4.1 - Deprecation
-- Strategy: Requires downtime (constraint change)

BEGIN;

-- First, verify all records have supplier_id
DO $$
DECLARE
    records_without_supplier_id INTEGER;
BEGIN
    SELECT COUNT(*) INTO records_without_supplier_id
    FROM supplier_payments
    WHERE supplier_id IS NULL;
    
    IF records_without_supplier_id > 0 THEN
        RAISE EXCEPTION 'Cannot enforce NOT NULL: % records still have NULL supplier_id. Complete migration first.', 
            records_without_supplier_id;
    END IF;
END $$;

-- Remove CHECK constraint
ALTER TABLE supplier_payments 
DROP CONSTRAINT IF EXISTS check_supplier_reference;

-- Add NOT NULL constraint
ALTER TABLE supplier_payments 
ALTER COLUMN supplier_id SET NOT NULL;

COMMIT;
```

##### 4.2 Remove `supplier_name` from `supplier_payments`

**File:** `backend/migrations/017_remove_supplier_name_from_supplier_payments.sql`

```sql
-- Migration: Remove supplier_name column from supplier_payments
-- Phase: 4.2 - Deprecation
-- Strategy: Requires downtime

BEGIN;

-- Verify supplier_id is NOT NULL (should be enforced in 4.1)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'supplier_payments' 
        AND column_name = 'supplier_id' 
        AND is_nullable = 'YES'
    ) THEN
        RAISE EXCEPTION 'supplier_id must be NOT NULL before removing supplier_name';
    END IF;
END $$;

-- Drop index on supplier_name
DROP INDEX IF EXISTS idx_supplier_payments_supplier_name;

-- Remove column
ALTER TABLE supplier_payments 
DROP COLUMN IF EXISTS supplier_name;

COMMIT;
```

##### 4.3 Remove `supplier_name` from `procurement_options`

**File:** `backend/migrations/018_remove_supplier_name_from_procurement_options.sql`

```sql
-- Migration: Remove supplier_name from procurement_options
-- Phase: 4.3 - Deprecation

BEGIN;

-- Verify all records have supplier_id
DO $$
DECLARE
    records_without_supplier_id INTEGER;
BEGIN
    SELECT COUNT(*) INTO records_without_supplier_id
    FROM procurement_options
    WHERE supplier_id IS NULL;
    
    IF records_without_supplier_id > 0 THEN
        RAISE EXCEPTION 'Cannot remove supplier_name: % records still have NULL supplier_id', 
            records_without_supplier_id;
    END IF;
END $$;

ALTER TABLE procurement_options 
DROP COLUMN IF EXISTS supplier_name;

COMMIT;
```

**Phase 4 Summary:**
- **Downtime Required:** Yes (maintenance window)
- **Rollback Strategy:** Restore from backup, re-add columns
- **Validation:** Full data integrity checks
- **Dependencies:** Phase 3 complete, all data migrated

---

### Backfill & Script Details

#### Deriving Package Records from Existing Data

**Pseudocode for FULL Package Creation:**

```python
def create_full_packages_for_project_items(db_session):
    """
    Creates FULL packages for all project items that have sub-items.
    Strategy: One FULL package per project item.
    """
    project_items_with_subitems = db_session.query(ProjectItem).join(
        ProjectItemSubitem
    ).distinct().all()
    
    for project_item in project_items_with_subitems:
        # Check if FULL package already exists
        existing_full = db_session.query(ProcurementPackage).filter(
            ProcurementPackage.project_item_id == project_item.id,
            ProcurementPackage.package_type == 'FULL'
        ).first()
        
        if not existing_full:
            # Create FULL package
            full_package = ProcurementPackage(
                project_item_id=project_item.id,
                package_name=f"{project_item.item_code} - Full Package",
                package_type='FULL',
                is_active=True
            )
            db_session.add(full_package)
            db_session.flush()
            
            # Create package_subitems entries
            for subitem in project_item.sub_items:
                package_subitem = PackageSubItem(
                    package_id=full_package.id,
                    project_item_subitem_id=subitem.id,
                    quantity_covered=subitem.quantity,
                    is_fully_covered=True,
                    coverage_percentage=100.0
                )
                db_session.add(package_subitem)
    
    db_session.commit()
```

#### Error Handling and Reconciliation

**Unmatched Suppliers Report:**

```sql
-- Query: Find procurement options with unmatched supplier names
SELECT 
    po.id,
    po.supplier_name,
    po.item_code,
    po.project_item_id,
    pi.item_code as project_item_code
FROM procurement_options po
LEFT JOIN project_items pi ON pi.id = po.project_item_id
WHERE po.supplier_id IS NULL
AND po.supplier_name IS NOT NULL
ORDER BY po.supplier_name;

-- Query: Find supplier_payments with unmatched supplier names
SELECT 
    sp.id,
    sp.supplier_name,
    sp.item_code,
    sp.decision_id,
    fd.project_item_id
FROM supplier_payments sp
LEFT JOIN finalized_decisions fd ON fd.id = sp.decision_id
WHERE sp.supplier_id IS NULL
AND sp.supplier_name IS NOT NULL
ORDER BY sp.supplier_name;
```

**Reconciliation Script:**

```sql
-- Manual reconciliation: Update unmatched suppliers
-- Step 1: Review unmatched_suppliers table
-- Step 2: Create missing suppliers or map to existing
-- Step 3: Update procurement_options/supplier_payments

-- Example: Create new supplier and link
INSERT INTO suppliers (supplier_id, company_name, status)
VALUES ('SUP-NEW-001', 'Unmatched Supplier Name', 'active')
RETURNING id;

-- Then update procurement_options
UPDATE procurement_options
SET supplier_id = <new_supplier_id>
WHERE supplier_name = 'Unmatched Supplier Name';
```

---

### Application Touchpoints

#### Phase 1-2: Model Updates

**Files to Update:**

1. **`backend/app/models.py`**
   - Add `ProcurementPackage` model
   - Add `PackageSubItem` model
   - Add `PackagePayment` model
   - Add `package_id` columns to existing models
   - Add `supplier_id` to `SupplierPayment` model

2. **`backend/app/schemas.py`**
   - Add Pydantic schemas for new models
   - Update existing schemas to include `package_id`
   - Add validation for package-aware operations

#### Phase 3: API/Service Updates

**Routers to Update:**

1. **`backend/app/routers/procurement.py`**
   - Update `create_procurement_option` to accept `package_id`
   - Update `get_procurement_options` to filter by package
   - Add package-aware validation

2. **`backend/app/routers/delivery_options.py`**
   - Update endpoints to accept `package_id` OR `project_item_id`
   - Add validation for CHECK constraint compliance

3. **`backend/app/routers/decisions.py`**
   - Update decision creation to link to packages
   - Update decision queries to include package information

**Services to Update:**

1. **`backend/app/optimization_engine_enhanced.py`**
   - Update `_load_data()` to read package-based options
   - Update cost calculation to use package costs
   - Update decision creation to link `package_id`

2. **`backend/app/budget_analysis_service.py`**
   - Update to aggregate by package when `package_id` present
   - Maintain backward compatibility for legacy decisions

3. **Finance Modules** (if exists):
   - Update invoice creation to accept `package_id`
   - Update payment tracking to link to packages
   - Update supplier payment tracking to use `supplier_id` FK

#### Feature Flags

**Configuration File:** `backend/app/config.py`

```python
# Feature flags for package-aware procurement
ENABLE_PACKAGE_AWARE_PROCUREMENT = os.getenv("ENABLE_PACKAGE_AWARE_PROCUREMENT", "false").lower() == "true"
ENABLE_PACKAGE_BASED_OPTIMIZATION = os.getenv("ENABLE_PACKAGE_BASED_OPTIMIZATION", "false").lower() == "true"
REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS = os.getenv("REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS", "false").lower() == "true"
```

**Usage in Code:**

```python
# Example: Procurement option creation
def create_procurement_option(data, db):
    if ENABLE_PACKAGE_AWARE_PROCUREMENT:
        # Require package_id for new options
        if REQUIRE_PACKAGE_ID_FOR_NEW_OPTIONS and not data.package_id:
            raise ValueError("package_id is required for new procurement options")
        
        # Use package-aware logic
        return create_package_aware_option(data, db)
    else:
        # Legacy logic (project_item_id or item_code)
        return create_legacy_option(data, db)
```

#### Background Workers

**Jobs to Update:**

1. **Package Creation Worker** (new):
   - Auto-create FULL packages for new project items
   - Monitor for orphaned options (no package_id, no project_item_id)

2. **Supplier Reconciliation Worker** (new):
   - Periodically match unmatched `supplier_name` to `supplier_id`
   - Alert on unmatched suppliers

---

### Testing & Rollback

#### Test Suites by Phase

##### Phase 1 Tests

**Unit Tests:**
- `test_procurement_packages_model.py`: Test model creation, relationships
- `test_package_subitems_model.py`: Test coverage calculations
- `test_package_id_columns.py`: Test nullable columns, constraints

**Integration Tests:**
- `test_create_full_package.py`: Test FULL package creation workflow
- `test_package_relationships.py`: Test FK relationships

**Data Validation Queries:**

```sql
-- Verify all new tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_name IN ('procurement_packages', 'package_subitems', 'package_payments');

-- Verify package_id columns added
SELECT column_name, is_nullable, data_type
FROM information_schema.columns
WHERE table_name IN ('procurement_options', 'finalized_decisions', 'delivery_options')
AND column_name = 'package_id';

-- Verify CHECK constraints
SELECT constraint_name, table_name
FROM information_schema.table_constraints
WHERE constraint_type = 'CHECK'
AND constraint_name LIKE '%package%' OR constraint_name LIKE '%supplier%';
```

##### Phase 2 Tests

**Unit Tests:**
- `test_full_package_creation.py`: Test FULL package creation for project items
- `test_package_subitems_creation.py`: Test sub-item linking
- `test_supplier_migration.py`: Test supplier_name to supplier_id migration

**Integration Tests:**
- `test_procurement_option_linking.py`: Test linking options to packages
- `test_financial_record_linking.py`: Test linking invoices/payments to packages

**Data Validation Queries:**

```sql
-- Verify FULL packages created for all project items with sub-items
SELECT 
    pi.id,
    pi.item_code,
    COUNT(DISTINCT pp.id) as full_packages_count
FROM project_items pi
LEFT JOIN project_item_subitems pis ON pis.project_item_id = pi.id
LEFT JOIN procurement_packages pp ON pp.project_item_id = pi.id AND pp.package_type = 'FULL'
WHERE EXISTS (SELECT 1 FROM project_item_subitems WHERE project_item_id = pi.id)
GROUP BY pi.id, pi.item_code
HAVING COUNT(DISTINCT pp.id) = 0;  -- Should return 0 rows

-- Verify package coverage (all sub-items covered)
SELECT 
    pis.id,
    pis.project_item_id,
    SUM(psi.quantity_covered) as total_covered,
    pis.quantity as required_quantity
FROM project_item_subitems pis
LEFT JOIN package_subitems psi ON psi.project_item_subitem_id = pis.id
LEFT JOIN procurement_packages pp ON pp.id = psi.package_id AND pp.package_type = 'FULL'
GROUP BY pis.id, pis.project_item_id, pis.quantity
HAVING SUM(psi.quantity_covered) < pis.quantity;  -- Should return 0 rows

-- Verify supplier_id migration
SELECT 
    COUNT(*) as total_options,
    COUNT(supplier_id) as options_with_supplier_id,
    COUNT(*) - COUNT(supplier_id) as options_without_supplier_id
FROM procurement_options
WHERE supplier_name IS NOT NULL;

-- Verify financial record linking
SELECT 
    'invoices' as table_name,
    COUNT(*) as total,
    COUNT(package_id) as linked_to_package
FROM invoices
UNION ALL
SELECT 
    'payments',
    COUNT(*),
    COUNT(package_id)
FROM payments
UNION ALL
SELECT 
    'supplier_payments',
    COUNT(*),
    COUNT(package_id)
FROM supplier_payments;
```

##### Phase 3 Tests

**Unit Tests:**
- `test_dual_mode_operation.py`: Test legacy and package-aware logic side-by-side
- `test_feature_flags.py`: Test feature flag toggling

**Integration Tests:**
- `test_api_backward_compatibility.py`: Test API accepts both legacy and new formats
- `test_optimization_engine_package_aware.py`: Test optimization with packages

##### Phase 4 Tests

**Unit Tests:**
- `test_supplier_id_not_null.py`: Test NOT NULL constraint enforcement
- `test_legacy_field_removal.py`: Test supplier_name removal

**Data Validation Queries:**

```sql
-- Verify all records have supplier_id before Phase 4
SELECT 
    'procurement_options' as table_name,
    COUNT(*) as total,
    COUNT(supplier_id) as with_supplier_id,
    COUNT(*) - COUNT(supplier_id) as without_supplier_id
FROM procurement_options
WHERE supplier_name IS NOT NULL
UNION ALL
SELECT 
    'supplier_payments',
    COUNT(*),
    COUNT(supplier_id),
    COUNT(*) - COUNT(supplier_id)
FROM supplier_payments
WHERE supplier_name IS NOT NULL;
```

#### Rollback Strategies

##### Phase 1 Rollback

```sql
-- Rollback: Remove new tables and columns
BEGIN;

-- Drop new tables
DROP TABLE IF EXISTS package_payments CASCADE;
DROP TABLE IF EXISTS package_subitems CASCADE;
DROP TABLE IF EXISTS procurement_packages CASCADE;

-- Remove package_id columns
ALTER TABLE procurement_options DROP COLUMN IF EXISTS package_id;
ALTER TABLE finalized_decisions DROP COLUMN IF EXISTS package_id;
ALTER TABLE delivery_options DROP COLUMN IF EXISTS package_id;

-- Remove constraints
ALTER TABLE delivery_options DROP CONSTRAINT IF EXISTS check_delivery_option_reference;
ALTER TABLE procurement_options DROP CONSTRAINT IF EXISTS check_procurement_option_reference;

-- Revert project_item_id to NOT NULL in delivery_options
ALTER TABLE delivery_options ALTER COLUMN project_item_id SET NOT NULL;

COMMIT;
```

##### Phase 2 Rollback

```sql
-- Rollback: Unlink packages, set package_id to NULL
BEGIN;

-- Unlink procurement_options
UPDATE procurement_options SET package_id = NULL;

-- Unlink finalized_decisions
UPDATE finalized_decisions SET package_id = NULL;

-- Unlink delivery_options
UPDATE delivery_options SET package_id = NULL;

-- Unlink financial records
UPDATE invoices SET package_id = NULL WHERE package_id IS NOT NULL;
UPDATE payments SET package_id = NULL WHERE package_id IS NOT NULL;
UPDATE supplier_payments SET package_id = NULL WHERE package_id IS NOT NULL;

-- Remove package_subitems
DELETE FROM package_subitems;

-- Delete FULL packages (optional - keep for reference)
-- DELETE FROM procurement_packages WHERE package_type = 'FULL';

COMMIT;
```

##### Phase 3 Rollback

**Application-Level:**
- Disable feature flags: `ENABLE_PACKAGE_AWARE_PROCUREMENT=false`
- Revert code to legacy logic
- No database changes required

##### Phase 4 Rollback

**Requires Backup Restoration:**
- Restore database from pre-Phase 4 backup
- OR manually re-add columns:

```sql
-- Re-add supplier_name columns
ALTER TABLE supplier_payments 
ADD COLUMN supplier_name VARCHAR(200);

ALTER TABLE procurement_options 
ADD COLUMN supplier_name TEXT;

-- Re-populate from backup or supplier_id FK
-- Then remove NOT NULL constraint
ALTER TABLE supplier_payments 
ALTER COLUMN supplier_id DROP NOT NULL;
```

---

*Design Document: Future-State Procurement Data Model*
*Date: 2025-01-XX*
*Status: Conceptual Design + Implementation Plan*

