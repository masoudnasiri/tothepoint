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
    DeliveryOption,
    FinalizedDecision,
    OptimizationResult,
    ProcurementCostComponent,
    ProcurementOption,
    ProcurementPackage,
    ProjectItem,
    SupplierPayment,
    User,
)
from app.models_invoice_payment import Invoice, Payment
from app.routers import financial_projections as projections_router_module
from app.routers.procurement import create_new_procurement_option
from app.routers.procurement_financials import (
    create_payment_method,
    create_procurement_option_cost_component,
)
from app.schemas import (
    PaymentMethodCreate,
    ProcurementCostComponentCreate,
    ProcurementOptionCreate,
)
from app.services import financial_projection_service as projection_service
from app.services.financial_projection_service import project_financials_for_project


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="test-hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_payment_method(db_session, suffix: str):
    finance_user = await _create_user(db_session, f"phase13f_fin_{suffix}", "finance")
    return await create_payment_method(
        PaymentMethodCreate(
            code=f"P13F{suffix}".upper(),
            name_en=f"Phase13F {suffix}",
            name_fa=f"فاز13F {suffix}",
            settlement_delay_days=5,
        ),
        current_user=finance_user,
        db=db_session,
    )


async def _create_delivery_option(db_session, project_item_id: int, invoice_per_unit: Decimal):
    delivery_option = DeliveryOption(
        project_item_id=project_item_id,
        delivery_date=date(2026, 7, 20),
        invoice_timing_type="RELATIVE",
        invoice_days_after_delivery=0,
        invoice_amount_per_unit=invoice_per_unit,
        is_active=True,
    )
    db_session.add(delivery_option)
    await db_session.commit()
    await db_session.refresh(delivery_option)
    return delivery_option


async def _create_option(
    *,
    db_session,
    procurement_user,
    test_project_item,
    test_package,
    test_supplier,
    test_currency,
    payment_method_id=None,
    planned_supplier_payment_date=None,
    supplier_actual_delivery_date=None,
    project_requested_delivery_date=None,
    delivery_option_id=None,
):
    payload = ProcurementOptionCreate(
        package_id=test_package.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        supplier_name=test_supplier.company_name,
        supplier_id=test_supplier.id,
        base_cost=Decimal("100"),
        currency_id=test_currency.id,
        shipping_cost=Decimal("0"),
        delivery_option_id=delivery_option_id,
        payment_terms={"type": "cash", "discount_percent": 0},
        payment_method_id=payment_method_id,
        planned_supplier_payment_date=planned_supplier_payment_date,
        project_requested_delivery_date=project_requested_delivery_date,
        supplier_actual_delivery_date=supplier_actual_delivery_date,
    )
    return await create_new_procurement_option(
        payload,
        current_user=procurement_user,
        db=db_session,
        request=None,
    )


async def _add_component(
    db_session,
    procurement_user,
    option_id: int,
    component_type: str,
    amount: str,
    currency: str,
):
    return await create_procurement_option_cost_component(
        option_id,
        ProcurementCostComponentCreate(
            component_type=component_type,
            amount_value=Decimal(amount),
            amount_currency=currency,
        ),
        current_user=procurement_user,
        db=db_session,
    )


