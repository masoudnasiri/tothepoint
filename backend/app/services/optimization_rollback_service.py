"""
Phase 12D: Controlled bulk rollback preview and execution service.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.currency_conversion_service import CurrencyConversionService
from app.models import (
    CashflowEvent,
    FinalizedDecision,
    OptimizationResult,
    OptimizationSubmission,
    ProcurementOption,
    ProcurementPackage,
    ProjectItem,
    Supplier,
    SupplierPayment,
)
from app.models_invoice_payment import Invoice, Payment
from app.services.package_combination_service import (
    SUBMISSION_STATE_SENT,
    compute_item_coverage_state,
    rollback_project_item_optimization_submission,
)
from app.services.package_service import calculate_coverage_summary


DOMESTIC_COUNTRY_ALIASES = {
    "iran",
    "ir",
    "iran, islamic republic of",
    "islamic republic of iran",
    "ایران",
}


def _as_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        try:
            if "T" in raw:
                return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
            return date.fromisoformat(raw)
        except ValueError:
            return None
    return None


def _safe_iso(value: Optional[date]) -> Optional[str]:
    return value.isoformat() if value else None


def _is_domestic_country(country: Optional[str]) -> Optional[bool]:
    if country is None:
        return None
    normalized = _normalize_text(country)
    if not normalized:
        return None
    return normalized in DOMESTIC_COUNTRY_ALIASES


def _cost_range_bucket(
    *,
    total_cost_irr: Optional[Decimal],
    min_cost_irr: Optional[Decimal],
    max_cost_irr: Optional[Decimal],
) -> str:
    if min_cost_irr is None and max_cost_irr is None:
        return "not_applied"
    if total_cost_irr is None:
        return "unavailable"
    if min_cost_irr is not None and total_cost_irr < min_cost_irr:
        return "below_min"
    if max_cost_irr is not None and total_cost_irr > max_cost_irr:
        return "above_max"
    return "in_range"


def _date_range_bucket(
    *,
    selected_date: Optional[date],
    date_from: Optional[date],
    date_to: Optional[date],
) -> str:
    if date_from is None and date_to is None:
        return "not_applied"
    if selected_date is None:
        return "unavailable"
    if date_from is not None and selected_date < date_from:
        return "out_of_range"
    if date_to is not None and selected_date > date_to:
        return "out_of_range"
    return "in_range"


def _derive_coverage_state_from_submission(selected_combination: Dict[str, Any]) -> Optional[str]:
    if not selected_combination:
        return None
    if bool(selected_combination.get("is_over_coverage")):
        return "over_covered"
    classification = (selected_combination.get("coverage_classification") or "").upper()
    if classification == "FULL_COVERAGE":
        return "full"
    if classification == "PARTIAL_COVERAGE":
        return "partial"
    if classification == "NO_COVERAGE":
        return "no_package"
    return None


def _derive_package_type_bucket(package_types: Set[str]) -> str:
    normalized = {p.upper() for p in package_types if p}
    if not normalized:
        return "unknown"
    if normalized == {"FULL"}:
        return "full"
    if normalized == {"PARTIAL"}:
        return "partial"
    return "mixed"


def _derive_supplier_bucket(domestic_count: int, foreign_count: int) -> str:
    if domestic_count > 0 and foreign_count == 0:
        return "domestic"
    if foreign_count > 0 and domestic_count == 0:
        return "foreign"
    if foreign_count > 0 and domestic_count > 0:
        return "mixed"
    return "unknown"


def _passes_checklist_filters(item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    package_type_bucket = item["package_type_bucket"]
    coverage_state = item["coverage_state"]
    supplier_bucket = item["supplier_bucket"]
    supplier_count = item["supplier_count"]
    warning_incomplete = bool(item["warning_incomplete_submission"])

    include_full = bool(filters.get("include_full_package_items", True))
    include_partial = bool(filters.get("include_partial_package_items", True))
    if package_type_bucket == "full" and not include_full:
        return False
    if package_type_bucket == "partial" and not include_partial:
        return False
    if package_type_bucket == "mixed" and not (include_full and include_partial):
        return False

    include_complete = bool(filters.get("include_complete_coverage_items", True))
    include_incomplete = bool(filters.get("include_incomplete_coverage_items", True))
    include_over = bool(filters.get("include_over_covered_items", True))
    if coverage_state == "full" and not include_complete:
        return False
    if coverage_state in {"partial", "no_package", "missing_components"} and not include_incomplete:
        return False
    if coverage_state == "over_covered" and not include_over:
        return False

    include_domestic = bool(filters.get("include_domestic_suppliers", True))
    include_foreign = bool(filters.get("include_foreign_suppliers", True))
    if supplier_bucket == "domestic" and not include_domestic:
        return False
    if supplier_bucket == "foreign" and not include_foreign:
        return False
    if supplier_bucket == "mixed" and not (include_domestic and include_foreign):
        return False

    include_single_supplier = bool(filters.get("include_single_supplier_items", True))
    include_multiple_supplier = bool(filters.get("include_multiple_supplier_items", True))
    if supplier_count <= 1 and not include_single_supplier:
        return False
    if supplier_count > 1 and not include_multiple_supplier:
        return False

    include_warning_incomplete = bool(
        filters.get("include_warning_incomplete_submissions", True)
    )
    if warning_incomplete and not include_warning_incomplete:
        return False

    return True


async def _resolve_cost_irr(
    *,
    db: AsyncSession,
    selected_combination: Dict[str, Any],
    options: Sequence[ProcurementOption],
    fallback_date: Optional[date],
) -> Tuple[Optional[Decimal], Optional[str]]:
    total_cost_irr = _as_decimal(selected_combination.get("total_cost_irr"))
    if total_cost_irr is not None:
        return total_cost_irr, None

    conversion_service = CurrencyConversionService(db)
    tx_date = fallback_date or date.today()

    costs_by_currency = selected_combination.get("costs_by_currency") or {}
    if isinstance(costs_by_currency, dict) and costs_by_currency:
        total = Decimal("0")
        for code, amount in costs_by_currency.items():
            amount_decimal = _as_decimal(amount) or Decimal("0")
            currency = (code or "IRR").strip().upper()
            if currency == "IRR":
                total += amount_decimal
                continue
            try:
                total += await conversion_service.convert_to_base(
                    amount_decimal, currency, tx_date
                )
            except ValueError as ex:
                return None, f"Missing exchange rate for {currency}: {str(ex)}"
        return total, None

    if not options:
        return None, "No option costs are available for IRR conversion"

    total = Decimal("0")
    for option in options:
        amount = (_as_decimal(option.cost_amount) or Decimal("0")) + (
            _as_decimal(option.shipping_cost) or Decimal("0")
        )
        currency = (option.cost_currency or "IRR").strip().upper()
        option_date = option.purchase_date or tx_date
        if currency == "IRR":
            total += amount
            continue
        try:
            total += await conversion_service.convert_to_base(amount, currency, option_date)
        except ValueError as ex:
            return None, f"Missing exchange rate for option {option.id}: {str(ex)}"
    return total, None


def _extract_project_need_date(project_item: ProjectItem) -> Optional[date]:
    raw = project_item.delivery_options
    if not raw or not isinstance(raw, list):
        return None
    parsed = sorted([d for d in (_parse_date(v) for v in raw) if d is not None])
    return parsed[0] if parsed else None


async def _evaluate_unsafe_dependencies(
    db: AsyncSession, *, project_item: ProjectItem
) -> List[Dict[str, Any]]:
    reasons: List[Dict[str, Any]] = []

    decisions_result = await db.execute(
        select(FinalizedDecision.id, FinalizedDecision.status, FinalizedDecision.delivery_status).where(
            FinalizedDecision.project_item_id == project_item.id
        )
    )
    decision_rows = decisions_result.all()
    decision_ids = [int(row[0]) for row in decision_rows]
    statuses = sorted({str(row[1]) for row in decision_rows if row[1]})

    if decision_rows:
        reasons.append(
            {
                "code": "decision_exists",
                "reason": "Optimization/finalized decisions already exist for this item",
                "count": len(decision_rows),
                "statuses": statuses,
            }
        )

    if decision_rows and any((row[2] or "AWAITING_DELIVERY") != "AWAITING_DELIVERY" for row in decision_rows):
        reasons.append(
            {
                "code": "procurement_execution_exists",
                "reason": "Procurement plan execution records already exist",
                "count": len(decision_rows),
            }
        )

    optimization_results_count = await db.scalar(
        select(func.count(OptimizationResult.id))
        .select_from(OptimizationResult)
        .outerjoin(
            ProcurementOption,
            ProcurementOption.id == OptimizationResult.procurement_option_id,
        )
        .where(
            or_(
                ProcurementOption.project_item_id == project_item.id,
                and_(
                    OptimizationResult.project_id == project_item.project_id,
                    OptimizationResult.item_code == project_item.item_code,
                ),
            )
        )
    )
    if (optimization_results_count or 0) > 0:
        reasons.append(
            {
                "code": "optimization_result_exists",
                "reason": "Optimization results already reference this item",
                "count": int(optimization_results_count or 0),
            }
        )

    if decision_ids:
        cashflow_count = await db.scalar(
            select(func.count(CashflowEvent.id)).where(
                CashflowEvent.related_decision_id.in_(decision_ids),
                CashflowEvent.is_cancelled == False,  # noqa: E712
            )
        )
        if (cashflow_count or 0) > 0:
            reasons.append(
                {
                    "code": "cashflow_exists",
                    "reason": "Cashflow events already depend on this item",
                    "count": int(cashflow_count or 0),
                }
            )

        supplier_payment_count = await db.scalar(
            select(func.count(SupplierPayment.id)).where(
                SupplierPayment.decision_id.in_(decision_ids)
            )
        )
        if (supplier_payment_count or 0) > 0:
            reasons.append(
                {
                    "code": "supplier_payment_exists",
                    "reason": "Supplier payment records already depend on this item",
                    "count": int(supplier_payment_count or 0),
                }
            )

        invoice_count = await db.scalar(
            select(func.count(Invoice.id)).where(Invoice.decision_id.in_(decision_ids))
        )
        if (invoice_count or 0) > 0:
            reasons.append(
                {
                    "code": "invoice_exists",
                    "reason": "Invoice records already depend on this item",
                    "count": int(invoice_count or 0),
                }
            )

        payment_count = await db.scalar(
            select(func.count(Payment.id)).where(Payment.decision_id.in_(decision_ids))
        )
        if (payment_count or 0) > 0:
            reasons.append(
                {
                    "code": "payment_exists",
                    "reason": "Payment records already depend on this item",
                    "count": int(payment_count or 0),
                }
            )

    return reasons


async def build_bulk_rollback_preview(
    db: AsyncSession,
    *,
    filters: Dict[str, Any],
) -> Dict[str, Any]:
    min_cost_irr = _as_decimal(filters.get("min_total_cost_irr"))
    max_cost_irr = _as_decimal(filters.get("max_total_cost_irr"))
    date_from = _parse_date(filters.get("date_from"))
    date_to = _parse_date(filters.get("date_to"))
    date_field = (filters.get("date_field") or "submitted_at").strip().lower()
    project_ids = [int(v) for v in (filters.get("project_ids") or []) if v is not None]
    supplier_ids_filter = {
        int(v) for v in (filters.get("supplier_ids") or []) if v is not None
    }

    submission_query = (
        select(OptimizationSubmission, ProjectItem)
        .join(ProjectItem, ProjectItem.id == OptimizationSubmission.project_item_id)
        .where(OptimizationSubmission.status == SUBMISSION_STATE_SENT)
    )
    if project_ids:
        submission_query = submission_query.where(ProjectItem.project_id.in_(project_ids))
    submission_query = submission_query.order_by(OptimizationSubmission.submitted_at.desc())

    rows = (await db.execute(submission_query)).all()
    if not rows:
        return {
            "matched_items": [],
            "rollbackable_items": [],
            "unsafe_items": [],
            "summary": {
                "matched_count": 0,
                "rollbackable_count": 0,
                "unsafe_count": 0,
                "by_package_type": {},
                "by_coverage_state": {},
                "by_supplier_type": {},
                "by_date_range": {},
                "by_cost_range": {},
            },
            "warnings": [],
            "applied_filters": {
                "date_field": date_field,
                "min_total_cost_irr": float(min_cost_irr) if min_cost_irr is not None else None,
                "max_total_cost_irr": float(max_cost_irr) if max_cost_irr is not None else None,
                "date_from": _safe_iso(date_from),
                "date_to": _safe_iso(date_to),
            },
        }

    warnings: List[str] = []
    matched_items: List[Dict[str, Any]] = []
    rollbackable_items: List[Dict[str, Any]] = []
    unsafe_items: List[Dict[str, Any]] = []

    by_package_type: Dict[str, int] = {}
    by_coverage_state: Dict[str, int] = {}
    by_supplier_type: Dict[str, int] = {}
    by_date_range: Dict[str, int] = {}
    by_cost_range: Dict[str, int] = {}

    for submission, project_item in rows:
        summary_payload = submission.summary_payload or {}
        selected_combination = summary_payload.get("selected_combination") or {}
        package_ids = {
            int(v)
            for v in (selected_combination.get("package_ids") or [])
            if v is not None
        }
        option_ids = {
            int(v)
            for v in (selected_combination.get("option_ids") or [])
            if v is not None
        }

        if not package_ids:
            package_rows = await db.execute(
                select(ProcurementPackage.id).where(
                    ProcurementPackage.project_item_id == project_item.id,
                    ProcurementPackage.is_active == True,  # noqa: E712
                )
            )
            package_ids = {int(row[0]) for row in package_rows.all()}

        package_result = (
            await db.execute(
                select(ProcurementPackage).where(ProcurementPackage.id.in_(list(package_ids)))
            )
            if package_ids
            else None
        )
        packages = package_result.scalars().all() if package_result else []
        package_type_bucket = _derive_package_type_bucket(
            {pkg.package_type for pkg in packages if pkg.package_type}
        )

        if not option_ids and package_ids:
            option_rows = await db.execute(
                select(ProcurementOption.id).where(
                    ProcurementOption.package_id.in_(list(package_ids)),
                    ProcurementOption.is_active == True,  # noqa: E712
                )
            )
            option_ids = {int(row[0]) for row in option_rows.all()}

        options_result = (
            await db.execute(
                select(ProcurementOption)
                .where(ProcurementOption.id.in_(list(option_ids)))
                .options()
            )
            if option_ids
            else None
        )
        options = options_result.scalars().all() if options_result else []

        supplier_ids: Set[int] = {
            int(v)
            for v in [
                *(pkg.supplier_id for pkg in packages if pkg.supplier_id is not None),
                *(opt.supplier_id for opt in options if opt.supplier_id is not None),
            ]
        }
        supplier_rows = (
            await db.execute(select(Supplier).where(Supplier.id.in_(list(supplier_ids))))
            if supplier_ids
            else None
        )
        suppliers = supplier_rows.scalars().all() if supplier_rows else []
        supplier_name_map = {int(s.id): s.company_name for s in suppliers}
        domestic_count = 0
        foreign_count = 0
        for supplier in suppliers:
            domestic_flag = _is_domestic_country(supplier.country)
            if domestic_flag is True:
                domestic_count += 1
            elif domestic_flag is False:
                foreign_count += 1
        supplier_bucket = _derive_supplier_bucket(domestic_count, foreign_count)
        supplier_count = len({name for name in supplier_name_map.values() if name}) or len(
            supplier_ids
        )

        if supplier_ids_filter and supplier_ids and not supplier_ids.intersection(supplier_ids_filter):
            continue

        coverage_state = _derive_coverage_state_from_submission(selected_combination)
        if coverage_state is None:
            coverage_summary = await calculate_coverage_summary(db, project_item.id)
            coverage_state = compute_item_coverage_state(coverage_summary).lower()

        warning_incomplete_submission = bool(submission.partial_coverage_acknowledged)

        total_cost_irr, conversion_warning = await _resolve_cost_irr(
            db=db,
            selected_combination=selected_combination,
            options=options,
            fallback_date=_parse_date(submission.submitted_at),
        )
        if conversion_warning:
            warnings.append(
                f"{project_item.item_code}: {conversion_warning}"
            )

        submitted_date = _parse_date(submission.submitted_at)
        latest_delivery_date = _parse_date(selected_combination.get("latest_delivery_date"))
        earliest_purchase_date = _parse_date(selected_combination.get("earliest_purchase_date"))
        if earliest_purchase_date is None:
            candidate_purchase_dates = [opt.purchase_date for opt in options if opt.purchase_date]
            earliest_purchase_date = min(candidate_purchase_dates) if candidate_purchase_dates else None
        project_need_date = _extract_project_need_date(project_item)

        selected_date_map = {
            "submitted_at": submitted_date,
            "delivery_date": latest_delivery_date,
            "purchase_date": earliest_purchase_date,
            "project_need_date": project_need_date,
        }
        selected_date = selected_date_map.get(date_field, submitted_date)

        candidate = {
            "project_item_id": int(project_item.id),
            "project_id": int(project_item.project_id),
            "item_code": project_item.item_code,
            "item_name": project_item.item_name,
            "submission_id": int(submission.id),
            "submitted_at": submission.submitted_at.isoformat() if submission.submitted_at else None,
            "package_ids": sorted(package_ids),
            "option_ids": sorted(option_ids),
            "package_type_bucket": package_type_bucket,
            "coverage_state": coverage_state,
            "supplier_bucket": supplier_bucket,
            "supplier_count": int(supplier_count),
            "supplier_ids": sorted(supplier_ids),
            "supplier_names": sorted(set(filter(None, supplier_name_map.values()))),
            "warning_incomplete_submission": warning_incomplete_submission,
            "total_cost_irr": float(total_cost_irr) if total_cost_irr is not None else None,
            "cost_currency_warning": conversion_warning,
            "date_field_used": date_field,
            "selected_date": _safe_iso(selected_date),
            "date_candidates": {
                "submitted_at": _safe_iso(submitted_date),
                "delivery_date": _safe_iso(latest_delivery_date),
                "purchase_date": _safe_iso(earliest_purchase_date),
                "project_need_date": _safe_iso(project_need_date),
            },
        }

        if not _passes_checklist_filters(candidate, filters):
            continue

        date_bucket = _date_range_bucket(
            selected_date=selected_date,
            date_from=date_from,
            date_to=date_to,
        )
        by_date_range[date_bucket] = by_date_range.get(date_bucket, 0) + 1
        if date_bucket == "out_of_range":
            continue
        if date_bucket == "unavailable":
            warnings.append(
                f"{project_item.item_code}: selected date field '{date_field}' is unavailable for filtering"
            )

        cost_bucket = _cost_range_bucket(
            total_cost_irr=total_cost_irr,
            min_cost_irr=min_cost_irr,
            max_cost_irr=max_cost_irr,
        )
        by_cost_range[cost_bucket] = by_cost_range.get(cost_bucket, 0) + 1
        if cost_bucket in {"below_min", "above_max"}:
            continue

        matched_items.append(candidate)
        by_package_type[package_type_bucket] = by_package_type.get(package_type_bucket, 0) + 1
        by_coverage_state[coverage_state] = by_coverage_state.get(coverage_state, 0) + 1
        by_supplier_type[supplier_bucket] = by_supplier_type.get(supplier_bucket, 0) + 1

        unsafe_reasons = await _evaluate_unsafe_dependencies(db, project_item=project_item)
        if cost_bucket == "unavailable":
            unsafe_reasons.append(
                {
                    "code": "cost_conversion_missing",
                    "reason": (
                        "Price range filter is active but IRR equivalent is unavailable due to missing "
                        "currency conversion data"
                    ),
                }
            )

        if unsafe_reasons:
            unsafe_items.append({**candidate, "skip_reasons": unsafe_reasons})
            continue

        rollbackable_items.append(candidate)

    summary = {
        "matched_count": len(matched_items),
        "rollbackable_count": len(rollbackable_items),
        "unsafe_count": len(unsafe_items),
        "by_package_type": by_package_type,
        "by_coverage_state": by_coverage_state,
        "by_supplier_type": by_supplier_type,
        "by_date_range": by_date_range,
        "by_cost_range": by_cost_range,
    }

    return {
        "matched_items": matched_items,
        "rollbackable_items": rollbackable_items,
        "unsafe_items": unsafe_items,
        "summary": summary,
        "warnings": sorted(set(warnings)),
        "applied_filters": {
            "date_field": date_field,
            "min_total_cost_irr": float(min_cost_irr) if min_cost_irr is not None else None,
            "max_total_cost_irr": float(max_cost_irr) if max_cost_irr is not None else None,
            "date_from": _safe_iso(date_from),
            "date_to": _safe_iso(date_to),
        },
    }


async def execute_bulk_rollback(
    db: AsyncSession,
    *,
    filters: Dict[str, Any],
    selected_item_ids: Optional[List[int]],
    confirmed: bool,
    user_id: Optional[int],
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit confirmation is required for bulk rollback execution",
        )

    preview = await build_bulk_rollback_preview(db, filters=filters)
    rollbackable_map = {
        int(item["project_item_id"]): item for item in preview.get("rollbackable_items", [])
    }
    unsafe_map = {
        int(item["project_item_id"]): item for item in preview.get("unsafe_items", [])
    }

    if selected_item_ids:
        target_ids = sorted({int(v) for v in selected_item_ids})
    else:
        target_ids = sorted(rollbackable_map.keys())

    rolled_back_items: List[Dict[str, Any]] = []
    skipped_items: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    for project_item_id in target_ids:
        if project_item_id in unsafe_map:
            unsafe_item = unsafe_map[project_item_id]
            skipped_items.append(
                {
                    "project_item_id": project_item_id,
                    "item_code": unsafe_item.get("item_code"),
                    "reason": "unsafe_for_rollback",
                    "skip_reasons": unsafe_item.get("skip_reasons", []),
                }
            )
            continue

        candidate = rollbackable_map.get(project_item_id)
        if not candidate:
            skipped_items.append(
                {
                    "project_item_id": project_item_id,
                    "reason": "not_matched_by_filters_or_not_sent",
                }
            )
            continue

        try:
            record = await rollback_project_item_optimization_submission(
                db,
                project_item_id=project_item_id,
                user_id=user_id,
                notes=notes or "Bulk rollback from optimization submission",
            )
            rolled_back_items.append(
                {
                    "project_item_id": project_item_id,
                    "item_code": candidate.get("item_code"),
                    "status": record.status,
                    "rolled_back_at": record.rolled_back_at.isoformat()
                    if record.rolled_back_at
                    else None,
                }
            )
        except HTTPException as exc:
            skipped_items.append(
                {
                    "project_item_id": project_item_id,
                    "item_code": candidate.get("item_code"),
                    "reason": "rollback_rejected",
                    "detail": exc.detail,
                    "status_code": exc.status_code,
                }
            )
        except Exception as exc:  # pragma: no cover - defensive
            errors.append(
                {
                    "project_item_id": project_item_id,
                    "item_code": candidate.get("item_code"),
                    "detail": str(exc),
                }
            )

    return {
        "rolled_back_items": rolled_back_items,
        "skipped_items": skipped_items,
        "warnings": preview.get("warnings", []),
        "errors": errors,
        "preview_summary": preview.get("summary", {}),
    }
