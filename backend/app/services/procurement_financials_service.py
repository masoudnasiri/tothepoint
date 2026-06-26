from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.currency_conversion_service import CurrencyConversionService
from app.models import (
    Currency,
    DeliveryOption,
    PaymentMethod,
    ProcurementCostComponent,
    ProcurementOption,
    ProcurementPackage,
    ProjectItem,
)

BASE_CURRENCY = "IRR"
SUPPORTED_COMPONENT_PAYMENT_TYPES = {"CASH", "INSTALLMENTS"}

DEFAULT_COMPONENT_PAYEE_BY_TYPE = {
    "BASE_PRICE": "SUPPLIER",
    "SHIPPING": "LOGISTICS_PROVIDER",
    "VAT": "SUPPLIER",
    "CUSTOMS": "CUSTOMS_OR_CLEARANCE",
    "CLEARANCE": "CUSTOMS_OR_CLEARANCE",
    "INSURANCE": "INSURANCE_PROVIDER",
    "BANK_FEE": "BANK_OR_EXCHANGE",
    "OTHER": "OTHER",
}


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    deduped: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _normalize_currency_code(raw_currency: Optional[str]) -> str:
    return (raw_currency or BASE_CURRENCY).strip().upper() or BASE_CURRENCY


def _parse_optional_date(raw_value: Any) -> Optional[date]:
    if raw_value is None or raw_value == "":
        return None
    if isinstance(raw_value, date):
        return raw_value
    try:
        return date.fromisoformat(str(raw_value).split("T")[0])
    except Exception:
        return None


def _as_decimal(raw_value: Any) -> Optional[Decimal]:
    if raw_value is None or raw_value == "":
        return None
    try:
        return Decimal(str(raw_value))
    except Exception:
        return None


def _default_component_payee_type(component_type: str) -> str:
    return DEFAULT_COMPONENT_PAYEE_BY_TYPE.get(component_type, "OTHER")


def _normalize_component_payment_metadata(
    component: ProcurementCostComponent,
) -> Dict[str, Any]:
    raw_metadata = (
        component.payment_metadata
        if isinstance(component.payment_metadata, dict)
        else {}
    )

    inherit_option_payment_schedule = bool(
        raw_metadata.get("inherit_option_payment_schedule", True)
    )
    payment_type = str(raw_metadata.get("payment_type") or "CASH").strip().upper()
    if payment_type not in SUPPORTED_COMPONENT_PAYMENT_TYPES:
        payment_type = "CASH"

    schedule_rows: List[Dict[str, Any]] = []
    for raw_row in raw_metadata.get("payment_schedule", []) or []:
        if not isinstance(raw_row, dict):
            continue
        schedule_rows.append(
            {
                "due_offset_days": (
                    int(raw_row["due_offset_days"])
                    if raw_row.get("due_offset_days") is not None
                    else None
                ),
                "due_date": _parse_optional_date(raw_row.get("due_date")),
                "percent": _as_decimal(raw_row.get("percent")),
                "amount_value": _as_decimal(raw_row.get("amount_value")),
                "derived_effective_receipt_date": _parse_optional_date(
                    raw_row.get("derived_effective_receipt_date")
                ),
            }
        )

    return {
        "inherit_option_payment_schedule": inherit_option_payment_schedule,
        "payee_type": str(raw_metadata.get("payee_type") or _default_component_payee_type(component.component_type)).strip().upper(),
        "payee_label": (
            str(raw_metadata.get("payee_label")).strip()
            if raw_metadata.get("payee_label") is not None
            else None
        ),
        "payment_method_id": (
            int(raw_metadata["payment_method_id"])
            if raw_metadata.get("payment_method_id") is not None
            else None
        ),
        "payment_type": payment_type,
        "planned_payment_date": _parse_optional_date(
            raw_metadata.get("planned_payment_date")
        ),
        "payment_schedule": schedule_rows,
        "notes": (
            str(raw_metadata.get("notes")).strip()
            if raw_metadata.get("notes") is not None
            else None
        ),
    }


