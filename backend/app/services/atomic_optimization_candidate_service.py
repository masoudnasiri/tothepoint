from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    DeliveryOption,
    ItemSubItem,
    PackageSubItem,
    PaymentMethod,
    ProcurementCostComponent,
    ProcurementOption,
    ProcurementPackage,
    Project,
    ProjectItem,
    ProjectItemSubItem,
    Supplier,
)
from app.services.procurement_financials_service import (
    calculate_procurement_option_landed_cost,
    get_procurement_option_readiness,
)


def _dedupe_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    deduped: List[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        deduped.append(value)
    return deduped


def _as_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _candidate_identity(
    *,
    project_id: Optional[int],
    project_item_id: Optional[int],
    package_id: Optional[int],
    procurement_option_id: int,
) -> str:
    return (
        f"candidate:{project_id if project_id is not None else 'na'}:"
        f"{project_item_id if project_item_id is not None else 'na'}:"
        f"{package_id if package_id is not None else 'na'}:{procurement_option_id}"
    )


def _pick_landed_cost_amount(
    *,
    totals_by_currency: Dict[str, Any],
    primary_currency: Optional[str],
    warnings: List[str],
    trace_lines: List[str],
) -> Tuple[Optional[Decimal], Optional[str]]:
    normalized_totals = {
        str(currency).strip().upper(): _as_decimal(amount)
        for currency, amount in (totals_by_currency or {}).items()
        if _as_decimal(amount) is not None
    }
    if not normalized_totals:
        warnings.append("LANDED_COST_NOT_AVAILABLE")
        trace_lines.append("Landed cost totals are unavailable for this procurement option.")
        return None, None

    if len(normalized_totals) > 1:
        warnings.append("MIXED_COMPONENT_CURRENCIES_NOT_CONVERTED")
        trace_lines.append(
            "Multiple active component currencies detected; no FX conversion applied in Sprint 3B."
        )
        return None, None

    if primary_currency:
        primary = primary_currency.strip().upper()
        if primary in normalized_totals:
            return normalized_totals[primary], primary

    only_currency = next(iter(normalized_totals.keys()))
    return normalized_totals[only_currency], only_currency


def _compute_revenue_snapshot(
    *,
    delivery_option: Optional[DeliveryOption],
    quantity: Optional[Decimal],
    landed_cost_currency: Optional[str],
    trace_lines: List[str],
) -> Optional[Decimal]:
    if delivery_option is None or quantity is None or quantity <= 0:
        trace_lines.append("CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_MARGIN")
        return None

    # DeliveryOption currently stores invoice amount per unit without an explicit currency column.
    # We only compute margin in Sprint 3B when landed-cost currency is clearly IRR.
    if (landed_cost_currency or "").upper() != "IRR":
        trace_lines.append("CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_MARGIN")
        return None

    per_unit = _as_decimal(delivery_option.invoice_amount_per_unit)
    if per_unit is None:
        trace_lines.append("CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_MARGIN")
        return None

    trace_lines.append(
        "Computed customer revenue from delivery_option.invoice_amount_per_unit * candidate quantity."
    )
    return per_unit * quantity


async def _load_option_context(
    *,
    db: AsyncSession,
    option_id: int,
) -> Dict[str, Any]:
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    option = option_result.scalar_one_or_none()
    if not option:
        raise ValueError(f"procurement option {option_id} not found")

    package: Optional[ProcurementPackage] = None
    if option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage).where(ProcurementPackage.id == option.package_id)
        )
        package = package_result.scalar_one_or_none()

    project_item_id = option.project_item_id or (package.project_item_id if package else None)
    project_item: Optional[ProjectItem] = None
    if project_item_id is not None:
        item_result = await db.execute(
            select(ProjectItem).where(ProjectItem.id == project_item_id)
        )
        project_item = item_result.scalar_one_or_none()

    project: Optional[Project] = None
    if project_item is not None:
        project_result = await db.execute(
            select(Project).where(Project.id == project_item.project_id)
        )
        project = project_result.scalar_one_or_none()

    supplier: Optional[Supplier] = None
    if option.supplier_id is not None:
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == option.supplier_id)
        )
        supplier = supplier_result.scalar_one_or_none()

    payment_method: Optional[PaymentMethod] = None
    if option.payment_method_id is not None:
        payment_result = await db.execute(
            select(PaymentMethod).where(PaymentMethod.id == option.payment_method_id)
        )
        payment_method = payment_result.scalar_one_or_none()

    delivery_option: Optional[DeliveryOption] = None
    if option.delivery_option_id is not None:
        delivery_result = await db.execute(
            select(DeliveryOption).where(DeliveryOption.id == option.delivery_option_id)
        )
        delivery_option = delivery_result.scalar_one_or_none()

    active_components_result = await db.execute(
        select(ProcurementCostComponent)
        .where(
            ProcurementCostComponent.procurement_option_id == option.id,
            ProcurementCostComponent.is_active == True,  # noqa: E712
        )
        .order_by(ProcurementCostComponent.id.asc())
    )
    active_components = list(active_components_result.scalars().all())

    package_subitems: List[PackageSubItem] = []
    if package is not None:
        package_subitems_result = await db.execute(
            select(PackageSubItem)
            .options(
                selectinload(PackageSubItem.project_item_subitem).selectinload(
                    ProjectItemSubItem.sub_item
                )
            )
            .where(PackageSubItem.package_id == package.id)
            .order_by(PackageSubItem.id.asc())
        )
        package_subitems = list(package_subitems_result.scalars().all())

    project_subitems: List[ProjectItemSubItem] = []
    if project_item is not None:
        project_subitems_result = await db.execute(
            select(ProjectItemSubItem)
            .options(selectinload(ProjectItemSubItem.sub_item))
            .where(ProjectItemSubItem.project_item_id == project_item.id)
            .order_by(ProjectItemSubItem.id.asc())
        )
        project_subitems = list(project_subitems_result.scalars().all())

    return {
        "option": option,
        "package": package,
        "project_item": project_item,
        "project": project,
        "supplier": supplier,
        "payment_method": payment_method,
        "delivery_option": delivery_option,
        "active_components": active_components,
        "package_subitems": package_subitems,
        "project_subitems": project_subitems,
    }


