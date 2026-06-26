from datetime import date
from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    CashflowEvent,
    FinalizedDecision,
    OptimizationResult,
    ProcurementOption as ProcurementOptionModel,
    User,
)
from app.routers import procurement as procurement_router_module
from app.routers.procurement import create_new_procurement_option
from app.routers.procurement_financials import (
    create_payment_method,
    create_procurement_option_cost_component,
    get_procurement_option_candidate_readiness,
)
from app.schemas import (
    PaymentMethodCreate,
    ProcurementCostComponentCreate,
    ProcurementOptionCreate,
)


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="test-hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


def _build_option_payload(
    *,
    test_project_item,
    test_package,
    test_supplier,
    test_currency,
    payment_method_id: int | None = None,
    planned_supplier_payment_date: date | None = None,
    project_requested_delivery_date: date | None = None,
    supplier_actual_delivery_date: date | None = None,
) -> ProcurementOptionCreate:
    return ProcurementOptionCreate(
        package_id=test_package.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        supplier_name=test_supplier.company_name,
        supplier_id=test_supplier.id,
        base_cost=Decimal("100"),
        currency_id=test_currency.id,
        shipping_cost=Decimal("0"),
        payment_terms={"type": "cash", "discount_percent": 0},
        payment_method_id=payment_method_id,
        planned_supplier_payment_date=planned_supplier_payment_date,
        project_requested_delivery_date=project_requested_delivery_date,
        supplier_actual_delivery_date=supplier_actual_delivery_date,
    )


@pytest.mark.asyncio
async def test_phase13c_test_1_cost_component_mapping_updates_compatibility_fields(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13c_proc_1", "procurement")
    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )

    await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="BASE_PRICE",
            amount_value=Decimal("250"),
            amount_currency="USD",
        ),
        current_user=procurement_user,
        db=db_session,
    )
    await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="SHIPPING",
            amount_value=Decimal("30"),
            amount_currency="USD",
        ),
        current_user=procurement_user,
        db=db_session,
    )

    refreshed = await db_session.get(ProcurementOptionModel, option.id)
    assert Decimal(str(refreshed.cost_amount)) == Decimal("250")
    assert Decimal(str(refreshed.base_cost)) == Decimal("250")
    assert refreshed.cost_currency == "USD"
    assert Decimal(str(refreshed.shipping_cost)) == Decimal("30")


@pytest.mark.asyncio
async def test_phase13c_test_2_payment_and_delivery_fields_are_persisted_and_derived(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    finance_user = await _create_user(db_session, "phase13c_fin_1", "finance")
    procurement_user = await _create_user(db_session, "phase13c_proc_2", "procurement")

    payment_method = await create_payment_method(
        PaymentMethodCreate(
            code="NET7",
            name_en="Net 7",
            name_fa="خالص ۷ روزه",
            settlement_delay_days=7,
        ),
        current_user=finance_user,
        db=db_session,
    )

    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
            payment_method_id=payment_method.id,
            planned_supplier_payment_date=date(2026, 7, 1),
            project_requested_delivery_date=date(2026, 7, 10),
            supplier_actual_delivery_date=date(2026, 7, 12),
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )

    assert option.payment_method_id == payment_method.id
    assert option.planned_supplier_payment_date == date(2026, 7, 1)
    assert option.supplier_effective_receipt_date == date(2026, 7, 8)
    assert option.selected_delivery_date == date(2026, 7, 12)
    assert option.delivery_date_variance_days == 2


@pytest.mark.asyncio
async def test_phase13c_test_3_server_defaults_customer_schedule_and_records_missing_inputs(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13c_proc_3", "procurement")
    test_project_item.invoice_submission_date = date(2026, 7, 20)
    test_project_item.expected_cash_in_date = date(2026, 8, 19)
    await db_session.commit()

    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
            project_requested_delivery_date=date(2026, 7, 10),
            supplier_actual_delivery_date=date(2026, 7, 12),
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )
    assert option.forecast_customer_invoice_date is not None
    assert option.forecast_customer_receipt_date is not None
    assert option.forecast_customer_invoice_date_source == "SYSTEM_DEFAULT"
    assert option.forecast_customer_receipt_date_source == "SYSTEM_DEFAULT"

    # Create another option with missing timing context to ensure diagnostics are preserved.
    test_project_item.invoice_submission_date = None
    test_project_item.expected_cash_in_date = None
    await db_session.commit()
    option_missing = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
            project_requested_delivery_date=None,
            supplier_actual_delivery_date=None,
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )
    assert option_missing.date_calculation_trace is not None
    assert any(
        "Missing timing inputs" in trace_line
        for trace_line in (option_missing.date_calculation_trace or [])
    )