def _candidate(
    *,
    candidate_id: str,
    procurement_option_id: int,
    project_id: int = 1,
    project_item_id: int = 1,
    package_id: int = 1,
    landed_cost_amount: str = "100",
    landed_cost_currency: str = "IRR",
    planned_supplier_payment_date: str | None = "2026-08-01",
    forecast_customer_receipt_date: str | None = "2026-08-10",
    forecast_customer_invoice_date: str | None = "2026-08-05",
    ready: bool = True,
    customer_revenue_amount: str | None = None,
    customer_revenue_currency: str | None = None,
    gross_margin_amount: str | None = "50",
    gross_margin_ratio: str | None = "0.333333",
):
    value = {
        "candidate_id": candidate_id,
        "project_id": project_id,
        "project_item_id": project_item_id,
        "package_id": package_id,
        "procurement_option_id": procurement_option_id,
        "supplier_id": 1,
        "supplier_name": "Supplier",
        "is_ready_for_candidate_builder": ready,
        "landed_cost_amount": Decimal(landed_cost_amount) if landed_cost_amount is not None else None,
        "landed_cost_currency": landed_cost_currency,
        "planned_supplier_payment_date": (
            date.fromisoformat(planned_supplier_payment_date)
            if planned_supplier_payment_date
            else None
        ),
        "forecast_customer_receipt_date": (
            date.fromisoformat(forecast_customer_receipt_date)
            if forecast_customer_receipt_date
            else None
        ),
        "forecast_customer_invoice_date": (
            date.fromisoformat(forecast_customer_invoice_date)
            if forecast_customer_invoice_date
            else None
        ),
        "cost_components_summary": [
            {
                "component_id": 1,
                "component_type": "BASE_PRICE",
                "amount_value": Decimal("80"),
                "amount_currency": landed_cost_currency,
            },
            {
                "component_id": 2,
                "component_type": "SHIPPING",
                "amount_value": Decimal("20"),
                "amount_currency": landed_cost_currency,
            },
        ],
        "gross_margin_amount": (
            Decimal(gross_margin_amount) if gross_margin_amount is not None else None
        ),
        "gross_margin_ratio": (
            Decimal(gross_margin_ratio) if gross_margin_ratio is not None else None
        ),
    }
    if customer_revenue_amount is not None:
        value["customer_revenue_amount"] = Decimal(customer_revenue_amount)
        value["customer_revenue_currency"] = customer_revenue_currency
    return value


@pytest.mark.asyncio
async def test_phase13f_valid_projection_outputs_events_periods_and_no_outflow_double_count(
    db_session, test_project, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13f_proc_valid", "procurement")
    payment_method = await _create_payment_method(db_session, "a")

    test_project_item.quantity = 2
    test_package.main_item_quantity = 2
    await db_session.commit()

    delivery_option = await _create_delivery_option(
        db_session, test_project_item.id, Decimal("120")
    )
    option = await _create_option(
        db_session=db_session,
        procurement_user=procurement_user,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        payment_method_id=payment_method.id,
        planned_supplier_payment_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 20),
        project_requested_delivery_date=date(2026, 7, 20),
        delivery_option_id=delivery_option.id,
    )
    await _add_component(db_session, procurement_user, option.id, "BASE_PRICE", "100", "IRR")
    await _add_component(db_session, procurement_user, option.id, "SHIPPING", "20", "IRR")

    result = await project_financials_for_project(db_session, test_project.id)

    assert result["is_projection_complete"] is True
    assert result["projected_candidates"] == 1
    event_types = {event["event_type"] for event in result["projection_events"]}
    assert "SUPPLIER_PAYMENT_OUTFLOW" in event_types
    assert "CUSTOMER_INVOICE_INFLOW" in event_types

    supplier_cash_events = [
        event
        for event in result["projection_events"]
        if event["event_type"] == "SUPPLIER_PAYMENT_OUTFLOW" and event["is_cash_effective"] is True
    ]
    assert len(supplier_cash_events) == 1
    component_rows = [
        event for event in result["projection_events"] if event["source_type"] == "COST_COMPONENT"
    ]
    assert component_rows
    assert all(event["is_cash_effective"] is False for event in component_rows)

    period = next(summary for summary in result["period_summaries"] if summary["currency"] == "IRR")
    assert period["total_outflow"] == supplier_cash_events[0]["amount"]


