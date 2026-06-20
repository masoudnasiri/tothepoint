"""
Phase 12E-0: Scenario-based optimization budget analysis and financial reporting.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.currency_conversion_service import CurrencyConversionService
from app.models import (
    BudgetData,
    FinalizedDecision,
    OptimizationResult,
    ProcurementOption,
    Project,
    ProjectItem,
)
from app.schemas import OptimizationFinancialAnalysis, OptimizationFinancialPeriod
from app.services.package_combination_service import (
    analyze_project_item_package_combinations,
)

ALLOWED_SCENARIOS = {
    "minimum_feasible",
    "average_candidate",
    "conservative",
    "selected_result",
}

ALLOWED_ACTIONS = [
    "optimize_within_available_budget",
    "optimize_all_with_shortage_analysis",
    "cancel_and_update_budget",
]

CURRENCY_SYMBOLS: Dict[str, str] = {
    "IRR": "ریال",
    "USD": "$",
    "EUR": "€",
    "AED": "د.إ",
    "CNY": "¥",
    "TRY": "₺",
}


def get_currency_symbol(currency: Optional[str]) -> str:
    code = _normalize_currency(currency)
    return CURRENCY_SYMBOLS.get(code, code)


@dataclass
class ScenarioCandidate:
    project_item_id: int
    project_id: int
    item_code: str
    item_name: Optional[str]
    source: str
    source_id: str
    total_cost_irr: Optional[Decimal]
    costs_by_currency: Dict[str, Decimal]
    purchase_date: Optional[date]


def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def _normalize_currency(value: Optional[str]) -> str:
    if not value:
        return "IRR"
    normalized = value.strip().upper()
    return normalized or "IRR"


def _period_key(value: Optional[date]) -> str:
    ref = value or date.today()
    return ref.strftime("%Y-%m")


def _safe_date(value: Any) -> Optional[date]:
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


async def _load_budget_capacity(
    db: AsyncSession,
) -> Tuple[Dict[str, Decimal], Dict[str, Decimal], List[str], Dict[str, Decimal], Dict[str, Dict[str, Decimal]]]:
    """
    Returns:
        totals_by_currency,
        totals_by_period_irr,
        warnings,
        available_irr_by_currency_converted,
        period_currency_totals
    """
    budgets_result = await db.execute(select(BudgetData).order_by(BudgetData.budget_date.asc()))
    budgets = budgets_result.scalars().all()

    totals_by_currency: Dict[str, Decimal] = {}
    period_currency_totals: Dict[str, Dict[str, Decimal]] = {}
    totals_by_period_irr: Dict[str, Decimal] = {}
    converted_available_by_currency: Dict[str, Decimal] = {}
    warnings: List[str] = []
    conversion_service = CurrencyConversionService(db)

    for budget in budgets:
        budget_date = budget.budget_date or date.today()
        period = _period_key(budget_date)
        period_currency_totals.setdefault(period, {})

        if budget.multi_currency_budget:
            payload = budget.multi_currency_budget
            if isinstance(payload, str):
                import json

                payload = json.loads(payload)
            currency_amounts = {
                _normalize_currency(code): _as_decimal(amount)
                for code, amount in (payload or {}).items()
            }
        else:
            currency_amounts = {"IRR": _as_decimal(budget.available_budget)}

        for currency, amount in currency_amounts.items():
            totals_by_currency[currency] = totals_by_currency.get(currency, Decimal("0")) + amount
            period_currency_totals[period][currency] = (
                period_currency_totals[period].get(currency, Decimal("0")) + amount
            )

            if currency == "IRR":
                totals_by_period_irr[period] = totals_by_period_irr.get(period, Decimal("0")) + amount
                converted_available_by_currency["IRR"] = converted_available_by_currency.get(
                    "IRR", Decimal("0")
                ) + amount
                continue

            try:
                converted = await conversion_service.convert_to_base(
                    amount, currency, budget_date
                )
                totals_by_period_irr[period] = totals_by_period_irr.get(period, Decimal("0")) + converted
                converted_available_by_currency[currency] = converted_available_by_currency.get(
                    currency, Decimal("0")
                ) + converted
            except ValueError as ex:
                warnings.append(
                    f"Budget conversion warning for {currency} on {budget_date}: {str(ex)}"
                )

    return (
        totals_by_currency,
        totals_by_period_irr,
        sorted(set(warnings)),
        converted_available_by_currency,
        period_currency_totals,
    )


async def _load_eligible_items_with_options(
    db: AsyncSession, project_ids: Optional[List[int]]
) -> Tuple[List[ProjectItem], Dict[int, List[ProcurementOption]]]:
    projects_query = select(Project.id).where(Project.is_active == True)  # noqa: E712
    if project_ids:
        projects_query = projects_query.where(Project.id.in_(project_ids))
    project_id_rows = (await db.execute(projects_query)).all()
    active_project_ids = [int(row[0]) for row in project_id_rows]
    if not active_project_ids:
        return [], {}

    decided_rows = (
        await db.execute(
            select(FinalizedDecision.project_item_id).where(
                FinalizedDecision.status.in_(["LOCKED", "PROPOSED"]),
                FinalizedDecision.project_item_id.is_not(None),
            )
        )
    ).all()
    decided_project_item_ids = {int(row[0]) for row in decided_rows}

    items_query = select(ProjectItem).where(
        ProjectItem.project_id.in_(active_project_ids),
        ProjectItem.is_finalized == True,  # noqa: E712
    )
    all_items = (await db.execute(items_query)).scalars().all()
    candidate_items = [
        item for item in all_items if int(item.id) not in decided_project_item_ids
    ]
    if not candidate_items:
        return [], {}

    item_ids = [int(item.id) for item in candidate_items]
    options_result = await db.execute(
        select(ProcurementOption).where(
            ProcurementOption.project_item_id.in_(item_ids),
            ProcurementOption.is_active == True,  # noqa: E712
            ProcurementOption.is_finalized == True,  # noqa: E712
        )
    )
    options = options_result.scalars().all()
    options_by_item: Dict[int, List[ProcurementOption]] = {}
    for option in options:
        if option.project_item_id is None:
            continue
        options_by_item.setdefault(int(option.project_item_id), []).append(option)

    eligible_items = [item for item in candidate_items if int(item.id) in options_by_item]
    return eligible_items, options_by_item


async def _build_option_candidates_for_item(
    db: AsyncSession,
    project_item: ProjectItem,
    options: Sequence[ProcurementOption],
) -> Tuple[List[ScenarioCandidate], List[str]]:
    conversion_service = CurrencyConversionService(db)
    warnings: List[str] = []
    candidates: List[ScenarioCandidate] = []

    for option in options:
        amount = _as_decimal(option.cost_amount) + _as_decimal(option.shipping_cost)
        currency = _normalize_currency(option.cost_currency)
        tx_date = option.purchase_date or date.today()
        total_irr: Optional[Decimal]

        if currency == "IRR":
            total_irr = amount
        else:
            try:
                total_irr = await conversion_service.convert_to_base(amount, currency, tx_date)
            except ValueError as ex:
                total_irr = None
                warnings.append(
                    f"{project_item.item_code}: Missing exchange rate for option {option.id}: {str(ex)}"
                )

        candidates.append(
            ScenarioCandidate(
                project_item_id=int(project_item.id),
                project_id=int(project_item.project_id),
                item_code=project_item.item_code,
                item_name=project_item.item_name,
                source="option",
                source_id=str(option.id),
                total_cost_irr=total_irr,
                costs_by_currency={currency: amount},
                purchase_date=option.purchase_date,
            )
        )

    return candidates, warnings


async def _build_combination_candidates_for_item(
    db: AsyncSession,
    project_item: ProjectItem,
    options: Sequence[ProcurementOption],
    include_incomplete: bool = False,
) -> Tuple[List[ScenarioCandidate], List[str], int]:
    """
    Builds package-combination alternatives for a project item.
    """
    analysis = await analyze_project_item_package_combinations(
        db,
        project_item_id=int(project_item.id),
    )
    warnings = list(analysis.get("warnings") or [])

    full = list(analysis.get("full_coverage_combinations") or [])
    incomplete = list(analysis.get("incomplete_coverage_combinations") or [])
    selected_raw = full if full else (incomplete if include_incomplete else [])

    if not selected_raw:
        return [], warnings, len(full) + len(incomplete)

    option_map = {int(opt.id): opt for opt in options}
    candidates: List[ScenarioCandidate] = []
    for combo in selected_raw:
        package_ids = [int(v) for v in (combo.get("package_ids") or [])]
        option_ids = [int(v) for v in (combo.get("option_ids") or [])]
        combo_costs = {
            _normalize_currency(code): _as_decimal(amount)
            for code, amount in (combo.get("costs_by_currency") or {}).items()
        }
        total_cost_irr = _as_decimal(combo.get("total_cost_irr")) if combo.get("total_cost_irr") is not None else None

        purchase_dates = []
        for option_id in option_ids:
            option = option_map.get(option_id)
            if option and option.purchase_date:
                purchase_dates.append(option.purchase_date)
        purchase_date = min(purchase_dates) if purchase_dates else None

        candidates.append(
            ScenarioCandidate(
                project_item_id=int(project_item.id),
                project_id=int(project_item.project_id),
                item_code=project_item.item_code,
                item_name=project_item.item_name,
                source="combination",
                source_id="+".join(str(v) for v in sorted(package_ids)) or "combo",
                total_cost_irr=total_cost_irr,
                costs_by_currency=combo_costs or {"IRR": Decimal("0")},
                purchase_date=purchase_date,
            )
        )

    return candidates, warnings, len(full) + len(incomplete)


def _pick_candidate_for_scenario(
    scenario: str, candidates: Sequence[ScenarioCandidate]
) -> Optional[ScenarioCandidate]:
    valid = [c for c in candidates if c.total_cost_irr is not None]
    if not valid:
        return None

    if scenario == "minimum_feasible":
        return min(valid, key=lambda c: (c.total_cost_irr or Decimal("0"), c.source_id))
    if scenario == "conservative":
        return max(valid, key=lambda c: (c.total_cost_irr or Decimal("0"), c.source_id))
    if scenario == "average_candidate":
        total = sum((c.total_cost_irr or Decimal("0")) for c in valid)
        avg = (total / Decimal(len(valid))) if valid else Decimal("0")
        head = valid[0]
        return ScenarioCandidate(
            project_item_id=head.project_item_id,
            project_id=head.project_id,
            item_code=head.item_code,
            item_name=head.item_name,
            source="scenario_average",
            source_id="average",
            total_cost_irr=avg,
            costs_by_currency={"IRR": avg},
            purchase_date=head.purchase_date,
        )
    return valid[0]


def _build_period_rows(
    required_by_period_irr: Dict[str, Decimal], available_by_period_irr: Dict[str, Decimal]
) -> List[OptimizationFinancialPeriod]:
    periods = sorted(set(required_by_period_irr.keys()) | set(available_by_period_irr.keys()))
    rows: List[OptimizationFinancialPeriod] = []
    for period in periods:
        required = required_by_period_irr.get(period, Decimal("0"))
        available = available_by_period_irr.get(period, Decimal("0"))
        gap = available - required
        rows.append(
            OptimizationFinancialPeriod(
                period=period,
                required_irr=required,
                available_irr=available,
                gap_irr=gap,
                status="OK" if gap >= 0 else "WARNING",
            )
        )
    return rows


def _derive_budget_status(required_irr: Decimal, available_irr: Decimal) -> str:
    if required_irr <= available_irr:
        return "OK"
    shortage = required_irr - available_irr
    if required_irr <= 0:
        return "WARNING"
    ratio = shortage / required_irr
    return "CRITICAL" if ratio >= Decimal("0.25") else "WARNING"


def _serialize_top_contributors(
    candidates: Iterable[ScenarioCandidate],
) -> List[Dict[str, Any]]:
    ranked = sorted(
        [c for c in candidates if c.total_cost_irr is not None],
        key=lambda c: c.total_cost_irr or Decimal("0"),
        reverse=True,
    )
    output: List[Dict[str, Any]] = []
    for candidate in ranked[:10]:
        output.append(
            {
                "project_item_id": candidate.project_item_id,
                "item_code": candidate.item_code,
                "source": candidate.source,
                "source_id": candidate.source_id,
                "required_irr": candidate.total_cost_irr,
            }
        )
    return output


def _build_recommendations(status: str) -> List[str]:
    if status == "OK":
        return [
            "Budget is sufficient for the selected scenario.",
            "Optimization can proceed without budget shortage risk.",
        ]
    return [
        "Run constrained optimization to stay within available budget.",
        "Run allow-shortage optimization to view full operational result with financial deficit details.",
        "Update budget allocations for shortage periods and currencies.",
    ]


async def build_optimization_budget_analysis(
    db: AsyncSession,
    *,
    scenario: str = "minimum_feasible",
    budget_mode: str = "analysis_only",
    project_ids: Optional[List[int]] = None,
    include_incomplete: bool = False,
    run_id: Optional[str] = None,
) -> OptimizationFinancialAnalysis:
    scenario_normalized = (scenario or "minimum_feasible").strip().lower()
    if scenario_normalized not in ALLOWED_SCENARIOS:
        scenario_normalized = "minimum_feasible"

    if scenario_normalized == "selected_result":
        return await analyze_optimization_run_financial(
            db,
            run_id=run_id,
            budget_mode=budget_mode,
        )

    eligible_items, options_by_item = await _load_eligible_items_with_options(db, project_ids)
    available_by_currency, available_by_period_irr, budget_warnings, _, _ = await _load_budget_capacity(db)
    available_irr = sum(available_by_period_irr.values()) if available_by_period_irr else Decimal("0")

    required_by_currency: Dict[str, Decimal] = {}
    required_by_period_irr: Dict[str, Decimal] = {}
    selected_candidates: List[ScenarioCandidate] = []
    warnings: List[str] = list(budget_warnings)
    candidate_count = 0
    combination_count = 0
    missing_candidates = 0

    for item in eligible_items:
        options = options_by_item.get(int(item.id), [])
        option_candidates, option_warnings = await _build_option_candidates_for_item(
            db, item, options
        )
        combo_candidates, combo_warnings, combo_count = await _build_combination_candidates_for_item(
            db,
            item,
            options,
            include_incomplete=include_incomplete,
        )
        warnings.extend(option_warnings)
        warnings.extend(combo_warnings)
        combination_count += combo_count

        # If package combinations exist, treat combinations as the candidate alternatives.
        item_candidates = combo_candidates if combo_candidates else option_candidates
        candidate_count += len(item_candidates)
        selected = _pick_candidate_for_scenario(scenario_normalized, item_candidates)
        if selected is None:
            missing_candidates += 1
            warnings.append(
                f"{item.item_code}: no eligible candidate with valid IRR conversion for scenario '{scenario_normalized}'"
            )
            continue

        selected_candidates.append(selected)
        for currency, amount in selected.costs_by_currency.items():
            required_by_currency[currency] = required_by_currency.get(currency, Decimal("0")) + _as_decimal(amount)
        if selected.total_cost_irr is not None:
            period = _period_key(selected.purchase_date)
            required_by_period_irr[period] = required_by_period_irr.get(period, Decimal("0")) + selected.total_cost_irr

    required_irr = sum(
        (candidate.total_cost_irr or Decimal("0")) for candidate in selected_candidates
    )
    surplus_or_shortage = available_irr - required_irr
    budget_status = _derive_budget_status(required_irr, available_irr)
    periods = _build_period_rows(required_by_period_irr, available_by_period_irr)
    recommendations = _build_recommendations(budget_status)

    shortage_abs = abs(surplus_or_shortage)
    if budget_status == "OK":
        narrative = (
            f"Scenario '{scenario_normalized}' requires {required_irr:,.2f} IRR and "
            f"available budget is {available_irr:,.2f} IRR. No shortage is detected."
        )
    else:
        narrative = (
            f"Scenario '{scenario_normalized}' requires {required_irr:,.2f} IRR while available budget is "
            f"{available_irr:,.2f} IRR. Shortage is {shortage_abs:,.2f} IRR and optimization can continue by user choice."
        )

    return OptimizationFinancialAnalysis(
        scenario=scenario_normalized,
        base_currency="IRR",
        budget_mode=budget_mode,
        items_analyzed=len(eligible_items),
        items_with_no_valid_candidate=missing_candidates,
        candidate_count=candidate_count,
        combination_count=combination_count,
        double_count_prevented=True,
        budget_required_irr=required_irr,
        budget_available_irr=available_irr,
        surplus_or_shortage_irr=surplus_or_shortage,
        budget_status=budget_status,
        is_blocking=False,
        can_continue_with_warning=True,
        allowed_actions=ALLOWED_ACTIONS,
        budget_required_by_currency=required_by_currency,
        budget_available_by_currency=available_by_currency,
        periods=periods,
        top_shortage_contributors=_serialize_top_contributors(selected_candidates),
        warnings=sorted(set(warnings)),
        recommendations=recommendations,
        narrative_report=narrative,
    )


async def _build_candidates_from_result_rows(
    db: AsyncSession, result_rows: Sequence[OptimizationResult]
) -> Tuple[List[ScenarioCandidate], List[str]]:
    warnings: List[str] = []
    if not result_rows:
        return [], warnings

    option_ids = [int(row.procurement_option_id) for row in result_rows]
    options_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id.in_(option_ids))
    )
    option_map = {int(opt.id): opt for opt in options_result.scalars().all()}
    conversion_service = CurrencyConversionService(db)
    candidates: List[ScenarioCandidate] = []

    for row in result_rows:
        option = option_map.get(int(row.procurement_option_id))
        if not option:
            warnings.append(
                f"Optimization result {row.id} references missing procurement option {row.procurement_option_id}"
            )
            continue
        amount = _as_decimal(option.cost_amount) + _as_decimal(option.shipping_cost)
        currency = _normalize_currency(option.cost_currency)
        tx_date = option.purchase_date or date.today()
        total_irr: Optional[Decimal] = None
        if currency == "IRR":
            total_irr = amount
        else:
            try:
                total_irr = await conversion_service.convert_to_base(amount, currency, tx_date)
            except ValueError as ex:
                warnings.append(
                    f"{row.item_code}: Missing exchange rate for {currency}: {str(ex)}"
                )

        candidates.append(
            ScenarioCandidate(
                project_item_id=int(option.project_item_id or 0),
                project_id=int(row.project_id or 0),
                item_code=row.item_code,
                item_name=None,
                source="selected_result",
                source_id=str(row.id),
                total_cost_irr=total_irr,
                costs_by_currency={currency: amount},
                purchase_date=option.purchase_date,
            )
        )

    return candidates, warnings


def _analysis_from_candidates(
    *,
    scenario: str,
    budget_mode: str,
    candidates: Sequence[ScenarioCandidate],
    available_by_currency: Dict[str, Decimal],
    available_by_period_irr: Dict[str, Decimal],
    extra_warnings: Sequence[str],
) -> OptimizationFinancialAnalysis:
    required_by_currency: Dict[str, Decimal] = {}
    required_by_period_irr: Dict[str, Decimal] = {}
    valid_candidates = [c for c in candidates if c.total_cost_irr is not None]
    missing = len(candidates) - len(valid_candidates)

    for candidate in valid_candidates:
        for currency, amount in candidate.costs_by_currency.items():
            required_by_currency[currency] = required_by_currency.get(currency, Decimal("0")) + _as_decimal(amount)
        period = _period_key(candidate.purchase_date)
        required_by_period_irr[period] = required_by_period_irr.get(period, Decimal("0")) + (
            candidate.total_cost_irr or Decimal("0")
        )

    required_irr = sum((c.total_cost_irr or Decimal("0")) for c in valid_candidates)
    available_irr = sum(available_by_period_irr.values()) if available_by_period_irr else Decimal("0")
    surplus_or_shortage = available_irr - required_irr
    budget_status = _derive_budget_status(required_irr, available_irr)
    periods = _build_period_rows(required_by_period_irr, available_by_period_irr)
    warnings = sorted(set(extra_warnings))

    if not candidates:
        warnings.append("No selected optimization result exists yet.")

    return OptimizationFinancialAnalysis(
        scenario=scenario,
        base_currency="IRR",
        budget_mode=budget_mode,
        items_analyzed=len(candidates),
        items_with_no_valid_candidate=missing,
        candidate_count=len(candidates),
        combination_count=0,
        double_count_prevented=True,
        budget_required_irr=required_irr,
        budget_available_irr=available_irr,
        surplus_or_shortage_irr=surplus_or_shortage,
        budget_status=budget_status if candidates else "WARNING",
        is_blocking=False,
        can_continue_with_warning=True,
        allowed_actions=ALLOWED_ACTIONS,
        budget_required_by_currency=required_by_currency,
        budget_available_by_currency=available_by_currency,
        periods=periods,
        top_shortage_contributors=_serialize_top_contributors(valid_candidates),
        warnings=warnings,
        recommendations=_build_recommendations(budget_status if candidates else "WARNING"),
        narrative_report=(
            "No selected optimization result exists yet."
            if not candidates
            else (
                f"Selected result requires {required_irr:,.2f} IRR and available budget is "
                f"{available_irr:,.2f} IRR."
            )
        ),
    )


async def analyze_optimization_run_financial(
    db: AsyncSession,
    *,
    run_id: Optional[str],
    budget_mode: str = "analysis_only",
) -> OptimizationFinancialAnalysis:
    available_by_currency, available_by_period_irr, warnings, _, _ = await _load_budget_capacity(db)

    resolved_run_id: Optional[uuid.UUID] = None
    if run_id:
        try:
            resolved_run_id = uuid.UUID(str(run_id))
        except ValueError:
            warnings.append(f"Invalid run_id format: {run_id}")
    else:
        latest_result = await db.execute(
            select(OptimizationResult.run_id)
            .order_by(OptimizationResult.run_timestamp.desc())
            .limit(1)
        )
        latest_row = latest_result.first()
        if latest_row and latest_row[0]:
            resolved_run_id = latest_row[0]

    result_rows: List[OptimizationResult] = []
    if resolved_run_id:
        result_rows = (
            await db.execute(
                select(OptimizationResult).where(OptimizationResult.run_id == resolved_run_id)
            )
        ).scalars().all()

    candidates, candidate_warnings = await _build_candidates_from_result_rows(db, result_rows)
    warnings.extend(candidate_warnings)
    return _analysis_from_candidates(
        scenario="selected_result",
        budget_mode=budget_mode,
        candidates=candidates,
        available_by_currency=available_by_currency,
        available_by_period_irr=available_by_period_irr,
        extra_warnings=warnings,
    )


async def analyze_proposal_decisions_financial(
    db: AsyncSession,
    *,
    decisions: Sequence[Dict[str, Any]],
    budget_mode: str = "analysis_only",
) -> OptimizationFinancialAnalysis:
    available_by_currency, available_by_period_irr, warnings, _, _ = await _load_budget_capacity(db)
    conversion_service = CurrencyConversionService(db)
    candidates: List[ScenarioCandidate] = []

    option_ids = [
        int(decision.get("procurement_option_id"))
        for decision in decisions
        if decision.get("procurement_option_id") is not None
    ]
    option_map: Dict[int, ProcurementOption] = {}
    if option_ids:
        option_rows = await db.execute(
            select(ProcurementOption).where(ProcurementOption.id.in_(option_ids))
        )
        option_map = {int(opt.id): opt for opt in option_rows.scalars().all()}

    for idx, decision in enumerate(decisions):
        option_id_raw = decision.get("procurement_option_id")
        item_code = str(decision.get("item_code") or f"ITEM-{idx+1}")
        if option_id_raw is None:
            warnings.append(f"{item_code}: decision has no procurement_option_id")
            continue

        option = option_map.get(int(option_id_raw))
        if option is None:
            warnings.append(f"{item_code}: procurement option {option_id_raw} not found")
            continue

        quantity = int(decision.get("quantity") or 1)
        amount = (_as_decimal(option.cost_amount) + _as_decimal(option.shipping_cost)) * Decimal(quantity)
        currency = _normalize_currency(option.cost_currency)
        purchase_date = _safe_date(decision.get("purchase_date")) or option.purchase_date or date.today()
        total_irr: Optional[Decimal]
        if currency == "IRR":
            total_irr = amount
        else:
            try:
                total_irr = await conversion_service.convert_to_base(amount, currency, purchase_date)
            except ValueError as ex:
                total_irr = None
                warnings.append(f"{item_code}: Missing exchange rate for {currency}: {str(ex)}")

        candidates.append(
            ScenarioCandidate(
                project_item_id=int(decision.get("project_item_id") or option.project_item_id or 0),
                project_id=int(decision.get("project_id") or 0),
                item_code=item_code,
                item_name=decision.get("item_name"),
                source="proposal",
                source_id=str(option.id),
                total_cost_irr=total_irr,
                costs_by_currency={currency: amount},
                purchase_date=purchase_date,
            )
        )

    return _analysis_from_candidates(
        scenario="selected_result",
        budget_mode=budget_mode,
        candidates=candidates,
        available_by_currency=available_by_currency,
        available_by_period_irr=available_by_period_irr,
        extra_warnings=warnings,
    )


async def select_decisions_within_budget(
    db: AsyncSession,
    *,
    decisions: Sequence[Dict[str, Any]],
    available_budget_irr: Decimal,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Greedy fallback for constrained mode:
    keep lowest-cost IRR decisions first until available budget is exhausted.
    """
    conversion_service = CurrencyConversionService(db)

    option_ids = [
        int(decision.get("procurement_option_id"))
        for decision in decisions
        if decision.get("procurement_option_id") is not None
    ]
    option_map: Dict[int, ProcurementOption] = {}
    if option_ids:
        option_rows = await db.execute(
            select(ProcurementOption).where(ProcurementOption.id.in_(option_ids))
        )
        option_map = {int(opt.id): opt for opt in option_rows.scalars().all()}

    scored: List[Tuple[Decimal, Dict[str, Any], Optional[str]]] = []
    deferred: List[Dict[str, Any]] = []
    for decision in decisions:
        option_id_raw = decision.get("procurement_option_id")
        if option_id_raw is None:
            deferred.append({**decision, "defer_reason": "missing_procurement_option"})
            continue
        option = option_map.get(int(option_id_raw))
        if option is None:
            deferred.append({**decision, "defer_reason": "missing_procurement_option"})
            continue

        quantity = int(decision.get("quantity") or 1)
        currency = _normalize_currency(option.cost_currency)
        purchase_date = _safe_date(decision.get("purchase_date")) or option.purchase_date or date.today()
        amount = (_as_decimal(option.cost_amount) + _as_decimal(option.shipping_cost)) * Decimal(quantity)
        try:
            amount_irr = (
                amount
                if currency == "IRR"
                else await conversion_service.convert_to_base(amount, currency, purchase_date)
            )
        except ValueError:
            deferred.append({**decision, "defer_reason": "missing_exchange_rate"})
            continue
        scored.append((amount_irr, dict(decision), None))

    scored.sort(key=lambda row: row[0])
    used = Decimal("0")
    kept: List[Dict[str, Any]] = []
    for cost_irr, decision, _ in scored:
        if used + cost_irr <= available_budget_irr:
            kept.append(decision)
            used += cost_irr
        else:
            deferred.append({**decision, "defer_reason": "insufficient_budget"})

    return kept, deferred

