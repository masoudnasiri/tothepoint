# Rivar Feature List (Current Implementation Snapshot)

## 1) Platform and Security

- JWT-based authentication (`/auth/*`)
- Role-based behavior across PM, PMO, procurement, finance, admin
- Audit log module and audit log UI (`/audit-logs`)
- Multi-language support (English/Persian)

## 2) Project and Item Management

- Project CRUD and assignment
- Project item CRUD
- Base/master item management
- Project item finalization/unfinalization
- Item/sub-item structure support for procurement planning

## 3) Supplier Management

- Supplier registry with normalized supplier IDs
- Supplier information and status management
- Supplier-aware procurement options

## 4) Procurement Option Management

- Procurement option CRUD
- Legacy item-based and package-aware references
- Payment terms capture and cost/currency fields
- Delivery option association

## 5) Package and Sub-item Procurement

- Procurement package CRUD (`FULL`, `PARTIAL`, etc.)
- Package sub-item composition CRUD
- Coverage summary calculation (per item/project)
- Package wizard UI for package authoring
- Coverage validation guardrails before locking decisions

## 6) Delivery Option Management

- Delivery option CRUD
- Invoice timing and amount-per-unit planning fields
- Package-aware delivery linkage

## 7) Optimization and Decisioning

- Optimization endpoints in finance domain
- Enhanced optimization pipeline support
- Save proposals as finalized decisions
- Decision lifecycle management:
  - `PROPOSED`
  - `LOCKED`
  - `REVERTED`
- Package-aware decision boundary behavior

## 8) Procurement Plan and Execution Tracking

- Locked decision listing in procurement plan
- Procurement delivery confirmation workflow
- PM delivery acceptance workflow
- Delivery status transitions and lifecycle fields

## 9) Finance Operations

- Invoice entry/list/delete (simple flow)
- Payment-in entry/list/delete (simple flow)
- Supplier payment entry/list/update/delete
- Finance actions reflected in cashflow data

## 10) Cashflow, Dashboard, Reports, Analytics

- Cashflow event model and sync service
- Dashboard APIs and UI
- Reports APIs and UI
- Analytics APIs and UI

## 11) Deployment and Operations

- Docker Compose based deployment
- Start/stop scripts for Windows/Linux
- Backup/restore scripts
- SQL-script based phased migration tools

## 12) Testing and Quality Artifacts

- Backend pytest coverage for phase-specific behavior
- Phase 5, Phase 6A, and Phase 8 RC smoke tests
- Frontend production build path (`npm run build`)

## 13) Release Candidate and Demo Readiness

- Deterministic demo dataset generator with cleanup mode (`DEMO_RC8_` tagging)
- Business-facing demo script (`docs/release/demo_script_phase8.md`)
- Product smoke test checklist (`docs/release/product_smoke_test_checklist.md`)
- Release candidate checklist gate (`docs/release/release_candidate_checklist.md`)

## Known Constraints (As of Current Snapshot)

- Mixed legacy and modern finance write paths still exist.
- Some integration tests are placeholder/skipped.
- Deployment scripts require careful DB backup verification.
- Package metadata/reporting is improved but still being hardened phase-by-phase.
