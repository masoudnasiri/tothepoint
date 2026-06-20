"""
Phase 12B regression tests for cashflow semantics.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.models import (
    BudgetData,
    CashflowEvent,
    ExchangeRate,
    FinalizedDecision,
    ProcurementOption,
    User,
)
from app.routers.dashboard import get_cashflow_analysis


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_option_and_decision(
    db_session,
    *,
    project_id: int,
    project_item_id: int,
    item_code: str,
    user_id: int,
    status: str,
    final_cost: Decimal = Decimal("1000.00"),
):
    option = ProcurementOption(
        project_item_id=project_item_id,
        item_code=item_code,
        supplier_name="Phase12B Supplier",
        cost_amount=final_cost,
        cost_currency="IRR",
        base_cost=final_cost,
        payment_terms={"type": "cash"},
        is_active=True,
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    decision = FinalizedDecision(
        project_id=project_id,
        project_item_id=project_item_id,
        item_code=item_code,
        procurement_option_id=option.id,
        purchase_date=date(2026, 1, 1),
        delivery_date=date(2026, 1, 15),
        quantity=1,
        final_cost_amount=final_cost,
        final_cost_currency="IRR",
        final_cost=final_cost,
        decision_maker_id=user_id,
        decision_date=datetime.utcnow(),
        status=status,
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)
    return decision


def _month_row(rows, month: str):
    return next((row for row in rows if row["month"] == month), None)


@pytest.mark.asyncio
async def test_phase12b_budget_only_excludes_predecision_forecast_and_actual(
    db_session, test_project, test_project_item
):
    admin_user = await _create_user(db_session, "phase12b_admin_a", "admin")

    db_session.add(
        BudgetData(
            budget_date=date(2026, 1, 1),
            available_budget=Decimal("1000000.00"),
            multi_currency_budget={},
        )
    )
    await db_session.commit()

    proposed_decision = await _create_option_and_decision(
        db_session,
        project_id=test_project.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        user_id=admin_user.id,
        status="PROPOSED",
        final_cost=Decimal("2000.00"),
    )

    # Candidate (pre-decision) forecast events should be excluded by lifecycle filters.
    db_session.add(
        CashflowEvent(
            related_decision_id=proposed_decision.id,
            event_type="INFLOW",
            forecast_type="FORECAST",
            event_date=date(2026, 1, 20),
            amount=Decimal("5000.00"),
            amount_value=Decimal("5000.00"),
            amount_currency="IRR",
            description="Pre-decision forecast inflow",
        )
    )
    db_session.add(
        CashflowEvent(
            related_decision_id=proposed_decision.id,
            event_type="OUTFLOW",
            forecast_type="FORECAST",
            event_date=date(2026, 1, 5),
            amount=Decimal("2000.00"),
            amount_value=Decimal("2000.00"),
            amount_currency="IRR",
            description="Pre-decision forecast outflow",
        )
    )
    await db_session.commit()

    response = await get_cashflow_analysis(
        forecast_type="FORECAST",
        current_user=admin_user,
        db=db_session,
    )

    jan = _month_row(response["time_series"], "2026-01")
    assert jan is not None
    assert jan["budget"] == 1000000.0
    assert jan["inflow"] == 0.0
    assert jan["outflow"] == 0.0
    assert response["summary"]["total_budget"] == 1000000.0
    assert response["summary"]["total_inflow"] == 0.0
    assert response["summary"]["total_outflow"] == 0.0
    assert response["summary"]["net_position"] == 0.0

    actual_response = await get_cashflow_analysis(
        forecast_type="ACTUAL",
        current_user=admin_user,
        db=db_session,
    )
    assert actual_response["summary"]["total_inflow"] == 0.0
    assert actual_response["summary"]["total_outflow"] == 0.0


@pytest.mark.asyncio
async def test_phase12b_locked_decision_includes_forecast_only(
    db_session, test_project, test_project_item
):
    admin_user = await _create_user(db_session, "phase12b_admin_b", "admin")

    locked_decision = await _create_option_and_decision(
        db_session,
        project_id=test_project.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        user_id=admin_user.id,
        status="LOCKED",
        final_cost=Decimal("3000.00"),
    )

    db_session.add(
        CashflowEvent(
            related_decision_id=locked_decision.id,
            event_type="INFLOW",
            forecast_type="FORECAST",
            event_date=date(2026, 2, 20),
            amount=Decimal("4500.00"),
            amount_value=Decimal("4500.00"),
            amount_currency="IRR",
            description="Locked forecast inflow",
        )
    )
    db_session.add(
        CashflowEvent(
            related_decision_id=locked_decision.id,
            event_type="OUTFLOW",
            forecast_type="FORECAST",
            event_date=date(2026, 2, 10),
            amount=Decimal("3000.00"),
            amount_value=Decimal("3000.00"),
            amount_currency="IRR",
            description="Locked forecast outflow",
        )
    )
    await db_session.commit()

    forecast_response = await get_cashflow_analysis(
        forecast_type="FORECAST",
        current_user=admin_user,
        db=db_session,
    )
    feb = _month_row(forecast_response["time_series"], "2026-02")
    assert feb is not None
    assert feb["inflow"] == 4500.0
    assert feb["outflow"] == 3000.0
    assert forecast_response["summary"]["total_inflow"] == 4500.0
    assert forecast_response["summary"]["total_outflow"] == 3000.0

    actual_response = await get_cashflow_analysis(
        forecast_type="ACTUAL",
        current_user=admin_user,
        db=db_session,
    )
    assert actual_response["summary"]["total_inflow"] == 0.0
    assert actual_response["summary"]["total_outflow"] == 0.0


@pytest.mark.asyncio
async def test_phase12b_actual_events_are_not_double_counted_with_forecast(
    db_session, test_project, test_project_item
):
    admin_user = await _create_user(db_session, "phase12b_admin_c", "admin")

    locked_decision = await _create_option_and_decision(
        db_session,
        project_id=test_project.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        user_id=admin_user.id,
        status="LOCKED",
        final_cost=Decimal("4000.00"),
    )

    # Forecast schedule
    db_session.add(
        CashflowEvent(
            related_decision_id=locked_decision.id,
            event_type="INFLOW",
            forecast_type="FORECAST",
            event_date=date(2026, 3, 20),
            amount=Decimal("6000.00"),
            amount_value=Decimal("6000.00"),
            amount_currency="IRR",
            description="Forecast inflow",
        )
    )
    db_session.add(
        CashflowEvent(
            related_decision_id=locked_decision.id,
            event_type="OUTFLOW",
            forecast_type="FORECAST",
            event_date=date(2026, 3, 5),
            amount=Decimal("4000.00"),
            amount_value=Decimal("4000.00"),
            amount_currency="IRR",
            description="Forecast outflow",
        )
    )

    # Actual finance events
    db_session.add(
        CashflowEvent(
            related_decision_id=locked_decision.id,
            event_type="INFLOW",
            forecast_type="ACTUAL",
            event_date=date(2026, 3, 22),
            amount=Decimal("5500.00"),
            amount_value=Decimal("5500.00"),
            amount_currency="IRR",
            description="Actual inflow",
        )
    )
    db_session.add(
        CashflowEvent(
            related_decision_id=locked_decision.id,
            event_type="OUTFLOW",
            forecast_type="ACTUAL",
            event_date=date(2026, 3, 8),
            amount=Decimal("3800.00"),
            amount_value=Decimal("3800.00"),
            amount_currency="IRR",
            description="Actual outflow",
        )
    )
    await db_session.commit()

    forecast_response = await get_cashflow_analysis(
        forecast_type="FORECAST",
        current_user=admin_user,
        db=db_session,
    )
    march_forecast = _month_row(forecast_response["time_series"], "2026-03")
    assert march_forecast["inflow"] == 6000.0
    assert march_forecast["outflow"] == 4000.0

    actual_response = await get_cashflow_analysis(
        forecast_type="ACTUAL",
        current_user=admin_user,
        db=db_session,
    )
    march_actual = _month_row(actual_response["time_series"], "2026-03")
    assert march_actual["inflow"] == 5500.0
    assert march_actual["outflow"] == 3800.0


@pytest.mark.asyncio
async def test_phase12b_currency_conversion_uses_exchange_rate_in_unified_view(
    db_session, test_project, test_project_item
):
    admin_user = await _create_user(db_session, "phase12b_admin_d", "admin")

    locked_decision = await _create_option_and_decision(
        db_session,
        project_id=test_project.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        user_id=admin_user.id,
        status="LOCKED",
        final_cost=Decimal("100.00"),
    )

    db_session.add(
        ExchangeRate(
            date=date(2026, 4, 1),
            from_currency="USD",
            to_currency="IRR",
            rate=Decimal("500000"),
            is_active=True,
        )
    )
    db_session.add(
        CashflowEvent(
            related_decision_id=locked_decision.id,
            event_type="OUTFLOW",
            forecast_type="FORECAST",
            event_date=date(2026, 4, 1),
            amount=Decimal("100.00"),
            amount_value=Decimal("100.00"),
            amount_currency="USD",
            description="USD forecast outflow",
        )
    )
    await db_session.commit()

    unified = await get_cashflow_analysis(
        forecast_type="FORECAST",
        currency_view="unified",
        current_user=admin_user,
        db=db_session,
    )
    apr_unified = _month_row(unified["time_series"], "2026-04")
    assert apr_unified is not None
    assert apr_unified["outflow"] == 50000000.0

    original = await get_cashflow_analysis(
        forecast_type="FORECAST",
        currency_view="original",
        current_user=admin_user,
        db=db_session,
    )
    usd_series = original["currencies"]["USD"]["time_series"]
    apr_usd = _month_row(usd_series, "2026-04")
    assert apr_usd is not None
    assert apr_usd["outflow"] == 100.0
