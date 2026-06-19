"""
Phase 5 tests for package/sub-item validation boundaries.
"""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    ItemMaster,
    ItemSubItem,
    ProjectItemSubItem,
    ProcurementPackage,
    PackageSubItem,
)
from app.services.package_service import (
    validate_main_item_quantity,
    validate_and_compute_subitem_coverage,
)


async def _create_project_item_subitem(
    db_session: AsyncSession,
    project_item_id: int,
    *,
    code_suffix: str,
    required_quantity: int,
) -> ProjectItemSubItem:
    """Create a sub-item requirement row linked to a project item."""
    master = ItemMaster(
        item_code=f"MASTER-{code_suffix}",
        company="TestCo",
        item_name=f"Test Item {code_suffix}",
        model="M1",
        is_active=True,
    )
    db_session.add(master)
    await db_session.commit()
    await db_session.refresh(master)

    subitem = ItemSubItem(
        item_master_id=master.id,
        name=f"SubItem {code_suffix}",
        part_number=f"PN-{code_suffix}",
    )
    db_session.add(subitem)
    await db_session.commit()
    await db_session.refresh(subitem)

    project_subitem = ProjectItemSubItem(
        project_item_id=project_item_id,
        item_subitem_id=subitem.id,
        quantity=required_quantity,
    )
    db_session.add(project_subitem)
    await db_session.commit()
    await db_session.refresh(project_subitem)
    return project_subitem


class TestPhase5PackageValidation:
    @pytest.mark.asyncio
    async def test_main_item_quantity_cannot_exceed_project_demand(
        self, db_session, test_project_item
    ):
        with pytest.raises(HTTPException) as exc_info:
            await validate_main_item_quantity(
                db_session,
                project_item_id=test_project_item.id,
                main_item_quantity=(test_project_item.quantity or 0) + 1,
            )
        assert exc_info.value.status_code == 400
        assert "cannot exceed required project item quantity" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_subitem_must_belong_to_same_project_item(
        self, db_session, test_project, test_project_item, test_package
    ):
        from app.models import ProjectItem

        other_item = ProjectItem(
            project_id=test_project.id,
            item_code="OTHER-ITEM",
            item_name="Other Item",
            quantity=2,
            delivery_options=[],
            status="PENDING",
        )
        db_session.add(other_item)
        await db_session.commit()
        await db_session.refresh(other_item)

        foreign_subitem = await _create_project_item_subitem(
            db_session,
            other_item.id,
            code_suffix="FOREIGN",
            required_quantity=2,
        )

        with pytest.raises(HTTPException) as exc_info:
            await validate_and_compute_subitem_coverage(
                db_session,
                package_id=test_package.id,
                project_item_subitem_id=foreign_subitem.id,
                quantity_covered=1,
            )
        assert exc_info.value.status_code == 400
        assert "does not belong to the same project item" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_total_active_coverage_cannot_overflow_requirement(
        self, db_session, test_project_item, test_package
    ):
        requirement = await _create_project_item_subitem(
            db_session,
            test_project_item.id,
            code_suffix="REQ",
            required_quantity=5,
        )

        second_package = ProcurementPackage(
            project_item_id=test_project_item.id,
            package_name="SECOND Package",
            package_type="PARTIAL",
            is_active=True,
        )
        db_session.add(second_package)
        await db_session.commit()
        await db_session.refresh(second_package)

        existing = PackageSubItem(
            package_id=second_package.id,
            project_item_subitem_id=requirement.id,
            quantity_covered=3,
            is_fully_covered=False,
            coverage_percentage=60,
        )
        db_session.add(existing)
        await db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await validate_and_compute_subitem_coverage(
                db_session,
                package_id=test_package.id,
                project_item_subitem_id=requirement.id,
                quantity_covered=3,  # 3 existing + 3 new > required(5)
            )
        assert exc_info.value.status_code == 400
        assert "Coverage overflow" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_subitem_coverage_fields_are_computed_for_valid_input(
        self, db_session, test_project_item, test_package
    ):
        requirement = await _create_project_item_subitem(
            db_session,
            test_project_item.id,
            code_suffix="VALID",
            required_quantity=4,
        )

        result = await validate_and_compute_subitem_coverage(
            db_session,
            package_id=test_package.id,
            project_item_subitem_id=requirement.id,
            quantity_covered=2,
        )

        assert result["required_quantity"] == 4
        assert result["is_fully_covered"] is False
        assert result["coverage_percentage"] == 50.0
