from __future__ import annotations

import json
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BudgetData, ExchangeRate, OptimizationResult, ProcurementOption, Project, ProjectItem
from app.services.optimization_budget_service import (
    analyze_optimization_run_financial,
    analyze_proposal_decisions_financial,
    build_optimization_budget_analysis,
)


async def _create_item(db: AsyncSession, project_code: str, item_code: str, quantity: int = 1) -> ProjectItem:
    project = Project(project_code=project_code, name=project_code, is_active=True)
    db.add(project)
    await db.flush()
    item = ProjectItem(
        project_id=project.id,
        item_code=item_code,
        item_name=item_code,
        quantity=quantity,
        delivery_options=[],
        status="PENDING",
        is_finalized=True,
    )
    db.add(item)
    await db.flush()
    return item


async def _add_option(
    db: AsyncSession,
    *,
    item: ProjectItem,
    supplier_name: str,
    cost: Decimal,
    currency: str = "IRR",
    payment_terms: dict | None = None,
    purchase_date: date = date(2026, 6, 1),
) -> ProcurementOption:
    option = ProcurementOption(
        item_code=item.item_code,
        project_item_id=item.id,
        supplier_name=supplier_name,
        cost_amount=cost,
        cost_currency=currency,
        shipping_cost=Decimal("0"),
        lomc_lead_time=0,
        payment_terms=payment_terms or {"type": "cash"},
        is_active=True,
        is_finalized=True,
        purchase_date=purchase_date,
        expected_delivery_date=date(2026, 6, 15),
    )
    db.add(option)
    await db.flush()
    return option


async def _add_budget(db: AsyncSession, amount: Decimal, budget_date: date = date(2026, 6, 1)) -> None:
    db.add(
        BudgetData(
            budget_date=budget_date,
            available_budget=amount,
            multi_currency_budget={"IRR": float(amount)},
        )
    )
    await db.flush()


@pytest.mark.asyncio
async def test_phase12e4_test_a_selected_result_financial_views_match(db_session: AsyncSession):
    item = await _create_item(db_session, "P12E4-A", "ITEM-A")
    selected = await _add_option(db_session, item=item, supplier_name="SUP-A", cost=Decimal("100"))
    _ = await _add_option(db_session, item=item, supplier_name="SUP-B", cost=Decimal("140"))
    await _add_budget(db_session, Decimal("1000"))
    run_id = uuid.uuid4()
    db_session.add(
        OptimizationResult(
            run_id=run_id,
            project_id=item.project_id,
            item_code=item.item_code,
            procurement_option_id=selected.id,
            purchase_time=1,
            delivery_time=1,
            quantity=1,
            final_cost=Decimal("100"),
        )
    )
    await db_session.commit()

    panel = await analyze_optimization_run_financial(db_session, run_id=str(run_id))
    tab = await build_optimization_budget_analysis(
        db_session,
        scenario="selected_result",
        run_id=str(run_id),
    )

    assert panel.total_purchase_cost_irr == Decimal("100")
    assert panel.budget_required_irr == Decimal("100")
    assert tab.budget_required_irr == Decimal("100")
    assert tab.budget_required_by_currency["IRR"] == Decimal("100")
    assert sum(row.required_irr for row in tab.periods) == Decimal("100")
    assert all(int(line["selected_candidate_id"]) == int(selected.id) for line in tab.trace_lines)


@pytest.mark.asyncio
async def test_phase12e4_test_b_weighted_objective_cost_is_distinct_from_purchase_cost(
    db_session: AsyncSession,
):
    item = await _create_item(db_session, "P12E4-B", "ITEM-B")
    option = await _add_option(db_session, item=item, supplier_name="SUP", cost=Decimal("100"))
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    analysis = await analyze_proposal_decisions_financial(
        db_session,
        decisions=[
            {
                "project_id": item.project_id,
                "project_item_id": item.id,
                "item_code": item.item_code,
                "procurement_option_id": option.id,
                "purchase_date": "2026-06-01",
                "quantity": 1,
                "final_cost": 100,
            }
        ],
        weighted_objective_cost_irr=Decimal("240"),
    )

    assert analysis.total_purchase_cost_irr == Decimal("100")
    assert analysis.weighted_objective_cost_irr == Decimal("240")
    assert analysis.total_purchase_cost_irr != analysis.weighted_objective_cost_irr
    assert analysis.reconciliation["weighted_objective_cost_irr"] == Decimal("240")


