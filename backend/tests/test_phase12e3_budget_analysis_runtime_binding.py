from datetime import date
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BudgetData, OptimizationResult, ProcurementOption, Project, ProjectItem
from app.services.optimization_budget_service import (
    analyze_optimization_run_financial,
    build_optimization_budget_analysis,
)


async def _create_item(db: AsyncSession, project_code: str, item_code: str) -> ProjectItem:
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


async def _add_option(db: AsyncSession, item: ProjectItem, supplier: str, cost: Decimal) -> ProcurementOption:
    option = ProcurementOption(
        item_code=item.item_code,
        project_item_id=item.id,
        supplier_name=supplier,
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
async def test_phase12e3_test_a_endpoint_scenarios_change_full_body_when_data_supports(
    db_session: AsyncSession,
):
    item = await _create_item(db_session, "P12E3-A", "ITEM-A")
    await _add_option(db_session, item, "S-1", Decimal("100"))
    await _add_option(db_session, item, "S-2", Decimal("120"))
    await _add_option(db_session, item, "S-3", Decimal("140"))
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    minimum = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    average = await build_optimization_budget_analysis(db_session, scenario="average_candidate")
    worst = await build_optimization_budget_analysis(db_session, scenario="worst_case")

    assert minimum.budget_required_irr == Decimal("100")
    assert average.budget_required_irr == Decimal("120")
    assert worst.budget_required_irr == Decimal("140")
    assert minimum.narrative_report != average.narrative_report
    assert average.narrative_report != worst.narrative_report
    assert sum(p.required_irr for p in minimum.periods) == minimum.budget_required_irr
    assert sum(p.required_irr for p in average.periods) == average.budget_required_irr
    assert sum(p.required_irr for p in worst.periods) == worst.budget_required_irr


@pytest.mark.asyncio
async def test_phase12e3_test_b_no_legacy_field_leakage_in_canonical_analysis(
    db_session: AsyncSession,
):
    item = await _create_item(db_session, "P12E3-B", "ITEM-B")
    await _add_option(db_session, item, "S-1", Decimal("100"))
    await _add_budget(db_session, Decimal("1000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    payload = result.model_dump(mode="json")

    assert payload["scenario"] == "minimum_feasible"
    assert "budget_required_by_currency" in payload
    assert "surplus_shortage_by_currency" in payload
    assert "selected_scenario_candidates" in payload
    assert "charts" in payload
    assert "total_needed_by_currency" not in payload
    assert "critical_months" not in payload
    assert "optimization_semantics" not in payload


@pytest.mark.asyncio
async def test_phase12e3_test_c_selected_result_uses_selected_candidates_only(
    db_session: AsyncSession,
):
    item = await _create_item(db_session, "P12E3-C", "ITEM-C")
    opt_a = await _add_option(db_session, item, "A", Decimal("100"))
    opt_b = await _add_option(db_session, item, "B", Decimal("140"))
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
    assert analysis_a.optimization_result_id == str(run_a)
    assert analysis_b.optimization_result_id == str(run_b)
    assert analysis_a.analysis_scope == "optimization_result"
    assert analysis_b.analysis_scope == "optimization_result"


@pytest.mark.asyncio
async def test_phase12e3_test_d_numeric_consistency_across_summary_period_chart_and_narrative(
    db_session: AsyncSession,
):
    item = await _create_item(db_session, "P12E3-D", "ITEM-D")
    await _add_option(db_session, item, "S-1", Decimal("450000000"))
    await _add_budget(db_session, Decimal("500000000"))
    await db_session.commit()

    result = await build_optimization_budget_analysis(db_session, scenario="minimum_feasible")
    periods_total = sum(row.required_irr for row in result.periods)
    charts_total = sum(row["required_irr"] for row in result.charts.get("periods", []))
    selected_total = sum(row["required_irr"] for row in result.selected_scenario_candidates)

    assert result.budget_required_irr == periods_total == charts_total == selected_total
    assert f"{result.budget_required_irr:,.2f}" in (result.narrative_report or "")
