from datetime import date
from decimal import Decimal
import re
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BudgetData, OptimizationResult, ProcurementOption, Project, ProjectItem
from app.services.optimization_budget_service import (
    analyze_optimization_run_financial,
    build_optimization_budget_analysis,
    get_currency_symbol,
)


async def _create_project_item(
    db: AsyncSession,
    *,
    project_code: str,
    item_code: str,
) -> ProjectItem:
    project = Project(project_code=project_code, name=project_code, is_active=True)
    db.add(project)
    await db.flush()
    item = ProjectItem(
        project_id=project.id,
        item_code=item_code,
        item_name=item_code,
        quantity=1,
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
) -> ProcurementOption:
    option = ProcurementOption(
        item_code=item.item_code,
        project_item_id=item.id,
        supplier_name=supplier_name,
        cost_amount=cost,
        cost_currency="IRR",
        shipping_cost=Decimal("0"),
        lomc_lead_time=0,
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
        purchase_date=date(2026, 6, 1),
        expected_delivery_date=date(2026, 6, 15),
    )
    db.add(option)
    await db.flush()
    return option


async def _add_budget(db: AsyncSession, amount: Decimal) -> None:
    db.add(
        BudgetData(
            budget_date=date(2026, 6, 1),
            available_budget=amount,
            multi_currency_budget={"IRR": float(amount)},
        )
    )
    await db.flush()


@pytest.mark.asyncio
async def test_phase12e2_test_a_scenario_drives_full_response(db_session: AsyncSession):
    item1 = await _create_project_item(db_session, project_code="P12E2-A1", item_code="ITEM-A1")
    item2 = await _create_project_item(db_session, project_code="P12E2-A2", item_code="ITEM-A2")
    for idx, value in enumerate([Decimal("100"), Decimal("120"), Decimal("140")], start=1):
        await _add_option(db_session, item=item1, supplier_name=f"S1-{idx}", cost=value)
    for idx, value in enumerate([Decimal("50"), Decimal("70"), Decimal("90")], start=1):
        await _add_option(db_session, item=item2, supplier_name=f"S2-{idx}", cost=value)
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    minimum = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    average = await build_optimization_budget_analysis(db_session, scenario="average_candidate")
    worst = await build_optimization_budget_analysis(db_session, scenario="worst_case")

    assert minimum.budget_required_irr == Decimal("150")
    assert average.budget_required_irr == Decimal("190")
    assert worst.budget_required_irr == Decimal("230")
    assert len({minimum.budget_required_irr, average.budget_required_irr, worst.budget_required_irr}) == 3
    assert sum(row.required_irr for row in minimum.periods) == minimum.budget_required_irr
    assert sum(row.required_irr for row in average.periods) == average.budget_required_irr
    assert sum(row.required_irr for row in worst.periods) == worst.budget_required_irr
    assert "150.00" in (minimum.narrative_report or "")
    assert "190.00" in (average.narrative_report or "")
    assert "230.00" in (worst.narrative_report or "")


@pytest.mark.asyncio
async def test_phase12e2_test_b_no_double_counting_in_all_sections(db_session: AsyncSession):
    item = await _create_project_item(db_session, project_code="P12E2-B", item_code="ITEM-B")
    await _add_option(db_session, item=item, supplier_name="S-1", cost=Decimal("100"))
    await _add_option(db_session, item=item, supplier_name="S-2", cost=Decimal("120"))
    await _add_option(db_session, item=item, supplier_name="S-3", cost=Decimal("140"))
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")

    assert result.budget_required_irr == Decimal("100")
    assert result.budget_required_by_currency["IRR"] == Decimal("100")
    assert sum(row.required_irr for row in result.periods) == Decimal("100")
    assert sum(row["required_irr"] for row in result.selected_scenario_candidates) == Decimal("100")
    assert "100.00" in (result.narrative_report or "")
    assert "360.00" not in (result.narrative_report or "")