def _resolve_component_payment_diagnostic(
    *,
    component: ProcurementCostComponent,
    option: ProcurementOption,
    default_payment_method: Optional[PaymentMethod],
    payment_methods_by_id: Dict[int, PaymentMethod],
) -> Dict[str, Any]:
    metadata = _normalize_component_payment_metadata(component)
    warnings: List[str] = []
    trace_lines: List[str] = []
    derived_effective_receipt_dates: List[date] = []

    inherit = bool(metadata["inherit_option_payment_schedule"])
    resolved_payment_type = metadata["payment_type"]
    resolved_payment_method_id: Optional[int] = None
    resolved_planned_payment_date: Optional[date] = None
    resolved_settlement_delay_days: Optional[int] = None

    if inherit:
        resolved_payment_method_id = option.payment_method_id
        resolved_planned_payment_date = option.planned_supplier_payment_date
        resolved_payment_type = str((option.payment_terms or {}).get("type") or "cash").strip().upper()
        resolved_settlement_delay_days = (
            default_payment_method.settlement_delay_days
            if default_payment_method is not None
            else None
        )
        if option.supplier_effective_receipt_date is not None:
            derived_effective_receipt_dates.append(option.supplier_effective_receipt_date)
        if resolved_payment_method_id is None:
            warnings.append("INHERITED_PAYMENT_METHOD_MISSING")
        if resolved_planned_payment_date is None:
            warnings.append("INHERITED_PLANNED_PAYMENT_DATE_MISSING")
        trace_lines.append(
            "Component payment inherits default option-level payment schedule."
        )
    else:
        resolved_payment_method_id = metadata["payment_method_id"]
        resolved_planned_payment_date = metadata["planned_payment_date"]
        if resolved_payment_method_id is None:
            warnings.append("CUSTOM_PAYMENT_METHOD_MISSING")
        custom_payment_method = payment_methods_by_id.get(resolved_payment_method_id or -1)
        if custom_payment_method is None and resolved_payment_method_id is not None:
            warnings.append("CUSTOM_PAYMENT_METHOD_NOT_FOUND")
        resolved_settlement_delay_days = (
            custom_payment_method.settlement_delay_days
            if custom_payment_method is not None
            else None
        )
        if resolved_payment_type == "CASH" and resolved_planned_payment_date is None:
            warnings.append("CUSTOM_CASH_PLANNED_PAYMENT_DATE_MISSING")
        trace_lines.append(
            "Component payment uses custom schedule metadata (override default option-level payment schedule)."
        )

    resolved_schedule_rows: List[Dict[str, Any]] = []
    schedule_rows = metadata.get("payment_schedule") or []
    if resolved_payment_type == "INSTALLMENTS":
        if len(schedule_rows) == 0:
            warnings.append("INSTALLMENT_SCHEDULE_MISSING")
        total_percent = Decimal("0")
        has_percent = False
        for index, row in enumerate(schedule_rows):
            due_date = row.get("due_date")
            due_offset_days = row.get("due_offset_days")
            if due_date is None and due_offset_days is not None and resolved_planned_payment_date is not None:
                due_date = resolved_planned_payment_date + timedelta(days=int(due_offset_days))
            if due_date is None:
                warnings.append(f"INSTALLMENT_ROW_{index}_DATE_MISSING")

            percent = row.get("percent")
            amount_value = row.get("amount_value")
            if percent is not None:
                has_percent = True
                total_percent += Decimal(str(percent))

            derived_effective_receipt_date = row.get("derived_effective_receipt_date")
            if (
                derived_effective_receipt_date is None
                and due_date is not None
                and resolved_settlement_delay_days is not None
            ):
                derived_effective_receipt_date = due_date + timedelta(
                    days=int(resolved_settlement_delay_days)
                )
            if derived_effective_receipt_date is not None:
                derived_effective_receipt_dates.append(derived_effective_receipt_date)

            resolved_schedule_rows.append(
                {
                    "due_offset_days": due_offset_days,
                    "due_date": due_date,
                    "percent": percent,
                    "amount_value": amount_value,
                    "derived_effective_receipt_date": derived_effective_receipt_date,
                }
            )

        if has_percent and abs(total_percent - Decimal("100")) > Decimal("0.01"):
            warnings.append("INSTALLMENT_PERCENT_TOTAL_MUST_EQUAL_100")
    else:
        if (
            resolved_planned_payment_date is not None
            and resolved_settlement_delay_days is not None
        ):
            derived_effective_receipt_dates.append(
                resolved_planned_payment_date
                + timedelta(days=int(resolved_settlement_delay_days))
            )
        elif resolved_planned_payment_date is not None and inherit:
            # Preserve existing persisted value when available for inherited default schedule.
            if option.supplier_effective_receipt_date is not None:
                derived_effective_receipt_dates.append(
                    option.supplier_effective_receipt_date
                )

    return {
        "component_id": int(component.id),
        "component_type": component.component_type,
        "inherit_option_payment_schedule": inherit,
        "payee_type": metadata["payee_type"],
        "payee_label": metadata["payee_label"],
        "payment_type": resolved_payment_type,
        "payment_method_id": resolved_payment_method_id,
        "planned_payment_date": resolved_planned_payment_date,
        "settlement_delay_days": resolved_settlement_delay_days,
        "effective_receipt_dates": sorted(list(dict.fromkeys(derived_effective_receipt_dates))),
        "payment_schedule": resolved_schedule_rows,
        "warnings": warnings,
        "trace_lines": trace_lines,
    }


def _extract_component_integrity_issues(
    components: List[ProcurementCostComponent],
) -> List[str]:
    issues: List[str] = []
    for component in components:
        amount_value = Decimal(str(component.amount_value or 0))
        currency = str(component.amount_currency or "").strip()
        if amount_value <= 0:
            issues.append(
                f"component:{component.id}:amount_value_must_be_positive"
            )
        if not currency:
            issues.append(f"component:{component.id}:amount_currency_required")
        if component.component_type == "OTHER" and not str(component.description or "").strip():
            issues.append(f"component:{component.id}:other_description_required")
    return issues


def _resolve_selected_delivery_date(
    *,
    requested_source: Optional[str],
    project_requested_delivery_date: Optional[date],
    supplier_actual_delivery_date: Optional[date],
    manual_selected_delivery_date: Optional[date],
    missing_inputs: List[str],
    trace_lines: List[str],
) -> Tuple[Optional[date], Optional[str]]:
    normalized_source = (requested_source or "").strip().upper() or None

    if normalized_source == "SUPPLIER_ACTUAL":
        if supplier_actual_delivery_date is not None:
            trace_lines.append(
                "Selected delivery date source SUPPLIER_ACTUAL; using supplier_actual_delivery_date."
            )
            return supplier_actual_delivery_date, "SUPPLIER_ACTUAL"
        missing_inputs.append("supplier_actual_delivery_date")
        trace_lines.append(
            "Delivery source SUPPLIER_ACTUAL requested but supplier_actual_delivery_date is missing."
        )

    if normalized_source == "PROJECT_OPTION":
        if project_requested_delivery_date is not None:
            trace_lines.append(
                "Selected delivery date source PROJECT_OPTION; using project_requested_delivery_date."
            )
            return project_requested_delivery_date, "PROJECT_OPTION"
        missing_inputs.append("project_requested_delivery_date")
        trace_lines.append(
            "Delivery source PROJECT_OPTION requested but project_requested_delivery_date is missing."
        )

    if normalized_source == "MANUAL":
        if manual_selected_delivery_date is not None:
            trace_lines.append(
                "Selected delivery date source MANUAL; using provided selected_delivery_date."
            )
            return manual_selected_delivery_date, "MANUAL"
        missing_inputs.append("selected_delivery_date")
        trace_lines.append(
            "Delivery source MANUAL requested but selected_delivery_date is missing."
        )

    # Deterministic fallback order when requested source is unavailable or omitted.
    if supplier_actual_delivery_date is not None:
        trace_lines.append(
            "Falling back selected delivery date to supplier_actual_delivery_date."
        )
        return supplier_actual_delivery_date, "SUPPLIER_ACTUAL"
    if project_requested_delivery_date is not None:
        trace_lines.append(
            "Falling back selected delivery date to project_requested_delivery_date."
        )
        return project_requested_delivery_date, "PROJECT_OPTION"
    if manual_selected_delivery_date is not None:
        trace_lines.append(
            "Falling back selected delivery date to manual selected_delivery_date."
        )
        return manual_selected_delivery_date, "MANUAL"

    missing_inputs.append("selected_delivery_date")
    trace_lines.append(
        "Unable to resolve selected delivery date from PROJECT_OPTION, SUPPLIER_ACTUAL, or MANUAL inputs."
    )
    return None, normalized_source