@pytest.mark.asyncio
async def test_phase13f_component_custom_schedule_creates_cash_effective_rows_without_double_count(
    db_session, test_project, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(
        db_session, "phase13f_proc_custom_component", "procurement"
    )
    payment_method = await _create_payment_method(db_session, "custom")
    test_project_item.quantity = 2
    test_package.main_item_quantity = 2
    await db_session.commit()

    delivery_option = await _create_delivery_option(
        db_session, test_project_item.id, Decimal("120")
    )
    option = await _create_option(
        db_session=db_session,
        procurement_user=procurement_user,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        payment_method_id=payment_method.id,
        planned_supplier_payment_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 20),
        project_requested_delivery_date=date(2026, 7, 20),
        delivery_option_id=delivery_option.id,
    )
    await create_procurement_option_cost_component(
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
            amount_value=Decimal("20"),
            amount_currency="IRR",
            payment_metadata={
                "inherit_option_payment_schedule": False,
                "payee_type": "LOGISTICS_PROVIDER",
                "payment_method_id": payment_method.id,
                "payment_type": "INSTALLMENTS",
                "planned_payment_date": date(2026, 7, 2),
                "payment_schedule": [
                    {"due_offset_days": 0, "percent": Decimal("50")},
                    {"due_offset_days": 10, "percent": Decimal("50")},
                ],
            },
        ),
        current_user=procurement_user,
        db=db_session,
    )

    result = await project_financials_for_project(db_session, test_project.id)
    assert result["is_projection_complete"] is True
    cash_effective_outflows = [
        row
        for row in result["projection_events"]
        if row["direction"] == "OUTFLOW" and row["is_cash_effective"] is True
    ]
    supplier_rows = [
        row for row in cash_effective_outflows if row["event_type"] == "SUPPLIER_PAYMENT_OUTFLOW"
    ]
    shipping_custom_rows = [
        row
        for row in cash_effective_outflows
        if row["source_type"] == "COST_COMPONENT_PAYMENT"
        and row["source_id"] == str(shipping_component.id)
    ]
    assert len(supplier_rows) == 1
    assert supplier_rows[0]["amount"] == Decimal("100")
    assert len(shipping_custom_rows) == 2
    assert sum(row["amount"] for row in shipping_custom_rows) == Decimal("20")


@pytest.mark.asyncio
async def test_phase13f_company_cash_gap_and_working_capital_exposure_rules(monkeypatch, db_session):
    async def _fake_builder(*args, **kwargs):
        return {
            "total_candidates": 2,
            "ready_candidates": 2,
            "not_ready_candidates": 0,
            "candidates": [
                _candidate(
                    candidate_id="candidate:1:1:1:100",
                    procurement_option_id=100,
                    planned_supplier_payment_date="2026-08-01",
                    forecast_customer_receipt_date="2026-08-10",
                ),
                _candidate(
                    candidate_id="candidate:1:1:1:101",
                    procurement_option_id=101,
                    planned_supplier_payment_date="2026-08-10",
                    forecast_customer_receipt_date="2026-08-01",
                ),
            ],
            "warnings": [],
            "trace_lines": [],
        }

    async def _fake_coverage(*args, **kwargs):
        return {
            "is_valid_for_solver_input": True,
            "blocking_issues": [],
            "warnings": [],
            "trace_lines": [],
        }

    monkeypatch.setattr(projection_service, "build_atomic_candidates_for_project", _fake_builder)
    monkeypatch.setattr(projection_service, "validate_candidate_coverage_for_project", _fake_coverage)
    result = await projection_service.project_financials_for_project(db_session, 1)

    by_candidate = {row["candidate_id"]: row for row in result["candidate_summaries"]}
    assert by_candidate["candidate:1:1:1:100"]["cash_gap_days"] == 9
    assert by_candidate["candidate:1:1:1:100"]["working_capital_exposure_amount"] == Decimal("100")
    assert by_candidate["candidate:1:1:1:101"]["cash_gap_days"] == -9
    assert by_candidate["candidate:1:1:1:101"]["working_capital_exposure_amount"] == Decimal("0")


