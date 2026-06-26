from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.atomic_optimization_candidate_service import (
    build_atomic_candidates_for_option,
    build_atomic_candidates_for_procurement_package,
    build_atomic_candidates_for_project,
)
from app.services.candidate_coverage_validation_service import (
    validate_candidate_coverage_for_option,
    validate_candidate_coverage_for_package,
    validate_candidate_coverage_for_project,
)


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _to_date(value: Any) -> Optional[date]:
    if isinstance(value, date):
        return value
    if value is None:
        return None
    try:
        return date.fromisoformat(str(value))
    except Exception:
        return None


def _candidate_id(candidate: Dict[str, Any], idx: int) -> str:
    return str(candidate.get("candidate_id") or f"candidate-index:{idx}")


def _issue(
    *,
    code: str,
    severity: str,
    message: str,
    candidate: Optional[Dict[str, Any]] = None,
    event_type: Optional[str] = None,
    field: Optional[str] = None,
    trace_lines: Optional[List[str]] = None,
) -> Dict[str, Any]:
    candidate = candidate or {}
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "candidate_id": candidate.get("candidate_id"),
        "project_id": candidate.get("project_id"),
        "project_item_id": candidate.get("project_item_id"),
        "package_id": candidate.get("package_id"),
        "procurement_option_id": candidate.get("procurement_option_id"),
        "event_type": event_type,
        "field": field,
        "trace_lines": trace_lines or [],
    }


def _add_issue(
    *,
    blocking_issues: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
    issue: Dict[str, Any],
) -> None:
    if issue.get("severity") == "BLOCKING":
        blocking_issues.append(issue)
    else:
        warnings.append(issue)


def _period_key(event_date: Optional[date]) -> Optional[str]:
    if event_date is None:
        return None
    return f"{event_date.year:04d}-{event_date.month:02d}"


def _event_id(
    *,
    candidate_id: str,
    event_type: str,
    source_id: Optional[str],
    event_date: Optional[date],
) -> str:
    return (
        f"projection:{candidate_id}:{event_type}:{source_id or 'na'}:"
        f"{event_date.isoformat() if event_date else 'na'}"
    )


def _component_event_type(component_type: str) -> str:
    mapping = {
        "BASE_PRICE": "PURCHASE_COST_OUTFLOW",
        "SHIPPING": "SHIPPING_OUTFLOW",
        "VAT": "VAT_OUTFLOW",
        "CUSTOMS": "CUSTOMS_OUTFLOW",
        "CLEARANCE": "CLEARANCE_OUTFLOW",
        "INSURANCE": "INSURANCE_OUTFLOW",
        "BANK_FEE": "BANK_FEE_OUTFLOW",
        "OTHER": "OTHER_COST_OUTFLOW",
    }
    return mapping.get(str(component_type or "").strip().upper(), "UNKNOWN_OUTFLOW")


def _normalize_component_payment_metadata(component: Dict[str, Any]) -> Dict[str, Any]:
    raw_metadata = component.get("payment_metadata") or {}
    if not isinstance(raw_metadata, dict):
        raw_metadata = {}
    inherit = bool(raw_metadata.get("inherit_option_payment_schedule", True))
    payment_type = str(raw_metadata.get("payment_type") or "CASH").strip().upper()
    if payment_type not in {"CASH", "INSTALLMENTS"}:
        payment_type = "CASH"
    return {
        "inherit_option_payment_schedule": inherit,
        "payment_type": payment_type,
        "payment_method_id": raw_metadata.get("payment_method_id"),
        "planned_payment_date": _to_date(raw_metadata.get("planned_payment_date")),
        "payment_schedule": (
            raw_metadata.get("payment_schedule")
            if isinstance(raw_metadata.get("payment_schedule"), list)
            else []
        ),
    }


