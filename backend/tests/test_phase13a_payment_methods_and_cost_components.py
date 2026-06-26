from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models import ProcurementOption, User
from app.routers.procurement_financials import (
    create_payment_method,
    create_procurement_option_cost_component,
    deactivate_payment_method,
    list_payment_methods,
    update_payment_method,
)
from app.schemas import (
    PaymentMethodCreate,
    PaymentMethodUpdate,
    ProcurementCostComponentCreate,
)
from app.services.procurement_financials_service import (
    calculate_procurement_option_landed_cost,
    calculate_supplier_effective_receipt_date,
)


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="test-hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_procurement_option(
    db_session,
    *,
    test_project_item,
    test_package,
    test_supplier,
    test_currency,
    cost_amount: Decimal = Decimal("100"),
    cost_currency: str = "IRR",
    shipping_cost: Decimal = Decimal("0"),
) -> ProcurementOption:
    option = ProcurementOption(
        package_id=test_package.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        supplier_name=test_supplier.company_name,
        supplier_id=test_supplier.id,
        cost_amount=cost_amount,
        cost_currency=cost_currency,
        shipping_cost=shipping_cost,
        base_cost=cost_amount,
        currency_id=test_currency.id,
        payment_terms={"type": "cash"},
        purchase_date=date(2026, 6, 1),
        is_active=True,
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)
    return option


@pytest.mark.asyncio
async def test_phase13a_test_1_create_list_update_deactivate_payment_method(db_session):
    finance_user = await _create_user(db_session, "phase13a_finance_1", "finance")

    created = await create_payment_method(
        PaymentMethodCreate(
            code="NET30",
            name_en="Net 30",
            name_fa="خالص ۳۰ روزه",
            description="Supplier receives funds after settlement window",
            settlement_delay_days=30,
        ),
        current_user=finance_user,
        db=db_session,
    )
    assert created.code == "NET30"
    assert created.settlement_delay_days == 30

    listed_active = await list_payment_methods(
        active_only=True, current_user=finance_user, db=db_session
    )
    assert any(row.id == created.id for row in listed_active)

    updated = await update_payment_method(
        created.id,
        PaymentMethodUpdate(name_en="Net 30 Updated", settlement_delay_days=35),
        current_user=finance_user,
        db=db_session,
    )
    assert updated.name_en == "Net 30 Updated"
    assert updated.settlement_delay_days == 35

    await deactivate_payment_method(created.id, current_user=finance_user, db=db_session)
    listed_active_after_deactivate = await list_payment_methods(
        active_only=True, current_user=finance_user, db=db_session
    )
    assert all(row.id != created.id for row in listed_active_after_deactivate)


@pytest.mark.asyncio
async def test_phase13a_test_2_settlement_delay_calculation(db_session):
    payment_method = await create_payment_method(
        PaymentMethodCreate(
            code="T1",
            name_en="Transfer +1",
            name_fa="انتقال +۱",
            settlement_delay_days=1,
        ),
        current_user=await _create_user(db_session, "phase13a_finance_2", "finance"),
        db=db_session,
    )
    effective_date = calculate_supplier_effective_receipt_date(
        payment_date=date(2026, 1, 10), payment_method=payment_method
    )
    assert effective_date == date(2026, 1, 11)


def test_phase13a_test_3_reject_negative_settlement_delay():
    with pytest.raises(ValidationError):
        PaymentMethodCreate(
            code="BAD",
            name_en="Bad",
            name_fa="بد",
            settlement_delay_days=-1,
        )


@pytest.mark.asyncio
async def test_phase13a_test_4_create_cost_component_for_procurement_option(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13a_proc_1", "procurement")
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
    )

    component = await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="BASE_PRICE",
            amount_value=Decimal("120"),
            amount_currency="IRR",
        ),
        current_user=procurement_user,
        db=db_session,
    )
    assert component.procurement_option_id == option.id
    assert component.component_type == "BASE_PRICE"


def test_phase13a_test_5_reject_zero_or_negative_cost_component_amount():
    with pytest.raises(ValidationError):
        ProcurementCostComponentCreate(
            component_type="VAT",
            amount_value=Decimal("0"),
            amount_currency="IRR",
        )
    with pytest.raises(ValidationError):
        ProcurementCostComponentCreate(
            component_type="VAT",
            amount_value=Decimal("-10"),
            amount_currency="IRR",
        )


def test_phase13a_test_6_require_description_for_other_component_type():
    with pytest.raises(ValidationError):
        ProcurementCostComponentCreate(
            component_type="OTHER",
            amount_value=Decimal("10"),
            amount_currency="IRR",
            description="",
        )