def _parse_project_item_delivery_options(delivery_options: Any) -> Optional[date]:
    if not isinstance(delivery_options, list):
        return None
    parsed_dates: List[date] = []
    for raw_value in delivery_options:
        if not isinstance(raw_value, str):
            continue
        raw_value = raw_value.strip()
        if not raw_value:
            continue
        # Accept YYYY-MM-DD and full ISO strings.
        try:
            parsed_dates.append(date.fromisoformat(raw_value.split("T")[0]))
        except ValueError:
            continue
    if not parsed_dates:
        return None
    return min(parsed_dates)


def calculate_delivery_variance_days(
    project_requested_delivery_date: Optional[date],
    supplier_actual_delivery_date: Optional[date],
) -> Optional[int]:
    """
    Returns supplier_actual_delivery_date - project_requested_delivery_date in days.
    """
    if project_requested_delivery_date is None or supplier_actual_delivery_date is None:
        return None
    return (supplier_actual_delivery_date - project_requested_delivery_date).days


def default_customer_invoice_and_receipt_dates(
    *,
    project_requested_delivery_date: Optional[date],
    supplier_actual_delivery_date: Optional[date],
    selected_delivery_date: Optional[date],
    delivery_option: Optional[DeliveryOption],
    project_item_invoice_submission_date: Optional[date],
    project_item_expected_cash_in_date: Optional[date],
    manual_invoice_date: Optional[date],
    manual_receipt_date: Optional[date],
    existing_receipt_delay_days: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Deterministic date defaulting for procurement-option financial preview.
    Does not mutate persisted state.
    """
    trace_lines: List[str] = []
    missing_inputs: List[str] = []

    delivery_date_variance_days = calculate_delivery_variance_days(
        project_requested_delivery_date=project_requested_delivery_date,
        supplier_actual_delivery_date=supplier_actual_delivery_date,
    )
    if delivery_date_variance_days is not None:
        trace_lines.append(
            "Computed delivery_date_variance_days as "
            f"{delivery_date_variance_days} (supplier_actual - project_requested)."
        )
    else:
        trace_lines.append(
            "Delivery variance not computed because project requested and/or supplier actual delivery date is missing."
        )

    forecast_customer_invoice_date: Optional[date] = None
    forecast_customer_invoice_date_source: Optional[str] = None

    if manual_invoice_date is not None:
        forecast_customer_invoice_date = manual_invoice_date
        forecast_customer_invoice_date_source = "MANUAL_OVERRIDE"
        trace_lines.append(
            "Using manual invoice override for forecast_customer_invoice_date."
        )
    else:
        timing_type = (
            str(delivery_option.invoice_timing_type).upper()
            if delivery_option and delivery_option.invoice_timing_type
            else None
        )
        if timing_type == "RELATIVE":
            days_after_delivery = delivery_option.invoice_days_after_delivery
            base_delivery_date = supplier_actual_delivery_date or selected_delivery_date
            if days_after_delivery is None:
                missing_inputs.append("invoice_days_after_delivery")
                trace_lines.append(
                    "Unable to default invoice date: RELATIVE timing configured but invoice_days_after_delivery is missing."
                )
            elif base_delivery_date is None:
                missing_inputs.append("selected_delivery_date")
                trace_lines.append(
                    "Unable to default invoice date: RELATIVE timing requires supplier/selected delivery date."
                )
            else:
                forecast_customer_invoice_date = base_delivery_date + timedelta(
                    days=int(days_after_delivery)
                )
                forecast_customer_invoice_date_source = "SYSTEM_DEFAULT"
                trace_lines.append(
                    f"Defaulted invoice date via RELATIVE timing: base {base_delivery_date.isoformat()} + "
                    f"{int(days_after_delivery)} days."
                )
        elif timing_type == "ABSOLUTE":
            absolute_invoice_date = (
                delivery_option.invoice_issue_date if delivery_option else None
            )
            if absolute_invoice_date is None and project_item_invoice_submission_date is not None:
                absolute_invoice_date = project_item_invoice_submission_date
                trace_lines.append(
                    "Using project_items.invoice_submission_date as ABSOLUTE invoice fallback."
                )

            if absolute_invoice_date is None:
                missing_inputs.append("invoice_issue_date")
                trace_lines.append(
                    "Unable to default invoice date: ABSOLUTE timing configured but invoice_issue_date is missing."
                )
            else:
                if (
                    supplier_actual_delivery_date is not None
                    and project_requested_delivery_date is not None
                    and supplier_actual_delivery_date != project_requested_delivery_date
                ):
                    offset_days = (
                        absolute_invoice_date - project_requested_delivery_date
                    ).days
                    forecast_customer_invoice_date = supplier_actual_delivery_date + timedelta(
                        days=offset_days
                    )
                    trace_lines.append(
                        "Defaulted invoice date via ABSOLUTE timing with preserved offset: "
                        f"offset {offset_days} days from project requested date applied to supplier actual date."
                    )
                else:
                    forecast_customer_invoice_date = absolute_invoice_date
                    trace_lines.append(
                        "Defaulted invoice date via ABSOLUTE timing using configured absolute invoice_issue_date."
                    )
                forecast_customer_invoice_date_source = "SYSTEM_DEFAULT"
        elif project_item_invoice_submission_date is not None:
            # Legacy fallback (read-only source): still deterministic and explicit in trace.
            if (
                supplier_actual_delivery_date is not None
                and project_requested_delivery_date is not None
                and supplier_actual_delivery_date != project_requested_delivery_date
            ):
                offset_days = (
                    project_item_invoice_submission_date - project_requested_delivery_date
                ).days
                forecast_customer_invoice_date = supplier_actual_delivery_date + timedelta(
                    days=offset_days
                )
                trace_lines.append(
                    "Defaulted invoice date from legacy project_items.invoice_submission_date with preserved offset."
                )
            else:
                forecast_customer_invoice_date = project_item_invoice_submission_date
                trace_lines.append(
                    "Defaulted invoice date from legacy project_items.invoice_submission_date without offset shift."
                )
            forecast_customer_invoice_date_source = "SYSTEM_DEFAULT"
        else:
            missing_inputs.append("invoice_timing")
            trace_lines.append(
                "Unable to calculate invoice date: no reliable invoice timing configuration is available."
            )

    forecast_customer_receipt_date: Optional[date] = None
    forecast_customer_receipt_date_source: Optional[str] = None
    forecast_customer_receipt_delay_days: Optional[int] = None

    if manual_receipt_date is not None:
        forecast_customer_receipt_date = manual_receipt_date
        forecast_customer_receipt_date_source = "MANUAL_OVERRIDE"
        trace_lines.append(
            "Using manual receipt override for forecast_customer_receipt_date."
        )
    else:
        if forecast_customer_invoice_date is None:
            missing_inputs.append("forecast_customer_invoice_date")
            trace_lines.append(
                "Unable to default receipt date because invoice date is unavailable."
            )
        else:
            inferred_gap_days: Optional[int] = None
            if (
                project_item_invoice_submission_date is not None
                and project_item_expected_cash_in_date is not None
            ):
                inferred_gap_days = (
                    project_item_expected_cash_in_date
                    - project_item_invoice_submission_date
                ).days
                trace_lines.append(
                    "Derived receipt delay from project item invoice_submission_date -> expected_cash_in_date gap."
                )
            elif existing_receipt_delay_days is not None:
                inferred_gap_days = int(existing_receipt_delay_days)
                trace_lines.append(
                    "Derived receipt delay from existing forecast_customer_receipt_delay_days on procurement option."
                )

            if inferred_gap_days is None:
                missing_inputs.append("customer_receipt_timing")
                trace_lines.append(
                    "Unable to calculate receipt date: no reliable invoice-to-receipt timing source."
                )
            else:
                forecast_customer_receipt_delay_days = inferred_gap_days
                forecast_customer_receipt_date = forecast_customer_invoice_date + timedelta(
                    days=inferred_gap_days
                )
                forecast_customer_receipt_date_source = "SYSTEM_DEFAULT"
                trace_lines.append(
                    f"Defaulted receipt date as invoice date + {inferred_gap_days} days."
                )

    if (
        forecast_customer_receipt_delay_days is None
        and forecast_customer_invoice_date is not None
        and forecast_customer_receipt_date is not None
    ):
        forecast_customer_receipt_delay_days = (
            forecast_customer_receipt_date - forecast_customer_invoice_date
        ).days

    return {
        "forecast_customer_invoice_date": forecast_customer_invoice_date,
        "forecast_customer_invoice_date_source": forecast_customer_invoice_date_source,
        "forecast_customer_receipt_date": forecast_customer_receipt_date,
        "forecast_customer_receipt_date_source": forecast_customer_receipt_date_source,
        "forecast_customer_receipt_delay_days": forecast_customer_receipt_delay_days,
        "delivery_date_variance_days": delivery_date_variance_days,
        "missing_inputs": _dedupe_preserve_order(missing_inputs),
        "trace_lines": trace_lines,
    }


async def calculate_procurement_option_delivery_financial_preview(
    option_id: int,
    db: AsyncSession,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a delivery/invoice/receipt preview for one procurement option without persistence.
    """
    payload = overrides or {}
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise ValueError(f"procurement option {option_id} not found")

    project_item_id = option.project_item_id
    if project_item_id is None and option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == option.package_id
            )
        )
        project_item_id = package_result.scalar_one_or_none()

    project_item: Optional[ProjectItem] = None
    if project_item_id is not None:
        project_item_result = await db.execute(
            select(ProjectItem).where(ProjectItem.id == project_item_id)
        )
        project_item = project_item_result.scalar_one_or_none()

    delivery_option: Optional[DeliveryOption] = None
    if option.delivery_option_id is not None:
        delivery_option_result = await db.execute(
            select(DeliveryOption).where(DeliveryOption.id == option.delivery_option_id)
        )
        delivery_option = delivery_option_result.scalar_one_or_none()

    trace_lines: List[str] = []
    missing_inputs: List[str] = []

    project_requested_delivery_date: Optional[date] = (
        option.project_requested_delivery_date
        or (delivery_option.delivery_date if delivery_option else None)
        or _parse_project_item_delivery_options(
            project_item.delivery_options if project_item else None
        )
    )

    if project_requested_delivery_date is None:
        missing_inputs.append("project_requested_delivery_date")
        trace_lines.append(
            "Project requested delivery date not found in procurement option, delivery option, or project_items.delivery_options."
        )
    elif option.project_requested_delivery_date is not None:
        trace_lines.append(
            "Project requested delivery date sourced from procurement option snapshot."
        )
    elif delivery_option is not None:
        trace_lines.append(
            "Project requested delivery date sourced from linked delivery option."
        )
    else:
        trace_lines.append(
            "Project requested delivery date sourced from legacy project_items.delivery_options fallback."
        )

    supplier_actual_delivery_date = payload.get(
        "supplier_actual_delivery_date", option.supplier_actual_delivery_date
    )
    manual_selected_delivery_date = payload.get(
        "selected_delivery_date", option.selected_delivery_date
    )
    requested_delivery_source = payload.get(
        "delivery_date_source", option.delivery_date_source
    )

    selected_delivery_date, resolved_delivery_source = _resolve_selected_delivery_date(
        requested_source=requested_delivery_source,
        project_requested_delivery_date=project_requested_delivery_date,
        supplier_actual_delivery_date=supplier_actual_delivery_date,
        manual_selected_delivery_date=manual_selected_delivery_date,
        missing_inputs=missing_inputs,
        trace_lines=trace_lines,
    )

    manual_invoice_date = payload.get("manual_invoice_date")
    if (
        manual_invoice_date is None
        and option.forecast_customer_invoice_date_source == "MANUAL_OVERRIDE"
    ):
        manual_invoice_date = option.forecast_customer_invoice_date

    manual_receipt_date = payload.get("manual_receipt_date")
    if (
        manual_receipt_date is None
        and option.forecast_customer_receipt_date_source == "MANUAL_OVERRIDE"
    ):
        manual_receipt_date = option.forecast_customer_receipt_date

    defaults = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=project_requested_delivery_date,
        supplier_actual_delivery_date=supplier_actual_delivery_date,
        selected_delivery_date=selected_delivery_date,
        delivery_option=delivery_option,
        project_item_invoice_submission_date=(
            project_item.invoice_submission_date if project_item else None
        ),
        project_item_expected_cash_in_date=(
            project_item.expected_cash_in_date if project_item else None
        ),
        manual_invoice_date=manual_invoice_date,
        manual_receipt_date=manual_receipt_date,
        existing_receipt_delay_days=option.forecast_customer_receipt_delay_days,
    )

    trace_lines.extend(defaults["trace_lines"])
    missing_inputs.extend(defaults["missing_inputs"])

    return {
        "project_requested_delivery_date": project_requested_delivery_date,
        "supplier_actual_delivery_date": supplier_actual_delivery_date,
        "selected_delivery_date": selected_delivery_date,
        "delivery_date_source": resolved_delivery_source,
        "delivery_date_variance_days": defaults["delivery_date_variance_days"],
        "forecast_customer_invoice_date": defaults["forecast_customer_invoice_date"],
        "forecast_customer_invoice_date_source": defaults[
            "forecast_customer_invoice_date_source"
        ],
        "forecast_customer_receipt_date": defaults["forecast_customer_receipt_date"],
        "forecast_customer_receipt_date_source": defaults[
            "forecast_customer_receipt_date_source"
        ],
        "forecast_customer_receipt_delay_days": defaults[
            "forecast_customer_receipt_delay_days"
        ],
        "missing_inputs": _dedupe_preserve_order(missing_inputs),
        "trace_lines": trace_lines,
    }