@pytest.mark.asyncio
async def test_phase13c_test_4_readiness_reports_missing_fields_for_incomplete_option(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13c_proc_4", "procurement")
    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )

    readiness = await get_procurement_option_candidate_readiness(
        option.id,
        current_user=procurement_user,
        db=db_session,
    )
    assert readiness["is_ready_for_candidate_builder"] is False
    assert "active_base_price_component" in readiness["missing_required_fields"]
    assert "payment_method_id" in readiness["missing_required_fields"]
    assert "planned_supplier_payment_date" in readiness["missing_required_fields"]


@pytest.mark.asyncio
async def test_phase13c_test_5_readiness_returns_ready_for_complete_option(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    finance_user = await _create_user(db_session, "phase13c_fin_2", "finance")
    procurement_user = await _create_user(db_session, "phase13c_proc_5", "procurement")

    payment_method = await create_payment_method(
        PaymentMethodCreate(
            code="NET15",
            name_en="Net 15",
            name_fa="خالص ۱۵ روزه",
            settlement_delay_days=15,
        ),
        current_user=finance_user,
        db=db_session,
    )
    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
            payment_method_id=payment_method.id,
            planned_supplier_payment_date=date(2026, 7, 1),
            project_requested_delivery_date=date(2026, 7, 8),
            supplier_actual_delivery_date=date(2026, 7, 8),
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )
    await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="BASE_PRICE",
            amount_value=Decimal("120"),
            amount_currency="IRR",
        ),
        current_user=procurement_user,
        db=db_session,
    )

    readiness = await get_procurement_option_candidate_readiness(
        option.id,
        current_user=procurement_user,
        db=db_session,
    )
    assert readiness["is_ready_for_candidate_builder"] is True
    assert readiness["missing_required_fields"] == []


@pytest.mark.asyncio
async def test_phase13c_test_6_readiness_endpoint_has_no_side_effects(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13c_proc_6", "procurement")
    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )

    before_cashflow = (
        await db_session.execute(select(func.count()).select_from(CashflowEvent))
    ).scalar_one()
    before_decisions = (
        await db_session.execute(select(func.count()).select_from(FinalizedDecision))
    ).scalar_one()
    before_optimization = (
        await db_session.execute(select(func.count()).select_from(OptimizationResult))
    ).scalar_one()

    await get_procurement_option_candidate_readiness(
        option.id,
        current_user=procurement_user,
        db=db_session,
    )

    after_cashflow = (
        await db_session.execute(select(func.count()).select_from(CashflowEvent))
    ).scalar_one()
    after_decisions = (
        await db_session.execute(select(func.count()).select_from(FinalizedDecision))
    ).scalar_one()
    after_optimization = (
        await db_session.execute(select(func.count()).select_from(OptimizationResult))
    ).scalar_one()

    assert after_cashflow == before_cashflow
    assert after_decisions == before_decisions
    assert after_optimization == before_optimization


@pytest.mark.asyncio
async def test_phase13c_test_6b_readiness_includes_component_payment_diagnostics(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    finance_user = await _create_user(db_session, "phase13c_fin_2b", "finance")
    procurement_user = await _create_user(db_session, "phase13c_proc_6b", "procurement")
    payment_method = await create_payment_method(
        PaymentMethodCreate(
            code="NET9",
            name_en="Net 9",
            name_fa="خالص ۹",
            settlement_delay_days=9,
        ),
        current_user=finance_user,
        db=db_session,
    )
    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
            payment_method_id=payment_method.id,
            planned_supplier_payment_date=date(2026, 7, 3),
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )
    base_component = await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="BASE_PRICE",
            amount_value=Decimal("100"),
            amount_currency="IRR",
            payment_metadata={
                "inherit_option_payment_schedule": True,
                "payee_type": "SUPPLIER",
            },
        ),
        current_user=procurement_user,
        db=db_session,
    )
    shipping_component = await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="SHIPPING",
            amount_value=Decimal("25"),
            amount_currency="IRR",
            payment_metadata={
                "inherit_option_payment_schedule": False,
                "payee_type": "LOGISTICS_PROVIDER",
                "payee_label": "Carrier B",
                "payment_method_id": payment_method.id,
                "payment_type": "INSTALLMENTS",
                "planned_payment_date": date(2026, 7, 4),
                "payment_schedule": [
                    {"due_offset_days": 0, "percent": Decimal("40")},
                    {"due_offset_days": 20, "percent": Decimal("60")},
                ],
            },
        ),
        current_user=procurement_user,
        db=db_session,
    )

    readiness = await get_procurement_option_candidate_readiness(
        option.id,
        current_user=procurement_user,
        db=db_session,
    )
    diagnostics = readiness["payment_summary"]["component_payment_diagnostics"]
    assert len(diagnostics) >= 2
    by_id = {row["component_id"]: row for row in diagnostics}
    assert by_id[int(base_component.id)]["inherit_option_payment_schedule"] is True
    assert by_id[int(shipping_component.id)]["inherit_option_payment_schedule"] is False
    assert by_id[int(shipping_component.id)]["payment_type"] == "INSTALLMENTS"
    assert len(by_id[int(shipping_component.id)]["payment_schedule"]) == 2


