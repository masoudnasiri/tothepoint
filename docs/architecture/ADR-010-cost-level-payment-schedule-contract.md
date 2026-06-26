# ADR-010: Cost-Level Payment Schedule Contract

## Status
Accepted (Sprint 3A-R3)

## Context

Sprint 3A-R2 restored option-level payment terms (`payment_method_id`, `planned_supplier_payment_date`, `payment_terms`) and cost-component pricing in Step 3.
Product review found a domain gap: multiple cost components can be paid to different parties (supplier, logistics, insurance, bank, customs), but the model only persisted one option-level payment schedule.

Without a component-level contract:

- payment timing cannot represent mixed payees safely,
- readiness cannot explain component-level payment gaps,
- financial projection can double-count or mis-time outflows when custom schedules are needed.

## Decision

1. **Add cost-component payment metadata**
   - `procurement_cost_components.payment_metadata` (JSON) is added as an optional field.
   - Default behavior is inheritance from option-level payment settings.

2. **Define component payment contract**
   - `inherit_option_payment_schedule` (default `true`)
   - `payee_type` (`SUPPLIER`, `LOGISTICS_PROVIDER`, `INSURANCE_PROVIDER`, `CUSTOMS_OR_CLEARANCE`, `BANK_OR_EXCHANGE`, `OTHER`)
   - `payee_label` (optional free text)
   - `payment_method_id` (required when inheritance disabled)
   - `payment_type` (`CASH`, `INSTALLMENTS`)
   - `planned_payment_date` (required for custom CASH)
   - `payment_schedule[]` rows for INSTALLMENTS (`due_offset_days` or `due_date`, plus `percent` or `amount_value`)

3. **Backwards compatibility by default inheritance**
   - Existing options/components remain valid with no migration rewrite.
   - If no custom metadata is present, read-model behavior stays option-level.

4. **Read-model integration**
   - Readiness returns `component_payment_diagnostics` and warning codes per component.
   - Atomic candidates include raw `payment_metadata` and resolved diagnostics.
   - Financial projection treats custom component schedules as cash-effective outflows and uses inherited subset for default supplier outflow to prevent double-counting.

5. **Save/reopen stability**
   - Procurement option save/update path materializes responses safely and avoids `MissingGreenlet` regressions in `PUT /procurement/option/{id}` flows.

## Consequences

- Product users can keep a default payment schedule while overriding only selected components.
- Readiness and projection diagnostics become explainable per component payee.
- Projection output remains deterministic and read-only while handling mixed payment timing safely.
- Installer runtime verification remains compatible; fixture discovery/reporting is dynamic and no longer tied to stale IDs.

