"""
Phase 8 release-candidate smoke tests.

Scope:
- package coverage fail/pass behavior
- locked decision visibility in procurement plan
- invoice/payment metadata package/supplier traceability
- supplier-payment by-decision endpoint behavior
- cashflow reflection after finance action
- audit log write for lifecycle action
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.config import settings
from app.models import (
    AuditLog,
    CashflowEvent,
    FinalizedDecision,
    ItemMaster,
    ItemSubItem,
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    ProjectItemSubItem,
    Supplier,
    SupplierPayment as SupplierPaymentModel,
    User,
)
from app.routers.invoice_payment_simple import create_payment, list_invoices
from app.routers.procurement_plan import list_procurement_plan
from app.routers.supplier_payments import create_supplier_payment, get_decision_supplier_payments
from app.schemas import PaymentCreate, SupplierPaymentCreate
from app.services.package_service import validate_package_coverage_for_lock


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_supplier(db_session, supplier_code: str, company_name: str) -> Supplier:
    supplier = Supplier(
        supplier_id=supplier_code,
        company_name=company_name,
        status="ACTIVE",
        risk_level="LOW",
        compliance_status="APPROVED",
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


async def _create_option_and_decision(
    db_session,
    *,
    project_id: int,
    project_item_id: int,
    item_code: str,
    user_id: int,
    package_id: int,
    supplier: Supplier,
    currency_id: int,
    status: str,
    final_cost: Decimal = Decimal("1000.00"),
):
    option = ProcurementOption(
        package_id=package_id,
        project_item_id=project_item_id,
        item_code=item_code,
        supplier_name=supplier.company_name,
        supplier_id=supplier.id,
        cost_amount=final_cost,
        cost_currency="USD",
        base_cost=final_cost,
        currency_id=currency_id,
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)

    decision = FinalizedDecision(
        project_id=project_id,
        project_item_id=project_item_id,
        package_id=package_id,
        item_code=item_code,
        procurement_option_id=option.id,
        purchase_date=date.today(),
        delivery_date=date.today(),
        quantity=1,
        final_cost_amount=final_cost,
        final_cost_currency="USD",
        final_cost=final_cost,
        decision_maker_id=user_id,
        decision_date=datetime.utcnow(),
        status=status,
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)
    return option, decision


@pytest.mark.asyncio
async def test_phase8_smoke_package_coverage_fail_and_pass(
    db_session, test_user, test_project_item, test_currency
):
    prev_pkg = settings.enable_package_procurement
    prev_guard = settings.enforce_package_coverage_on_lock
    settings.enable_package_procurement = True
    settings.enforce_package_coverage_on_lock = True

    try:
        supplier = await _create_supplier(
            db_session, "DEMO-RC8-SUP-COVER", "DEMO RC8 Coverage Supplier"
        )

        master = ItemMaster(
            item_code="DEMO-RC8-MASTER-COVER",
            company="DemoCo",
            item_name="Coverage Item",
            model="COV-1",
            is_active=True,
        )
        db_session.add(master)
        await db_session.commit()
        await db_session.refresh(master)

        subitem = ItemSubItem(
            item_master_id=master.id,
            name="CPU",
            part_number="DEMO-RC8-PN-COVER",
        )
        db_session.add(subitem)
        await db_session.commit()
        await db_session.refresh(subitem)

        requirement = ProjectItemSubItem(
            project_item_id=test_project_item.id,
            item_subitem_id=subitem.id,
            quantity=5,
        )
        db_session.add(requirement)
        await db_session.commit()
        await db_session.refresh(requirement)

        pkg_incomplete = ProcurementPackage(
            project_item_id=test_project_item.id,
            package_name="DEMO-RC8-PKG-INCOMPLETE",
            package_type="PARTIAL",
            supplier_id=supplier.id,
            is_active=True,
        )
        pkg_complete = ProcurementPackage(
            project_item_id=test_project_item.id,
            package_name="DEMO-RC8-PKG-COMPLETE",
            package_type="FULL",
            supplier_id=supplier.id,
            is_active=True,
        )
        db_session.add(pkg_incomplete)
        db_session.add(pkg_complete)
        await db_session.commit()
        await db_session.refresh(pkg_incomplete)
        await db_session.refresh(pkg_complete)

        db_session.add(
            PackageSubItem(
                package_id=pkg_incomplete.id,
                project_item_subitem_id=requirement.id,
                quantity_covered=2,
                is_fully_covered=False,
                coverage_percentage=Decimal("40"),
            )
        )
        db_session.add(
            PackageSubItem(
                package_id=pkg_complete.id,
                project_item_subitem_id=requirement.id,
                quantity_covered=5,
                is_fully_covered=True,
                coverage_percentage=Decimal("100"),
            )
        )
        await db_session.commit()

        _, fail_decision = await _create_option_and_decision(
            db_session,
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            user_id=test_user.id,
            package_id=pkg_incomplete.id,
            supplier=supplier,
            currency_id=test_currency.id,
            status="PROPOSED",
        )
        _, pass_decision = await _create_option_and_decision(
            db_session,
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            user_id=test_user.id,
            package_id=pkg_complete.id,
            supplier=supplier,
            currency_id=test_currency.id,
            status="PROPOSED",
        )

        with pytest.raises(HTTPException) as exc_info:
            await validate_package_coverage_for_lock(db_session, [fail_decision.id])
        assert exc_info.value.status_code == 400

        await validate_package_coverage_for_lock(db_session, [pass_decision.id])
    finally:
        settings.enable_package_procurement = prev_pkg
        settings.enforce_package_coverage_on_lock = prev_guard


@pytest.mark.asyncio
async def test_phase8_smoke_procurement_plan_and_metadata(
    db_session, test_user, test_project, test_project_item, test_currency
):
    procurement_user = await _create_user(
        db_session, "phase8_procurement", "procurement"
    )
    supplier = await _create_supplier(
        db_session, "DEMO-RC8-SUP-META", "DEMO RC8 Metadata Supplier"
    )

    package = ProcurementPackage(
        project_item_id=test_project_item.id,
        package_name="DEMO-RC8-PKG-META",
        package_type="FULL",
        supplier_id=supplier.id,
        is_active=True,
    )
    db_session.add(package)
    await db_session.commit()
    await db_session.refresh(package)

    _, decision = await _create_option_and_decision(
        db_session,
        project_id=test_project.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        user_id=test_user.id,
        package_id=package.id,
        supplier=supplier,
        currency_id=test_currency.id,
        status="LOCKED",
        final_cost=Decimal("1500.00"),
    )
    decision.actual_invoice_issue_date = date.today()
    decision.actual_invoice_amount = Decimal("1700.00")
    decision.actual_invoice_amount_currency = "USD"
    await db_session.commit()

    supplier_payment = SupplierPaymentModel(
        decision_id=decision.id,
        package_id=package.id,
        supplier_id=supplier.id,
        supplier_name=supplier.company_name,
        item_code=test_project_item.item_code,
        project_id=test_project.id,
        payment_date=date.today(),
        payment_amount=Decimal("900.00"),
        currency="USD",
        payment_method="bank_transfer",
        status="completed",
        created_by_id=test_user.id,
    )
    db_session.add(supplier_payment)
    await db_session.commit()

    plan = await list_procurement_plan(current_user=procurement_user, db=db_session)
    assert any(item["id"] == decision.id for item in plan["items"])

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
    matched = [inv for inv in invoices if inv.decision_id == decision.id]
    assert matched
    assert matched[0].package_id == package.id
    assert matched[0].supplier_id == supplier.id

    supplier_rows = await get_decision_supplier_payments(
        decision_id=decision.id,
        current_user=procurement_user,
        db=db_session,
    )
    assert supplier_rows
    assert supplier_rows[0]["package_id"] == package.id
    assert supplier_rows[0]["supplier_id"] == supplier.id


@pytest.mark.asyncio
async def test_phase8_smoke_cashflow_and_audit_lifecycle(
    db_session, test_project, test_project_item, test_currency
):
    admin_user = await _create_user(db_session, "phase8_admin", "admin")
    supplier = await _create_supplier(
        db_session, "DEMO-RC8-SUP-FIN", "DEMO RC8 Finance Supplier"
    )

    package = ProcurementPackage(
        project_item_id=test_project_item.id,
        package_name="DEMO-RC8-PKG-FIN",
        package_type="FULL",
        supplier_id=supplier.id,
        is_active=True,
    )
    db_session.add(package)
    await db_session.commit()
    await db_session.refresh(package)

    _, decision = await _create_option_and_decision(
        db_session,
        project_id=test_project.id,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        user_id=admin_user.id,
        package_id=package.id,
        supplier=supplier,
        currency_id=test_currency.id,
        status="LOCKED",
        final_cost=Decimal("1200.00"),
    )

    await create_payment(
        payment=PaymentCreate(
            invoice_id=decision.id,
            payment_date=date.today().isoformat(),
            payment_amount=Decimal("1400.00"),
            currency="USD",
            payment_method="bank_transfer",
            reference_number="DEMO-RC8-PAY-IN",
            notes="phase8 smoke inflow",
        ),
        db=db_session,
    )

    cashflow_rows = (
        await db_session.execute(
            select(CashflowEvent).where(
                CashflowEvent.related_decision_id == decision.id,
                CashflowEvent.event_type == "INFLOW",
                CashflowEvent.forecast_type == "ACTUAL",
            )
        )
    ).scalars().all()
    assert cashflow_rows, "Expected ACTUAL INFLOW cashflow row after payment create"

    supplier_payment_response = await create_supplier_payment(
        payment_data=SupplierPaymentCreate(
            decision_id=decision.id,
            supplier_name=supplier.company_name,
            supplier_id=supplier.id,
            item_code=test_project_item.item_code,
            project_id=test_project.id,
            package_id=package.id,
            payment_date=date.today(),
            payment_amount=Decimal("800.00"),
            currency="USD",
            payment_method="bank_transfer",
            reference_number="DEMO-RC8-PAY-OUT",
            notes="phase8 smoke outflow",
            status="completed",
        ),
        current_user=admin_user,
        db=db_session,
    )

    audit_row = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.action == "SUPPLIER_PAYMENT_CREATE",
                AuditLog.entity_id == supplier_payment_response["id"],
            )
        )
    ).scalar_one_or_none()
    assert audit_row is not None, "Expected audit log row for supplier payment creation"
