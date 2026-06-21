from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BudgetData, OptimizationResult, ProcurementOption, Project, ProjectItem
from app.services.optimization_budget_service import (
    analyze_optimization_run_financial,
    analyze_proposal_decisions_financial,
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


@pytest.mark.asyncio
async def test_phase12e4c_selected_result_payload_has_semantic_fields(db_session: AsyncSession):
    item = await _create_item(db_session, "P12E4C-A", "ITEM-A")
    selected = await _add_option(db_session, item=item, supplier_name="SUP-A", cost=Decimal("250"))
    db_session.add(
        BudgetData(
            budget_date=date(2026, 6, 1),
            available_budget=Decimal("1000"),
            multi_currency_budget={"IRR": 1000},
        )
    )
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
            final_cost=Decimal("250"),
        )
    )
    await db_session.commit()

    analysis = await analyze_optimization_run_financial(db_session, run_id=str(run_id))

    assert analysis.total_purchase_cost_irr == Decimal("250")
    assert analysis.budget_required_irr == Decimal("250")
    assert analysis.trace_lines
    assert analysis.reconciliation is not None
    assert analysis.narrative_report
    assert "تحلیل مالی مدل انتخابی" in analysis.narrative_report


@pytest.mark.asyncio
async def test_phase12e4c_reconciliation_contains_human_readable_reasons(db_session: AsyncSession):
    item = await _create_item(db_session, "P12E4C-B", "ITEM-B")
    option = await _add_option(db_session, item=item, supplier_name="SUP-B", cost=Decimal("300"))
    db_session.add(
        BudgetData(
            budget_date=date(2026, 6, 1),
            available_budget=Decimal("2000"),
            multi_currency_budget={"IRR": 2000},
        )
    )
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
                "final_cost": 300,
            }
        ],
        weighted_objective_cost_irr=Decimal("900"),
    )

    reasons = analysis.reconciliation.get("reasons") or []
    assert reasons
    assert any("internal optimization score" in reason for reason in reasons)