async def build_atomic_candidate_for_option(
    db: AsyncSession,
    option_id: int,
    include_not_ready: bool = False,
) -> Optional[Dict[str, Any]]:
    context = await _load_option_context(db=db, option_id=option_id)
    option: ProcurementOption = context["option"]
    package: Optional[ProcurementPackage] = context["package"]
    project_item: Optional[ProjectItem] = context["project_item"]
    project: Optional[Project] = context["project"]
    supplier: Optional[Supplier] = context["supplier"]
    payment_method: Optional[PaymentMethod] = context["payment_method"]
    delivery_option: Optional[DeliveryOption] = context["delivery_option"]
    active_components: List[ProcurementCostComponent] = context["active_components"]
    package_subitems: List[PackageSubItem] = context["package_subitems"]
    project_subitems: List[ProjectItemSubItem] = context["project_subitems"]

    readiness = await get_procurement_option_readiness(option_id=option_id, db=db)
    is_ready = bool(readiness.get("is_ready_for_candidate_builder"))
    if not include_not_ready and not is_ready:
        return None

    landed_cost_preview = await calculate_procurement_option_landed_cost(
        option_id=option_id,
        db=db,
    )

    warnings: List[str] = []
    trace_lines: List[str] = []
    coverage_trace_lines: List[str] = []
    metrics_trace_lines: List[str] = []

    requested_main_quantity = _as_decimal(project_item.quantity) if project_item else None
    covered_main_quantity = _as_decimal(package.main_item_quantity) if package else None
    coverage_ratio: Optional[Decimal] = None
    if requested_main_quantity is not None and requested_main_quantity > 0:
        if covered_main_quantity is not None:
            coverage_ratio = covered_main_quantity / requested_main_quantity
    else:
        coverage_trace_lines.append("Requested main quantity unavailable for coverage ratio.")

    if package and package.package_type in {"PARTIAL", "CUSTOM"}:
        warnings.append("COVERAGE_VALIDATION_DEFERRED_TO_SPRINT_3C")
        coverage_trace_lines.append(
            "Complex package coverage validation is deferred to Sprint 3C."
        )

    covered_subitems: List[Dict[str, Any]] = []
    requested_by_project_subitem: Dict[int, Decimal] = {}
    for project_subitem in project_subitems:
        requested_by_project_subitem[project_subitem.id] = _as_decimal(
            project_subitem.quantity
        ) or Decimal("0")

    for package_subitem in package_subitems:
        project_item_subitem = package_subitem.project_item_subitem
        sub_item: Optional[ItemSubItem] = (
            project_item_subitem.sub_item if project_item_subitem else None
        )
        covered_subitems.append(
            {
                "subitem_id": int(sub_item.id) if sub_item else None,
                "subitem_name": sub_item.name if sub_item else None,
                "requested_quantity": (
                    requested_by_project_subitem.get(project_item_subitem.id)
                    if project_item_subitem
                    else None
                ),
                "covered_quantity": _as_decimal(package_subitem.quantity_covered),
                "unit": None,
            }
        )

    totals_by_currency = landed_cost_preview.get("totals_by_currency", {})
    primary_currency = (
        readiness.get("cost_summary", {}).get("base_component", {}) or {}
    ).get("amount_currency") or option.cost_currency
    landed_cost_amount, landed_cost_currency = _pick_landed_cost_amount(
        totals_by_currency=totals_by_currency,
        primary_currency=primary_currency,
        warnings=warnings,
        trace_lines=trace_lines,
    )

    base_component = (readiness.get("cost_summary", {}).get("base_component", {}) or {})
    shipping_component = (
        readiness.get("cost_summary", {}).get("shipping_component", {}) or {}
    )
    base_price_amount = _as_decimal(base_component.get("amount_value"))
    base_price_currency = base_component.get("amount_currency")
    shipping_cost_amount = _as_decimal(shipping_component.get("amount_value"))
    if shipping_cost_amount is None:
        shipping_cost_amount = _as_decimal(option.shipping_cost)

    component_payment_diagnostics_by_id = {
        row.get("component_id"): row
        for row in (readiness.get("payment_summary", {}).get("component_payment_diagnostics", []) or [])
    }

    cost_components_summary = [
        {
            "component_id": int(component.id),
            "component_type": component.component_type,
            "amount_value": _as_decimal(component.amount_value),
            "amount_currency": str(component.amount_currency or "").strip().upper(),
            "description": component.description,
            "payment_metadata": (
                component.payment_metadata if isinstance(component.payment_metadata, dict) else None
            ),
            "component_payment_diagnostic": component_payment_diagnostics_by_id.get(
                int(component.id)
            ),
        }
        for component in active_components
    ]

    quantity_for_revenue = (
        covered_main_quantity
        if covered_main_quantity is not None and covered_main_quantity > 0
        else requested_main_quantity
    )
    revenue_amount = _compute_revenue_snapshot(
        delivery_option=delivery_option,
        quantity=quantity_for_revenue,
        landed_cost_currency=landed_cost_currency,
        trace_lines=metrics_trace_lines,
    )
    gross_margin_amount: Optional[Decimal] = None
    gross_margin_ratio: Optional[Decimal] = None
    if revenue_amount is not None and landed_cost_amount is not None:
        gross_margin_amount = revenue_amount - landed_cost_amount
        if revenue_amount != 0:
            gross_margin_ratio = gross_margin_amount / revenue_amount
        metrics_trace_lines.append("Gross margin computed from customer revenue minus landed cost.")
    elif not metrics_trace_lines:
        metrics_trace_lines.append("CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_MARGIN")

    cash_gap_days: Optional[int] = None
    supplier_effective_receipt_date = readiness.get("payment_summary", {}).get(
        "supplier_effective_receipt_date"
    )
    forecast_customer_receipt_date = readiness.get(
        "derived_customer_schedule_summary", {}
    ).get("forecast_customer_receipt_date")
    if (
        supplier_effective_receipt_date is not None
        and forecast_customer_receipt_date is not None
    ):
        cash_gap_days = (
            forecast_customer_receipt_date - supplier_effective_receipt_date
        ).days
        metrics_trace_lines.append(
            "Cash gap days computed as forecast_customer_receipt_date - supplier_effective_receipt_date."
        )
    else:
        metrics_trace_lines.append("Cash gap not computed due to missing schedule/payment dates.")

    candidate = {
        "candidate_id": _candidate_identity(
            project_id=project.id if project else None,
            project_item_id=project_item.id if project_item else None,
            package_id=package.id if package else None,
            procurement_option_id=option.id,
        ),
        "project_id": project.id if project else None,
        "project_code": project.project_code if project else None,
        "project_name": project.name if project else None,
        "project_item_id": project_item.id if project_item else None,
        "project_item_name": project_item.item_name if project_item else None,
        "package_id": package.id if package else None,
        "package_name": package.package_name if package else None,
        "package_type": package.package_type if package else None,
        "procurement_option_id": option.id,
        "supplier_id": option.supplier_id,
        "supplier_name": (
            supplier.company_name if supplier is not None else option.supplier_name
        ),
        "covered_main_quantity": covered_main_quantity,
        "requested_main_quantity": requested_main_quantity,
        "coverage_ratio": coverage_ratio,
        "covered_subitems": covered_subitems,
        "coverage_trace_lines": _dedupe_preserve_order(coverage_trace_lines),
        "landed_cost_amount": landed_cost_amount,
        "landed_cost_currency": landed_cost_currency,
        "base_price_amount": base_price_amount,
        "base_price_currency": base_price_currency,
        "shipping_cost_amount": shipping_cost_amount,
        "cost_components_summary": cost_components_summary,
        "cost_trace_lines": _dedupe_preserve_order(
            list(landed_cost_preview.get("trace_lines", []))
            + (readiness.get("cost_summary", {}).get("invalid_active_cost_components", []) or [])
            + trace_lines
        ),
        "payment_method_id": option.payment_method_id,
        "payment_method_code": readiness.get("payment_summary", {}).get(
            "payment_method_code"
        ),
        "payment_method_name": (
            payment_method.name_en if payment_method is not None else None
        ),
        "planned_supplier_payment_date": option.planned_supplier_payment_date,
        "supplier_effective_receipt_date": supplier_effective_receipt_date,
        "payment_trace_lines": _dedupe_preserve_order(
            [
                line
                for line in readiness.get("trace_lines", [])
                if "payment" in line.lower() or "supplier effective receipt" in line.lower()
            ]
        ),
        "project_requested_delivery_date": readiness.get("delivery_summary", {}).get(
            "project_requested_delivery_date"
        ),
        "supplier_actual_delivery_date": readiness.get("delivery_summary", {}).get(
            "supplier_actual_delivery_date"
        ),
        "selected_delivery_date": readiness.get("delivery_summary", {}).get(
            "selected_delivery_date"
        ),
        "delivery_date_variance_days": readiness.get("delivery_summary", {}).get(
            "delivery_date_variance_days"
        ),
        "delivery_trace_lines": _dedupe_preserve_order(
            [
                line
                for line in readiness.get("trace_lines", [])
                if "delivery" in line.lower()
            ]
        ),
        "forecast_customer_invoice_date": readiness.get(
            "derived_customer_schedule_summary", {}
        ).get("forecast_customer_invoice_date"),
        "forecast_customer_receipt_date": forecast_customer_receipt_date,
        "customer_schedule_trace_lines": _dedupe_preserve_order(
            [
                line
                for line in readiness.get("trace_lines", [])
                if "invoice" in line.lower() or "receipt" in line.lower()
            ]
        ),
        "gross_margin_amount": gross_margin_amount,
        "gross_margin_ratio": gross_margin_ratio,
        "cash_gap_days": cash_gap_days,
        "working_capital_exposure_amount": landed_cost_amount,
        "metrics_trace_lines": _dedupe_preserve_order(metrics_trace_lines),
        "is_ready_for_candidate_builder": is_ready,
        "readiness_missing_required_fields": readiness.get(
            "missing_required_fields", []
        )
        or [],
        "readiness_warnings": readiness.get("warnings", []) or [],
        "readiness_trace_lines": readiness.get("trace_lines", []) or [],
        "blocking_issues": readiness.get("missing_required_fields", []) or [],
        "warnings": _dedupe_preserve_order((readiness.get("warnings", []) or []) + warnings),
        "trace_lines": _dedupe_preserve_order(
            [
                f"Candidate identity: {_candidate_identity(project_id=project.id if project else None, project_item_id=project_item.id if project_item else None, package_id=package.id if package else None, procurement_option_id=option.id)}",
                "Readiness projection reused from Sprint 3A readiness service.",
                "Coverage snapshot is informational; final coverage validation is deferred to Sprint 3C.",
            ]
            + trace_lines
            + coverage_trace_lines
            + metrics_trace_lines
        ),
    }

    return candidate