def calculate_supplier_effective_receipt_date(
    payment_date: Optional[date], payment_method: Optional[PaymentMethod]
) -> date:
    """
    Deterministic supplier effective receipt date based on settlement delay.
    """
    if payment_date is None:
        raise ValueError("payment_date is required")
    if payment_method is None:
        raise ValueError("payment_method is required")

    delay_days = payment_method.settlement_delay_days
    if delay_days is None or delay_days < 0:
        raise ValueError("payment_method.settlement_delay_days must be >= 0")

    return payment_date + timedelta(days=int(delay_days))


async def calculate_procurement_option_landed_cost(
    option_id: int, db: AsyncSession
) -> Dict[str, Any]:
    """
    Preview landed cost for a procurement option without mutating persisted state.
    """
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise ValueError(f"procurement option {option_id} not found")

    component_result = await db.execute(
        select(ProcurementCostComponent)
        .where(
            ProcurementCostComponent.procurement_option_id == option_id,
            ProcurementCostComponent.is_active == True,  # noqa: E712
        )
        .order_by(ProcurementCostComponent.id.asc())
    )
    active_components = list(component_result.scalars().all())

    trace_lines: List[str] = []
    component_lines: List[Dict[str, Any]] = []
    missing_exchange_rates: List[Dict[str, Any]] = []

    base_component = next(
        (c for c in active_components if c.component_type == "BASE_PRICE"), None
    )
    has_shipping_component = any(
        c.component_type == "SHIPPING" for c in active_components
    )

    if base_component:
        trace_lines.append(
            f"BASE_PRICE component found (id={base_component.id}); legacy procurement_options.cost_amount fallback not used."
        )
    else:
        trace_lines.append(
            "No BASE_PRICE component found; using procurement_options.cost_amount as base fallback."
        )
        component_lines.append(
            {
                "component_id": None,
                "component_type": "BASE_PRICE",
                "description": "Fallback from procurement_options.cost_amount",
                "amount_value": Decimal(str(option.cost_amount or 0)),
                "amount_currency": (option.cost_currency or BASE_CURRENCY).upper(),
                "amount_irr": None,
                "source": "fallback:procurement_options.cost_amount",
                "exchange_rate_date": option.purchase_date,
            }
        )

    for component in active_components:
        component_lines.append(
            {
                "component_id": int(component.id),
                "component_type": component.component_type,
                "description": component.description,
                "amount_value": Decimal(str(component.amount_value)),
                "amount_currency": (component.amount_currency or BASE_CURRENCY).upper(),
                "amount_irr": (
                    Decimal(str(component.amount_irr))
                    if component.amount_irr is not None
                    else None
                ),
                "source": "component",
                "exchange_rate_date": component.exchange_rate_date,
            }
        )

    if has_shipping_component:
        trace_lines.append(
            "SHIPPING component exists; legacy procurement_options.shipping_cost fallback not used."
        )
    elif option.shipping_cost and Decimal(str(option.shipping_cost)) > 0:
        trace_lines.append(
            "No SHIPPING component found; using procurement_options.shipping_cost fallback."
        )
        component_lines.append(
            {
                "component_id": None,
                "component_type": "SHIPPING",
                "description": "Fallback from procurement_options.shipping_cost",
                "amount_value": Decimal(str(option.shipping_cost)),
                "amount_currency": (option.cost_currency or BASE_CURRENCY).upper(),
                "amount_irr": None,
                "source": "fallback:procurement_options.shipping_cost",
                "exchange_rate_date": option.purchase_date,
            }
        )

    totals_by_currency: Dict[str, Decimal] = {}
    conversion_service = CurrencyConversionService(db)
    running_total_irr = Decimal("0")
    has_missing_irr = False

    for line in component_lines:
        amount_currency = str(line["amount_currency"]).upper()
        amount_value = Decimal(str(line["amount_value"]))
        exchange_rate_date = line.get("exchange_rate_date") or option.purchase_date or date.today()

        totals_by_currency[amount_currency] = totals_by_currency.get(
            amount_currency, Decimal("0")
        ) + amount_value

        amount_irr: Optional[Decimal] = line.get("amount_irr")
        if amount_irr is None:
            if amount_currency == BASE_CURRENCY:
                amount_irr = amount_value
            else:
                try:
                    rate_to_irr = await conversion_service.get_rate_to_base(
                        amount_currency, exchange_rate_date
                    )
                    amount_irr = amount_value * rate_to_irr
                except ValueError as exc:
                    has_missing_irr = True
                    missing_exchange_rates.append(
                        {
                            "component_type": line["component_type"],
                            "currency": amount_currency,
                            "rate_date": exchange_rate_date.isoformat(),
                            "reason": str(exc),
                        }
                    )

        line["amount_irr"] = amount_irr
        line.pop("exchange_rate_date", None)

        if amount_irr is not None:
            running_total_irr += amount_irr

        trace_lines.append(
            f"{line['component_type']} ({line['source']}): {amount_value} {amount_currency}"
            + (f" -> {amount_irr} {BASE_CURRENCY}" if amount_irr is not None else " -> IRR unavailable")
        )

    base_amount = {
        "amount_value": (
            Decimal(str(base_component.amount_value))
            if base_component
            else Decimal(str(option.cost_amount or 0))
        ),
        "amount_currency": (
            (base_component.amount_currency if base_component else option.cost_currency)
            or BASE_CURRENCY
        ).upper(),
        "source": (
            f"component:{base_component.id}"
            if base_component
            else "fallback:procurement_options.cost_amount"
        ),
    }

    return {
        "option_id": int(option.id),
        "base_amount": base_amount,
        "component_lines": component_lines,
        "totals_by_currency": totals_by_currency,
        "total_irr": None if has_missing_irr else running_total_irr,
        "missing_exchange_rates": missing_exchange_rates,
        "trace_lines": trace_lines,
    }