@pytest.mark.asyncio
async def test_phase13f_margin_rules_same_currency_missing_revenue_and_mixed_currency(monkeypatch, db_session):
    async def _fake_builder(*args, **kwargs):
        return {
            "total_candidates": 3,
            "ready_candidates": 3,
            "not_ready_candidates": 0,
            "candidates": [
                _candidate(
                    candidate_id="candidate:1:1:1:200",
                    procurement_option_id=200,
                    customer_revenue_amount="150",
                    customer_revenue_currency="IRR",
                ),
                _candidate(
                    candidate_id="candidate:1:1:1:201",
                    procurement_option_id=201,
                    customer_revenue_amount=None,
                    gross_margin_amount=None,
                    gross_margin_ratio=None,
                ),
                _candidate(
                    candidate_id="candidate:1:1:1:202",
                    procurement_option_id=202,
                    customer_revenue_amount="150",
                    customer_revenue_currency="USD",
                ),
            ],
            "warnings": [],
            "trace_lines": [],
        }

    async def _fake_coverage(*args, **kwargs):
        return {
            "is_valid_for_solver_input": True,
            "blocking_issues": [],
            "warnings": [],
            "trace_lines": [],
        }

    monkeypatch.setattr(projection_service, "build_atomic_candidates_for_project", _fake_builder)
    monkeypatch.setattr(projection_service, "validate_candidate_coverage_for_project", _fake_coverage)
    result = await projection_service.project_financials_for_project(db_session, 1)
    warn_codes = {issue["code"] for issue in result["warnings"]}
    assert "CUSTOMER_REVENUE_NOT_AVAILABLE_FOR_MARGIN" in warn_codes
    assert "MARGIN_REQUIRES_FX_CONVERSION" in warn_codes

    by_candidate = {row["candidate_id"]: row for row in result["candidate_summaries"]}
    assert by_candidate["candidate:1:1:1:200"]["gross_margin_amount"] == Decimal("50")
    assert by_candidate["candidate:1:1:1:200"]["gross_margin_ratio"] is not None
    assert by_candidate["candidate:1:1:1:201"]["gross_margin_amount"] is None
    assert by_candidate["candidate:1:1:1:202"]["gross_margin_amount"] is None


@pytest.mark.asyncio
async def test_phase13f_multi_currency_period_summary_grouping_without_conversion(monkeypatch, db_session):
    async def _fake_builder(*args, **kwargs):
        return {
            "total_candidates": 2,
            "ready_candidates": 2,
            "not_ready_candidates": 0,
            "candidates": [
                _candidate(
                    candidate_id="candidate:1:1:1:300",
                    procurement_option_id=300,
                    landed_cost_currency="IRR",
                    customer_revenue_amount="150",
                    customer_revenue_currency="IRR",
                ),
                _candidate(
                    candidate_id="candidate:1:1:1:301",
                    procurement_option_id=301,
                    landed_cost_currency="USD",
                    customer_revenue_amount="150",
                    customer_revenue_currency="USD",
                ),
            ],
            "warnings": [],
            "trace_lines": [],
        }

    async def _fake_coverage(*args, **kwargs):
        return {
            "is_valid_for_solver_input": True,
            "blocking_issues": [],
            "warnings": [],
            "trace_lines": [],
        }

    monkeypatch.setattr(projection_service, "build_atomic_candidates_for_project", _fake_builder)
    monkeypatch.setattr(projection_service, "validate_candidate_coverage_for_project", _fake_coverage)
    result = await projection_service.project_financials_for_project(db_session, 1)
    warn_codes = {issue["code"] for issue in result["warnings"]}
    assert "MULTI_CURRENCY_PROJECTION_GROUPED_WITHOUT_CONVERSION" in warn_codes
    period_rows = [row for row in result["period_summaries"] if row["period_key"] == "2026-08"]
    assert len(period_rows) >= 2
    assert {"IRR", "USD"}.issubset({row["currency"] for row in period_rows})