def _component_cash_schedule_rows(
    *,
    component: Dict[str, Any],
    metadata: Dict[str, Any],
    fallback_payment_date: Optional[date],
    candidate: Dict[str, Any],
    warnings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    amount = _to_decimal(component.get("amount_value"))
    if amount is None:
        return []

    if metadata.get("payment_type") != "INSTALLMENTS":
        planned_date = metadata.get("planned_payment_date") or fallback_payment_date
        if planned_date is None:
            _add_issue(
                blocking_issues=[],
                warnings=warnings,
                issue=_issue(
                    code="COMPONENT_CUSTOM_PAYMENT_DATE_MISSING",
                    severity="WARNING",
                    message="Custom component payment is missing planned payment date; excluded from cash-effective outflow rows.",
                    candidate=candidate,
                    event_type=_component_event_type(component.get("component_type")),
                ),
            )
            return []
        return [
            {
                "event_date": planned_date,
                "amount": amount,
                "trace_lines": [
                    "Cash outflow row derived from custom CASH component payment metadata."
                ],
            }
        ]

    schedule_rows = metadata.get("payment_schedule") or []
    if not schedule_rows:
        _add_issue(
            blocking_issues=[],
            warnings=warnings,
            issue=_issue(
                code="COMPONENT_INSTALLMENT_SCHEDULE_MISSING",
                severity="WARNING",
                message="Custom INSTALLMENTS component payment has no schedule; excluded from cash-effective outflow rows.",
                candidate=candidate,
                event_type=_component_event_type(component.get("component_type")),
            ),
        )
        return []

    row_results: List[Dict[str, Any]] = []
    total_percent = Decimal("0")
    has_percent_rows = False
    for row in schedule_rows:
        if not isinstance(row, dict):
            continue
        due_date = _to_date(row.get("due_date"))
        due_offset_days = row.get("due_offset_days")
        if (
            due_date is None
            and due_offset_days is not None
            and metadata.get("planned_payment_date") is not None
        ):
            due_date = metadata["planned_payment_date"] + timedelta(
                days=int(due_offset_days)
            )
        if due_date is None:
            continue

        row_amount = _to_decimal(row.get("amount_value"))
        if row_amount is None:
            percent = _to_decimal(row.get("percent"))
            if percent is not None:
                has_percent_rows = True
                total_percent += percent
                row_amount = (amount * percent) / Decimal("100")
        if row_amount is None:
            continue

        row_results.append(
            {
                "event_date": due_date,
                "amount": row_amount,
                "trace_lines": [
                    "Cash outflow row derived from custom INSTALLMENTS component payment metadata."
                ],
            }
        )

    if has_percent_rows and abs(total_percent - Decimal("100")) > Decimal("0.01"):
        _add_issue(
            blocking_issues=[],
            warnings=warnings,
            issue=_issue(
                code="COMPONENT_INSTALLMENT_PERCENT_TOTAL_MISMATCH",
                severity="WARNING",
                message="Custom INSTALLMENTS component schedule percent total is not 100; projected amounts may be incomplete.",
                candidate=candidate,
                event_type=_component_event_type(component.get("component_type")),
            ),
        )
    return row_results


def _derive_customer_revenue(
    candidate: Dict[str, Any],
) -> Tuple[Optional[Decimal], Optional[str], List[str]]:
    trace_lines: List[str] = []

    explicit_amount = _to_decimal(candidate.get("customer_revenue_amount"))
    explicit_currency = candidate.get("customer_revenue_currency")
    if explicit_amount is not None:
        trace_lines.append("Derived customer revenue from explicit candidate revenue fields.")
        return explicit_amount, explicit_currency or candidate.get("landed_cost_currency"), trace_lines

    landed_cost = _to_decimal(candidate.get("landed_cost_amount"))
    gross_margin = _to_decimal(candidate.get("gross_margin_amount"))
    landed_currency = candidate.get("landed_cost_currency")
    if landed_cost is not None and gross_margin is not None:
        trace_lines.append(
            "Derived customer revenue from landed_cost_amount + gross_margin_amount."
        )
        return landed_cost + gross_margin, landed_currency, trace_lines

    trace_lines.append("CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_PROJECTION")
    return None, None, trace_lines


def _build_projection_for_candidate(
    *,
    candidate: Dict[str, Any],
    candidate_id: str,
    blocking_issues: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    candidate_events: List[Dict[str, Any]] = []
    candidate_trace_lines: List[str] = []

    landed_cost_amount = _to_decimal(candidate.get("landed_cost_amount"))
    landed_cost_currency = candidate.get("landed_cost_currency")
    planned_payment_date = _to_date(candidate.get("planned_supplier_payment_date"))
    supplier_effective_receipt_date = _to_date(candidate.get("supplier_effective_receipt_date"))
    invoice_date = _to_date(candidate.get("forecast_customer_invoice_date"))
    receipt_date = _to_date(candidate.get("forecast_customer_receipt_date"))

    if planned_payment_date is None:
        planned_payment_date = supplier_effective_receipt_date
        if planned_payment_date is not None:
            _add_issue(
                blocking_issues=blocking_issues,
                warnings=warnings,
                issue=_issue(
                    code="SUPPLIER_PAYMENT_DATE_DEFAULTED_TO_SUPPLIER_EFFECTIVE_RECEIPT_DATE",
                    severity="WARNING",
                    message=(
                        "Planned supplier payment date was missing; defaulted to supplier effective receipt date."
                    ),
                    candidate=candidate,
                    event_type="SUPPLIER_PAYMENT_OUTFLOW",
                    field="planned_supplier_payment_date",
                ),
            )

    component_rows = list(candidate.get("cost_components_summary") or [])
    normalized_component_rows = [
        {
            "component": component,
            "payment_metadata": _normalize_component_payment_metadata(component),
        }
        for component in component_rows
    ]
    custom_component_rows = [
        row
        for row in normalized_component_rows
        if not row["payment_metadata"].get("inherit_option_payment_schedule", True)
    ]
    inherited_component_rows = [
        row
        for row in normalized_component_rows
        if row["payment_metadata"].get("inherit_option_payment_schedule", True)
    ]

    def _sum_component_amounts(rows: List[Dict[str, Any]]) -> Tuple[Optional[Decimal], Optional[str], bool]:
        running_total = Decimal("0")
        running_currency: Optional[str] = None
        mixed_currency = False
        has_values = False
        for row in rows:
            component = row["component"]
            amount = _to_decimal(component.get("amount_value"))
            currency = str(component.get("amount_currency") or "").strip().upper()
            if amount is None or not currency:
                continue
            has_values = True
            if running_currency is None:
                running_currency = currency
            elif running_currency != currency:
                mixed_currency = True
            running_total += amount
        if not has_values:
            return None, None, mixed_currency
        return running_total, running_currency, mixed_currency

    supplier_outflow_amount = landed_cost_amount
    supplier_outflow_currency = landed_cost_currency
    if custom_component_rows:
        inherited_total, inherited_currency, inherited_mixed_currency = _sum_component_amounts(
            inherited_component_rows
        )
        if inherited_mixed_currency:
            _add_issue(
                blocking_issues=blocking_issues,
                warnings=warnings,
                issue=_issue(
                    code="MULTI_CURRENCY_INHERITED_COMPONENTS_NOT_PROJECTED_AS_SINGLE_TOTAL",
                    severity="WARNING",
                    message=(
                        "Inherited default-schedule components use multiple currencies; no combined default supplier-payment amount inferred."
                    ),
                    candidate=candidate,
                    field="cost_components_summary",
                ),
            )
            supplier_outflow_amount = None
            supplier_outflow_currency = None
        else:
            supplier_outflow_amount = inherited_total
            supplier_outflow_currency = inherited_currency
        candidate_trace_lines.append(
            "Detected custom component-level payment overrides; default supplier outflow uses inherited component subset to avoid double counting."
        )
    elif supplier_outflow_amount is None and component_rows:
        component_total, component_currency, mixed_currency = _sum_component_amounts(
            normalized_component_rows
        )
        if mixed_currency:
            _add_issue(
                blocking_issues=blocking_issues,
                warnings=warnings,
                issue=_issue(
                    code="MULTI_CURRENCY_COMPONENTS_NOT_PROJECTED_AS_SINGLE_TOTAL",
                    severity="WARNING",
                    message=(
                        "Cost components use multiple currencies; no combined supplier-payment amount inferred."
                    ),
                    candidate=candidate,
                    field="cost_components_summary",
                ),
            )
        elif component_currency:
            supplier_outflow_amount = component_total
            supplier_outflow_currency = component_currency
            candidate_trace_lines.append(
                "Supplier payment outflow amount derived from active component sum."
            )

    if supplier_outflow_amount is None or supplier_outflow_currency is None:
        _add_issue(
            blocking_issues=blocking_issues,
            warnings=warnings,
            issue=_issue(
                code="SUPPLIER_OUTFLOW_AMOUNT_NOT_AVAILABLE",
                severity="WARNING",
                message="Unable to determine supplier outflow amount/currency for candidate.",
                candidate=candidate,
                event_type="SUPPLIER_PAYMENT_OUTFLOW",
                field="landed_cost_amount",
            ),
        )
    elif planned_payment_date is None:
        _add_issue(
            blocking_issues=blocking_issues,
            warnings=warnings,
            issue=_issue(
                code="SUPPLIER_PAYMENT_DATE_MISSING",
                severity="WARNING",
                message="Unable to determine supplier payment date for candidate projection.",
                candidate=candidate,
                event_type="SUPPLIER_PAYMENT_OUTFLOW",
                field="planned_supplier_payment_date",
            ),
        )
    else:
        candidate_events.append(
            {
                "projection_event_id": _event_id(
                    candidate_id=candidate_id,
                    event_type="SUPPLIER_PAYMENT_OUTFLOW",
                    source_id=str(candidate.get("procurement_option_id") or "na"),
                    event_date=planned_payment_date,
                ),
                "candidate_id": candidate_id,
                "project_id": candidate.get("project_id"),
                "project_item_id": candidate.get("project_item_id"),
                "package_id": candidate.get("package_id"),
                "procurement_option_id": candidate.get("procurement_option_id"),
                "supplier_id": candidate.get("supplier_id"),
                "event_type": "SUPPLIER_PAYMENT_OUTFLOW",
                "direction": "OUTFLOW",
                "forecast_or_actual": "FORECAST",
                "event_date": planned_payment_date,
                "period_key": _period_key(planned_payment_date),
                "calendar_system": "GREGORIAN",
                "amount": supplier_outflow_amount,
                "currency": supplier_outflow_currency,
                "source_type": "ATOMIC_CANDIDATE",
                "source_id": str(candidate.get("procurement_option_id") or "na"),
                "is_cash_effective": True,
                "trace_lines": [
                    (
                        "Company cash outflow uses default planned supplier payment date for inherited/default-schedule component costs."
                        if custom_component_rows
                        else "Company cash outflow uses planned_supplier_payment_date in Sprint 3D."
                    )
                ],
            }
        )

    for row in custom_component_rows:
        component = row["component"]
        metadata = row["payment_metadata"]
        cash_rows = _component_cash_schedule_rows(
            component=component,
            metadata=metadata,
            fallback_payment_date=planned_payment_date,
            candidate=candidate,
            warnings=warnings,
        )
        event_type = _component_event_type(component.get("component_type"))
        currency = str(component.get("amount_currency") or "").strip().upper() or None
        for cash_index, cash_row in enumerate(cash_rows):
            event_date = cash_row.get("event_date")
            if event_date is None or currency is None:
                continue
            candidate_events.append(
                {
                    "projection_event_id": _event_id(
                        candidate_id=candidate_id,
                        event_type=event_type,
                        source_id=f"{component.get('component_id') or 'na'}:{cash_index}",
                        event_date=event_date,
                    ),
                    "candidate_id": candidate_id,
                    "project_id": candidate.get("project_id"),
                    "project_item_id": candidate.get("project_item_id"),
                    "package_id": candidate.get("package_id"),
                    "procurement_option_id": candidate.get("procurement_option_id"),
                    "supplier_id": candidate.get("supplier_id"),
                    "event_type": event_type,
                    "direction": "OUTFLOW",
                    "forecast_or_actual": "FORECAST",
                    "event_date": event_date,
                    "period_key": _period_key(event_date),
                    "calendar_system": "GREGORIAN",
                    "amount": cash_row.get("amount"),
                    "currency": currency,
                    "source_type": "COST_COMPONENT_PAYMENT",
                    "source_id": str(component.get("component_id") or "na"),
                    "is_cash_effective": True,
                    "trace_lines": cash_row.get("trace_lines") or [],
                }
            )

    for component in candidate.get("cost_components_summary", []):
        amount = _to_decimal(component.get("amount_value"))
        currency = str(component.get("amount_currency") or "").strip().upper() or None
        if amount is None or currency is None:
            continue
        component_date = planned_payment_date
        component_trace = []
        if component_date is None:
            component_date = supplier_effective_receipt_date
            if component_date is not None:
                component_trace.append(
                    "COMPONENT_PAYMENT_DATE_DEFAULTED_TO_SUPPLIER_EFFECTIVE_RECEIPT_DATE"
                )
        if component_date is None:
            component_trace.append("COMPONENT_PAYMENT_DATE_MISSING")
        event_type = _component_event_type(component.get("component_type"))
        candidate_events.append(
            {
                "projection_event_id": _event_id(
                    candidate_id=candidate_id,
                    event_type=event_type,
                    source_id=str(component.get("component_id") or "na"),
                    event_date=component_date,
                ),
                "candidate_id": candidate_id,
                "project_id": candidate.get("project_id"),
                "project_item_id": candidate.get("project_item_id"),
                "package_id": candidate.get("package_id"),
                "procurement_option_id": candidate.get("procurement_option_id"),
                "supplier_id": candidate.get("supplier_id"),
                "event_type": event_type,
                "direction": "OUTFLOW",
                "forecast_or_actual": "FORECAST",
                "event_date": component_date,
                "period_key": _period_key(component_date),
                "calendar_system": "GREGORIAN",
                "amount": amount,
                "currency": currency,
                "source_type": "COST_COMPONENT",
                "source_id": str(component.get("component_id") or "na"),
                "is_cash_effective": False,
                "trace_lines": (
                    component_trace
                    + [
                        "Component rows are analytical (non-cash-effective) to avoid outflow double counting."
                    ]
                ),
            }
        )

    revenue_amount, revenue_currency, revenue_trace = _derive_customer_revenue(candidate)
    candidate_trace_lines.extend(revenue_trace)

    if invoice_date is not None:
        if revenue_amount is not None and revenue_currency is not None:
            candidate_events.append(
                {
                    "projection_event_id": _event_id(
                        candidate_id=candidate_id,
                        event_type="CUSTOMER_INVOICE_INFLOW",
                        source_id=str(candidate.get("procurement_option_id") or "na"),
                        event_date=invoice_date,
                    ),
                    "candidate_id": candidate_id,
                    "project_id": candidate.get("project_id"),
                    "project_item_id": candidate.get("project_item_id"),
                    "package_id": candidate.get("package_id"),
                    "procurement_option_id": candidate.get("procurement_option_id"),
                    "supplier_id": candidate.get("supplier_id"),
                    "event_type": "CUSTOMER_INVOICE_INFLOW",
                    "direction": "INFLOW",
                    "forecast_or_actual": "FORECAST",
                    "event_date": invoice_date,
                    "period_key": _period_key(invoice_date),
                    "calendar_system": "GREGORIAN",
                    "amount": revenue_amount,
                    "currency": revenue_currency,
                    "source_type": "CUSTOMER_SCHEDULE",
                    "source_id": str(candidate.get("procurement_option_id") or "na"),
                    "is_cash_effective": False,
                    "trace_lines": [
                        "Invoice projection is analytical/non-cash-effective in Sprint 3D."
                    ],
                }
            )
        else:
            _add_issue(
                blocking_issues=blocking_issues,
                warnings=warnings,
                issue=_issue(
                    code="CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_INVOICE_PROJECTION",
                    severity="WARNING",
                    message=(
                        "Customer invoice date exists but revenue amount is unavailable for projection."
                    ),
                    candidate=candidate,
                    event_type="CUSTOMER_INVOICE_INFLOW",
                ),
            )

    if receipt_date is not None:
        if revenue_amount is not None and revenue_currency is not None:
            candidate_events.append(
                {
                    "projection_event_id": _event_id(
                        candidate_id=candidate_id,
                        event_type="CUSTOMER_RECEIPT_INFLOW",
                        source_id=str(candidate.get("procurement_option_id") or "na"),
                        event_date=receipt_date,
                    ),
                    "candidate_id": candidate_id,
                    "project_id": candidate.get("project_id"),
                    "project_item_id": candidate.get("project_item_id"),
                    "package_id": candidate.get("package_id"),
                    "procurement_option_id": candidate.get("procurement_option_id"),
                    "supplier_id": candidate.get("supplier_id"),
                    "event_type": "CUSTOMER_RECEIPT_INFLOW",
                    "direction": "INFLOW",
                    "forecast_or_actual": "FORECAST",
                    "event_date": receipt_date,
                    "period_key": _period_key(receipt_date),
                    "calendar_system": "GREGORIAN",
                    "amount": revenue_amount,
                    "currency": revenue_currency,
                    "source_type": "CUSTOMER_SCHEDULE",
                    "source_id": str(candidate.get("procurement_option_id") or "na"),
                    "is_cash_effective": True,
                    "trace_lines": ["Customer receipt inflow is cash-effective."],
                }
            )
        else:
            _add_issue(
                blocking_issues=blocking_issues,
                warnings=warnings,
                issue=_issue(
                    code="CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_RECEIPT_PROJECTION",
                    severity="WARNING",
                    message=(
                        "Customer receipt date exists but revenue amount is unavailable for projection."
                    ),
                    candidate=candidate,
                    event_type="CUSTOMER_RECEIPT_INFLOW",
                ),
            )

    company_cash_gap_days = None
    if planned_payment_date is not None and receipt_date is not None:
        company_cash_gap_days = (receipt_date - planned_payment_date).days

    working_capital_exposure_amount = None
    if landed_cost_amount is not None:
        if planned_payment_date is not None and receipt_date is not None:
            working_capital_exposure_amount = (
                landed_cost_amount if planned_payment_date < receipt_date else Decimal("0")
            )
        else:
            _add_issue(
                blocking_issues=blocking_issues,
                warnings=warnings,
                issue=_issue(
                    code="WORKING_CAPITAL_EXPOSURE_DATES_MISSING",
                    severity="WARNING",
                    message=(
                        "Working capital exposure could not be fully evaluated due to missing payment/receipt dates."
                    ),
                    candidate=candidate,
                ),
            )

    gross_margin_amount = None
    gross_margin_ratio = None
    if revenue_amount is not None and landed_cost_amount is not None:
        if revenue_currency != landed_cost_currency:
            _add_issue(
                blocking_issues=blocking_issues,
                warnings=warnings,
                issue=_issue(
                    code="MARGIN_REQUIRES_FX_CONVERSION",
                    severity="WARNING",
                    message=(
                        "Revenue and landed cost currencies differ; margin is omitted without FX conversion."
                    ),
                    candidate=candidate,
                ),
            )
        else:
            gross_margin_amount = revenue_amount - landed_cost_amount
            if revenue_amount != 0:
                gross_margin_ratio = gross_margin_amount / revenue_amount
    else:
        _add_issue(
            blocking_issues=blocking_issues,
            warnings=warnings,
            issue=_issue(
                code="CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_MARGIN",
                severity="WARNING",
                message="Gross margin omitted because revenue is not safely available.",
                candidate=candidate,
            ),
        )

    cash_events = [event for event in candidate_events if event.get("is_cash_effective")]
    cash_inflow_total = sum(
        (event["amount"] for event in cash_events if event["direction"] == "INFLOW" and event["amount"] is not None),
        Decimal("0"),
    )
    cash_outflow_total = sum(
        (event["amount"] for event in cash_events if event["direction"] == "OUTFLOW" and event["amount"] is not None),
        Decimal("0"),
    )
    first_outflow_date = min(
        [event["event_date"] for event in cash_events if event["direction"] == "OUTFLOW" and event["event_date"] is not None],
        default=None,
    )
    first_inflow_date = min(
        [event["event_date"] for event in cash_events if event["direction"] == "INFLOW" and event["event_date"] is not None],
        default=None,
    )
    last_cash_event_date = max(
        [event["event_date"] for event in cash_events if event["event_date"] is not None],
        default=None,
    )

    candidate_summary = {
        "candidate_id": candidate_id,
        "project_id": candidate.get("project_id"),
        "project_item_id": candidate.get("project_item_id"),
        "package_id": candidate.get("package_id"),
        "procurement_option_id": candidate.get("procurement_option_id"),
        "supplier_id": candidate.get("supplier_id"),
        "currency": landed_cost_currency or revenue_currency,
        "total_forecast_inflow": cash_inflow_total,
        "total_forecast_outflow": cash_outflow_total,
        "net_forecast_cash_impact": cash_inflow_total - cash_outflow_total,
        "cash_gap_days": company_cash_gap_days,
        "working_capital_exposure_amount": working_capital_exposure_amount,
        "gross_margin_amount": gross_margin_amount,
        "gross_margin_ratio": gross_margin_ratio,
        "first_outflow_date": first_outflow_date,
        "first_inflow_date": first_inflow_date,
        "last_cash_event_date": last_cash_event_date,
        "trace_lines": list(dict.fromkeys(candidate_trace_lines)),
    }

    return {
        "events": candidate_events,
        "candidate_summary": candidate_summary,
    }


def _build_period_summaries(
    *,
    projection_events: List[Dict[str, Any]],
    warnings: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    cash_events = [event for event in projection_events if event.get("is_cash_effective")]
    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    currencies_by_period: Dict[str, set[str]] = {}

    for event in cash_events:
        period_key = event.get("period_key")
        currency = event.get("currency")
        if period_key is None or currency is None:
            continue
        key = (period_key, currency)
        if key not in grouped:
            grouped[key] = {
                "period_key": period_key,
                "currency": currency,
                "total_inflow": Decimal("0"),
                "total_outflow": Decimal("0"),
                "candidate_ids": set(),
                "event_count": 0,
                "trace_lines": [],
            }
        row = grouped[key]
        amount = _to_decimal(event.get("amount")) or Decimal("0")
        if event.get("direction") == "INFLOW":
            row["total_inflow"] += amount
        elif event.get("direction") == "OUTFLOW":
            row["total_outflow"] += amount
        row["candidate_ids"].add(event.get("candidate_id"))
        row["event_count"] += 1
        currencies_by_period.setdefault(period_key, set()).add(currency)

    for period_key, currencies in currencies_by_period.items():
        if len(currencies) > 1:
            warnings.append(
                _issue(
                    code="MULTI_CURRENCY_PROJECTION_GROUPED_WITHOUT_CONVERSION",
                    severity="WARNING",
                    message=(
                        "Multiple currencies exist in the same period; grouped separately without FX conversion."
                    ),
                    trace_lines=[f"period_key={period_key}", f"currencies={sorted(currencies)}"],
                )
            )

    output = []
    for _, row in sorted(grouped.items()):
        output.append(
            {
                "period_key": row["period_key"],
                "currency": row["currency"],
                "total_inflow": row["total_inflow"],
                "total_outflow": row["total_outflow"],
                "net_cash_impact": row["total_inflow"] - row["total_outflow"],
                "candidate_ids": sorted([cid for cid in row["candidate_ids"] if cid]),
                "event_count": row["event_count"],
                "trace_lines": row["trace_lines"],
            }
        )
    return output


def _coverage_issues_to_projection_issues(
    issues: List[Dict[str, Any]],
    *,
    default_severity: str = "WARNING",
) -> List[Dict[str, Any]]:
    output = []
    for issue in issues or []:
        output.append(
            {
                "code": issue.get("code") or "COVERAGE_VALIDATION_DIAGNOSTIC",
                "severity": issue.get("severity") or default_severity,
                "message": issue.get("message") or "Coverage validation diagnostic propagated.",
                "candidate_id": issue.get("candidate_id"),
                "project_id": issue.get("project_id"),
                "project_item_id": issue.get("project_item_id"),
                "package_id": issue.get("package_id"),
                "procurement_option_id": issue.get("procurement_option_id"),
                "event_type": None,
                "field": issue.get("field"),
                "trace_lines": issue.get("trace_lines") or [],
            }
        )
    return output


def _build_projection_result(
    *,
    scope_type: str,
    scope_id: int,
    include_not_ready: bool,
    include_invalid_coverage: bool,
    candidate_collection: Dict[str, Any],
    coverage_validation: Dict[str, Any],
) -> Dict[str, Any]:
    blocking_issues: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    trace_lines: List[str] = []
    projection_events: List[Dict[str, Any]] = []
    candidate_summaries: List[Dict[str, Any]] = []

    total_candidates = int(candidate_collection.get("total_candidates", 0))
    candidates = list(candidate_collection.get("candidates") or [])
    coverage_blocking = _coverage_issues_to_projection_issues(
        coverage_validation.get("blocking_issues") or [],
        default_severity="BLOCKING",
    )
    coverage_warning = _coverage_issues_to_projection_issues(
        coverage_validation.get("warnings") or [],
        default_severity="WARNING",
    )
    warnings.extend(coverage_warning)

    coverage_is_valid = bool(coverage_validation.get("is_valid_for_solver_input"))
    if not coverage_is_valid:
        if include_invalid_coverage:
            warnings.append(
                _issue(
                    code="COVERAGE_VALIDATION_FAILED",
                    severity="WARNING",
                    message=(
                        "Coverage validation reported blocking issues; projection continues in diagnostic mode."
                    ),
                    trace_lines=[f"scope_type={scope_type}", f"scope_id={scope_id}"],
                )
            )
            warnings.extend(coverage_blocking)
        else:
            blocking_issues.append(
                _issue(
                    code="COVERAGE_VALIDATION_FAILED",
                    severity="BLOCKING",
                    message=(
                        "Coverage validation reported blocking issues; projection rows excluded by default."
                    ),
                    trace_lines=[f"scope_type={scope_type}", f"scope_id={scope_id}"],
                )
            )
            blocking_issues.extend(coverage_blocking)

    projected_candidate_ids: List[str] = []
    excluded_candidate_ids: List[str] = []
    not_ready_included = 0

    for idx, candidate in enumerate(candidates):
        candidate_id = _candidate_id(candidate, idx)
        if not bool(candidate.get("is_ready_for_candidate_builder")):
            excluded_candidate_ids.append(candidate_id)
            if include_not_ready:
                not_ready_included += 1
                warnings.append(
                    _issue(
                        code="NOT_READY_CANDIDATE_EXCLUDED_FROM_PROJECTION",
                        severity="WARNING",
                        message=(
                            "Not-ready candidate included diagnostically but excluded from projection event computation."
                        ),
                        candidate=candidate,
                    )
                )
            continue

        if (not coverage_is_valid) and (not include_invalid_coverage):
            excluded_candidate_ids.append(candidate_id)
            continue

        projected_candidate_ids.append(candidate_id)
        projection = _build_projection_for_candidate(
            candidate=candidate,
            candidate_id=candidate_id,
            blocking_issues=blocking_issues,
            warnings=warnings,
        )
        projection_events.extend(projection["events"])
        candidate_summaries.append(projection["candidate_summary"])

    if not include_not_ready and (candidate_collection.get("not_ready_candidates", 0) > 0):
        warnings.append(
            _issue(
                code="NOT_READY_CANDIDATES_EXCLUDED_BY_DEFAULT",
                severity="WARNING",
                message="Not-ready candidates were excluded from financial projection by default.",
            )
        )

    is_projection_complete = True
    if blocking_issues:
        is_projection_complete = False
    if (not coverage_is_valid) and include_invalid_coverage:
        is_projection_complete = False
    if include_not_ready and not_ready_included > 0:
        is_projection_complete = False
    if include_invalid_coverage and coverage_blocking:
        is_projection_complete = False

    period_summaries = _build_period_summaries(
        projection_events=projection_events,
        warnings=warnings,
    )

    trace_lines.extend(candidate_collection.get("trace_lines") or [])
    trace_lines.extend(coverage_validation.get("trace_lines") or [])
    trace_lines.append(f"scope_type={scope_type}")
    trace_lines.append(f"scope_id={scope_id}")
    trace_lines.append(
        "Supplier payment outflow row is cash-effective; component rows are analytical/non-cash-effective."
    )
    trace_lines.append(
        "Company cash gap uses forecast_customer_receipt_date - planned_supplier_payment_date."
    )

    return {
        "scope_type": scope_type,
        "scope_id": scope_id,
        "is_projection_complete": is_projection_complete,
        "total_candidates": total_candidates,
        "projected_candidates": len(projected_candidate_ids),
        "excluded_candidates": sorted(list(dict.fromkeys(excluded_candidate_ids))),
        "projection_events": projection_events,
        "period_summaries": period_summaries,
        "candidate_summaries": candidate_summaries,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "trace_lines": list(dict.fromkeys(trace_lines)),
    }


async def project_financials_for_project(
    db: AsyncSession,
    project_id: int,
    include_not_ready: bool = False,
    include_invalid_coverage: bool = False,
) -> Dict[str, Any]:
    candidates = await build_atomic_candidates_for_project(
        db=db,
        project_id=project_id,
        include_not_ready=include_not_ready,
    )
    coverage = await validate_candidate_coverage_for_project(
        db=db,
        project_id=project_id,
        include_not_ready=include_not_ready,
    )
    return _build_projection_result(
        scope_type="PROJECT",
        scope_id=project_id,
        include_not_ready=include_not_ready,
        include_invalid_coverage=include_invalid_coverage,
        candidate_collection=candidates,
        coverage_validation=coverage,
    )


async def project_financials_for_package(
    db: AsyncSession,
    package_id: int,
    include_not_ready: bool = False,
    include_invalid_coverage: bool = False,
) -> Dict[str, Any]:
    candidates = await build_atomic_candidates_for_procurement_package(
        db=db,
        package_id=package_id,
        include_not_ready=include_not_ready,
    )
    coverage = await validate_candidate_coverage_for_package(
        db=db,
        package_id=package_id,
        include_not_ready=include_not_ready,
    )
    return _build_projection_result(
        scope_type="PACKAGE",
        scope_id=package_id,
        include_not_ready=include_not_ready,
        include_invalid_coverage=include_invalid_coverage,
        candidate_collection=candidates,
        coverage_validation=coverage,
    )


async def project_financials_for_option(
    db: AsyncSession,
    option_id: int,
    include_not_ready: bool = False,
    include_invalid_coverage: bool = False,
) -> Dict[str, Any]:
    candidates = await build_atomic_candidates_for_option(
        db=db,
        option_id=option_id,
        include_not_ready=include_not_ready,
    )
    coverage = await validate_candidate_coverage_for_option(
        db=db,
        option_id=option_id,
        include_not_ready=include_not_ready,
    )
    return _build_projection_result(
        scope_type="OPTION",
        scope_id=option_id,
        include_not_ready=include_not_ready,
        include_invalid_coverage=include_invalid_coverage,
        candidate_collection=candidates,
        coverage_validation=coverage,
    )
