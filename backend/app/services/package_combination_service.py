"""
Package combination and optimization-submission helpers (Phase 12C).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.currency_conversion_service import CurrencyConversionService
from app.models import (
    FinalizedDecision,
    ItemSubItem,
    OptimizationSubmission,
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    ProjectItem,
    ProjectItemSubItem,
)

MAX_COMBINATION_CANDIDATES = 128
SUBMISSION_STATE_SENT = "SENT"
SUBMISSION_STATE_ROLLED_BACK = "ROLLED_BACK"


@dataclass
class PackageCandidate:
    package_id: int
    package_name: str
    package_type: str
    main_item_quantity: int
    subitem_coverages: Dict[int, int]
    selected_option_id: int
    selected_option_cost: Decimal
    selected_option_currency: str
    selected_option_purchase_date: Optional[date]
    selected_option_delivery_date: Optional[date]
    selected_option_supplier: Optional[str]


def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalize_currency(code: Optional[str]) -> str:
    if not code:
        return "IRR"
    return code.strip().upper()


def _serialize_date(value: Optional[date]) -> Optional[str]:
    return value.isoformat() if value else None


def _serialize_decimal(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


async def get_project_item_submission_record(
    db: AsyncSession, project_item_id: int
) -> Optional[OptimizationSubmission]:
    result = await db.execute(
        select(OptimizationSubmission).where(
            OptimizationSubmission.project_item_id == project_item_id
        )
    )
    return result.scalar_one_or_none()


async def get_project_item_optimization_state(db: AsyncSession, project_item_id: int) -> str:
    record = await get_project_item_submission_record(db, project_item_id)
    if not record:
        return "NOT_SENT"
    return record.status


async def is_project_item_sent_to_optimization(
    db: AsyncSession, project_item_id: int
) -> bool:
    return (await get_project_item_optimization_state(db, project_item_id)) == SUBMISSION_STATE_SENT


async def ensure_project_item_not_sent_to_optimization(
    db: AsyncSession, project_item_id: int
) -> None:
    if await is_project_item_sent_to_optimization(db, project_item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Item has already been sent to optimization. "
                "Rollback is required before changing packages."
            ),
        )


async def get_package_finalization_map(
    db: AsyncSession, package_ids: Sequence[int]
) -> Dict[int, bool]:
    if not package_ids:
        return {}
    result = await db.execute(
        select(
            ProcurementOption.package_id,
            func.count(ProcurementOption.id).label("options_count"),
            func.sum(case((ProcurementOption.is_finalized == True, 1), else_=0)).label(  # noqa: E712
                "finalized_count"
            ),
        )
        .where(
            ProcurementOption.is_active == True,  # noqa: E712
            ProcurementOption.package_id.in_(list(package_ids)),
        )
        .group_by(ProcurementOption.package_id)
    )
    rows = result.all()
    finalized: Dict[int, bool] = {int(pkg_id): False for pkg_id in package_ids}
    for pkg_id, options_count, finalized_count in rows:
        finalized[int(pkg_id)] = bool(options_count and options_count == finalized_count)
    return finalized


async def _load_project_item_requirements(
    db: AsyncSession, project_item_id: int
) -> Tuple[ProjectItem, Dict[int, Dict[str, Any]]]:
    item_result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == project_item_id)
    )
    project_item = item_result.scalar_one_or_none()
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project item {project_item_id} not found",
        )

    req_result = await db.execute(
        select(ProjectItemSubItem, ItemSubItem)
        .outerjoin(ItemSubItem, ItemSubItem.id == ProjectItemSubItem.item_subitem_id)
        .where(ProjectItemSubItem.project_item_id == project_item_id)
    )
    requirements: Dict[int, Dict[str, Any]] = {}
    for rel, sub in req_result.all():
        requirements[int(rel.id)] = {
            "required": int(rel.quantity or 0),
            "name": sub.name if sub else None,
            "part_number": sub.part_number if sub else None,
        }

    return project_item, requirements


async def _load_finalized_package_candidates(
    db: AsyncSession, project_item_id: int
) -> List[PackageCandidate]:
    package_result = await db.execute(
        select(ProcurementPackage).where(
            ProcurementPackage.project_item_id == project_item_id,
            ProcurementPackage.is_active == True,  # noqa: E712
        )
    )
    packages = package_result.scalars().all()
    if not packages:
        return []

    package_ids = [int(pkg.id) for pkg in packages]
    finalized_map = await get_package_finalization_map(db, package_ids)

    options_result = await db.execute(
        select(ProcurementOption).where(
            ProcurementOption.is_active == True,  # noqa: E712
            ProcurementOption.package_id.in_(package_ids),
        )
    )
    options = options_result.scalars().all()

    options_by_package: Dict[int, List[ProcurementOption]] = {}
    for option in options:
        if option.package_id is None:
            continue
        options_by_package.setdefault(int(option.package_id), []).append(option)

    subitems_result = await db.execute(
        select(PackageSubItem).where(PackageSubItem.package_id.in_(package_ids))
    )
    subitems = subitems_result.scalars().all()
    subitems_by_package: Dict[int, Dict[int, int]] = {}
    for row in subitems:
        package_id = int(row.package_id)
        project_item_subitem_id = int(row.project_item_subitem_id)
        subitems_by_package.setdefault(package_id, {})
        subitems_by_package[package_id][project_item_subitem_id] = (
            subitems_by_package[package_id].get(project_item_subitem_id, 0)
            + int(row.quantity_covered or 0)
        )

    candidates: List[PackageCandidate] = []
    for package in packages:
        package_id = int(package.id)
        if not finalized_map.get(package_id, False):
            continue
        finalized_options = [
            opt for opt in options_by_package.get(package_id, []) if bool(opt.is_finalized)
        ]
        if not finalized_options:
            continue

        def option_sort_key(opt: ProcurementOption) -> Tuple[Decimal, date, int]:
            cost = _as_decimal(opt.cost_amount or opt.base_cost or 0) + _as_decimal(opt.shipping_cost or 0)
            delivery = opt.expected_delivery_date or date.max
            return (cost, delivery, int(opt.id))

        selected = sorted(finalized_options, key=option_sort_key)[0]
        selected_cost = _as_decimal(selected.cost_amount or selected.base_cost or 0) + _as_decimal(
            selected.shipping_cost or 0
        )

        supplier_name = selected.supplier_name

        candidates.append(
            PackageCandidate(
                package_id=package_id,
                package_name=package.package_name or f"Package {package_id}",
                package_type=package.package_type,
                main_item_quantity=int(package.main_item_quantity or 0),
                subitem_coverages=subitems_by_package.get(package_id, {}),
                selected_option_id=int(selected.id),
                selected_option_cost=selected_cost,
                selected_option_currency=_normalize_currency(selected.cost_currency),
                selected_option_purchase_date=selected.purchase_date,
                selected_option_delivery_date=selected.expected_delivery_date,
                selected_option_supplier=supplier_name,
            )
        )

    candidates.sort(key=lambda c: c.package_id)
    return candidates


def _evaluate_combination(
    *,
    project_item_required_quantity: int,
    subitem_requirements: Dict[int, Dict[str, Any]],
    combo_candidates: Sequence[PackageCandidate],
) -> Dict[str, Any]:
    covered_main = sum(c.main_item_quantity for c in combo_candidates)
    required_main = int(project_item_required_quantity or 0)

    covered_subitems: Dict[int, int] = {}
    for pkg in combo_candidates:
        for subitem_id, qty in pkg.subitem_coverages.items():
            covered_subitems[subitem_id] = covered_subitems.get(subitem_id, 0) + int(qty or 0)

    missing_components: List[Dict[str, Any]] = []
    surplus_components: List[Dict[str, Any]] = []

    if covered_main < required_main:
        missing_components.append(
            {
                "component": "main_item",
                "required": required_main,
                "covered": covered_main,
                "missing": required_main - covered_main,
            }
        )
    elif covered_main > required_main:
        surplus_components.append(
            {
                "component": "main_item",
                "required": required_main,
                "covered": covered_main,
                "surplus": covered_main - required_main,
            }
        )

    for subitem_id, req in subitem_requirements.items():
        required_qty = int(req["required"] or 0)
        covered_qty = int(covered_subitems.get(subitem_id, 0))
        if covered_qty < required_qty:
            missing_components.append(
                {
                    "component": f"subitem:{subitem_id}",
                    "subitem_id": subitem_id,
                    "name": req.get("name"),
                    "part_number": req.get("part_number"),
                    "required": required_qty,
                    "covered": covered_qty,
                    "missing": required_qty - covered_qty,
                }
            )
        elif covered_qty > required_qty:
            surplus_components.append(
                {
                    "component": f"subitem:{subitem_id}",
                    "subitem_id": subitem_id,
                    "name": req.get("name"),
                    "part_number": req.get("part_number"),
                    "required": required_qty,
                    "covered": covered_qty,
                    "surplus": covered_qty - required_qty,
                }
            )

    full_coverage = len(missing_components) == 0
    has_any_coverage = covered_main > 0 or any(v > 0 for v in covered_subitems.values())
    coverage_classification = (
        "FULL_COVERAGE"
        if full_coverage
        else "PARTIAL_COVERAGE"
        if has_any_coverage
        else "NO_COVERAGE"
    )

    total_required = required_main + sum(int(v["required"] or 0) for v in subitem_requirements.values())
    total_covered = covered_main + sum(covered_subitems.values())
    coverage_percentage = (
        (Decimal(total_covered) / Decimal(total_required) * Decimal("100"))
        if total_required > 0
        else Decimal("100")
    )

    costs_by_currency: Dict[str, Decimal] = {}
    earliest_delivery: Optional[date] = None
    latest_delivery: Optional[date] = None
    suppliers: List[str] = []
    option_ids: List[int] = []
    package_ids: List[int] = []
    for pkg in combo_candidates:
        package_ids.append(pkg.package_id)
        option_ids.append(pkg.selected_option_id)
        costs_by_currency[pkg.selected_option_currency] = (
            costs_by_currency.get(pkg.selected_option_currency, Decimal("0")) + pkg.selected_option_cost
        )
        if pkg.selected_option_delivery_date:
            if earliest_delivery is None or pkg.selected_option_delivery_date < earliest_delivery:
                earliest_delivery = pkg.selected_option_delivery_date
            if latest_delivery is None or pkg.selected_option_delivery_date > latest_delivery:
                latest_delivery = pkg.selected_option_delivery_date
        if pkg.selected_option_supplier:
            suppliers.append(pkg.selected_option_supplier)

    return {
        "package_ids": sorted(package_ids),
        "option_ids": sorted(option_ids),
        "coverage_percentage": _serialize_decimal(coverage_percentage),
        "coverage_classification": coverage_classification,
        "is_full_coverage": full_coverage,
        "is_over_coverage": len(surplus_components) > 0,
        "missing_components": missing_components,
        "surplus_components": surplus_components,
        "main_item": {"required": required_main, "covered": covered_main},
        "costs_by_currency": {k: _serialize_decimal(v) for k, v in costs_by_currency.items()},
        "earliest_delivery_date": _serialize_date(earliest_delivery),
        "latest_delivery_date": _serialize_date(latest_delivery),
        "supplier_list": sorted(set(suppliers)),
        "_sort_total_cost": sum(costs_by_currency.values()),
        "_sort_latest_delivery": latest_delivery or date.max,
    }


def _remove_dominated_combinations(combos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if len(combos) < 2:
        return combos

    keep = [True] * len(combos)
    package_sets = [set(combo["package_ids"]) for combo in combos]
    for i, combo_i in enumerate(combos):
        if not keep[i]:
            continue
        for j, combo_j in enumerate(combos):
            if i == j or not keep[j]:
                continue
            set_i = package_sets[i]
            set_j = package_sets[j]
            if not set_i.issubset(set_j):
                continue
            i_cost = combo_i["_sort_total_cost"]
            j_cost = combo_j["_sort_total_cost"]
            i_latest = combo_i["_sort_latest_delivery"]
            j_latest = combo_j["_sort_latest_delivery"]
            if i_cost <= j_cost and i_latest <= j_latest:
                if set_i != set_j or (i_cost < j_cost or i_latest < j_latest):
                    keep[j] = False
    return [combo for idx, combo in enumerate(combos) if keep[idx]]


def _iter_deterministic_subsets(
    candidates: Sequence[PackageCandidate], max_subsets: int
) -> Iterable[Tuple[PackageCandidate, ...]]:
    count = 0
    for size in range(1, len(candidates) + 1):
        for combo in combinations(candidates, size):
            if count >= max_subsets:
                return
            count += 1
            yield combo


async def analyze_project_item_package_combinations(
    db: AsyncSession,
    *,
    project_item_id: int,
    max_combinations: int = MAX_COMBINATION_CANDIDATES,
) -> Dict[str, Any]:
    project_item, requirements = await _load_project_item_requirements(db, project_item_id)
    candidates = await _load_finalized_package_candidates(db, project_item_id)

    warnings: List[str] = []
    if not candidates:
        return {
            "project_item_id": project_item_id,
            "item_code": project_item.item_code,
            "item_name": project_item.item_name,
            "required_quantity": int(project_item.quantity or 0),
            "finalized_packages": [],
            "generated_combinations": [],
            "full_coverage_combinations": [],
            "incomplete_coverage_combinations": [],
            "aggregate_finalized_coverage": {
                "coverage_percentage": 0.0,
                "coverage_classification": "NO_COVERAGE",
                "missing_components": [],
                "surplus_components": [],
            },
            "warnings": warnings,
            "combination_threshold": max_combinations,
            "threshold_exceeded": False,
        }

    potential_total = (2 ** len(candidates)) - 1
    threshold_exceeded = potential_total > max_combinations
    if threshold_exceeded:
        warnings.append(
            (
                "Potential package combinations exceed threshold "
                f"({potential_total} > {max_combinations}). "
                "A deterministic subset was evaluated."
            )
        )

    evaluated_combos: List[Dict[str, Any]] = []
    for combo_tuple in _iter_deterministic_subsets(candidates, max_combinations):
        evaluated = _evaluate_combination(
            project_item_required_quantity=int(project_item.quantity or 0),
            subitem_requirements=requirements,
            combo_candidates=list(combo_tuple),
        )
        evaluated_combos.append(evaluated)

    full_combos = [c for c in evaluated_combos if c["is_full_coverage"]]
    full_combos = _remove_dominated_combinations(full_combos)
    full_combos.sort(
        key=lambda c: (
            len(c["package_ids"]),
            c["_sort_total_cost"],
            c["_sort_latest_delivery"],
            c["package_ids"],
        )
    )
    partial_combos = [c for c in evaluated_combos if not c["is_full_coverage"]]
    partial_combos.sort(
        key=lambda c: (
            -c["coverage_percentage"],
            len(c["missing_components"]),
            len(c["package_ids"]),
            c["package_ids"],
        )
    )

    aggregate_finalized = _evaluate_combination(
        project_item_required_quantity=int(project_item.quantity or 0),
        subitem_requirements=requirements,
        combo_candidates=candidates,
    )

    conversion_service = CurrencyConversionService(db)
    conversion_warnings: List[str] = []
    for combo in full_combos + partial_combos:
        total_irr = Decimal("0")
        can_convert_all = True
        for pkg in candidates:
            if pkg.package_id not in combo["package_ids"]:
                continue
            tx_date = pkg.selected_option_purchase_date or date.today()
            try:
                converted = await conversion_service.convert_to_base(
                    pkg.selected_option_cost,
                    pkg.selected_option_currency,
                    tx_date,
                )
                total_irr += converted
            except ValueError as ex:
                can_convert_all = False
                conversion_warnings.append(
                    f"Package {pkg.package_id} conversion warning: {str(ex)}"
                )
        combo["total_cost_irr"] = _serialize_decimal(total_irr) if can_convert_all else None

    warnings.extend(sorted(set(conversion_warnings)))

    def _strip_internal(combo: Dict[str, Any]) -> Dict[str, Any]:
        c = dict(combo)
        c.pop("_sort_total_cost", None)
        c.pop("_sort_latest_delivery", None)
        return c

    return {
        "project_item_id": project_item_id,
        "item_code": project_item.item_code,
        "item_name": project_item.item_name,
        "required_quantity": int(project_item.quantity or 0),
        "finalized_packages": [
            {
                "package_id": c.package_id,
                "package_name": c.package_name,
                "package_type": c.package_type,
                "main_item_quantity": c.main_item_quantity,
                "selected_option_id": c.selected_option_id,
                "selected_option_cost": _serialize_decimal(c.selected_option_cost),
                "selected_option_currency": c.selected_option_currency,
                "selected_option_purchase_date": _serialize_date(c.selected_option_purchase_date),
                "selected_option_delivery_date": _serialize_date(c.selected_option_delivery_date),
                "selected_option_supplier": c.selected_option_supplier,
            }
            for c in candidates
        ],
        "generated_combinations": [_strip_internal(c) for c in (full_combos + partial_combos)],
        "full_coverage_combinations": [_strip_internal(c) for c in full_combos],
        "incomplete_coverage_combinations": [_strip_internal(c) for c in partial_combos],
        "aggregate_finalized_coverage": _strip_internal(aggregate_finalized),
        "warnings": warnings,
        "combination_threshold": max_combinations,
        "threshold_exceeded": threshold_exceeded,
    }


async def mark_project_item_sent_to_optimization(
    db: AsyncSession,
    *,
    project_item_id: int,
    user_id: Optional[int],
    partial_coverage_acknowledged: bool,
    summary_payload: Dict[str, Any],
    notes: Optional[str] = None,
) -> OptimizationSubmission:
    existing = await get_project_item_submission_record(db, project_item_id)
    now = datetime.utcnow()
    if existing:
        existing.status = SUBMISSION_STATE_SENT
        existing.partial_coverage_acknowledged = partial_coverage_acknowledged
        existing.summary_payload = summary_payload
        existing.notes = notes
        existing.submitted_at = now
        existing.submitted_by_id = user_id
        existing.rolled_back_at = None
        existing.rolled_back_by_id = None
        await db.flush()
        return existing

    record = OptimizationSubmission(
        project_item_id=project_item_id,
        status=SUBMISSION_STATE_SENT,
        partial_coverage_acknowledged=partial_coverage_acknowledged,
        submitted_at=now,
        submitted_by_id=user_id,
        notes=notes,
        summary_payload=summary_payload,
    )
    db.add(record)
    await db.flush()
    return record


async def rollback_project_item_optimization_submission(
    db: AsyncSession,
    *,
    project_item_id: int,
    user_id: Optional[int],
    notes: Optional[str] = None,
) -> OptimizationSubmission:
    record = await get_project_item_submission_record(db, project_item_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No optimization submission found for this item",
        )

    if record.status != SUBMISSION_STATE_SENT:
        return record

    blocking_decision_result = await db.execute(
        select(FinalizedDecision.id).where(
            and_(
                FinalizedDecision.project_item_id == project_item_id,
                FinalizedDecision.status.in_(["PROPOSED", "LOCKED"]),
            )
        )
    )
    blocking_decision = blocking_decision_result.first()
    if blocking_decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Rollback is not allowed because this item already has PROPOSED/LOCKED "
                "finalized decisions. Revert those decisions first."
            ),
        )

    record.status = SUBMISSION_STATE_ROLLED_BACK
    record.rolled_back_at = datetime.utcnow()
    record.rolled_back_by_id = user_id
    if notes:
        record.notes = notes
    await db.flush()
    return record


def compute_item_coverage_state(coverage_summary: Dict[str, Any]) -> str:
    packages = coverage_summary.get("packages", []) or []
    if len(packages) == 0:
        return "NO_PACKAGE"

    main_required = int((coverage_summary.get("main_item") or {}).get("required", 0))
    main_covered = int((coverage_summary.get("main_item") or {}).get("covered", 0))
    subitems = coverage_summary.get("subitems", {}) or {}

    missing_components = any(
        int(values.get("covered", 0)) < int(values.get("required", 0))
        for values in subitems.values()
    )
    over_components = any(
        int(values.get("covered", 0)) > int(values.get("required", 0))
        for values in subitems.values()
    )
    if main_covered > main_required:
        over_components = True

    is_full = bool(coverage_summary.get("is_fully_covered"))
    if missing_components and main_covered >= main_required:
        return "MISSING_COMPONENTS"
    if over_components and is_full:
        return "OVER_COVERED"
    if is_full:
        return "FULL"
    return "PARTIAL"

