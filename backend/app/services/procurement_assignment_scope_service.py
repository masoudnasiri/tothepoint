"""
Procurement assignment scope helpers for future Sprint 5E/5F enforcement.
These helpers do NOT restrict existing procurement package/option endpoints in Sprint 5D.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProcurementAssignment, User


async def get_assigned_project_ids_for_user(db: AsyncSession, user_id: int) -> List[int]:
    """Active project-level and item-level assignments collapsed to distinct project IDs."""
    result = await db.execute(
        select(ProcurementAssignment.project_id)
        .where(
            ProcurementAssignment.assignee_user_id == user_id,
            ProcurementAssignment.status == "active",
        )
        .distinct()
    )
    return sorted({row[0] for row in result.fetchall()})


async def get_assigned_project_item_ids_for_user(db: AsyncSession, user_id: int) -> List[int]:
    """Active item-scoped assignment project_item IDs for a user."""
    result = await db.execute(
        select(ProcurementAssignment.project_item_id)
        .where(
            ProcurementAssignment.assignee_user_id == user_id,
            ProcurementAssignment.status == "active",
            ProcurementAssignment.assignment_scope == "project_item",
            ProcurementAssignment.project_item_id.isnot(None),
        )
        .distinct()
    )
    return sorted({row[0] for row in result.fetchall()})


async def get_user_procurement_assignment_scope(
    db: AsyncSession, user_id: int
) -> Dict[str, List[int]]:
    """Return assigned project and project_item IDs for future scoped procurement UX."""
    return {
        "project_ids": await get_assigned_project_ids_for_user(db, user_id),
        "project_item_ids": await get_assigned_project_item_ids_for_user(db, user_id),
    }


async def user_has_active_procurement_assignment(
    db: AsyncSession,
    user_id: int,
    project_id: int,
    project_item_id: Optional[int] = None,
) -> bool:
    """True when user has an active project or matching item assignment."""
    project_result = await db.execute(
        select(ProcurementAssignment.id)
        .where(
            ProcurementAssignment.assignee_user_id == user_id,
            ProcurementAssignment.project_id == project_id,
            ProcurementAssignment.status == "active",
            ProcurementAssignment.assignment_scope == "project",
        )
        .limit(1)
    )
    if project_result.scalar_one_or_none() is not None:
        return True

    if project_item_id is None:
        item_result = await db.execute(
            select(ProcurementAssignment.id)
            .where(
                ProcurementAssignment.assignee_user_id == user_id,
                ProcurementAssignment.project_id == project_id,
                ProcurementAssignment.status == "active",
                ProcurementAssignment.assignment_scope == "project_item",
            )
            .limit(1)
        )
        return item_result.scalar_one_or_none() is not None

    item_result = await db.execute(
        select(ProcurementAssignment.id)
        .where(
            ProcurementAssignment.assignee_user_id == user_id,
            ProcurementAssignment.project_id == project_id,
            ProcurementAssignment.project_item_id == project_item_id,
            ProcurementAssignment.status == "active",
            ProcurementAssignment.assignment_scope == "project_item",
        )
        .limit(1)
    )
    return item_result.scalar_one_or_none() is not None


async def can_user_access_procurement_assignment(user: User, assignment: ProcurementAssignment) -> bool:
    """View access for a single assignment row (assignee can always view own row)."""
    return assignment.assignee_user_id == user.id


def user_can_view_all_assignments(permission_keys: Set[str]) -> bool:
    """Managers with create/edit/delete can list all assignments; view-only users see own rows."""
    manager_keys = {
        "procurement.assignments.create",
        "procurement.assignments.edit",
        "procurement.assignments.delete",
        "procurement.assignments.complete",
        "procurement.assignments.cancel",
    }
    return bool(manager_keys & permission_keys)
