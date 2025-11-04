# Procurement Data Model Analysis Report

## Executive Summary

This report analyzes the current procurement data model to identify limitations preventing supplier assignment at both the **project item** and **subitem/package** levels. The analysis is based on examination of SQL migrations, SQLAlchemy models, and existing relationships.

---

## Current Entity-Relationship Summary

| Entity | Key Columns | Primary Relationships | Purpose |
|--------|-------------|----------------------|---------|
| **items_master** | `id`, `item_code`, `company`, `item_name`, `model`, `category`, `part_number` | → `item_subitems` (1:N), → `project_items` (1:N) | Master catalog of all items/products |
| **item_subitems** | `id`, `item_master_id` (FK), `name`, `description`, `part_number` | → `items_master` (N:1), → `project_item_subitems` (1:N) | Sub-item definitions (components/parts) within a master item |
| **project_items** | `id`, `project_id` (FK), `master_item_id` (FK), `item_code`, `quantity`, `status`, `is_finalized` | → `projects` (N:1), → `items_master` (N:1), → `project_item_subitems` (1:N), → `procurement_options` (1:N), → `finalized_decisions` (1:N), → `delivery_options` (1:N) | Project-specific item instances |
| **project_item_subitems** | `id`, `project_item_id` (FK), `item_subitem_id` (FK), `quantity` | → `project_items` (N:1), → `item_subitems` (N:1) | Quantities of sub-items required for a specific project item |
| **procurement_options** | `id`, `item_code`, `supplier_id` (FK, nullable), `supplier_name` (legacy), `project_item_id` (FK, nullable), `cost_amount`, `cost_currency`, `delivery_option_id` (FK), `is_active`, `is_finalized` | → `suppliers` (N:1), → `project_items` (N:1), → `delivery_options` (N:1), → `finalized_decisions` (1:N) | Available procurement options/quotes for items |
| **finalized_decisions** | `id`, `project_item_id` (FK), `procurement_option_id` (FK), `quantity`, `final_cost_amount`, `final_cost_currency`, `status`, `delivery_status` | → `project_items` (N:1), → `procurement_options` (N:1), → `supplier_payments` (1:N) | Final procurement decisions and execution tracking |
| **suppliers** | `id`, `supplier_id` (unique), `company_name`, `category`, `status`, `compliance_status` | → `procurement_options` (1:N), → `supplier_contacts` (1:N), → `supplier_documents` (1:N) | Centralized supplier master data |
| **delivery_options** | `id`, `project_item_id` (FK), `delivery_date`, `invoice_amount_per_unit`, `invoice_timing_type` | → `project_items` (N:1), → `procurement_options` (N:1) | Delivery timing and invoice configuration for project items |
| **supplier_payments** | `id`, `decision_id` (FK), `package_id` (FK, nullable, future), `supplier_id` (FK, nullable, **required for new records**), `supplier_name` (legacy, deprecated), `item_code`, `project_id` (FK), `payment_amount`, `currency`, `payment_date`, `status` | → `finalized_decisions` (N:1), → `procurement_packages` (N:1, future), → `suppliers` (N:1, future), → `projects` (N:1) | Payment tracking for supplier transactions. Future: package-level payments with normalized supplier FK. supplier_id required for new records, nullable during transition. |

### Critical Relationship Notes

1. **procurement_options** → **project_items**: 
   - `project_item_id` is **nullable** and optional
   - Can exist without a specific project item (legacy `item_code`-based approach)
   - **Supports multiple options per project item**

2. **procurement_options** → **suppliers**:
   - `supplier_id` is **nullable** (legacy `supplier_name` still exists)
   - Migration attempts to match names, but some may remain unlinked

3. **project_item_subitems**:
   - **No direct relationship to procurement options or suppliers**
   - Only tracks quantities of sub-items per project item
   - **Cannot assign suppliers at sub-item level**

4. **finalized_decisions**:
   - Always references a **project_item_id** (not nullable)
   - References a **procurement_option_id** (which may have supplier)
   - **No sub-item-level decision tracking**

---

## Pain Points for Package-Level Procurement

### 1. **No Supplier Assignment at Sub-Item Level**

**Current State:**
- `project_item_subitems` only stores quantities (`project_item_id`, `item_subitem_id`, `quantity`)
- No `supplier_id` or `procurement_option_id` fields
- Sub-items are treated as part of the parent project item, not as independent procurement targets

**Impact:**
- Cannot assign different suppliers to different sub-items within the same project item
- Example: A "Server Rack" project item may have sub-items: "Cisco Router", "HP Switch", "Dell Server". Currently, all must come from the same supplier, but in reality, different suppliers may provide each component.

**Business Case:**
- Complex equipment often requires sourcing components from multiple suppliers
- Different suppliers may specialize in different sub-components
- Cost optimization requires comparing sub-item suppliers independently

---

### 2. **Procurement Options Only at Project Item Level**

**Current State:**
- `procurement_options` links to `project_item_id` (nullable) or uses `item_code` (string)
- One procurement option = one supplier quote for the entire project item
- Cannot create procurement options for individual sub-items

**Impact:**
- Procurement team cannot create quotes/options for sub-items separately
- Optimization engine cannot compare sub-item-level supplier options
- Cannot track "Supplier A for Router, Supplier B for Switch" within the same project item

**Business Case:**
- Procurement teams receive quotes at component level, not just assembly level
- Need to compare "Router from Supplier A" vs "Router from Supplier B" independently
- Sub-item-level procurement enables better cost optimization

---

### 3. **Finalized Decisions Cannot Track Sub-Item Suppliers**

