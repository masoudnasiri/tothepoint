# Sprint 3A-R2 - Payment and Cost Contract Restoration

- Status: PASS WITH MINOR ISSUES
- Date: 2026-06-25
- Branch: `recovery/sprint3a-r2-payment-cost-contract`

## Why R1 Was Incomplete

Sprint 3A-R1 restored the visible 3-section Step 3 layout, but manual review found that operational payment/cost contract details were still incomplete:

- `BASE_PRICE` was required at save-time but not always present as a default visible row.
- quantity/package discount controls were no longer visible in Step 3.
- payment terms controls for cash/installments were removed from Step 3.
- the payment section label used the missing translation key `procurement.payment`.

## Accepted Behavior Evidence Used

### Payment terms and discount evidence

- `frontend/src/components/PackageWizard/PackageWizardStep3.tsx` in prior baseline (`7bc20a5` and `restart/accepted-through-sprint4a-clean-fix`) included:
  - cash/installments selector
  - installment schedule editor
  - bundle discount threshold/percent controls
- `backend/app/models.py` includes persisted fields:
  - `payment_terms` (JSON)
  - `discount_bundle_threshold`
  - `discount_bundle_percent`
  - `payment_method_id`
  - `planned_supplier_payment_date`
  - `supplier_effective_receipt_date`
- `backend/app/schemas.py` defines installments contract as `payment_terms.schedule` rows (`due_offset`, `percent`) summing to 100.

### Cost component contract evidence

- `docs/architecture/ADR-005-procurement-option-persistence-contract.md` confirms accepted contract:
  - cost components are source of truth
  - exactly one active `BASE_PRICE` required
  - optional component types include `SHIPPING`, `VAT`, `CUSTOMS`, `CLEARANCE`, `INSURANCE`, `BANK_FEE`, `OTHER`
  - `payment_method_id` + `planned_supplier_payment_date` persist
  - `supplier_effective_receipt_date` is derived from settlement delay

## Restoration Scope Decision

- Restored:
  - default visible `BASE_PRICE` row in Step 3 (non-removable when it is the only base row)
  - optional component controls preserved
  - bundle discount fields restored in Pricing and Costs section
  - payment terms selector restored with backend-compatible installment shape (`schedule`)
  - planned supplier payment date label made explicit
  - payment section translation key fixed (`procurement.payment`)
- Deferred (explicit):
  - per-part persisted payment rows with separate amount/date/method/effective-receipt per part were **not** restored because current backend contract persists payment terms JSON + one planned supplier payment date (no dedicated payment-part persistence model in procurement option contract).

## Persistence Contract Outcome

- Confirmed unchanged backend persistence for:
  - `BASE_PRICE` and optional components via cost component APIs
  - `payment_method_id`
  - `planned_supplier_payment_date`
  - `supplier_actual_delivery_date`
- Confirmed derived behavior remains server-side:
  - `supplier_effective_receipt_date`
  - `selected_delivery_date`
  - `forecast_customer_invoice_date`
  - `forecast_customer_receipt_date`
- Readiness endpoint remains read-only.

## Files Changed

- `frontend/src/components/PackageWizard/PackageWizard.tsx`
- `frontend/src/components/PackageWizard/PackageWizardStep3.tsx`
- `frontend/src/components/PackageWizard/PackageWizard.saveBoundary.test.tsx`
- `frontend/src/components/PackageWizard/PackageWizardStep3.test.tsx`
- `frontend/src/i18n/en.json`
- `frontend/src/i18n/fa.json`
- `docs/restart-audit/49_sprint3a_r2_payment_cost_contract_restoration.md`
- `docs/restart-audit/08_recommended_continuation_plan.md`

## Tests Executed

Frontend:

- `npm test -- --watch=false PackageWizard` -> pass
- `npm test -- --watch=false` -> pass
- `CI=false npm run build` -> pass with pre-existing warnings outside R2 scope

Backend regression guards:

- `python -m pytest tests/test_phase13c_procurement_option_persistence_readiness.py -q` -> pass
- `python -m pytest tests/test_project_item_procurement_eligibility.py -q` -> pass
- `python -m pytest tests -q` -> pass

## Deployment and Runtime Smoke (R2)

- To be completed in this sprint's release step using scope-clean artifact and `/opt/rivar-demo` installer flow.
- Required artifact must include all changed Step 3 files and this audit note.

## Remaining Risks

- Installment terms are now persisted in backend-compatible `schedule` shape, but company cash-outflow timing still uses single `planned_supplier_payment_date` in current projection/readiness flow.
- Frontend test logs still show known test-environment warnings (supplier fallback mock and MUI out-of-range select warning) that do not block contract behavior.