async def synchronize_procurement_option_legacy_pricing_fields(
    *,
    option_id: int,
    db: AsyncSession,
    require_base_price: bool = False,
) -> Dict[str, Any]:
    """
    Keep legacy compatibility pricing fields aligned with active cost components.
    """
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise ValueError(f"procurement option {option_id} not found")

    component_result = await db.execute(
        select(ProcurementCostComponent)
        .where(
            ProcurementCostComponent.procurement_option_id == option_id,
            ProcurementCostComponent.is_active == True,  # noqa: E712
        )
        .order_by(ProcurementCostComponent.id.asc())
    )
    active_components = list(component_result.scalars().all())
    if not active_components:
        return {
            "option_id": int(option.id),
            "has_base_price": False,
            "has_shipping": False,
            "active_component_count": 0,
            "cost_amount": option.cost_amount,
            "cost_currency": option.cost_currency,
            "shipping_cost": option.shipping_cost,
        }

    integrity_issues = _extract_component_integrity_issues(active_components)
    if integrity_issues:
        raise ValueError(
            "Invalid active cost components: " + ", ".join(integrity_issues)
        )

    base_components = [
        component
        for component in active_components
        if component.component_type == "BASE_PRICE"
    ]
    shipping_components = [
        component
        for component in active_components
        if component.component_type == "SHIPPING"
    ]

    if len(base_components) > 1:
        raise ValueError(
            "Invalid active cost components: multiple BASE_PRICE components are active."
        )
    if len(shipping_components) > 1:
        raise ValueError(
            "Invalid active cost components: multiple SHIPPING components are active."
        )
    if require_base_price and not base_components:
        raise ValueError("BASE_PRICE component is required.")

    if base_components:
        base_component = base_components[0]
        option.cost_amount = base_component.amount_value
        option.base_cost = base_component.amount_value
        option.cost_currency = _normalize_currency_code(base_component.amount_currency)

        currency_result = await db.execute(
            select(Currency.id).where(
                func.upper(Currency.code) == option.cost_currency.upper()
            )
        )
        mapped_currency_id = currency_result.scalar_one_or_none()
        if mapped_currency_id is not None:
            option.currency_id = mapped_currency_id

    option.shipping_cost = (
        shipping_components[0].amount_value if shipping_components else Decimal("0")
    )

    return {
        "option_id": int(option.id),
        "has_base_price": len(base_components) == 1,
        "has_shipping": len(shipping_components) == 1,
        "active_component_count": len(active_components),
        "cost_amount": option.cost_amount,
        "cost_currency": option.cost_currency,
        "shipping_cost": option.shipping_cost,
    }