@pytest.mark.asyncio
async def test_phase12e2_test_c_numeric_consistency_across_sections(db_session: AsyncSession):
    item = await _create_project_item(db_session, project_code="P12E2-C", item_code="ITEM-C")
    await _add_option(db_session, item=item, supplier_name="S-1", cost=Decimal("450000000"))
    await _add_budget(db_session, Decimal("500000000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    periods_total = sum(row.required_irr for row in result.periods)
    selected_total = sum(row["required_irr"] for row in result.selected_scenario_candidates)
    charts_total = sum(row["required_irr"] for row in result.charts.get("periods", []))

    assert result.budget_required_irr == periods_total == selected_total == charts_total
    assert f"{result.budget_required_irr:,.2f}" in (result.narrative_report or "")


@pytest.mark.asyncio
async def test_phase12e2_test_d_selected_result_financial_analysis_uses_selected_candidates(
    db_session: AsyncSession,
):
    item = await _create_project_item(db_session, project_code="P12E2-D", item_code="ITEM-D")
    opt_a = await _add_option(db_session, item=item, supplier_name="RUN-A", cost=Decimal("100"))
    opt_b = await _add_option(db_session, item=item, supplier_name="RUN-B", cost=Decimal("140"))
    await _add_budget(db_session, Decimal("1000"))
    run_a = uuid.uuid4()
    run_b = uuid.uuid4()
    db_session.add(
        OptimizationResult(
            run_id=run_a,
            project_id=item.project_id,
            item_code=item.item_code,
            procurement_option_id=opt_a.id,
            purchase_time=1,
            delivery_time=1,
            quantity=1,
            final_cost=Decimal("100"),
        )
    )
    db_session.add(
        OptimizationResult(
            run_id=run_b,
            project_id=item.project_id,
            item_code=item.item_code,
            procurement_option_id=opt_b.id,
            purchase_time=1,
            delivery_time=1,
            quantity=1,
            final_cost=Decimal("140"),
        )
    )
    await db_session.commit()

    analysis_a = await analyze_optimization_run_financial(db_session, run_id=str(run_a))
    analysis_b = await analyze_optimization_run_financial(db_session, run_id=str(run_b))

    assert analysis_a.budget_required_irr == Decimal("100")
    assert analysis_b.budget_required_irr == Decimal("140")
    assert analysis_a.analysis_scope == "optimization_result"
    assert analysis_b.analysis_scope == "optimization_result"
    assert analysis_a.optimization_result_id == str(run_a)
    assert analysis_b.optimization_result_id == str(run_b)
    assert "تحلیل مالی مدل انتخابی" in (analysis_a.narrative_report or "")
    assert "تحلیل مالی مدل انتخابی" in (analysis_b.narrative_report or "")


@pytest.mark.asyncio
async def test_phase12e2_test_e_non_blocking_shortage_language(db_session: AsyncSession):
    item = await _create_project_item(db_session, project_code="P12E2-E", item_code="ITEM-E")
    await _add_option(db_session, item=item, supplier_name="S-E", cost=Decimal("1000"))
    await _add_budget(db_session, Decimal("100"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")

    assert result.budget_status in {"WARNING", "CRITICAL"}
    assert "can continue by user choice" in (result.narrative_report or "")
    assert "قبل از اجرای بهینه‌سازی بودجه اضافه کنید" not in (result.narrative_report or "")
    assert "هنگامی که بودجه کافی شد" not in (result.narrative_report or "")


@pytest.mark.asyncio
async def test_phase12e2_test_f_no_gregorian_periods_leak_in_narrative(db_session: AsyncSession):
    item = await _create_project_item(db_session, project_code="P12E2-F", item_code="ITEM-F")
    option = await _add_option(db_session, item=item, supplier_name="S-F", cost=Decimal("100"))
    await _add_budget(db_session, Decimal("1000"))
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

    scenario_analysis = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    result_analysis = await analyze_optimization_run_financial(db_session, run_id=str(run_id))

    assert not re.search(r"\b\d{4}-\d{2}\b", scenario_analysis.narrative_report or "")
    assert not re.search(r"\b\d{4}-\d{2}\b", result_analysis.narrative_report or "")


def test_phase12e2_test_g_currency_symbol_consistency():
    assert get_currency_symbol("IRR") == "ریال"
    assert get_currency_symbol("USD") == "$"
    assert get_currency_symbol("EUR") == "€"
    assert get_currency_symbol("AED") == "د.إ"
    assert get_currency_symbol("CNY") == "¥"
    assert get_currency_symbol("TRY") == "₺"