@pytest.mark.asyncio
async def test_phase12e4_test_c_currency_conversion_is_single_and_labeled_correctly(
    db_session: AsyncSession,
):
    item = await _create_item(db_session, "P12E4-C", "ITEM-C")
    option = await _add_option(
        db_session,
        item=item,
        supplier_name="SUP-USD",
        cost=Decimal("100"),
        currency="USD",
    )
    await _add_budget(db_session, Decimal("100000000"))
    db_session.add(
        ExchangeRate(
            date=date(2026, 6, 1),
            from_currency="USD",
            to_currency="IRR",
            rate=Decimal("600000"),
            is_active=True,
        )
    )
    run_id = uuid.uuid4()
    db_session.add(
        OptimizationResult(
            run_id=run_id,
            project_id=item.project_id,
            item_code=item.item_code,
            procurement_option_id=option.id,
            purchase_time=1,
            delivery_time=1,
            quantity=1,
            final_cost=Decimal("100"),
        )
    )
    await db_session.commit()

    analysis = await analyze_optimization_run_financial(db_session, run_id=str(run_id))

    assert analysis.budget_required_by_currency["USD"] == Decimal("100")
    assert analysis.budget_required_irr == Decimal("60000000")
    assert analysis.trace_lines[0]["currency"] == "USD"
    assert Decimal(str(analysis.trace_lines[0]["payment_amount_original"])) == Decimal("100")
    assert Decimal(str(analysis.trace_lines[0]["payment_amount_irr"])) == Decimal("60000000")


@pytest.mark.asyncio
async def test_phase12e4_test_d_period_allocation_uses_schedule_without_duplication(db_session: AsyncSession):
    item = await _create_item(db_session, "P12E4-D", "ITEM-D")
    option = await _add_option(
        db_session,
        item=item,
        supplier_name="SUP-SPLIT",
        cost=Decimal("100"),
        payment_terms={
            "type": "installments",
            "schedule": [{"percent": 30, "due_offset": 0}, {"percent": 70, "due_offset": 30}],
        },
    )
    await _add_budget(db_session, Decimal("1000"), budget_date=date(2026, 6, 1))
    await _add_budget(db_session, Decimal("1000"), budget_date=date(2026, 7, 1))
    run_id = uuid.uuid4()
    db_session.add(
        OptimizationResult(
            run_id=run_id,
            project_id=item.project_id,
            item_code=item.item_code,
            procurement_option_id=option.id,
            purchase_time=1,
            delivery_time=1,
            quantity=1,
            final_cost=Decimal("100"),
        )
    )
    await db_session.commit()

    analysis = await analyze_optimization_run_financial(db_session, run_id=str(run_id))
    by_period = {row.period: row.required_irr for row in analysis.periods}

    assert analysis.budget_required_irr == Decimal("100")
    assert by_period["2026-06"] == Decimal("30")
    assert by_period["2026-07"] == Decimal("70")
    assert sum(row.required_irr for row in analysis.periods) == Decimal("100")


@pytest.mark.asyncio
async def test_phase12e4_test_e_minimum_feasible_uses_single_candidate_trace(db_session: AsyncSession):
    item = await _create_item(db_session, "P12E4-E", "ITEM-E")
    low = await _add_option(db_session, item=item, supplier_name="SUP-1", cost=Decimal("100"))
    await _add_option(db_session, item=item, supplier_name="SUP-2", cost=Decimal("120"))
    await _add_option(db_session, item=item, supplier_name="SUP-3", cost=Decimal("140"))
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    analysis = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")

    assert analysis.budget_required_irr == Decimal("100")
    assert len(analysis.trace_lines) == 1
    assert int(analysis.trace_lines[0]["source_id"]) == int(low.id)
    assert analysis.selected_scenario_candidates[0]["required_irr"] == Decimal("100")


def test_phase12e4_test_f_persian_budget_shortage_modal_labels_exist():
    root = Path(__file__).resolve().parents[2]
    fa_path = root / "frontend" / "src" / "i18n" / "fa.json"
    data = json.loads(fa_path.read_text(encoding="utf-8"))
    opt = data.get("optimization", {})

    assert opt.get("budgetShortageDetected") == "کسری بودجه شناسایی شد"
    assert (
        opt.get("budgetShortageDecisionMessage")
        == "کسری بودجه باید به‌عنوان هشدار و نقطه تصمیم‌گیری نمایش داده شود. روش ادامه را انتخاب کنید."
    )
    assert opt.get("scenario") == "سناریو"
    assert opt.get("budgetStatusLabel") == "وضعیت بودجه"
    assert opt.get("requiredBudget") == "بودجه مورد نیاز"
    assert opt.get("availableBudget") == "بودجه موجود"
    assert opt.get("shortage") == "کسری بودجه"
    assert opt.get("optimizeWithinCurrentBudget") == "ادامه با بودجه موجود"
    assert (
        opt.get("optimizeAllWithShortageAnalysis")
        == "بهینه‌سازی همه اقلام با نمایش تحلیل کسری بودجه"
    )
    assert opt.get("cancelAndUpdateBudget") == "لغو و بازگشت به مدیریت بودجه"