@pytest.mark.asyncio
async def test_phase13a_test_7_landed_cost_preview_fallback_base_price(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        cost_amount=Decimal("200"),
        shipping_cost=Decimal("0"),
    )

    preview = await calculate_procurement_option_landed_cost(option.id, db_session)
    assert preview["base_amount"]["source"] == "fallback:procurement_options.cost_amount"
    assert preview["totals_by_currency"]["IRR"] == Decimal("200")


@pytest.mark.asyncio
async def test_phase13a_test_8_landed_cost_preview_uses_base_price_component(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13a_proc_2", "procurement")
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        cost_amount=Decimal("200"),
        shipping_cost=Decimal("0"),
    )
    await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="BASE_PRICE",
            amount_value=Decimal("250"),
            amount_currency="IRR",
        ),
        current_user=procurement_user,
        db=db_session,
    )

    preview = await calculate_procurement_option_landed_cost(option.id, db_session)
    assert preview["base_amount"]["amount_value"] == Decimal("250")
    assert preview["base_amount"]["source"].startswith("component:")
    assert preview["totals_by_currency"]["IRR"] == Decimal("250")


@pytest.mark.asyncio
async def test_phase13a_test_9_shipping_component_avoids_legacy_double_counting(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13a_proc_3", "procurement")
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        cost_amount=Decimal("100"),
        shipping_cost=Decimal("20"),
    )
    await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="SHIPPING",
            amount_value=Decimal("30"),
            amount_currency="IRR",
        ),
        current_user=procurement_user,
        db=db_session,
    )

    preview = await calculate_procurement_option_landed_cost(option.id, db_session)
    assert preview["totals_by_currency"]["IRR"] == Decimal("130")


@pytest.mark.asyncio
async def test_phase13a_test_10_missing_exchange_rate_returns_warning_not_crash(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13a_proc_4", "procurement")
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        cost_amount=Decimal("100"),
        shipping_cost=Decimal("0"),
    )
    await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="VAT",
            amount_value=Decimal("10"),
            amount_currency="USD",
            exchange_rate_date=date(2026, 1, 15),
        ),
        current_user=procurement_user,
        db=db_session,
    )

    preview = await calculate_procurement_option_landed_cost(option.id, db_session)
    assert preview["total_irr"] is None
    assert len(preview["missing_exchange_rates"]) >= 1
    assert any(row["currency"] == "USD" for row in preview["missing_exchange_rates"])


@pytest.mark.asyncio
async def test_phase13a_test_11_landed_cost_preview_contains_trace_lines(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        cost_amount=Decimal("80"),
    )

    preview = await calculate_procurement_option_landed_cost(option.id, db_session)
    assert preview["trace_lines"]
    assert any("BASE_PRICE" in line for line in preview["trace_lines"])


@pytest.mark.asyncio
async def test_phase13a_test_12_create_component_with_custom_payment_metadata(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13a_proc_5", "procurement")
    finance_user = await _create_user(db_session, "phase13a_finance_3", "finance")
    payment_method = await create_payment_method(
        PaymentMethodCreate(
            code="NET12",
            name_en="Net 12",
            name_fa="خالص ۱۲",
            settlement_delay_days=12,
        ),
        current_user=finance_user,
        db=db_session,
    )
    option = await _create_procurement_option(
        db_session,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
    )

    component = await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="SHIPPING",
            amount_value=Decimal("45"),
            amount_currency="IRR",
            payment_metadata={
                "inherit_option_payment_schedule": False,
                "payee_type": "LOGISTICS_PROVIDER",
                "payee_label": "Carrier A",
                "payment_method_id": payment_method.id,
                "payment_type": "INSTALLMENTS",
                "planned_payment_date": date(2026, 7, 1),
                "payment_schedule": [
                    {"due_offset_days": 0, "percent": Decimal("50")},
                    {"due_offset_days": 15, "percent": Decimal("50")},
                ],
            },
        ),
        current_user=procurement_user,
        db=db_session,
    )
    assert component.payment_metadata is not None
    assert component.payment_metadata["inherit_option_payment_schedule"] is False
    assert component.payment_metadata["payee_type"] == "LOGISTICS_PROVIDER"
    assert component.payment_metadata["payment_type"] == "INSTALLMENTS"


def test_phase13a_test_13_reject_invalid_component_installment_percent_total():
    with pytest.raises(ValidationError):
        ProcurementCostComponentCreate(
            component_type="INSURANCE",
            amount_value=Decimal("30"),
            amount_currency="IRR",
            payment_metadata={
                "inherit_option_payment_schedule": False,
                "payment_method_id": 1,
                "payment_type": "INSTALLMENTS",
                "planned_payment_date": date(2026, 7, 1),
                "payment_schedule": [
                    {"due_offset_days": 0, "percent": Decimal("70")},
                    {"due_offset_days": 30, "percent": Decimal("20")},
                ],
            },
        )