**Current State:**
- `finalized_decisions` has `project_item_id` and `procurement_option_id`
- One decision = one supplier for entire project item
- No sub-item-level decision tracking

**Impact:**
- Cannot finalize "Supplier A for Router, Supplier B for Switch" in the same decision
- Cannot track delivery status per sub-item supplier
- Payment tracking (`supplier_payments`) only at decision level, not sub-item level

**Business Case:**
- Execution phase requires tracking which sub-item came from which supplier
- Delivery tracking needs sub-item granularity
- Payment processing needs to split payments across multiple suppliers for one project item

---

### 4. **No Package/Assembly Concept**

**Current State:**
- `project_item_subitems` is a simple quantity mapping
- No concept of "packages" or "assemblies" that can be procured as units
- No way to group sub-items into procurement packages

**Impact:**
- Cannot define procurement packages like "Network Package: Router + Switch + Cables"
- Cannot assign one supplier to a package while another supplier handles individual components
- Cannot track package-level pricing vs component-level pricing

**Business Case:**
- Suppliers often offer package deals
- Need flexibility to procure "package A from Supplier X" and "package B from Supplier Y"
- Packages may overlap with individual component procurement

---

### 5. **Supplier Reference Inconsistency**

**Current State:**
- `procurement_options.supplier_id` is nullable (migration incompleteness)
- Legacy `supplier_name` field still exists
- `supplier_payments.supplier_name` is a string (not FK to suppliers table)
- `supplier_payments` lacks `package_id` and `supplier_id` FK fields

**Impact:**
- Some procurement options may not be linked to supplier master data
- Payment tracking uses string names instead of FK relationships
- Data integrity issues when supplier names change
- Cannot track supplier payments at package level
- Cannot split payments across multiple suppliers for one project item

**Business Case:**
- Need consistent supplier references across all procurement data
- Supplier master data includes compliance, contacts, documents
- Missing links prevent proper supplier relationship management
- Package-level procurement requires package-level supplier payment tracking

**Future State (from FUTURE_STATE_PROCUREMENT_MODEL.md):**
- `supplier_payments.supplier_id` (FK, nullable during transition, **required for new records**)
- `supplier_payments.package_id` (FK, nullable) for package-level payment tracking
- CHECK constraint: `(supplier_id IS NOT NULL) OR (supplier_name IS NOT NULL)` during transition
- Phase 4: Enforce `supplier_id` NOT NULL after migration, remove `supplier_name`

---

### 6. **Delivery Options Only at Project Item Level**

**Current State:**
- `delivery_options` links to `project_item_id` only
- No sub-item or package-level delivery options

**Impact:**
- Cannot specify different delivery dates for different sub-items
- Cannot track "Router arrives Jan 15, Switch arrives Jan 20" separately
- Invoice timing is tied to project item, not sub-item

**Business Case:**
- Different sub-items may have different lead times
- Need to track staggered deliveries for complex items
- Invoice timing should reflect actual delivery of sub-items

---

## Summary of Limitations

The current data model supports **project item-level procurement** but lacks:

1. ✅ **Sub-item supplier assignment** - Cannot assign suppliers to individual sub-items
2. ✅ **Sub-item procurement options** - Cannot create quotes/options at sub-item level
3. ✅ **Sub-item finalized decisions** - Cannot track which supplier provided which sub-item
4. ✅ **Package/assembly procurement** - Cannot group sub-items into procurement packages
5. ✅ **Sub-item delivery tracking** - Cannot track delivery dates per sub-item
6. ✅ **Sub-item payment tracking** - Cannot split payments across sub-item suppliers
7. ✅ **Consistent supplier references** - Legacy string fields and nullable FKs

---

## Recommendations (Analysis Only - No Implementation)

To enable package-level procurement, the following extensions would be needed:

1. **Add supplier assignment to `project_item_subitems`**
   - Optional `supplier_id` FK
   - Optional `procurement_option_id` FK
   - Allow sub-items to be assigned to suppliers independently

2. **Create `procurement_packages` table**
   - Group sub-items into packages
   - Link packages to suppliers
   - Enable package-level pricing and procurement

3. **Extend `finalized_decisions` or create `finalized_subitem_decisions`**
   - Track supplier assignments per sub-item
   - Link to sub-item-level procurement options

4. **Add sub-item-level delivery options**
   - Extend `delivery_options` or create separate table
   - Link to `project_item_subitems` instead of just `project_items`

5. **Normalize supplier references**
   - Remove legacy `supplier_name` string fields
   - Make `supplier_id` non-nullable where appropriate
   - Update `supplier_payments` to use FK instead of string
   - **supplier_payments.supplier_id**: Required (NOT NULL) for new records, nullable during transition
   - CHECK constraint during transition: `(supplier_id IS NOT NULL) OR (supplier_name IS NOT NULL)`

6. **Add sub-item payment tracking**
   - Extend `supplier_payments` to link to packages via `package_id` (FK, nullable)
   - Enable payment splitting across multiple suppliers for one project item
   - Support both consolidated payments (`package_id = NULL`) and split payments (`package_id` set)

---

## Conclusion

The current model supports **monolithic procurement** (one supplier per project item) but does not support **granular package-level procurement** (different suppliers for different sub-items within the same project item). This limitation prevents procurement teams from optimizing costs by sourcing components from multiple suppliers and tracking execution at the sub-item level.

The most critical gap is the **absence of supplier assignment at the sub-item level**, which blocks the entire package-level procurement workflow from quote creation through final payment.

---

*Report generated: Analysis of SQL migrations and models*
*Date: 2025-01-XX*