@pytest.mark.asyncio
async def test_phase13f_coverage_failure_interaction_default_and_include_invalid(monkeypatch, db_session):
    async def _fake_builder(*args, **kwargs):
        return {
            "total_candidates": 1,
            "ready_candidates": 1,
            "not_ready_candidates": 0,
            "candidates": [_candidate(candidate_id="candidate:1:1:1:400", procurement_option_id=400)],
            "warnings": [],
            "trace_lines": [],
        }

    async def _fake_coverage(*args, **kwargs):
        return {
            "is_valid_for_solver_input": False,
            "blocking_issues": [
                {
                    "code": "INSUFFICIENT_CANDIDATE_POOL_COVERAGE",
                    "severity": "BLOCKING",
                    "message": "insufficient",
                    "trace_lines": [],
                }
            ],
            "warnings": [],
            "trace_lines": [],
        }

    monkeypatch.setattr(projection_service, "build_atomic_candidates_for_project", _fake_builder)
    monkeypatch.setattr(projection_service, "validate_candidate_coverage_for_project", _fake_coverage)

    default_result = await projection_service.project_financials_for_project(
        db_session, 1, include_invalid_coverage=False
    )
    default_block_codes = {issue["code"] for issue in default_result["blocking_issues"]}
    assert "COVERAGE_VALIDATION_FAILED" in default_block_codes
    assert default_result["projected_candidates"] == 0
    assert default_result["is_projection_complete"] is False

    include_result = await projection_service.project_financials_for_project(
        db_session, 1, include_invalid_coverage=True
    )
    include_warn_codes = {issue["code"] for issue in include_result["warnings"]}
    assert "COVERAGE_VALIDATION_FAILED" in include_warn_codes
    assert include_result["projected_candidates"] == 1
    assert include_result["is_projection_complete"] is False


@pytest.mark.asyncio
async def test_phase13f_not_ready_behavior(monkeypatch, db_session):
    async def _fake_builder(*args, **kwargs):
        include_not_ready = kwargs.get("include_not_ready", False)
        ready_candidate = _candidate(candidate_id="candidate:1:1:1:500", procurement_option_id=500, ready=True)
        not_ready_candidate = _candidate(
            candidate_id="candidate:1:1:1:501",
            procurement_option_id=501,
            ready=False,
            planned_supplier_payment_date=None,
        )
        candidates = [ready_candidate, not_ready_candidate] if include_not_ready else [ready_candidate]
        return {
            "total_candidates": len(candidates),
            "ready_candidates": 1,
            "not_ready_candidates": 1 if include_not_ready else 0,
            "candidates": candidates,
            "warnings": [],
            "trace_lines": [],
        }

    async def _fake_coverage(*args, **kwargs):
        return {
            "is_valid_for_solver_input": True,
            "blocking_issues": [],
            "warnings": [],
            "trace_lines": [],
        }

    monkeypatch.setattr(projection_service, "build_atomic_candidates_for_project", _fake_builder)
    monkeypatch.setattr(projection_service, "validate_candidate_coverage_for_project", _fake_coverage)

    default_result = await projection_service.project_financials_for_project(
        db_session, 1, include_not_ready=False
    )
    assert default_result["projected_candidates"] == 1
    assert default_result["is_projection_complete"] is True

    include_result = await projection_service.project_financials_for_project(
        db_session, 1, include_not_ready=True
    )
    include_warn_codes = {issue["code"] for issue in include_result["warnings"]}
    assert "NOT_READY_CANDIDATE_EXCLUDED_FROM_PROJECTION" in include_warn_codes
    assert include_result["projected_candidates"] == 1
    assert include_result["is_projection_complete"] is False
    assert "candidate:1:1:1:501" in include_result["excluded_candidates"]