async def _build_collection(
    *,
    db: AsyncSession,
    option_ids: List[int],
    include_not_ready: bool,
    scope_label: str,
) -> Dict[str, Any]:
    candidates: List[Dict[str, Any]] = []
    trace_lines: List[str] = []
    warnings: List[str] = []
    skipped_not_ready = 0

    for option_id in option_ids:
        candidate = await build_atomic_candidate_for_option(
            db=db,
            option_id=option_id,
            include_not_ready=include_not_ready,
        )
        if candidate is None:
            skipped_not_ready += 1
            trace_lines.append(
                f"Skipped option {option_id} because include_not_ready=false and readiness is false."
            )
            continue
        candidates.append(candidate)

    ready_candidates = len(
        [item for item in candidates if item.get("is_ready_for_candidate_builder")]
    )
    not_ready_candidates = len(candidates) - ready_candidates
    if skipped_not_ready > 0:
        warnings.append("NOT_READY_OPTIONS_SKIPPED_BY_DEFAULT")

    return {
        "total_candidates": len(candidates),
        "ready_candidates": ready_candidates,
        "not_ready_candidates": not_ready_candidates,
        "candidates": candidates,
        "warnings": _dedupe_preserve_order(warnings),
        "trace_lines": _dedupe_preserve_order(
            [f"Atomic candidate preview built for {scope_label}."] + trace_lines
        ),
    }


