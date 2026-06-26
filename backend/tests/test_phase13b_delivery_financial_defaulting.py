from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import (
    CashflowEvent,
    DeliveryOption,
    FinalizedDecision,
    OptimizationResult,
    ProcurementOption,
    User,
)
from app.routers.procurement_financials import (
    get_procurement_option_delivery_financial_preview,
)
from app.schemas import ProcurementOptionDeliveryFinancialPreviewRequest
from app.services.procurement_financials_service import (
    calculate_delivery_variance_days,
    default_customer_invoice_and_receipt_dates,
)


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="test-hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_delivery_option(
    db_session,
    *,
    test_project_item,
    test_package,
    invoice_timing_type: str,
    delivery_date_value: date,
    invoice_issue_date: date | None = None,
    invoice_days_after_delivery: int | None = 30,
) -> DeliveryOption:
    delivery_option = DeliveryOption(
        package_id=test_package.id,
        project_item_id=test_project_item.id,
        delivery_slot=1,
        delivery_date=delivery_date_value,
        invoice_timing_type=invoice_timing_type,
        invoice_issue_date=invoice_issue_date,
        invoice_days_after_delivery=invoice_days_after_delivery,
        invoice_amount_per_unit=Decimal("100"),
        is_active=True,
    )
    db_session.add(delivery_option)
    await db_session.commit()
    await db_session.refresh(delivery_option)
    return delivery_option


async def _create_procurement_option(
    db_session,
    *,
    test_project_item,
    test_package,
    test_supplier,
    test_currency,
    delivery_option_id: int,
) -> ProcurementOption:
    option = ProcurementOption(
        package_id=test_package.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        supplier_name=test_supplier.company_name,
        supplier_id=test_supplier.id,
        cost_amount=Decimal("100"),
        cost_currency="IRR",
        shipping_cost=Decimal("0"),
        base_cost=Decimal("100"),
        currency_id=test_currency.id,
        payment_terms={"type": "cash"},
        delivery_option_id=delivery_option_id,
        purchase_date=date(2026, 6, 15),
        expected_delivery_date=date(2026, 7, 1),
        is_active=True,
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)
    return option


@pytest.mark.asyncio
async def test_phase13b_test_1_delivery_variance_calculation_early_on_time_delayed():
    assert calculate_delivery_variance_days(date(2026, 7, 10), date(2026, 7, 8)) == -2
    assert calculate_delivery_variance_days(date(2026, 7, 10), date(2026, 7, 10)) == 0
    assert calculate_delivery_variance_days(date(2026, 7, 10), date(2026, 7, 13)) == 3


@pytest.mark.asyncio
async def test_phase13b_test_2_invoice_default_from_relative_timing():
    delivery_option = DeliveryOption(
        id=999,
        delivery_date=date(2026, 7, 1),
        invoice_timing_type="RELATIVE",
        invoice_days_after_delivery=10,
        invoice_amount_per_unit=Decimal("100"),
    )

    result = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 5),
        selected_delivery_date=date(2026, 7, 5),
        delivery_option=delivery_option,
        project_item_invoice_submission_date=None,
        project_item_expected_cash_in_date=None,
        manual_invoice_date=None,
        manual_receipt_date=None,
    )

    assert result["forecast_customer_invoice_date"] == date(2026, 7, 15)
    assert result["forecast_customer_invoice_date_source"] == "SYSTEM_DEFAULT"


@pytest.mark.asyncio
async def test_phase13b_test_3_invoice_default_absolute_preserves_offset():
    delivery_option = DeliveryOption(
        id=1000,
        delivery_date=date(2026, 7, 1),
        invoice_timing_type="ABSOLUTE",
        invoice_issue_date=date(2026, 7, 21),
        invoice_days_after_delivery=None,
        invoice_amount_per_unit=Decimal("100"),
    )

    result = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 6),
        selected_delivery_date=date(2026, 7, 6),
        delivery_option=delivery_option,
        project_item_invoice_submission_date=None,
        project_item_expected_cash_in_date=None,
        manual_invoice_date=None,
        manual_receipt_date=None,
    )

    # Original ABSOLUTE offset is +20 days from requested delivery date.
    assert result["forecast_customer_invoice_date"] == date(2026, 7, 26)
    assert result["forecast_customer_invoice_date_source"] == "SYSTEM_DEFAULT"


@pytest.mark.asyncio
async def test_phase13b_test_4_manual_invoice_override():
    delivery_option = DeliveryOption(
        id=1001,
        delivery_date=date(2026, 7, 1),
        invoice_timing_type="RELATIVE",
        invoice_days_after_delivery=10,
        invoice_amount_per_unit=Decimal("100"),
    )

    result = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 5),
        selected_delivery_date=date(2026, 7, 5),
        delivery_option=delivery_option,
        project_item_invoice_submission_date=None,
        project_item_expected_cash_in_date=None,
        manual_invoice_date=date(2026, 7, 30),
        manual_receipt_date=None,
    )

    assert result["forecast_customer_invoice_date"] == date(2026, 7, 30)
    assert result["forecast_customer_invoice_date_source"] == "MANUAL_OVERRIDE"