@pytest.mark.asyncio
async def test_phase13f_projection_endpoint_is_read_only_no_side_effects(
    db_session, test_project, test_project_item, test_package, test_supplier, test_currency
):
    procurement_user = await _create_user(db_session, "phase13f_proc_readonly", "procurement")
    payment_method = await _create_payment_method(db_session, "e")

    test_project_item.quantity = 2
    test_package.main_item_quantity = 2
    await db_session.commit()

    delivery_option = await _create_delivery_option(
        db_session, test_project_item.id, Decimal("120")
    )
    option = await _create_option(
        db_session=db_session,
        procurement_user=procurement_user,
        test_project_item=test_project_item,
        test_package=test_package,
        test_supplier=test_supplier,
        test_currency=test_currency,
        payment_method_id=payment_method.id,
        planned_supplier_payment_date=date(2026, 7, 1),
        supplier_actual_delivery_date=date(2026, 7, 20),
        project_requested_delivery_date=date(2026, 7, 20),
        delivery_option_id=delivery_option.id,
    )
    await _add_component(db_session, procurement_user, option.id, "BASE_PRICE", "100", "IRR")
    await _add_component(db_session, procurement_user, option.id, "SHIPPING", "20", "IRR")

    before_counts = {
        "optimization_results": (
            await db_session.execute(select(func.count()).select_from(OptimizationResult))
        ).scalar_one(),
        "finalized_decisions": (
            await db_session.execute(select(func.count()).select_from(FinalizedDecision))
        ).scalar_one(),
        "cashflow_events": (
            await db_session.execute(select(func.count()).select_from(CashflowEvent))
        ).scalar_one(),
        "invoices": (await db_session.execute(select(func.count()).select_from(Invoice))).scalar_one(),
        "payments": (await db_session.execute(select(func.count()).select_from(Payment))).scalar_one(),
        "supplier_payments": (
            await db_session.execute(select(func.count()).select_from(SupplierPayment))
        ).scalar_one(),
        "procurement_options": (
            await db_session.execute(select(func.count()).select_from(ProcurementOption))
        ).scalar_one(),
        "procurement_cost_components": (
            await db_session.execute(select(func.count()).select_from(ProcurementCostComponent))
        ).scalar_one(),
        "project_items": (await db_session.execute(select(func.count()).select_from(ProjectItem))).scalar_one(),
        "packages": (await db_session.execute(select(func.count()).select_from(ProcurementPackage))).scalar_one(),
    }
    before_option = await db_session.get(ProcurementOption, option.id)
    before_item = await db_session.get(ProjectItem, test_project_item.id)
    before_package = await db_session.get(ProcurementPackage, test_package.id)

    app = FastAPI()
    app.include_router(projections_router_module.router)

    async def _override_get_db():
        yield db_session

    async def _override_get_current_user():
        return procurement_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get(f"/financial-projections/by-project/{test_project.id}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    after_counts = {
        "optimization_results": (
            await db_session.execute(select(func.count()).select_from(OptimizationResult))
        ).scalar_one(),
        "finalized_decisions": (
            await db_session.execute(select(func.count()).select_from(FinalizedDecision))
        ).scalar_one(),
        "cashflow_events": (
            await db_session.execute(select(func.count()).select_from(CashflowEvent))
        ).scalar_one(),
        "invoices": (await db_session.execute(select(func.count()).select_from(Invoice))).scalar_one(),
        "payments": (await db_session.execute(select(func.count()).select_from(Payment))).scalar_one(),
        "supplier_payments": (
            await db_session.execute(select(func.count()).select_from(SupplierPayment))
        ).scalar_one(),
        "procurement_options": (
            await db_session.execute(select(func.count()).select_from(ProcurementOption))
        ).scalar_one(),
        "procurement_cost_components": (
            await db_session.execute(select(func.count()).select_from(ProcurementCostComponent))
        ).scalar_one(),
        "project_items": (await db_session.execute(select(func.count()).select_from(ProjectItem))).scalar_one(),
        "packages": (await db_session.execute(select(func.count()).select_from(ProcurementPackage))).scalar_one(),
    }
    after_option = await db_session.get(ProcurementOption, option.id)
    after_item = await db_session.get(ProjectItem, test_project_item.id)
    after_package = await db_session.get(ProcurementPackage, test_package.id)

    assert before_counts == after_counts
    assert after_option.updated_at == before_option.updated_at
    assert after_item.updated_at == before_item.updated_at
    assert after_package.updated_at == before_package.updated_at
