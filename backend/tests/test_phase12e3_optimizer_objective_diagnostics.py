from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BudgetData, ProcurementOption, Project, ProjectItem
from app.optimization_engine_enhanced import (
    EnhancedProcurementOptimizer,
    OptimizationStrategy,
    SolverType,
)
from app.schemas import OptimizationDecision, OptimizationProposal, OptimizationRunRequest
from app.services.optimization_budget_service import analyze_proposal_decisions_financial


def _make_decision(option_id: int, cost: Decimal, item_code: str = "ITEM-1") -> OptimizationDecision:
    return OptimizationDecision(
        project_id=1,
        project_code="P1",
        item_code=item_code,
        item_name=item_code,
        procurement_option_id=option_id,
        supplier_name="SUP",
        purchase_date=date(2026, 6, 1),
        delivery_date=date(2026, 6, 15),
        quantity=1,
        unit_cost=cost,
        final_cost=cost,
        payment_terms="cash",
        project_item_id=1,
    )


@pytest.mark.asyncio
async def test_phase12e3_test_e_objective_mode_strategies_are_accepted_and_reflected_in_response():
    optimizer = EnhancedProcurementOptimizer(db=None, solver_type=SolverType.CP_SAT, budget_mode="allow_shortage")
    request = OptimizationRunRequest(max_time_slots=12, time_limit_seconds=30, require_all_items=False)

    async def fake_load_data():
        return None

    def fake_build_dependency_graph():
        return None

    async def fake_generate_multiple_proposals(_request, strategies):
        assert strategies == [OptimizationStrategy.LOWEST_COST, OptimizationStrategy.SMOOTH_CASHFLOW]
        return [
            OptimizationProposal(
                proposal_name="Lowest Cost",
                strategy_type="LOWEST_COST",
                total_cost=Decimal("100"),
                weighted_cost=Decimal("100"),
                status="OPTIMAL",
                items_count=1,
                decisions=[_make_decision(1, Decimal("100"), "ITEM-A")],
            ),
            OptimizationProposal(
                proposal_name="Smooth Cashflow",
                strategy_type="SMOOTH_CASHFLOW",
                total_cost=Decimal("110"),
                weighted_cost=Decimal("110"),
                status="FEASIBLE",
                items_count=1,
                decisions=[_make_decision(2, Decimal("110"), "ITEM-A")],
            ),
        ]

    async def fake_save_run(_request, _status, _proposals):
        return None

    async def fake_save_results(_proposals):
        return None

    optimizer._load_data = fake_load_data
    optimizer._build_dependency_graph = fake_build_dependency_graph
    optimizer._generate_multiple_proposals = fake_generate_multiple_proposals
    optimizer._save_optimization_run = fake_save_run
    optimizer._save_optimization_results = fake_save_results

    response = await optimizer.run_optimization(
        request,
        generate_multiple_proposals=True,
        strategies=[OptimizationStrategy.LOWEST_COST, OptimizationStrategy.SMOOTH_CASHFLOW],
    )

    assert response.status == "OPTIMAL"
    assert response.total_cost == Decimal("100")
    assert response.items_optimized == 1
    assert len(response.proposals) == 2
    assert response.diagnostics["budget_mode"] == "allow_shortage"
    assert response.diagnostics["budget_constraints_enabled"] is False


async def _create_item_with_two_options(db: AsyncSession) -> tuple[ProjectItem, ProcurementOption, ProcurementOption]:
    project = Project(project_code="P12E3-OPT", name="P12E3-OPT", is_active=True)
    db.add(project)
    await db.flush()
    item = ProjectItem(
        project_id=project.id,
        item_code="ITEM-OPT",
        item_name="ITEM-OPT",
        quantity=1,
        delivery_options=[],
        status="PENDING",
        is_finalized=True,
    )
    db.add(item)
    await db.flush()
    option_1 = ProcurementOption(
        item_code=item.item_code,
        project_item_id=item.id,
        supplier_name="SUP-A",
        cost_amount=Decimal("100"),
        cost_currency="IRR",
        shipping_cost=Decimal("0"),
        lomc_lead_time=0,
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
        purchase_date=date(2026, 6, 1),
        expected_delivery_date=date(2026, 6, 15),
    )
    option_2 = ProcurementOption(
        item_code=item.item_code,
        project_item_id=item.id,
        supplier_name="SUP-B",
        cost_amount=Decimal("60"),
        cost_currency="IRR",
        shipping_cost=Decimal("0"),
        lomc_lead_time=0,
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
        purchase_date=date(2026, 6, 1),
        expected_delivery_date=date(2026, 6, 15),
    )
    db.add_all([option_1, option_2])
    db.add(
        BudgetData(
            budget_date=date(2026, 6, 1),
            available_budget=Decimal("1000"),
            multi_currency_budget={"IRR": 1000.0},
        )
    )
    await db.flush()
    return item, option_1, option_2


@pytest.mark.asyncio
async def test_phase12e3_test_f_financial_summary_recomputes_when_decisions_change(db_session: AsyncSession):
    item, option_1, option_2 = await _create_item_with_two_options(db_session)
    await db_session.commit()

    full_decisions = [
        {
            "project_id": item.project_id,
            "project_item_id": item.id,
            "item_code": item.item_code,
            "procurement_option_id": option_1.id,
            "purchase_date": "2026-06-01",
            "quantity": 1,
        },
        {
            "project_id": item.project_id,
            "project_item_id": item.id,
            "item_code": f"{item.item_code}-ALT",
            "procurement_option_id": option_2.id,
            "purchase_date": "2026-06-01",
            "quantity": 1,
        },
    ]
    reduced_decisions = [full_decisions[1]]

    full_analysis = await analyze_proposal_decisions_financial(db_session, decisions=full_decisions)
    reduced_analysis = await analyze_proposal_decisions_financial(db_session, decisions=reduced_decisions)

    assert full_analysis.budget_required_irr == Decimal("160")
    assert reduced_analysis.budget_required_irr == Decimal("60")
    assert reduced_analysis.budget_required_irr < full_analysis.budget_required_irr
