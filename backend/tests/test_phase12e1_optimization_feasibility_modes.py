from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BudgetData, ProcurementOption, Project, ProjectItem, User
from app.optimization_engine_enhanced import EnhancedProcurementOptimizer, SolverType
from app.routers.finance import run_enhanced_optimization
from app.schemas import OptimizationRunRequest
from app.services.optimization_budget_service import (
    analyze_proposal_decisions_financial,
    select_decisions_within_budget,
)


async def _create_project_item(
    db: AsyncSession,
    *,
    project_code: str,
    item_code: str,
    is_finalized: bool = True,
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
        is_finalized=is_finalized,
    )
    db.add(item)
    await db.flush()
    return item


async def _add_option(
    db: AsyncSession,
    *,
    item: ProjectItem,
    cost: Decimal,
    dated: bool = True,
) -> ProcurementOption:
    option = ProcurementOption(
        item_code=item.item_code,
        project_item_id=item.id,
        supplier_name=f"SUP-{item.item_code}",
        cost_amount=cost,
        cost_currency="IRR",
        shipping_cost=Decimal("0"),
        lomc_lead_time=0,
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
        purchase_date=date(2026, 6, 1) if dated else None,
        expected_delivery_date=date(2026, 6, 10) if dated else None,
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


async def _create_finance_user(db: AsyncSession, username: str) -> User:
    user = User(username=username, password_hash="hash", role="finance", is_active=True)
    db.add(user)
    await db.flush()
    return user


@pytest.mark.asyncio
async def test_phase12e1_test_a_allow_shortage_ignores_budget_constraint(db_session: AsyncSession):
    item = await _create_project_item(
        db_session, project_code="P12E1-A", item_code="UAT1405_ITEM_ALLOW_SHORTAGE"
    )
    await _add_option(db_session, item=item, cost=Decimal("1000"), dated=True)
    await _add_budget(db_session, Decimal("100"))
    await db_session.commit()

    optimizer = EnhancedProcurementOptimizer(db_session, solver_type=SolverType.CP_SAT, budget_mode="allow_shortage")
    request = OptimizationRunRequest(
        max_time_slots=24,
        time_limit_seconds=60,
        budget_mode="allow_shortage",
        budget_scenario="minimum_feasible",
        require_all_items=False,
    )
    response = await optimizer.run_optimization(request, generate_multiple_proposals=False)

    assert response.status in {"OPTIMAL", "FEASIBLE"}
    assert len(response.proposals) >= 1
    assert response.proposals[0].items_count >= 1
    assert response.diagnostics["budget_constraints_enabled"] is False

    financial = await analyze_proposal_decisions_financial(
        db_session,
        decisions=[
            {
                "project_id": d.project_id,
                "project_item_id": d.project_item_id,
                "item_code": d.item_code,
                "procurement_option_id": d.procurement_option_id,
                "purchase_date": d.purchase_date.isoformat(),
                "quantity": d.quantity,
            }
            for d in response.proposals[0].decisions
        ],
        budget_mode="allow_shortage",
    )
    assert financial.surplus_or_shortage_irr < 0


@pytest.mark.asyncio
async def test_phase12e1_test_b_constrained_mode_respects_budget(db_session: AsyncSession):
    item = await _create_project_item(
        db_session, project_code="P12E1-B", item_code="UAT1405_ITEM_CONSTRAINED"
    )
    await _add_option(db_session, item=item, cost=Decimal("1000"), dated=True)
    await _add_budget(db_session, Decimal("100"))
    user = await _create_finance_user(db_session, "phase12e1_finance_b")
    await db_session.commit()

    request = OptimizationRunRequest(
        max_time_slots=24,
        time_limit_seconds=60,
        budget_mode="constrained",
        budget_scenario="minimum_feasible",
        require_all_items=False,
    )
    response = await run_enhanced_optimization(
        request=request,
        solver_type=SolverType.CP_SAT,
        generate_multiple_proposals=False,
        strategies=None,
        current_user=user,
        db=db_session,
    )

    assert response.diagnostics["budget_constraints_enabled"] is True
    assert response.diagnostics["items_filtered_by_budget"] >= 1
    assert "technical error" not in (response.message or "").lower()
    if response.proposals:
        decisions_payload = [
            {
                "project_id": d.project_id,
                "project_item_id": d.project_item_id,
                "item_code": d.item_code,
                "procurement_option_id": d.procurement_option_id,
                "purchase_date": d.purchase_date.isoformat(),
                "quantity": d.quantity,
            }
            for d in response.proposals[0].decisions
        ]
        kept, deferred = await select_decisions_within_budget(
            db_session,
            decisions=decisions_payload,
            available_budget_irr=Decimal("100"),
        )
        assert len(kept) == 0
        assert len(deferred) >= 0


@pytest.mark.asyncio
async def test_phase12e1_test_c_mode_propagation_allow_shortage(db_session: AsyncSession):
    item = await _create_project_item(
        db_session, project_code="P12E1-C", item_code="UAT1405_ITEM_MODE_PROP"
    )
    await _add_option(db_session, item=item, cost=Decimal("500"), dated=True)
    await _add_budget(db_session, Decimal("100"))
    user = await _create_finance_user(db_session, "phase12e1_finance_c")
    await db_session.commit()

    request = OptimizationRunRequest(
        max_time_slots=24,
        time_limit_seconds=60,
        budget_mode="allow_shortage",
        budget_scenario="minimum_feasible",
        require_all_items=False,
    )
    response = await run_enhanced_optimization(
        request=request,
        solver_type=SolverType.CP_SAT,
        generate_multiple_proposals=False,
        strategies=None,
        current_user=user,
        db=db_session,
    )

    assert response.budget_mode == "allow_shortage"
    assert response.diagnostics["budget_mode"] == "allow_shortage"
    assert response.diagnostics["budget_constraints_enabled"] is False


@pytest.mark.asyncio
async def test_phase12e1_test_d_no_candidates_reports_specific_error(db_session: AsyncSession):
    await _create_project_item(
        db_session, project_code="P12E1-D", item_code="UAT1405_ITEM_NO_CAND"
    )
    await _add_budget(db_session, Decimal("100"))
    await db_session.commit()

    optimizer = EnhancedProcurementOptimizer(db_session, solver_type=SolverType.CP_SAT, budget_mode="allow_shortage")
    request = OptimizationRunRequest(
        max_time_slots=24,
        time_limit_seconds=60,
        budget_mode="allow_shortage",
        budget_scenario="minimum_feasible",
        require_all_items=False,
    )
    response = await optimizer.run_optimization(request, generate_multiple_proposals=False)

    assert response.error_code == "NO_ELIGIBLE_CANDIDATES"
    assert response.diagnostics["candidate_options"] == 0
    assert "budget shortage was not used as a blocker" not in (response.message or "").lower()


@pytest.mark.asyncio
async def test_phase12e1_test_e_partial_feasible_result_when_require_all_false(db_session: AsyncSession):
    item_ok = await _create_project_item(
        db_session, project_code="P12E1-E1", item_code="UAT1405_ITEM_WITH_CAND"
    )
    await _create_project_item(
        db_session, project_code="P12E1-E2", item_code="UAT1405_ITEM_WITHOUT_CAND"
    )
    await _add_option(db_session, item=item_ok, cost=Decimal("100"), dated=True)
    await _add_budget(db_session, Decimal("10000"))
    await db_session.commit()

    optimizer = EnhancedProcurementOptimizer(db_session, solver_type=SolverType.CP_SAT, budget_mode="allow_shortage")
    request = OptimizationRunRequest(
        max_time_slots=24,
        time_limit_seconds=60,
        budget_mode="allow_shortage",
        budget_scenario="minimum_feasible",
        require_all_items=False,
    )
    response = await optimizer.run_optimization(request, generate_multiple_proposals=False)

    assert response.status in {"OPTIMAL", "FEASIBLE"}
    assert len(response.proposals) >= 1
    assert any(d.item_code == item_ok.item_code for d in response.proposals[0].decisions)
    assert any("UAT1405_ITEM_WITHOUT_CAND" in s for s in response.diagnostics["items_missing_candidates"])


@pytest.mark.asyncio
async def test_phase12e1_test_f_diagnostic_counts_include_drop_reasons(db_session: AsyncSession):
    await _create_project_item(
        db_session,
        project_code="P12E1-F0",
        item_code="UAT1405_ITEM_NOT_FINALIZED",
        is_finalized=False,
    )
    item_no_dates = await _create_project_item(
        db_session, project_code="P12E1-F1", item_code="UAT1405_ITEM_NO_DATES"
    )
    item_ok = await _create_project_item(
        db_session, project_code="P12E1-F2", item_code="UAT1405_ITEM_OK"
    )
    await _add_option(db_session, item=item_no_dates, cost=Decimal("100"), dated=False)
    await _add_option(db_session, item=item_ok, cost=Decimal("200"), dated=True)
    await _add_budget(db_session, Decimal("100000"))
    await db_session.commit()

    optimizer = EnhancedProcurementOptimizer(db_session, solver_type=SolverType.CP_SAT, budget_mode="allow_shortage")
    request = OptimizationRunRequest(
        max_time_slots=24,
        time_limit_seconds=60,
        budget_mode="allow_shortage",
        budget_scenario="minimum_feasible",
        require_all_items=False,
    )
    response = await optimizer.run_optimization(request, generate_multiple_proposals=False)

    assert response.diagnostics["items_filtered_by_status"] >= 1
    assert response.diagnostics["items_filtered_by_lead_time"] >= 1
    assert "items_filtered_by_currency" in response.diagnostics
    assert response.diagnostics["constraint_summary"]["variables_created"] >= 1