@pytest.mark.asyncio
async def test_phase13c_test_7_put_procurement_option_returns_materialized_response_no_missing_greenlet(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    finance_user = await _create_user(db_session, "phase13c_fin_3", "finance")
    procurement_user = await _create_user(db_session, "phase13c_proc_7", "procurement")

    payment_method = await create_payment_method(
        PaymentMethodCreate(
            code="NET2",
            name_en="Net 2",
            name_fa="خالص ۲",
            settlement_delay_days=2,
        ),
        current_user=finance_user,
        db=db_session,
    )
    option = await create_new_procurement_option(
        _build_option_payload(
            test_project_item=test_project_item,
            test_package=test_package,
            test_supplier=test_supplier,
            test_currency=test_currency,
        ),
        current_user=procurement_user,
        db=db_session,
        request=None,
    )
    await create_procurement_option_cost_component(
        option.id,
        ProcurementCostComponentCreate(
            component_type="BASE_PRICE",
            amount_value=Decimal("1000"),
            amount_currency="IRR",
        ),
        current_user=procurement_user,
        db=db_session,
    )

    app = FastAPI()
    app.include_router(procurement_router_module.router)

    async def _override_get_db():
        yield db_session

    async def _override_get_current_user():
        return procurement_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.put(
                f"/procurement/option/{option.id}",
                json={
                    "payment_method_id": payment_method.id,
                    "planned_supplier_payment_date": "2026-07-07",
                    "supplier_actual_delivery_date": "2026-07-22",
                    "payment_terms": {
                        "type": "installments",
                        "schedule": [
                            {"due_offset": 0, "percent": 60},
                            {"due_offset": 30, "percent": 40},
                        ],
                    },
                    "discount_bundle_threshold": 10,
                    "discount_bundle_percent": 5,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["id"] == option.id
    assert body["payment_method_id"] == payment_method.id
    assert body["planned_supplier_payment_date"] == "2026-07-07"
    assert body["supplier_effective_receipt_date"] == "2026-07-09"
    assert body["supplier_actual_delivery_date"] == "2026-07-22"
    assert body["payment_terms"]["type"] == "installments"
    assert body["payment_terms"]["schedule"] == [
        {"due_offset": 0, "percent": 60},
        {"due_offset": 30, "percent": 40},
    ]


@pytest.mark.asyncio
async def test_phase13c_test_8_post_procurement_option_returns_materialized_response_no_missing_greenlet(
    db_session, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13c_proc_8", "procurement")

    app = FastAPI()
    app.include_router(procurement_router_module.router)

    async def _override_get_db():
        yield db_session

    async def _override_get_current_user():
        return procurement_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    transport = ASGITransport(app=app)
    payload = {
        "package_id": test_package.id,
        "project_item_id": test_project_item.id,
        "item_code": test_project_item.item_code,
        "supplier_name": test_supplier.company_name,
        "supplier_id": test_supplier.id,
        "base_cost": 100,
        "currency_id": test_currency.id,
        "shipping_cost": 0,
        "payment_terms": {"type": "cash", "discount_percent": 0},
    }
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post("/procurement/options", json=payload)
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["item_code"] == test_project_item.item_code
    assert body["project_item_id"] == test_project_item.id
    assert body["supplier_name"] == test_supplier.company_name
