"""
Phase 5 tests for package coverage enforcement at lock/finalize boundary.
"""

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.config import settings
from app.models import (
    ItemMaster,
    ItemSubItem,
    ProjectItemSubItem,
    ProcurementOption,
    ProcurementPackage,
    PackageSubItem,
    FinalizedDecision,
)
from app.services.package_service import validate_package_coverage_for_lock


async def _create_requirement(db_session, project_item_id: int, required_quantity: int):
    master = ItemMaster(
        item_code=f"REQ-{project_item_id}-{required_quantity}",
        company="TestCo",
        item_name="Requirement Item",
        model="M1",
        is_active=True,
    )
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    subitem = ItemSubItem(
        item_master_id=master.id,
        name="Sub requirement",
        part_number=f"PN-{master.id}",
    )
    db_session.add(subitem)
    await db_session.commit()
    await db_session.refresh(subitem)

    requirement = ProjectItemSubItem(
        project_item_id=project_item_id,
        item_subitem_id=subitem.id,
        quantity=required_quantity,
    )
    db_session.add(requirement)
    await db_session.commit()
    await db_session.refresh(requirement)
    return requirement


async def _create_option_and_decision(
    db_session,
    *,
    package_id: int,
    project_id: int,
    project_item_id: int,
    item_code: str,
    user_id: int,
    status: str,
):
    option = ProcurementOption(
        package_id=package_id,
        project_item_id=project_item_id,
        item_code=item_code,
        supplier_name=f"Supplier-{package_id}",
        cost_amount=Decimal("1000"),
        cost_currency="IRR",
        base_cost=Decimal("1000"),
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
        final_cost_amount=Decimal("1000"),
        final_cost_currency="IRR",
        final_cost=Decimal("1000"),
        decision_maker_id=user_id,
        decision_date=datetime.utcnow(),
        status=status,
    )
    db_session.add(decision)
    await db_session.commit()
    await db_session.refresh(decision)
    return decision


@pytest.mark.asyncio
async def test_lock_coverage_enforcement_disabled_is_noop(
    db_session, test_user, test_project_item, test_package
):
    prev_pkg = settings.enable_package_procurement
    prev_guard = settings.enforce_package_coverage_on_lock
    settings.enable_package_procurement = True
    settings.enforce_package_coverage_on_lock = False

    try:
        requirement = await _create_requirement(db_session, test_project_item.id, required_quantity=5)
        db_session.add(
            PackageSubItem(
                package_id=test_package.id,
                project_item_subitem_id=requirement.id,
                quantity_covered=2,
                is_fully_covered=False,
                coverage_percentage=40,
            )
        )
        await db_session.commit()

        decision = await _create_option_and_decision(
            db_session,
            package_id=test_package.id,
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            user_id=test_user.id,
            status="PROPOSED",
        )

        # Should not raise when guard flag is disabled.
        await validate_package_coverage_for_lock(db_session, [decision.id])
    finally:
        settings.enable_package_procurement = prev_pkg
        settings.enforce_package_coverage_on_lock = prev_guard


@pytest.mark.asyncio
async def test_lock_coverage_blocks_incomplete_subitem_coverage(
    db_session, test_user, test_project_item, test_package
):
    prev_pkg = settings.enable_package_procurement
    prev_guard = settings.enforce_package_coverage_on_lock
    settings.enable_package_procurement = True
    settings.enforce_package_coverage_on_lock = True

    try:
        requirement = await _create_requirement(db_session, test_project_item.id, required_quantity=5)
        db_session.add(
            PackageSubItem(
                package_id=test_package.id,
                project_item_subitem_id=requirement.id,
                quantity_covered=2,
                is_fully_covered=False,
                coverage_percentage=40,
            )
        )
        await db_session.commit()

        decision = await _create_option_and_decision(
            db_session,
            package_id=test_package.id,
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            user_id=test_user.id,
            status="PROPOSED",
        )

        with pytest.raises(HTTPException) as exc_info:
            await validate_package_coverage_for_lock(db_session, [decision.id])
        assert exc_info.value.status_code == 400
        assert "coverage is incomplete" in exc_info.value.detail
    finally:
        settings.enable_package_procurement = prev_pkg
        settings.enforce_package_coverage_on_lock = prev_guard


@pytest.mark.asyncio
async def test_lock_coverage_allows_when_locked_and_target_packages_complete_coverage(
    db_session, test_user, test_project_item
):
    prev_pkg = settings.enable_package_procurement
    prev_guard = settings.enforce_package_coverage_on_lock
    settings.enable_package_procurement = True
    settings.enforce_package_coverage_on_lock = True

    try:
        requirement = await _create_requirement(db_session, test_project_item.id, required_quantity=5)

        package_a = ProcurementPackage(
            project_item_id=test_project_item.id,
            package_name="PKG-A-COV",
            package_type="PARTIAL",
            is_active=True,
        )
        package_b = ProcurementPackage(
            project_item_id=test_project_item.id,
            package_name="PKG-B-COV",
            package_type="PARTIAL",
            is_active=True,
        )
        db_session.add(package_a)
        db_session.add(package_b)
        await db_session.commit()
        await db_session.refresh(package_a)
        await db_session.refresh(package_b)

        db_session.add(
            PackageSubItem(
                package_id=package_a.id,
                project_item_subitem_id=requirement.id,
                quantity_covered=2,
                is_fully_covered=False,
                coverage_percentage=40,
            )
        )
        db_session.add(
            PackageSubItem(
                package_id=package_b.id,
                project_item_subitem_id=requirement.id,
                quantity_covered=3,
                is_fully_covered=False,
                coverage_percentage=60,
            )
        )
        await db_session.commit()

        await _create_option_and_decision(
            db_session,
            package_id=package_a.id,
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            user_id=test_user.id,
            status="LOCKED",
        )
        target_decision = await _create_option_and_decision(
            db_session,
            package_id=package_b.id,
            project_id=test_project_item.project_id,
            project_item_id=test_project_item.id,
            item_code=test_project_item.item_code,
            user_id=test_user.id,
            status="PROPOSED",
        )

        # Should pass because existing LOCKED package + target package covers 5/5.
        await validate_package_coverage_for_lock(db_session, [target_decision.id])
    finally:
        settings.enable_package_procurement = prev_pkg
        settings.enforce_package_coverage_on_lock = prev_guard
