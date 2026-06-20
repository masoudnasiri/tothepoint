"""
Phase 12C regression tests for package finalization and optimization submission gate.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import select

from app.models import (
    FinalizedDecision,
    ItemMaster,
    ItemSubItem,
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    ProjectItemSubItem,
    User,
)
from app.routers.packages import (
    create_package,
    delete_package,
    rollback_packages_from_optimization,
    submit_packages_to_optimization,
    update_package,
)
from app.schemas import (
    OptimizationSubmissionRequest,
    OptimizationSubmissionRollbackRequest,
    ProcurementPackageCreate,
    ProcurementPackageUpdate,
)
from app.services.package_combination_service import (
    analyze_project_item_package_combinations,
    compute_item_coverage_state,
)
from app.services.package_service import calculate_coverage_summary


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def _create_requirement(
    db_session, *, project_item_id: int, required_quantity: int, suffix: str
) -> ProjectItemSubItem:
    master = ItemMaster(
        item_code=f"PH12C-REQ-{suffix}",
        company="Phase12C",
        item_name=f"Req {suffix}",
        model=f"M-{suffix}",
        is_active=True,
    )
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    subitem = ItemSubItem(
        item_master_id=master.id,
        name=f"Sub {suffix}",
        part_number=f"PN-{suffix}",
    )
    db_session.add(subitem)
    await db_session.commit()
    await db_session.refresh(subitem)

    req = ProjectItemSubItem(
        project_item_id=project_item_id,
        item_subitem_id=subitem.id,
        quantity=required_quantity,
    )
    db_session.add(req)
    await db_session.commit()
    await db_session.refresh(req)
    return req


async def _create_package_with_option(
    db_session,
    *,
    project_item_id: int,
    item_code: str,
    package_name: str,
    main_qty: int,
    is_finalized: bool,
    cost: Decimal = Decimal("1000.00"),
) -> ProcurementPackage:
    package = ProcurementPackage(
        project_item_id=project_item_id,
        package_name=package_name,
        package_type="PARTIAL",
        is_active=True,
        main_item_quantity=main_qty,
    )
    db_session.add(package)
    await db_session.commit()
    await db_session.refresh(package)

    option = ProcurementOption(
        package_id=package.id,
        project_item_id=project_item_id,
        item_code=item_code,
        supplier_name=f"Supplier-{package_name}",
        cost_amount=cost,
        cost_currency="IRR",
        base_cost=cost,
        shipping_cost=Decimal("0"),
        payment_terms={"type": "cash"},
        is_active=True,
        is_finalized=is_finalized,
        purchase_date=date(2026, 1, 1),
        expected_delivery_date=date(2026, 1, 10),
    )
    db_session.add(option)
    await db_session.commit()
    await db_session.refresh(option)
    return package


@pytest.mark.asyncio
async def test_phase12c_test_a_finalized_package_status_and_nonfinalized_exclusion(
    db_session, test_project_item
):
    procurement_user = await _create_user(db_session, "phase12c_proc_a", "procurement")

    finalized_pkg = await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-FINAL",
        main_qty=1,
        is_finalized=True,
    )
    await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-DRAFT",
        main_qty=1,
        is_finalized=False,
    )

    analysis = await analyze_project_item_package_combinations(
        db_session, project_item_id=test_project_item.id
    )
    finalized_ids = {p["package_id"] for p in analysis["finalized_packages"]}
    assert finalized_pkg.id in finalized_ids

    # Remove finalized flag by deactivating finalized option path and verify submission rejects draft-only items.
    await db_session.execute(
        ProcurementOption.__table__.update()
        .where(ProcurementOption.package_id == finalized_pkg.id)
        .values(is_finalized=False)
    )
    await db_session.commit()

    response = await submit_packages_to_optimization(
        request=OptimizationSubmissionRequest(project_item_id=test_project_item.id),
        current_user=procurement_user,
        db=db_session,
    )
    assert response["submitted_items"] == []
    assert any(
        row.get("reason") == "no_finalized_packages" for row in response["skipped_items"]
    )


@pytest.mark.asyncio
async def test_phase12c_test_b_partial_packages_can_form_full_combination(
    db_session, test_project_item
):
    sub_a = await _create_requirement(
        db_session, project_item_id=test_project_item.id, required_quantity=5, suffix="A"
    )
    sub_b = await _create_requirement(
        db_session, project_item_id=test_project_item.id, required_quantity=5, suffix="B"
    )

    pkg_a = await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-A",
        main_qty=0,
        is_finalized=True,
    )
    pkg_b = await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-B",
        main_qty=1,
        is_finalized=True,
    )
    db_session.add(
        PackageSubItem(
            package_id=pkg_a.id,
            project_item_subitem_id=sub_a.id,
            quantity_covered=5,
            is_fully_covered=True,
            coverage_percentage=Decimal("100.00"),
        )
    )
    db_session.add(
        PackageSubItem(
            package_id=pkg_b.id,
            project_item_subitem_id=sub_b.id,
            quantity_covered=5,
            is_fully_covered=True,
            coverage_percentage=Decimal("100.00"),
        )
    )
    await db_session.commit()

    analysis = await analyze_project_item_package_combinations(
        db_session, project_item_id=test_project_item.id
    )
    full_sets = [tuple(c["package_ids"]) for c in analysis["full_coverage_combinations"]]
    assert tuple(sorted([pkg_a.id, pkg_b.id])) in full_sets


@pytest.mark.asyncio
async def test_phase12c_test_c_multiple_valid_combinations_generated(
    db_session, test_project_item
):
    test_project_item.quantity = 10
    await db_session.commit()

    p1 = await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-1",
        main_qty=5,
        is_finalized=True,
        cost=Decimal("1000"),
    )
    p2 = await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-2",
        main_qty=5,
        is_finalized=True,
        cost=Decimal("1200"),
    )
    p3 = await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-3",
        main_qty=5,
        is_finalized=True,
        cost=Decimal("900"),
    )

    analysis = await analyze_project_item_package_combinations(
        db_session, project_item_id=test_project_item.id
    )
    combos = [set(c["package_ids"]) for c in analysis["full_coverage_combinations"]]
    assert {p1.id, p2.id} in combos
    assert {p2.id, p3.id} in combos


@pytest.mark.asyncio
async def test_phase12c_test_d_incomplete_requires_confirmation(
    db_session, test_project_item
):
    procurement_user = await _create_user(db_session, "phase12c_proc_d", "procurement")
    test_project_item.quantity = 10
    await db_session.commit()

    await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-PARTIAL",
        main_qty=4,
        is_finalized=True,
    )

    first = await submit_packages_to_optimization(
        request=OptimizationSubmissionRequest(project_item_id=test_project_item.id),
        current_user=procurement_user,
        db=db_session,
    )
    assert first["submitted_items"] == []
    assert len(first["incomplete_items_requiring_confirmation"]) == 1

    second = await submit_packages_to_optimization(
        request=OptimizationSubmissionRequest(
            project_item_id=test_project_item.id,
            include_incomplete_with_confirmation=True,
            confirmed_incomplete_item_ids=[test_project_item.id],
        ),
        current_user=procurement_user,
        db=db_session,
    )
    assert len(second["submitted_items"]) == 1
    assert second["submitted_items"][0]["partial_coverage_acknowledged"] is True


@pytest.mark.asyncio
async def test_phase12c_test_e_sent_items_lock_and_safe_rollback(
    db_session, test_project_item
):
    procurement_user = await _create_user(db_session, "phase12c_proc_e", "procurement")
    pm_user = await _create_user(db_session, "phase12c_pm_e", "pm")
    package = await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-LOCK",
        main_qty=1,
        is_finalized=True,
    )

    submit_response = await submit_packages_to_optimization(
        request=OptimizationSubmissionRequest(project_item_id=test_project_item.id),
        current_user=procurement_user,
        db=db_session,
    )
    assert len(submit_response["submitted_items"]) == 1

    with pytest.raises(HTTPException) as create_exc:
        await create_package(
            package_data=ProcurementPackageCreate(
                project_item_id=test_project_item.id,
                package_name="PKG-NEW-BLOCKED",
                package_type="PARTIAL",
                supplier_id=None,
                description=None,
                is_active=True,
                main_item_quantity=1,
                is_finalized=False,
            ),
            current_user=procurement_user,
            db=db_session,
        )
    assert create_exc.value.status_code == 400

    # Rollback blocked when active decisions exist.
    option_result = await db_session.execute(
        select(ProcurementOption).where(ProcurementOption.package_id == package.id)
    )
    option = option_result.scalar_one()
    db_session.add(
        FinalizedDecision(
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            package_id=package.id,
            item_code=test_project_item.item_code,
            procurement_option_id=option.id,
            purchase_date=date.today(),
            delivery_date=date.today(),
            quantity=1,
            final_cost_amount=Decimal("1000"),
            final_cost_currency="IRR",
            final_cost=Decimal("1000"),
            decision_maker_id=pm_user.id,
            decision_date=datetime.utcnow(),
            status="LOCKED",
        )
    )
    await db_session.commit()

    with pytest.raises(HTTPException) as rollback_exc:
        await rollback_packages_from_optimization(
            project_item_id=test_project_item.id,
            request=OptimizationSubmissionRollbackRequest(notes="unsafe rollback"),
            current_user=procurement_user,
            db=db_session,
        )
    assert rollback_exc.value.status_code == 400

    # Clear blocking decision, rollback succeeds, editing is restored.
    await db_session.execute(
        FinalizedDecision.__table__.delete().where(
            FinalizedDecision.project_item_id == test_project_item.id
        )
    )
    await db_session.commit()

    rollback_response = await rollback_packages_from_optimization(
        project_item_id=test_project_item.id,
        request=OptimizationSubmissionRollbackRequest(notes="safe rollback"),
        current_user=procurement_user,
        db=db_session,
    )
    assert rollback_response["status"] == "ROLLED_BACK"

    updated = await update_package(
        package_id=package.id,
        package_data=ProcurementPackageUpdate(description="editable-again"),
        current_user=procurement_user,
        db=db_session,
    )
    assert updated.description == "editable-again"

    await delete_package(package_id=package.id, current_user=procurement_user, db=db_session)


@pytest.mark.asyncio
async def test_phase12c_test_f_coverage_semantics_consistency(
    db_session, test_project_item
):
    test_project_item.quantity = 10
    await db_session.commit()

    await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-OVR-1",
        main_qty=10,
        is_finalized=True,
    )
    await _create_package_with_option(
        db_session,
        project_item_id=test_project_item.id,
        item_code=test_project_item.item_code,
        package_name="PKG-OVR-2",
        main_qty=10,
        is_finalized=True,
    )

    summary = await calculate_coverage_summary(db_session, test_project_item.id)
    assert summary["main_item"]["covered"] == 20
    assert summary["main_item"]["required"] == 10
    assert summary["is_fully_covered"] is True
    assert compute_item_coverage_state(summary) == "OVER_COVERED"
