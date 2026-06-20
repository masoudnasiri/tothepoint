# Rivar Full Application Overview and Description

## What Rivar Is

Rivar is a project-based procurement decision support platform designed for organizations that need to plan, compare, optimize, and execute procurement across multiple projects while tracking financial impact and delivery lifecycle.

It combines operational procurement workflows with decision analytics and cashflow visibility.

## Business Problem It Solves

Organizations often manage procurement using disconnected spreadsheets and partial supplier data.  
Rivar provides one integrated workflow to:

- define project demand,
- compare supplier options,
- optimize timing/cost decisions,
- finalize and execute procurement plans,
- monitor invoice/payment and cashflow outcomes.

## Core Functional Domains

1. Project and item planning
2. Supplier and procurement option management
3. Package/sub-item procurement (full or partial coverage)
4. Optimization-assisted decisioning
5. Procurement execution tracking (delivery and acceptance)
6. Finance operations (invoice/payment in/out)
7. Cashflow/dashboard/reporting/analytics
8. Auditability and operational traceability

## System Architecture (High Level)

- Backend API: FastAPI app with SQLAlchemy async ORM
- Frontend app: React + TypeScript + Material UI
- Database: PostgreSQL in runtime (Docker)
- Test DB: SQLite (pytest fixtures)
- Deployment model: Docker Compose with script-based operations
- Migration model: SQL script phases (schema + data migration scripts)

## Main User Roles

- Admin: platform control and cross-domain access
- PMO: project-level oversight and planning coordination
- PM: project delivery acceptance and project-scoped execution
- Procurement: supplier/package operations and delivery confirmation
- Finance: decision locking, finance entries, optimization/financial flows
- Management view: reporting/analytics consumption

## End-to-End Workflow (Current Product Shape)

1. Create projects and project items.
2. Define sub-items/components where required.
3. Create supplier options and package offers.
4. Add delivery options and financial timing assumptions.
5. Run optimization / generate proposals.
6. Save decisions and finalize (lock) approved choices.
7. Execute procurement plan (delivery confirm + PM accept).
8. Enter invoice/payment records and supplier payments.
9. Track cashflow, dashboard KPIs, and reports.

## Package/Sub-item Capability

The platform supports parent-item decomposition into sub-items and supplier packages that may cover:

- full component set, or
- partial component set.

Decision lock can enforce complete package coverage for required components (feature-flag and validation-path dependent).

## Financial and Analytical Perspective

Rivar supports both planning (forecast) and execution (actual) views:

- forecast-oriented invoice/payment timing fields,
- actual invoice/payment and supplier payment records,
- cashflow events for inflow/outflow,
- dashboard/reporting and analytics endpoints/pages.

## Current Maturity Snapshot

- Core operational modules already exist and are active.
- Recent hardening phases focused on package-aware compatibility and integration consistency.
- Legacy + package-aware paths currently coexist, so strict deprecation requires controlled rollout.
- Release-candidate support now includes deterministic demo dataset tooling and smoke-test checklists.

## Strategic Direction (Near-Term)

Based on restart audit and hardening phases, near-term work should prioritize:

1. compatibility hardening over subsystem rebuild,
2. stronger regression coverage for cross-module flows,
3. deployment/update safety and backup verification,
4. progressive cleanup of legacy pathways with explicit migration planning.

## Related Documents

- `docs/restart-audit/01_project_overview.md`
- `docs/restart-audit/02_architecture_map.md`
- `docs/restart-audit/03_run_and_deployment.md`
- `docs/restart-audit/05_procurement_subitem_package_feature.md`
- `docs/restart-audit/14_existing_operational_modules_regression_audit.md`