async def apply_procurement_option_persistence_contract(
    *,
    option_id: int,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Canonical save mapping for delivery/payment/derived schedule persistence.
    """
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise ValueError(f"procurement option {option_id} not found")

    project_item_id = option.project_item_id
    if project_item_id is None and option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == option.package_id
            )
        )
        project_item_id = package_result.scalar_one_or_none()

    project_item: Optional[ProjectItem] = None
    if project_item_id is not None:
        project_item_result = await db.execute(
            select(ProjectItem).where(ProjectItem.id == project_item_id)
        )
        project_item = project_item_result.scalar_one_or_none()

    delivery_option: Optional[DeliveryOption] = None
    if option.delivery_option_id is not None:
        delivery_option_result = await db.execute(
            select(DeliveryOption).where(DeliveryOption.id == option.delivery_option_id)
        )
        delivery_option = delivery_option_result.scalar_one_or_none()

    trace_lines: List[str] = []
    missing_inputs: List[str] = []

    payment_method: Optional[PaymentMethod] = None
    if option.payment_method_id is not None:
        payment_method_result = await db.execute(
            select(PaymentMethod).where(PaymentMethod.id == option.payment_method_id)
        )
        payment_method = payment_method_result.scalar_one_or_none()
        if payment_method is None:
            raise ValueError(
                f"payment_method_id={option.payment_method_id} does not exist"
            )

    if option.payment_method_id is None:
        missing_inputs.append("payment_method_id")
        option.supplier_effective_receipt_date = None
        trace_lines.append(
            "Supplier effective receipt date unavailable because payment_method_id is missing."
        )
    elif option.planned_supplier_payment_date is None:
        missing_inputs.append("planned_supplier_payment_date")
        option.supplier_effective_receipt_date = None
        trace_lines.append(
            "Supplier effective receipt date unavailable because planned_supplier_payment_date is missing."
        )
    else:
        option.supplier_effective_receipt_date = calculate_supplier_effective_receipt_date(
            payment_date=option.planned_supplier_payment_date,
            payment_method=payment_method,
        )
        trace_lines.append(
            "Computed supplier_effective_receipt_date from planned supplier payment date and settlement delay."
        )

    project_requested_delivery_date = (
        option.project_requested_delivery_date
        or (delivery_option.delivery_date if delivery_option else None)
        or _parse_project_item_delivery_options(
            project_item.delivery_options if project_item else None
        )
    )
    option.project_requested_delivery_date = project_requested_delivery_date

    if project_requested_delivery_date is None:
        missing_inputs.append("project_requested_delivery_date")

    if option.supplier_actual_delivery_date is not None:
        option.selected_delivery_date = option.supplier_actual_delivery_date
        option.delivery_date_source = "SUPPLIER_ACTUAL"
        trace_lines.append(
            "Selected delivery date set from supplier_actual_delivery_date (contract priority)."
        )
    elif project_requested_delivery_date is not None:
        option.selected_delivery_date = project_requested_delivery_date
        option.delivery_date_source = "PROJECT_OPTION"
        trace_lines.append(
            "Selected delivery date set from project_requested_delivery_date fallback."
        )
    else:
        option.selected_delivery_date = None
        option.delivery_date_source = None
        missing_inputs.append("selected_delivery_date")
        trace_lines.append(
            "Selected delivery date unavailable because supplier and project requested delivery dates are both missing."
        )

    if (
        option.selected_delivery_date is not None
        and project_requested_delivery_date is not None
    ):
        option.delivery_date_variance_days = (
            option.selected_delivery_date - project_requested_delivery_date
        ).days
    else:
        option.delivery_date_variance_days = None

    defaults = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=project_requested_delivery_date,
        supplier_actual_delivery_date=option.supplier_actual_delivery_date,
        selected_delivery_date=option.selected_delivery_date,
        delivery_option=delivery_option,
        project_item_invoice_submission_date=(
            project_item.invoice_submission_date if project_item else None
        ),
        project_item_expected_cash_in_date=(
            project_item.expected_cash_in_date if project_item else None
        ),
        manual_invoice_date=None,
        manual_receipt_date=None,
        existing_receipt_delay_days=option.forecast_customer_receipt_delay_days,
    )
    option.forecast_customer_invoice_date = defaults["forecast_customer_invoice_date"]
    option.forecast_customer_invoice_date_source = defaults[
        "forecast_customer_invoice_date_source"
    ]
    option.forecast_customer_receipt_date = defaults["forecast_customer_receipt_date"]
    option.forecast_customer_receipt_date_source = defaults[
        "forecast_customer_receipt_date_source"
    ]
    option.forecast_customer_receipt_delay_days = defaults[
        "forecast_customer_receipt_delay_days"
    ]

    missing_inputs.extend(defaults["missing_inputs"])
    trace_lines.extend(defaults["trace_lines"])
    if defaults["missing_inputs"]:
        trace_lines.append(
            "Missing timing inputs: " + ", ".join(defaults["missing_inputs"])
        )
    option.date_calculation_trace = _dedupe_preserve_order(trace_lines)

    return {
        "option_id": int(option.id),
        "missing_inputs": _dedupe_preserve_order(missing_inputs),
        "trace_lines": option.date_calculation_trace or [],
        "project_requested_delivery_date": option.project_requested_delivery_date,
        "selected_delivery_date": option.selected_delivery_date,
        "delivery_date_variance_days": option.delivery_date_variance_days,
        "supplier_effective_receipt_date": option.supplier_effective_receipt_date,
        "forecast_customer_invoice_date": option.forecast_customer_invoice_date,
        "forecast_customer_receipt_date": option.forecast_customer_receipt_date,
    }


async def get_procurement_option_readiness(
    *,
    option_id: int,
    db: AsyncSession,
) -> Dict[str, Any]:
    """
    Read-only readiness projection for future candidate-builder usage.
    """
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise ValueError(f"procurement option {option_id} not found")

    component_result = await db.execute(
        select(ProcurementCostComponent)
        .where(
            ProcurementCostComponent.procurement_option_id == option_id,
            ProcurementCostComponent.is_active == True,  # noqa: E712
        )
        .order_by(ProcurementCostComponent.id.asc())
    )
    active_components = list(component_result.scalars().all())
    integrity_issues = _extract_component_integrity_issues(active_components)

    base_components = [
        component
        for component in active_components
        if component.component_type == "BASE_PRICE"
    ]
    shipping_component = next(
        (
            component
            for component in active_components
            if component.component_type == "SHIPPING"
        ),
        None,
    )

    selected_delivery_date = (
        option.selected_delivery_date
        or option.supplier_actual_delivery_date
        or option.project_requested_delivery_date
    )

    payment_method: Optional[PaymentMethod] = None
    if option.payment_method_id is not None:
        payment_method_result = await db.execute(
            select(PaymentMethod).where(PaymentMethod.id == option.payment_method_id)
        )
        payment_method = payment_method_result.scalar_one_or_none()

    custom_component_payment_method_ids = sorted(
        list(
            {
                int(raw_metadata.get("payment_method_id"))
                for raw_metadata in [
                    component.payment_metadata
                    if isinstance(component.payment_metadata, dict)
                    else {}
                    for component in active_components
                ]
                if raw_metadata.get("inherit_option_payment_schedule") is False
                and raw_metadata.get("payment_method_id") is not None
            }
        )
    )
    payment_methods_by_id: Dict[int, PaymentMethod] = {}
    if custom_component_payment_method_ids:
        payment_methods_result = await db.execute(
            select(PaymentMethod).where(
                PaymentMethod.id.in_(custom_component_payment_method_ids)
            )
        )
        payment_methods_by_id = {
            int(method.id): method
            for method in payment_methods_result.scalars().all()
        }

    component_payment_diagnostics = [
        _resolve_component_payment_diagnostic(
            component=component,
            option=option,
            default_payment_method=payment_method,
            payment_methods_by_id=payment_methods_by_id,
        )
        for component in active_components
    ]

    missing_required_fields: List[str] = []
    trace_lines: List[str] = []

    if len(base_components) == 0:
        missing_required_fields.append("active_base_price_component")
    elif len(base_components) > 1:
        missing_required_fields.append("single_active_base_price_component")
    else:
        base_component = base_components[0]
        if Decimal(str(base_component.amount_value or 0)) <= 0:
            missing_required_fields.append("base_price_amount_positive")
        if not str(base_component.amount_currency or "").strip():
            missing_required_fields.append("base_price_currency")

    if selected_delivery_date is None:
        missing_required_fields.append("selected_delivery_date")

    if option.payment_method_id is None or payment_method is None:
        missing_required_fields.append("payment_method_id")

    if option.planned_supplier_payment_date is None:
        missing_required_fields.append("planned_supplier_payment_date")

    if integrity_issues:
        missing_required_fields.append("no_invalid_active_cost_components")

    warnings: List[str] = []
    if option.forecast_customer_invoice_date is None:
        warnings.append("missing_forecast_customer_invoice_date")
    if option.forecast_customer_receipt_date is None:
        warnings.append("missing_forecast_customer_receipt_date")
    for diagnostic in component_payment_diagnostics:
        if diagnostic["warnings"]:
            warnings.extend(
                [
                    f"component:{diagnostic['component_id']}:{warning_code}"
                    for warning_code in diagnostic["warnings"]
                ]
            )

    landed_cost_preview = await calculate_procurement_option_landed_cost(
        option_id=option_id,
        db=db,
    )
    if landed_cost_preview["missing_exchange_rates"]:
        warnings.append("missing_exchange_rates_for_irr_conversion")

    if (
        selected_delivery_date is not None
        and option.project_requested_delivery_date is not None
        and selected_delivery_date > option.project_requested_delivery_date
    ):
        warnings.append("supplier_delivery_later_than_project_requested")

    if missing_required_fields:
        trace_lines.append(
            "Missing required fields: " + ", ".join(_dedupe_preserve_order(missing_required_fields))
        )
    if warnings:
        trace_lines.append("Warnings: " + ", ".join(_dedupe_preserve_order(warnings)))

    delivery_variance_days: Optional[int] = None
    if selected_delivery_date is not None and option.project_requested_delivery_date is not None:
        delivery_variance_days = (
            selected_delivery_date - option.project_requested_delivery_date
        ).days

    return {
        "option_id": int(option.id),
        "is_ready_for_candidate_builder": len(_dedupe_preserve_order(missing_required_fields))
        == 0,
        "missing_required_fields": _dedupe_preserve_order(missing_required_fields),
        "warnings": _dedupe_preserve_order(warnings),
        "cost_summary": {
            "active_component_count": len(active_components),
            "base_component": (
                {
                    "component_id": int(base_components[0].id),
                    "amount_value": base_components[0].amount_value,
                    "amount_currency": _normalize_currency_code(
                        base_components[0].amount_currency
                    ),
                }
                if len(base_components) == 1
                else None
            ),
            "shipping_component": (
                {
                    "component_id": int(shipping_component.id),
                    "amount_value": shipping_component.amount_value,
                    "amount_currency": _normalize_currency_code(
                        shipping_component.amount_currency
                    ),
                }
                if shipping_component is not None
                else None
            ),
            "legacy_compatibility": {
                "cost_amount": option.cost_amount,
                "cost_currency": option.cost_currency,
                "shipping_cost": option.shipping_cost,
            },
            "totals_by_currency": landed_cost_preview["totals_by_currency"],
            "total_irr": landed_cost_preview["total_irr"],
            "invalid_active_cost_components": integrity_issues,
        },
        "delivery_summary": {
            "project_requested_delivery_date": option.project_requested_delivery_date,
            "supplier_actual_delivery_date": option.supplier_actual_delivery_date,
            "selected_delivery_date": selected_delivery_date,
            "delivery_date_variance_days": delivery_variance_days,
            "delivery_date_source": option.delivery_date_source,
        },
        "payment_summary": {
            "payment_method_id": option.payment_method_id,
            "payment_method_code": payment_method.code if payment_method else None,
            "payment_method_settlement_delay_days": (
                payment_method.settlement_delay_days if payment_method else None
            ),
            "planned_supplier_payment_date": option.planned_supplier_payment_date,
            "supplier_effective_receipt_date": option.supplier_effective_receipt_date,
            "default_payment_type": str((option.payment_terms or {}).get("type") or "cash"),
            "component_payment_diagnostics": component_payment_diagnostics,
            "components_inheriting_default_schedule": len(
                [
                    row
                    for row in component_payment_diagnostics
                    if row.get("inherit_option_payment_schedule")
                ]
            ),
            "components_with_custom_schedule": len(
                [
                    row
                    for row in component_payment_diagnostics
                    if not row.get("inherit_option_payment_schedule")
                ]
            ),
        },
        "derived_customer_schedule_summary": {
            "forecast_customer_invoice_date": option.forecast_customer_invoice_date,
            "forecast_customer_invoice_date_source": option.forecast_customer_invoice_date_source,
            "forecast_customer_receipt_date": option.forecast_customer_receipt_date,
            "forecast_customer_receipt_date_source": option.forecast_customer_receipt_date_source,
            "forecast_customer_receipt_delay_days": option.forecast_customer_receipt_delay_days,
        },
        "trace_lines": trace_lines + landed_cost_preview["trace_lines"],
    }
