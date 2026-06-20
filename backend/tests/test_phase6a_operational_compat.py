"""
Phase 6A regression tests for operational compatibility hardening.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest

from app.models import FinalizedDecision, ProcurementOption, SupplierPayment as SupplierPaymentModel
from app.routers.invoice_payment_simple import list_invoices
from app.routers.procurement_plan import _batch_calculate_payment_statuses
from app.routers.supplier_payments import get_decision_supplier_payments


async def _create_procurement_option(db_session, test_project_item, test_supplier, test_currency, test_package):
    option = ProcurementOption(
        package_id=test_package.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        supplier_name=test_supplier.company_name,
        supplier_id=test_supplier.id,
        cost_amount=Decimal("1000.00"),
        cost_currency="USD",
        base_cost=Decimal("1000.00"),
        currency_id=test_currency.id,
        payment_terms={"type": "cash"},
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)
    return option


async def _create_locked_decision(db_session, test_user, test_project, test_project_item, option, test_package):
    decision = FinalizedDecision(
        project_id=test_project.id,
        project_item_id=test_project_item.id,
        package_id=test_package.id,
        item_code=test_project_item.item_code,
        procurement_option_id=option.id,
        purchase_date=date.today(),
        delivery_date=date.today(),
        quantity=1,
        final_cost_amount=Decimal("1000.00"),
        final_cost_currency="USD",
        final_cost=Decimal("1000.00"),
        status="LOCKED",
        decision_maker_id=test_user.id,
        decision_date=datetime.utcnow(),
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)
    return decision


@pytest.mark.asyncio
async def test_supplier_payment_decision_endpoint_uses_orm_model(
    db_session, test_user, test_project, test_project_item, test_supplier, test_currency, test_package
):
    option = await _create_procurement_option(
        db_session, test_project_item, test_supplier, test_currency, test_package
    )
    decision = await _create_locked_decision(
        db_session, test_user, test_project, test_project_item, option, test_package
    )

    payment = SupplierPaymentModel(
        decision_id=decision.id,
        package_id=test_package.id,
        supplier_id=test_supplier.id,
        supplier_name=test_supplier.company_name,
        item_code=test_project_item.item_code,
        project_id=test_project.id,
        payment_date=date.today(),
        payment_amount=Decimal("500.00"),
        currency="USD",
        payment_method="bank_transfer",
        status="completed",
        created_by_id=test_user.id,
    )
    db_session.add(payment)
    await db_session.commit()

    rows = await get_decision_supplier_payments(
        decision_id=decision.id,
        current_user=test_user,
        db=db_session,
    )

    assert len(rows) == 1
    assert rows[0]["decision_id"] == decision.id
    assert rows[0]["package_id"] == test_package.id
    assert rows[0]["supplier_id"] == test_supplier.id


@pytest.mark.asyncio
async def test_procurement_plan_payment_in_status_falls_back_to_decision_fields(
    db_session, test_user, test_project, test_project_item, test_supplier, test_currency, test_package
):
    option = await _create_procurement_option(
        db_session, test_project_item, test_supplier, test_currency, test_package
    )
    decision = await _create_locked_decision(
        db_session, test_user, test_project, test_project_item, option, test_package
    )
    decision.actual_invoice_amount = Decimal("1000.00")
    decision.actual_payment_amount = Decimal("1000.00")
    decision.actual_invoice_issue_date = date.today()
    decision.actual_payment_date = date.today()
    await db_session.commit()

    statuses = await _batch_calculate_payment_statuses([decision.id], db_session)

    assert statuses[decision.id]["payment_in_status"] == "fully_paid"


@pytest.mark.asyncio
async def test_invoice_list_exposes_package_and_supplier_traceability(
    db_session, test_user, test_project, test_project_item, test_supplier, test_currency, test_package
):
    option = await _create_procurement_option(
        db_session, test_project_item, test_supplier, test_currency, test_package
    )
    decision = await _create_locked_decision(
        db_session, test_user, test_project, test_project_item, option, test_package
    )
    decision.actual_invoice_issue_date = date.today()
    decision.actual_invoice_amount = Decimal("1200.00")
    decision.actual_invoice_amount_currency = "USD"
    await db_session.commit()

    invoices = await list_invoices(
        search=None,
        status=None,
        project_id=None,
        supplier_id=None,
        start_date=None,
        end_date=None,
        page=1,
        limit=50,
        db=db_session,
    )

    assert len(invoices) == 1
    assert invoices[0].package_id == test_package.id
    assert invoices[0].package_name == test_package.package_name
    assert invoices[0].supplier_id == test_supplier.id
    assert invoices[0].supplier_name == test_supplier.company_name
