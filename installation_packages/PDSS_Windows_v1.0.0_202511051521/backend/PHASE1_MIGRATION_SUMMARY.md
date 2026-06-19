# Phase 1 Migration Summary - Additive Changes

## Overview
Phase 1 adds new tables and nullable columns without breaking existing functionality. All migrations are online (no downtime required).

## Migration Tasks Mapping

| Task | Description | File Name | Status |
|------|-------------|-----------|--------|
| 1.1 | Create `procurement_packages` table | `create_procurement_packages_table.sql` | To Create |
| 1.2 | Create `package_subitems` table | `create_package_subitems_table.sql` | To Create |
| 1.3 | Create `package_payments` table | `create_package_payments_table.sql` | To Create |
| 1.4 | Add `package_id` columns (nullable) | `add_package_id_columns.sql` | To Create |
| 1.5 | Make `project_item_id` nullable in `delivery_options` | `make_delivery_options_project_item_nullable.sql` | To Create |
| 1.6 | Add `supplier_id` to `supplier_payments` | `add_supplier_id_to_supplier_payments.sql` | To Create |
| 1.7 | Increase `invoice_amount_per_unit` precision | `increase_invoice_amount_precision.sql` | **Already Exists** |
| 1.8 | Add CHECK constraint for `procurement_options` | `add_procurement_options_check_constraint.sql` | To Create |

## Execution Order

1. **1.1** - Must run first (creates base table for FK references)
2. **1.2** - Depends on 1.1 (FK to procurement_packages)
3. **1.3** - Depends on 1.1 (FK to procurement_packages)
4. **1.4** - Depends on 1.1 (FK to procurement_packages)
5. **1.5** - Depends on 1.4 (needs package_id column first)
6. **1.6** - Independent (modifies supplier_payments)
7. **1.7** - Independent (already exists, can skip if already applied)
8. **1.8** - Depends on 1.4 (needs package_id column first)

## Constraints Summary

### New Tables
- `procurement_packages`: CHECK constraint on `package_type` (FULL, PARTIAL, CUSTOM)
- `package_subitems`: UNIQUE constraint on (package_id, project_item_subitem_id)
- `package_payments`: CHECK constraints on `payment_method` and `status`

### Modified Tables
- `delivery_options`: CHECK constraint ensuring `project_item_id OR package_id` is NOT NULL
- `procurement_options`: CHECK constraint ensuring at least one reference (package_id, project_item_id, or item_code)
- `supplier_payments`: CHECK constraint ensuring `supplier_id OR supplier_name` is NOT NULL

## Indexes Created

- All new tables: Primary key indexes
- All foreign keys: Indexes for performance
- `procurement_packages`: Indexes on `project_item_id`, `supplier_id`, `package_type`, `is_active`
- Unique index on `procurement_packages(project_item_id, package_name)` where name is NOT NULL

## Notes

- All migrations use `BEGIN;` / `COMMIT;` for atomicity
- All use `IF NOT EXISTS` / `IF EXISTS` for idempotency
- All columns added are nullable (backward compatible)
- Migration 1.7 already exists in repository - verify if already applied before running