async def build_atomic_candidates_for_project(
    db: AsyncSession,
    project_id: int,
    include_not_ready: bool = False,
) -> Dict[str, Any]:
    option_ids_result = await db.execute(
        select(ProcurementOption.id)
        .outerjoin(
            ProcurementPackage, ProcurementPackage.id == ProcurementOption.package_id
        )
        .outerjoin(
            ProjectItem,
            or_(
                ProjectItem.id == ProcurementOption.project_item_id,
                ProjectItem.id == ProcurementPackage.project_item_id,
            ),
        )
        .where(
            ProcurementOption.is_active == True,  # noqa: E712
            ProjectItem.project_id == project_id,
        )
        .order_by(ProcurementOption.id.asc())
    )
    option_ids = [int(value) for value in option_ids_result.scalars().all()]
    collection = await _build_collection(
        db=db,
        option_ids=option_ids,
        include_not_ready=include_not_ready,
        scope_label=f"project {project_id}",
    )
    collection["project_id"] = project_id
    return collection


async def build_atomic_candidates_for_procurement_package(
    db: AsyncSession,
    package_id: int,
    include_not_ready: bool = False,
) -> Dict[str, Any]:
    option_ids_result = await db.execute(
        select(ProcurementOption.id)
        .where(
            ProcurementOption.is_active == True,  # noqa: E712
            ProcurementOption.package_id == package_id,
        )
        .order_by(ProcurementOption.id.asc())
    )
    option_ids = [int(value) for value in option_ids_result.scalars().all()]
    collection = await _build_collection(
        db=db,
        option_ids=option_ids,
        include_not_ready=include_not_ready,
        scope_label=f"package {package_id}",
    )
    collection["package_id"] = package_id
    return collection


async def build_atomic_candidates_for_option(
    db: AsyncSession,
    option_id: int,
    include_not_ready: bool = False,
) -> Dict[str, Any]:
    candidate = await build_atomic_candidate_for_option(
        db=db,
        option_id=option_id,
        include_not_ready=include_not_ready,
    )
    candidates = [candidate] if candidate is not None else []
    ready_candidates = len(
        [item for item in candidates if item.get("is_ready_for_candidate_builder")]
    )
    return {
        "procurement_option_id": option_id,
        "total_candidates": len(candidates),
        "ready_candidates": ready_candidates,
        "not_ready_candidates": len(candidates) - ready_candidates,
        "candidates": candidates,
        "warnings": (
            ["NOT_READY_OPTION_SKIPPED_BY_DEFAULT"]
            if not candidates and not include_not_ready
            else []
        ),
        "trace_lines": (
            [
                f"Skipped option {option_id} because include_not_ready=false and readiness is false."
            ]
            if not candidates and not include_not_ready
            else [f"Atomic candidate preview built for option {option_id}."]
        ),
    }
