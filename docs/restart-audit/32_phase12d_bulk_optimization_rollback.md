# Phase 12D - Bulk Rollback for Optimization Submission

## Scope

- Phase: `12D`
- Product: `Rivar`
- Producer: `Corbit`
- Version: `1.0.0-rc1`
- Context: UAT follow-up for controlled, filter-driven rollback of sent-to-optimization procurement items.

## User Requirement

- Add a bulk rollback flow that mirrors bulk send behavior.
- Allow procurement users to preview and select rollback targets using checklist and range filters.
- Enforce server-side safety checks; unsafe items must be skipped with explicit reasons.
- Preserve package/procurement data and unlock editing only for safely rolled-back items.

## Rollback Eligibility Rules Implemented

- Item must have active optimization submission status `SENT`.
- Rollback is blocked when any downstream dependencies exist, including:
  - optimization results referencing the item/options,
  - finalized decisions (any lifecycle status),
  - procurement execution state beyond waiting delivery,
  - active cashflow events,
  - invoice/payment/supplier payment records.
- Price-range execution requires resolvable IRR-equivalent cost; missing conversion becomes an unsafe skip reason.

## Filter Criteria Implemented

- Checklist filters:
  - package type (`full`, `partial`)
  - coverage state (`complete`, `incomplete`, `over-covered`)
  - supplier geography (`domestic`, `foreign`)
  - supplier multiplicity (`single`, `multiple`)
  - warning-confirmed incomplete submissions
- Price range:
  - `min_total_cost_irr`
  - `max_total_cost_irr`
  - uses IRR-equivalent amount when available
- Date range:
  - `date_from`, `date_to`
  - selectable field: `submitted_at`, `delivery_date`, `purchase_date`, `project_need_date`

## Backend Endpoints Added

- `POST /packages/optimization-rollback-preview`
  - non-mutating preview
  - returns `matched_items`, `rollbackable_items`, `unsafe_items`, grouped summary, warnings
- `POST /packages/optimization-rollback`
  - requires explicit `confirmed=true`
  - re-validates eligibility via preview logic inside execution
  - rolls back only safe selected items
  - skips unsafe/unmatched items with reason payload

## Backend Services Added

- `backend/app/services/optimization_rollback_service.py`
  - `build_bulk_rollback_preview(...)`
  - `execute_bulk_rollback(...)`
  - dependency and data-consistency safety checks
  - grouped preview summaries by package/coverage/supplier/date/cost categories

## Frontend UI Added

- Procurement page header action:
  - `Rollback from optimization / بازگردانی از بهینه‌سازی`
- Bulk rollback dialog:
  - checklist filters
  - IRR min/max cost filters
  - date field selector and date range filters
  - preview action and summary counts
  - unsafe section with skip reasons
  - selectable rollbackable items and explicit confirmation execution
- Post-execution UX:
  - procurement list refresh
  - item optimization state update
  - package create/edit/delete re-enabled for rolled-back items
  - rolled-back/skipped summary notice

## Safety and Audit Behavior

- Execution refuses non-confirmed requests.
- Unsafe items are never rolled back silently.
- Audit records are written for:
  - per-item rollback success,
  - per-item skip reasons,
  - bulk execution summary.

## Tests Added

- `backend/tests/test_phase12d_bulk_optimization_rollback.py`
  - Test A: safe sent item appears rollbackable in preview
  - Test B: unsafe item is previewed/skipped with reasons
  - Test C: checklist filters (package/coverage) gate preview correctly
  - Test D: IRR price range filter behavior
  - Test E: date range filter behavior
  - Test F: execute rollback unlocks package create flow
  - Test G: confirmation is mandatory

## Manual Verification Result

- Pending business-owner UI verification on UAT for:
  - filter combinations and preview summaries
  - unsafe skip messaging
  - unlock behavior after confirmed rollback
  - audit visibility in runtime views/logs

## Remaining Limitations

- Supplier-type classification relies on supplier country master data quality.
- Items missing exchange-rate data are intentionally marked unsafe for price-filtered rollback execution.

## Phase 12D Status

- Implementation in codebase: complete.
- UAT runtime verification: pending command run + manual UI confirmation.
