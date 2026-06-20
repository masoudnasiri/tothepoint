"""
Phase 12D regression tests for controlled bulk optimization rollback.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models import (
    FinalizedDecision,
    ProcurementOption,
    ProcurementPackage,
    ProjectItem,
    Supplier,
    User,
)
from app.routers.packages import create_package
from app.schemas import ProcurementPackageCreate
from app.services.optimization_rollback_service import (
    build_bulk_rollback_preview,
    execute_bulk_rollback,
)
from app.services.package_combination_service import mark_project_item_sent_to_optimization


async def _create_user(db_session, username: str, role: str = "procurement") -> User:
    user = User(username=username, password_hash="hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_project_item(
    db_session,
    *,
    project_id: int,
    item_code: str,
    item_name: str,
    quantity: int = 1,
) -> ProjectItem:
    item = ProjectItem(
        project_id=project_id,
        item_code=item_code,
        item_name=item_name,
        quantity=quantity,
        delivery_options=["2026-02-01"],
        status="PENDING",
        is_finalized=True,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _create_supplier(
    db_session, *, supplier_id: str, company_name: str, country: str
) -> Supplier:
    supplier = Supplier(
        supplier_id=supplier_id,
        company_name=company_name,
        country=country,
        status="ACTIVE",
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    return supplier


async def _create_package_with_option(
    db_session,
    *,
    project_item: ProjectItem,
    supplier: Supplier,
    package_name: str,
    package_type: str,
    cost_amount: Decimal,
    purchase_date_value: date,
    delivery_date_value: date,
) -> tuple[ProcurementPackage, ProcurementOption]:
    package = ProcurementPackage(
        project_item_id=project_item.id,
        package_name=package_name,
        package_type=package_type,
        supplier_id=supplier.id,
        is_active=True,
        main_item_quantity=project_item.quantity,
    )
    db_session.add(package)
    await db_session.commit()
    await db_session.refresh(package)

    option = ProcurementOption(
        package_id=package.id,
        project_item_id=project_item.id,
        item_code=project_item.item_code,
        supplier_id=supplier.id,
        supplier_name=supplier.company_name,
        cost_amount=cost_amount,
        cost_currency="IRR",
        base_cost=cost_amount,
        shipping_cost=Decimal("0"),
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=True,
        purchase_date=purchase_date_value,
        expected_delivery_date=delivery_date_value,
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)
    return package, option


async def _mark_sent(
    db_session,
    *,
    project_item: ProjectItem,
    user_id: int,
    package: ProcurementPackage,
    option: ProcurementOption,
    coverage_classification: str = "FULL_COVERAGE",
    total_cost_irr: Decimal = Decimal("1000"),
    submitted_at: datetime | None = None,
    partial_coverage_acknowledged: bool = False,
):
    record = await mark_project_item_sent_to_optimization(
        db_session,
        project_item_id=project_item.id,
        user_id=user_id,
        partial_coverage_acknowledged=partial_coverage_acknowledged,
        summary_payload={
            "item_code": project_item.item_code,
            "item_name": project_item.item_name,
            "selected_combination": {
                "package_ids": [package.id],
                "option_ids": [option.id],
                "coverage_classification": coverage_classification,
                "is_over_coverage": False,
                "total_cost_irr": float(total_cost_irr),
                "latest_delivery_date": option.expected_delivery_date.isoformat()
                if option.expected_delivery_date
                else None,
                "earliest_purchase_date": option.purchase_date.isoformat()
                if option.purchase_date
                else None,
            },
        },
        notes="phase12d test submission",
    )
    if submitted_at is not None:
        record.submitted_at = submitted_at
    await db_session.commit()
    await db_session.refresh(record)
    return record


@pytest.mark.asyncio
async def test_phase12d_test_a_preview_finds_safe_sent_items(db_session, test_project):
    user = await _create_user(db_session, "phase12d_user_a", "procurement")
    supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-A",
        company_name="Local Supplier A",
        country="Iran",
    )
    item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-A",
        item_name="Phase12D Item A",
    )
    package, option = await _create_package_with_option(
        db_session,
        project_item=item,
        supplier=supplier,
        package_name="PKG-12D-A",
        package_type="FULL",
        cost_amount=Decimal("1200"),
        purchase_date_value=date(2026, 1, 1),
        delivery_date_value=date(2026, 1, 10),
    )
    await _mark_sent(
        db_session,
        project_item=item,
        user_id=user.id,
        package=package,
        option=option,
    )

    preview = await build_bulk_rollback_preview(db_session, filters={})
    rollback_ids = {row["project_item_id"] for row in preview["rollbackable_items"]}
    assert item.id in rollback_ids
    assert preview["summary"]["rollbackable_count"] >= 1


@pytest.mark.asyncio
async def test_phase12d_test_b_unsafe_item_skipped_with_reason(db_session, test_project):
    procurement_user = await _create_user(db_session, "phase12d_user_b_proc", "procurement")
    pm_user = await _create_user(db_session, "phase12d_user_b_pm", "pm")
    supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-B",
        company_name="Local Supplier B",
        country="Iran",
    )
    item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-B",
        item_name="Phase12D Item B",
    )
    package, option = await _create_package_with_option(
        db_session,
        project_item=item,
        supplier=supplier,
        package_name="PKG-12D-B",
        package_type="FULL",
        cost_amount=Decimal("900"),
        purchase_date_value=date(2026, 1, 2),
        delivery_date_value=date(2026, 1, 12),
    )
    await _mark_sent(
        db_session,
        project_item=item,
        user_id=procurement_user.id,
        package=package,
        option=option,
    )

    decision = FinalizedDecision(
        project_id=item.project_id,
        project_item_id=item.id,
        package_id=package.id,
        item_code=item.item_code,
        procurement_option_id=option.id,
        purchase_date=date(2026, 1, 5),
        delivery_date=date(2026, 1, 25),
        quantity=1,
        final_cost=Decimal("900"),
        final_cost_amount=Decimal("900"),
        final_cost_currency="IRR",
        status="LOCKED",
        decision_maker_id=pm_user.id,
        decision_date=datetime.utcnow(),
    )
    db_session.add(decision)
    await db_session.commit()

    preview = await build_bulk_rollback_preview(db_session, filters={})
    unsafe = [row for row in preview["unsafe_items"] if row["project_item_id"] == item.id]
    assert len(unsafe) == 1
    assert any(reason["code"] == "decision_exists" for reason in unsafe[0]["skip_reasons"])

    result = await execute_bulk_rollback(
        db_session,
        filters={},
        selected_item_ids=[item.id],
        confirmed=True,
        user_id=procurement_user.id,
    )
    assert result["rolled_back_items"] == []
    assert any(row["project_item_id"] == item.id for row in result["skipped_items"])


@pytest.mark.asyncio
async def test_phase12d_test_c_checklist_filter_applies_package_and_coverage(db_session, test_project):
    user = await _create_user(db_session, "phase12d_user_c", "procurement")
    domestic_supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-C1",
        company_name="Domestic C1",
        country="Iran",
    )
    foreign_supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-C2",
        company_name="Foreign C2",
        country="Germany",
    )

    full_item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-C-FULL",
        item_name="Phase12D Full",
    )
    full_package, full_option = await _create_package_with_option(
        db_session,
        project_item=full_item,
        supplier=domestic_supplier,
        package_name="PKG-12D-C-FULL",
        package_type="FULL",
        cost_amount=Decimal("1000"),
        purchase_date_value=date(2026, 1, 3),
        delivery_date_value=date(2026, 1, 13),
    )
    await _mark_sent(
        db_session,
        project_item=full_item,
        user_id=user.id,
        package=full_package,
        option=full_option,
        coverage_classification="FULL_COVERAGE",
    )

    partial_item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-C-PART",
        item_name="Phase12D Partial",
    )
    partial_package, partial_option = await _create_package_with_option(
        db_session,
        project_item=partial_item,
        supplier=foreign_supplier,
        package_name="PKG-12D-C-PART",
        package_type="PARTIAL",
        cost_amount=Decimal("1500"),
        purchase_date_value=date(2026, 1, 4),
        delivery_date_value=date(2026, 1, 15),
    )
    await _mark_sent(
        db_session,
        project_item=partial_item,
        user_id=user.id,
        package=partial_package,
        option=partial_option,
        coverage_classification="PARTIAL_COVERAGE",
        partial_coverage_acknowledged=True,
    )

    full_only = await build_bulk_rollback_preview(
        db_session,
        filters={
            "include_full_package_items": True,
            "include_partial_package_items": False,
            "include_complete_coverage_items": True,
            "include_incomplete_coverage_items": False,
        },
    )
    full_ids = {row["project_item_id"] for row in full_only["rollbackable_items"]}
    assert full_item.id in full_ids
    assert partial_item.id not in full_ids

    partial_only = await build_bulk_rollback_preview(
        db_session,
        filters={
            "include_full_package_items": False,
            "include_partial_package_items": True,
            "include_complete_coverage_items": False,
            "include_incomplete_coverage_items": True,
        },
    )
    partial_ids = {row["project_item_id"] for row in partial_only["rollbackable_items"]}
    assert partial_item.id in partial_ids
    assert full_item.id not in partial_ids


@pytest.mark.asyncio
async def test_phase12d_test_d_price_range_filter_uses_irr_equivalent(db_session, test_project):
    user = await _create_user(db_session, "phase12d_user_d", "procurement")
    supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-D",
        company_name="Supplier D",
        country="Iran",
    )

    low_item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-D-LOW",
        item_name="Low Cost Item",
    )
    low_package, low_option = await _create_package_with_option(
        db_session,
        project_item=low_item,
        supplier=supplier,
        package_name="PKG-12D-D-LOW",
        package_type="FULL",
        cost_amount=Decimal("1000"),
        purchase_date_value=date(2026, 1, 6),
        delivery_date_value=date(2026, 1, 16),
    )
    await _mark_sent(
        db_session,
        project_item=low_item,
        user_id=user.id,
        package=low_package,
        option=low_option,
        total_cost_irr=Decimal("1000"),
    )

    high_item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-D-HIGH",
        item_name="High Cost Item",
    )
    high_package, high_option = await _create_package_with_option(
        db_session,
        project_item=high_item,
        supplier=supplier,
        package_name="PKG-12D-D-HIGH",
        package_type="FULL",
        cost_amount=Decimal("5000"),
        purchase_date_value=date(2026, 1, 7),
        delivery_date_value=date(2026, 1, 17),
    )
    await _mark_sent(
        db_session,
        project_item=high_item,
        user_id=user.id,
        package=high_package,
        option=high_option,
        total_cost_irr=Decimal("5000"),
    )

    preview = await build_bulk_rollback_preview(
        db_session,
        filters={"min_total_cost_irr": 2000, "max_total_cost_irr": 6000},
    )
    rollback_ids = {row["project_item_id"] for row in preview["rollbackable_items"]}
    assert high_item.id in rollback_ids
    assert low_item.id not in rollback_ids


@pytest.mark.asyncio
async def test_phase12d_test_e_date_range_filter_uses_selected_date_field(db_session, test_project):
    user = await _create_user(db_session, "phase12d_user_e", "procurement")
    supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-E",
        company_name="Supplier E",
        country="Iran",
    )

    jan_item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-E-JAN",
        item_name="Jan Item",
    )
    jan_package, jan_option = await _create_package_with_option(
        db_session,
        project_item=jan_item,
        supplier=supplier,
        package_name="PKG-12D-E-JAN",
        package_type="FULL",
        cost_amount=Decimal("900"),
        purchase_date_value=date(2026, 1, 8),
        delivery_date_value=date(2026, 1, 20),
    )
    await _mark_sent(
        db_session,
        project_item=jan_item,
        user_id=user.id,
        package=jan_package,
        option=jan_option,
        submitted_at=datetime(2026, 1, 10, 8, 0, 0),
    )

    mar_item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-E-MAR",
        item_name="Mar Item",
    )
    mar_package, mar_option = await _create_package_with_option(
        db_session,
        project_item=mar_item,
        supplier=supplier,
        package_name="PKG-12D-E-MAR",
        package_type="FULL",
        cost_amount=Decimal("1100"),
        purchase_date_value=date(2026, 3, 5),
        delivery_date_value=date(2026, 3, 20),
    )
    await _mark_sent(
        db_session,
        project_item=mar_item,
        user_id=user.id,
        package=mar_package,
        option=mar_option,
        submitted_at=datetime(2026, 3, 10, 9, 0, 0),
    )

    preview = await build_bulk_rollback_preview(
        db_session,
        filters={
            "date_field": "submitted_at",
            "date_from": "2026-02-01",
            "date_to": "2026-04-01",
        },
    )
    rollback_ids = {row["project_item_id"] for row in preview["rollbackable_items"]}
    assert mar_item.id in rollback_ids
    assert jan_item.id not in rollback_ids


@pytest.mark.asyncio
async def test_phase12d_test_f_execute_rollback_unlocks_item_for_package_edit(db_session, test_project):
    procurement_user = await _create_user(db_session, "phase12d_user_f_proc", "procurement")
    supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-F",
        company_name="Supplier F",
        country="Iran",
    )
    item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-F",
        item_name="Unlock Item",
    )
    package, option = await _create_package_with_option(
        db_session,
        project_item=item,
        supplier=supplier,
        package_name="PKG-12D-F",
        package_type="FULL",
        cost_amount=Decimal("1300"),
        purchase_date_value=date(2026, 1, 9),
        delivery_date_value=date(2026, 1, 25),
    )
    await _mark_sent(
        db_session,
        project_item=item,
        user_id=procurement_user.id,
        package=package,
        option=option,
    )

    with pytest.raises(HTTPException) as locked_error:
        await create_package(
            package_data=ProcurementPackageCreate(
                project_item_id=item.id,
                package_name="PKG-LOCKED-ATTEMPT",
                package_type="PARTIAL",
                supplier_id=supplier.id,
                description="Should fail while item is sent",
                main_item_quantity=1,
            ),
            current_user=procurement_user,
            db=db_session,
        )
    assert locked_error.value.status_code == 400

    result = await execute_bulk_rollback(
        db_session,
        filters={},
        selected_item_ids=[item.id],
        confirmed=True,
        user_id=procurement_user.id,
    )
    assert len(result["rolled_back_items"]) == 1
    await db_session.commit()

    unlocked_package = await create_package(
        package_data=ProcurementPackageCreate(
            project_item_id=item.id,
            package_name="PKG-UNLOCKED-OK",
            package_type="PARTIAL",
            supplier_id=supplier.id,
            description="Should succeed after rollback",
            main_item_quantity=1,
        ),
        current_user=procurement_user,
        db=db_session,
    )
    assert unlocked_package.id is not None


@pytest.mark.asyncio
async def test_phase12d_test_g_execute_requires_confirmation(db_session, test_project):
    user = await _create_user(db_session, "phase12d_user_g", "procurement")
    supplier = await _create_supplier(
        db_session,
        supplier_id="SUP-12D-G",
        company_name="Supplier G",
        country="Iran",
    )
    item = await _create_project_item(
        db_session,
        project_id=test_project.id,
        item_code="PH12D-G",
        item_name="Confirm Required Item",
    )
    package, option = await _create_package_with_option(
        db_session,
        project_item=item,
        supplier=supplier,
        package_name="PKG-12D-G",
        package_type="FULL",
        cost_amount=Decimal("1000"),
        purchase_date_value=date(2026, 1, 11),
        delivery_date_value=date(2026, 1, 21),
    )
    await _mark_sent(
        db_session,
        project_item=item,
        user_id=user.id,
        package=package,
        option=option,
    )

    with pytest.raises(HTTPException) as exc:
        await execute_bulk_rollback(
            db_session,
            filters={},
            selected_item_ids=[item.id],
            confirmed=False,
            user_id=user.id,
        )
    assert exc.value.status_code == 400
