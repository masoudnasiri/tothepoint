# Rivar Restart Audit - Database and Domain Model

## Data Model Strategy

- Runtime schema is driven by SQLAlchemy models (`backend/app/models.py`, `backend/app/models_invoice_payment.py`) and created at startup.
- Incremental schema/data migrations for Phase 3 package rollout are in raw SQL scripts under `backend/`.
- Alembic revision chain is not present in this repo snapshot.

## Domain Map (Core Entities)

## Projects

- **Model/table:** `Project` / `projects`
- **Important fields:** `project_code`, `name`, `priority_weight`, `is_active`
- **Relationships:** phases, assignments, items
- **APIs:** `/projects/*` (`backend/app/routers/projects.py`)
- **UI:** `frontend/src/pages/ProjectsPage.tsx`
- **Status:** complete and in use

## Users and Roles

- **Model/table:** `User` / `users`
- **Important fields:** `username`, `password_hash`, `role`, `is_active`
- **Relationships:** assignments, created/updated references
- **APIs:** `/auth/*`, `/users/*`
- **UI:** `frontend/src/pages/LoginPage.tsx`, `frontend/src/pages/UsersPage.tsx`
- **Status:** complete; role helper functions exist but endpoint-level strict role gating is inconsistent

## Project Items (Procurement Demand)

- **Model/table:** `ProjectItem` / `project_items`
- **Important fields:** `project_id`, `item_code`, `item_name`, `quantity`, `status`, `master_item_id`
- **Relationships:** `delivery_options_rel`, `sub_items_quantities`, `packages`
- **APIs:** `/items/*`
- **UI:** `frontend/src/pages/ProjectItemsPage.tsx`, `frontend/src/pages/ProcurementPage.tsx`
- **Status:** complete, actively used

## Master Items

- **Model/table:** `ItemMaster` / `items_master`
- **Important fields:** master metadata and normalization fields
- **Relationships:** has many `ItemSubItem`; referenced by `ProjectItem.master_item_id`
- **APIs:** `/items-master/*`
- **UI:** `frontend/src/pages/ItemsMasterPage.tsx`, Project Item creation flow
- **Status:** complete and used

## Item Components / Sub-items

- **Model/table:** `ItemSubItem` / `item_subitems`
- **Important fields:** `item_master_id`, `name`, `part_number`, description
- **Relationships:** belongs to master item; projected into project-level requirements via `ProjectItemSubItem`
- **APIs:** nested under `/items-master/{id}/subitems`
- **UI:** Project item breakdown editing in `ProjectItemsPage`
- **Status:** complete for master-level definition

## Project-Level Sub-item Quantities (BOM-like)

- **Model/table:** `ProjectItemSubItem` / `project_item_subitems`
- **Important fields:** `project_item_id`, `item_subitem_id`, `quantity`
- **Relationships:** links project item demand to component requirements
- **APIs:** `/items/{item_id}/subitems`, create/update item payload
- **UI:** `ProjectItemsPage` item form and display
- **Status:** complete and central to package coverage logic

## Suppliers

- **Model/table:** `Supplier`, `SupplierContact`, `SupplierDocument`
- **Important fields:** `supplier_id`, `company_name`, status/compliance/risk, contacts/docs
- **Relationships:** referenced by packages and procurement options
- **APIs:** `/suppliers/*`
- **UI:** `frontend/src/pages/SuppliersPage.tsx`
- **Status:** complete and used

## Supplier Offers / Procurement Options

- **Model/table:** `ProcurementOption` / `procurement_options`
- **Important fields:** `project_item_id`, `item_code`, `package_id`, `supplier_id`, `supplier_name`(legacy), costs, payment/delivery metadata
- **Relationships:** linked to project item and optionally package
- **APIs:** `/procurement/options*`
- **UI:** Procurement flows and package wizard pricing step
- **Status:** complete but dual-mode transitional

## Supplier Packages / Bundles

- **Model/table:** `ProcurementPackage` / `procurement_packages`
- **Important fields:** `project_item_id`, `package_name`, `package_type`, `supplier_id`, `main_item_quantity`, `is_active`
- **Relationships:** has many `PackageSubItem`; can be linked by options/delivery/decisions
- **APIs:** `/packages/*`, project coverage endpoints
- **UI:** `ProcurementPage`, `PackageWizard`, `PackageList`
- **Status:** implemented and actively integrated

## Package Component Coverage

- **Model/table:** `PackageSubItem` / `package_subitems`
- **Important fields:** `package_id`, `project_item_subitem_id`, `quantity_covered`, `coverage_percentage`
- **Relationships:** bridge package <-> project subitem requirement
- **APIs:** `/packages/subitems/*`
- **UI:** wizard step 2 composition + coverage
- **Status:** implemented

## Delivery Planning

- **Model/table:** `DeliveryOption` / `delivery_options`
- **Important fields:** `project_item_id`, `package_id`, `delivery_date`, invoice timing fields
- **Relationships:** linked to item/package and later decisions
- **APIs:** `/delivery-options/*`
- **UI:** delivery management components, package wizard step 3
- **Status:** complete with package-aware extension

## Decisions / Decision Lifecycle

- **Model/table:** `FinalizedDecision` / `finalized_decisions`
- **Important fields:** run linkage, item/option/package refs, dates, cost, status (`PROPOSED`, `LOCKED`, `REVERTED`)
- **Relationships:** tied to optimization runs/results, cashflow events
- **APIs:** `/decisions/*`
- **UI:** `frontend/src/pages/FinalizedDecisionsPage.tsx`
- **Status:** complete with package reference enrichment

## Finance, Cashflow, Budget

- **Model/table:** `BudgetData`, `CashflowEvent`, optimization run/result tables, invoice/payment tables
- **Important fields:** budget dates/amounts, event dates/types, status and amounts
- **Relationships:** decisions generate inflow/outflow events
- **APIs:** `/finance/*`, `/procurement-plan/*`, invoice/payment routers
- **UI:** finance, analytics, procurement-plan pages
- **Status:** substantial and integrated

## Audit Logs

- **Model/table:** `AuditLog` + migration audit structures (`migration_audit_log` in SQL scripts)
- **Important fields:** action metadata, actor, timestamps
- **Relationships:** cross-cutting telemetry
- **APIs:** `/audit-logs/*`
- **UI:** `frontend/src/pages/AuditLogsPage.tsx`
- **Status:** implemented; phase-specific logs used in package rollout

## Procurement Sub-item/Package Migration Lineage

Primary scripts evidencing phased rollout:

- Schema phase:
  - `create_procurement_packages_table.sql`
  - `create_package_subitems_table.sql`
  - `create_package_payments_table.sql`
  - `add_package_id_columns.sql`
  - `add_procurement_options_check_constraint.sql`
- Data phase:
  - `create_full_packages_for_project_items.sql`
  - `populate_package_subitems.sql`
  - `link_procurement_options_to_packages.sql`
  - `link_finalized_decisions_to_packages.sql`
  - `link_delivery_options_to_packages.sql`
  - `normalize_supplier_names_to_ids.sql`
  - `link_financial_records_to_packages.sql`
  - `validate_phase2_migration.sql`

## Completeness Readout (Domain-Level)

- **Complete and used:** projects, users/auth, items, suppliers, options, delivery, decisions, finance basics
- **Phase 3 implemented but still transitional:** package-first procurement with legacy fallback and feature flags
- **Partially completed/at risk:** strict package-only enforcement, package-native optimization behavior, complete test maturity for integration/API paths