@pytest.mark.asyncio
async def test_phase13b_test_5_receipt_default_from_invoice_to_receipt_gap():
    delivery_option = DeliveryOption(
        id=1002,
        delivery_date=date(2026, 7, 1),
        invoice_timing_type="RELATIVE",
        invoice_days_after_delivery=5,
        invoice_amount_per_unit=Decimal("100"),
    )

    result = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 5),
        selected_delivery_date=date(2026, 7, 5),
        delivery_option=delivery_option,
        project_item_invoice_submission_date=date(2026, 7, 10),
        project_item_expected_cash_in_date=date(2026, 8, 9),
        manual_invoice_date=None,
        manual_receipt_date=None,
    )

    # Gap is 30 days (Aug 9 - Jul 10), applied to calculated invoice date Jul 10.
    assert result["forecast_customer_invoice_date"] == date(2026, 7, 10)
    assert result["forecast_customer_receipt_date"] == date(2026, 8, 9)
    assert result["forecast_customer_receipt_date_source"] == "SYSTEM_DEFAULT"
    assert result["forecast_customer_receipt_delay_days"] == 30


@pytest.mark.asyncio
async def test_phase13b_test_6_manual_receipt_override():
    delivery_option = DeliveryOption(
        id=1003,
        delivery_date=date(2026, 7, 1),
        invoice_timing_type="RELATIVE",
        invoice_days_after_delivery=5,
        invoice_amount_per_unit=Decimal("100"),
    )

    result = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 5),
        selected_delivery_date=date(2026, 7, 5),
        delivery_option=delivery_option,
        project_item_invoice_submission_date=date(2026, 7, 10),
        project_item_expected_cash_in_date=date(2026, 8, 9),
        manual_invoice_date=None,
        manual_receipt_date=date(2026, 8, 30),
    )

    assert result["forecast_customer_receipt_date"] == date(2026, 8, 30)
    assert result["forecast_customer_receipt_date_source"] == "MANUAL_OVERRIDE"


@pytest.mark.asyncio
async def test_phase13b_test_7_missing_invoice_timing_returns_diagnostic():
    result = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 5),
        selected_delivery_date=date(2026, 7, 5),
        delivery_option=None,
        project_item_invoice_submission_date=None,
        project_item_expected_cash_in_date=None,
        manual_invoice_date=None,
        manual_receipt_date=None,
    )

    assert result["forecast_customer_invoice_date"] is None
    assert "invoice_timing" in result["missing_inputs"]


@pytest.mark.asyncio
async def test_phase13b_test_8_missing_receipt_timing_returns_diagnostic():
    delivery_option = DeliveryOption(
        id=1004,
        delivery_date=date(2026, 7, 1),
        invoice_timing_type="RELATIVE",
        invoice_days_after_delivery=5,
        invoice_amount_per_unit=Decimal("100"),
    )
    result = default_customer_invoice_and_receipt_dates(
        project_requested_delivery_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 5),
        selected_delivery_date=date(2026, 7, 5),
        delivery_option=delivery_option,
        project_item_invoice_submission_date=None,
        project_item_expected_cash_in_date=None,
        manual_invoice_date=None,
        manual_receipt_date=None,
    )

    assert result["forecast_customer_invoice_date"] == date(2026, 7, 10)
    assert result["forecast_customer_receipt_date"] is None
    assert "customer_receipt_timing" in result["missing_inputs"]


@pytest.mark.asyncio
async def test_phase13b_test_9_preview_endpoint_returns_trace_and_missing_inputs(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    test_project_item.invoice_submission_date = date(2026, 7, 12)
    test_project_item.expected_cash_in_date = date(2026, 8, 11)
    await db_session.commit()

    delivery_option = await _create_delivery_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        invoice_timing_type="RELATIVE",
        delivery_date_value=date(2026, 7, 1),
        invoice_days_after_delivery=7,
    )
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        delivery_option_id=delivery_option.id,
    )
    current_user = await _create_user(db_session, "phase13b_preview_user", "procurement")

    preview = await get_procurement_option_delivery_financial_preview(
        option.id,
        ProcurementOptionDeliveryFinancialPreviewRequest(
            delivery_date_source="SUPPLIER_ACTUAL",
            supplier_actual_delivery_date=date(2026, 7, 5),
        ),
        current_user=current_user,
        db=db_session,
    )

    assert preview["trace_lines"]
    assert isinstance(preview["missing_inputs"], list)
    assert preview["forecast_customer_invoice_date"] == date(2026, 7, 12)
    assert preview["forecast_customer_receipt_date"] == date(2026, 8, 11)


@pytest.mark.asyncio
async def test_phase13b_test_10_preview_has_no_cashflow_decision_or_optimization_side_effects(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    delivery_option = await _create_delivery_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        invoice_timing_type="RELATIVE",
        delivery_date_value=date(2026, 7, 1),
        invoice_days_after_delivery=7,
    )
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        delivery_option_id=delivery_option.id,
    )
    current_user = await _create_user(db_session, "phase13b_preview_sidefx", "procurement")

    before_cashflow = (
        await db_session.execute(select(func.count()).select_from(CashflowEvent))
    ).scalar_one()
    before_decisions = (
        await db_session.execute(select(func.count()).select_from(FinalizedDecision))
    ).scalar_one()
    before_optimization_results = (
        await db_session.execute(select(func.count()).select_from(OptimizationResult))
    ).scalar_one()

    await get_procurement_option_delivery_financial_preview(
        option.id,
        ProcurementOptionDeliveryFinancialPreviewRequest(
            delivery_date_source="SUPPLIER_ACTUAL",
            supplier_actual_delivery_date=date(2026, 7, 6),
        ),
        current_user=current_user,
        db=db_session,
    )

    after_cashflow = (
        await db_session.execute(select(func.count()).select_from(CashflowEvent))
    ).scalar_one()
    after_decisions = (
        await db_session.execute(select(func.count()).select_from(FinalizedDecision))
    ).scalar_one()
    after_optimization_results = (
        await db_session.execute(select(func.count()).select_from(OptimizationResult))
    ).scalar_one()

    assert after_cashflow == before_cashflow
    assert after_decisions == before_decisions
    assert after_optimization_results == before_optimization_results

