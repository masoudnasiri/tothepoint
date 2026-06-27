"""
Procurement assignment business logic (Sprint 5D).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import log_audit
from app.models import (
    ProcurementAssignment,
    Project,
    ProjectAssignment,
    ProjectItem,
    User,
)
from app.schemas import (
    ProcurementAssignmentBulkCreate,
    ProcurementAssignmentCreate,
    ProcurementAssignmentUpdate,
)
from app.services.procurement_assignment_scope_service import user_can_view_all_assignments
from app.services.rbac_service import get_effective_permissions, user_has_system_admin_role


class DuplicateActiveAssignmentError(Exception):
    pass


async def _ensure_project_exists(db: AsyncSession, project_id: int) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _ensure_active_user(db: AsyncSession, user_id: int, label: str = "User") -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} not found or inactive",
        )
    return user


async def _ensure_project_item_belongs(
    db: AsyncSession,
    project_id: int,
    project_item_id: int,
    *,
    require_finalized: bool = False,
) -> ProjectItem:
    result = await db.execute(
        select(ProjectItem).where(
            ProjectItem.id == project_item_id,
            ProjectItem.project_id == project_id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project item not found or does not belong to project",
        )
    if require_finalized and not bool(item.is_finalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only finalized project items can be assigned at item level",
        )
    return item


async def user_can_manage_project_assignments(
    db: AsyncSession, actor: User, project_id: int
) -> bool:
    """PMO/system admin can manage all projects; PM must be assigned to the project."""
    if not actor.is_active:
        return False
    if actor.role == "admin":
        return True
    if await user_has_system_admin_role(db, actor):
        return True
    perms = await get_effective_permissions(db, actor)
    if "procurement.assignments.create" not in perms and "procurement.assignments.edit" not in perms:
        return False
    if actor.role == "pmo":
        return True
    if actor.role == "pm":
        result = await db.execute(
            select(ProjectAssignment.project_id).where(
                ProjectAssignment.user_id == actor.id,
                ProjectAssignment.project_id == project_id,
            )
        )
        return result.scalar_one_or_none() is not None
    # Other roles with create permission (e.g. custom PMO-like role)
    if "procurement.assignments.create" in perms:
        return True
    return False


async def _assert_can_manage_project(db: AsyncSession, actor: User, project_id: int) -> None:
    if not await user_can_manage_project_assignments(db, actor, project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for this project assignment",
        )


async def _find_duplicate_active(
    db: AsyncSession,
    *,
    project_id: int,
    assignee_user_id: int,
    assignment_scope: str,
    project_item_id: Optional[int],
) -> Optional[ProcurementAssignment]:
    query = select(ProcurementAssignment).where(
        ProcurementAssignment.project_id == project_id,
        ProcurementAssignment.assignee_user_id == assignee_user_id,
        ProcurementAssignment.assignment_scope == assignment_scope,
        ProcurementAssignment.status == "active",
    )
    if assignment_scope == "project":
        query = query.where(ProcurementAssignment.project_item_id.is_(None))
    else:
        query = query.where(ProcurementAssignment.project_item_id == project_item_id)
    result = await db.execute(query.limit(1))
    return result.scalar_one_or_none()


async def list_procurement_assignments(
    db: AsyncSession,
    actor: User,
    *,
    project_id: Optional[int] = None,
    project_item_id: Optional[int] = None,
    assignee_user_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    assignment_scope: Optional[str] = None,
) -> List[ProcurementAssignment]:
    perms = await get_effective_permissions(db, actor)
    if "procurement.assignments.view" not in perms and actor.role != "admin":
        if not await user_has_system_admin_role(db, actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    can_view_all = (
        actor.role == "admin"
        or await user_has_system_admin_role(db, actor)
        or user_can_view_all_assignments(perms)
    )

    query = select(ProcurementAssignment).order_by(ProcurementAssignment.created_at.desc())

    if project_id is not None:
        query = query.where(ProcurementAssignment.project_id == project_id)
    if project_item_id is not None:
        query = query.where(ProcurementAssignment.project_item_id == project_item_id)
    if status_filter is not None:
        query = query.where(ProcurementAssignment.status == status_filter)
    if assignment_scope is not None:
        query = query.where(ProcurementAssignment.assignment_scope == assignment_scope)

    if can_view_all:
        if assignee_user_id is not None:
            query = query.where(ProcurementAssignment.assignee_user_id == assignee_user_id)
    else:
        if assignee_user_id is not None and assignee_user_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view assignments for other users",
            )
        query = query.where(ProcurementAssignment.assignee_user_id == actor.id)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_procurement_assignment(
    db: AsyncSession, actor: User, assignment_id: int
) -> ProcurementAssignment:
    result = await db.execute(
        select(ProcurementAssignment).where(ProcurementAssignment.id == assignment_id)
    )
    assignment = result.scalar_one_or_none()
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    perms = await get_effective_permissions(db, actor)
    can_view_all = (
        actor.role == "admin"
        or await user_has_system_admin_role(db, actor)
        or user_can_view_all_assignments(perms)
    )
    if not can_view_all and assignment.assignee_user_id != actor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
    if "procurement.assignments.view" not in perms and actor.role != "admin":
        if not await user_has_system_admin_role(db, actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return assignment


async def create_procurement_assignment(
    db: AsyncSession,
    actor: User,
    payload: ProcurementAssignmentCreate,
) -> ProcurementAssignment:
    await _ensure_project_exists(db, payload.project_id)
    await _assert_can_manage_project(db, actor, payload.project_id)
    await _ensure_active_user(db, payload.assignee_user_id, "Assignee")

    if payload.project_item_id is None:
        scope = "project"
        project_item_id = None
    else:
        await _ensure_project_item_belongs(
            db,
            payload.project_id,
            payload.project_item_id,
            require_finalized=True,
        )
        scope = "project_item"
        project_item_id = payload.project_item_id

    duplicate = await _find_duplicate_active(
        db,
        project_id=payload.project_id,
        assignee_user_id=payload.assignee_user_id,
        assignment_scope=scope,
        project_item_id=project_item_id,
    )
    if duplicate is not None:
        await log_audit(
            db,
            user_id=actor.id,
            action="PROCUREMENT_ASSIGNMENT_DUPLICATE_BLOCKED",
            entity_type="procurement_assignment",
            details={
                "project_id": payload.project_id,
                "project_item_id": project_item_id,
                "assignee_user_id": payload.assignee_user_id,
                "assignment_scope": scope,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active assignment already exists for this assignee and scope",
        )

    row = ProcurementAssignment(
        project_id=payload.project_id,
        project_item_id=project_item_id,
        assignee_user_id=payload.assignee_user_id,
        assigned_by_user_id=actor.id,
        status="active",
        assignment_scope=scope,
        note=payload.note,
    )
    db.add(row)
    await db.flush()
    await log_audit(
        db,
        user_id=actor.id,
        action="PROCUREMENT_ASSIGNMENT_CREATE",
        entity_type="procurement_assignment",
        entity_id=row.id,
        details={
            "project_id": row.project_id,
            "project_item_id": row.project_item_id,
            "assignee_user_id": row.assignee_user_id,
            "assigned_by_user_id": row.assigned_by_user_id,
            "status": row.status,
            "assignment_scope": row.assignment_scope,
        },
    )
    await db.commit()
    await db.refresh(row)
    return row


async def bulk_create_procurement_assignments(
    db: AsyncSession,
    actor: User,
    payload: ProcurementAssignmentBulkCreate,
) -> List[ProcurementAssignment]:
    await _ensure_project_exists(db, payload.project_id)
    await _assert_can_manage_project(db, actor, payload.project_id)

    for uid in payload.assignee_user_ids:
        await _ensure_active_user(db, uid, "Assignee")

    created: List[ProcurementAssignment] = []
    item_ids = payload.project_item_ids or []

    targets: Sequence[tuple[str, Optional[int]]]
    if item_ids:
        for item_id in item_ids:
            await _ensure_project_item_belongs(
                db,
                payload.project_id,
                item_id,
                require_finalized=True,
            )
        targets = [("project_item", item_id) for item_id in item_ids]
    else:
        targets = [("project", None)]

    for scope, project_item_id in targets:
        for assignee_id in payload.assignee_user_ids:
            duplicate = await _find_duplicate_active(
                db,
                project_id=payload.project_id,
                assignee_user_id=assignee_id,
                assignment_scope=scope,
                project_item_id=project_item_id,
            )
            if duplicate is not None:
                await log_audit(
                    db,
                    user_id=actor.id,
                    action="PROCUREMENT_ASSIGNMENT_DUPLICATE_BLOCKED",
                    entity_type="procurement_assignment",
                    details={
                        "project_id": payload.project_id,
                        "project_item_id": project_item_id,
                        "assignee_user_id": assignee_id,
                        "assignment_scope": scope,
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Active assignment already exists for one or more assignees",
                )

            row = ProcurementAssignment(
                project_id=payload.project_id,
                project_item_id=project_item_id,
                assignee_user_id=assignee_id,
                assigned_by_user_id=actor.id,
                status="active",
                assignment_scope=scope,
                note=payload.note,
            )
            db.add(row)
            created.append(row)

    await db.flush()
    await log_audit(
        db,
        user_id=actor.id,
        action="PROCUREMENT_ASSIGNMENT_BULK_CREATE",
        entity_type="procurement_assignment",
        details={
            "project_id": payload.project_id,
            "project_item_ids": item_ids or None,
            "assignee_user_ids": payload.assignee_user_ids,
            "created_count": len(created),
        },
    )
    await db.commit()
    for row in created:
        await db.refresh(row)
    return created


async def update_procurement_assignment(
    db: AsyncSession,
    actor: User,
    assignment_id: int,
    payload: ProcurementAssignmentUpdate,
) -> ProcurementAssignment:
    assignment = await get_procurement_assignment(db, actor, assignment_id)
    await _assert_can_manage_project(db, actor, assignment.project_id)

    if assignment.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active assignments can be edited",
        )

    if payload.note is not None:
        assignment.note = payload.note
    assignment.updated_at = datetime.now(timezone.utc)

    await log_audit(
        db,
        user_id=actor.id,
        action="PROCUREMENT_ASSIGNMENT_UPDATE",
        entity_type="procurement_assignment",
        entity_id=assignment.id,
        details={
            "project_id": assignment.project_id,
            "project_item_id": assignment.project_item_id,
            "assignee_user_id": assignment.assignee_user_id,
            "status": assignment.status,
        },
    )
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def complete_procurement_assignment(
    db: AsyncSession, actor: User, assignment_id: int
) -> ProcurementAssignment:
    assignment = await get_procurement_assignment(db, actor, assignment_id)
    await _assert_can_manage_project(db, actor, assignment.project_id)

    if assignment.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active assignments can be completed",
        )

    now = datetime.now(timezone.utc)
    assignment.status = "completed"
    assignment.completed_at = now
    assignment.updated_at = now

    await log_audit(
        db,
        user_id=actor.id,
        action="PROCUREMENT_ASSIGNMENT_COMPLETE",
        entity_type="procurement_assignment",
        entity_id=assignment.id,
        details={
            "project_id": assignment.project_id,
            "project_item_id": assignment.project_item_id,
            "assignee_user_id": assignment.assignee_user_id,
            "status": assignment.status,
        },
    )
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def cancel_procurement_assignment(
    db: AsyncSession,
    actor: User,
    assignment_id: int,
    cancelled_reason: str,
) -> ProcurementAssignment:
    assignment = await get_procurement_assignment(db, actor, assignment_id)
    await _assert_can_manage_project(db, actor, assignment.project_id)

    if assignment.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only active assignments can be cancelled",
        )

    now = datetime.now(timezone.utc)
    assignment.status = "cancelled"
    assignment.cancelled_at = now
    assignment.cancelled_reason = cancelled_reason
    assignment.updated_at = now

    await log_audit(
        db,
        user_id=actor.id,
        action="PROCUREMENT_ASSIGNMENT_CANCEL",
        entity_type="procurement_assignment",
        entity_id=assignment.id,
        details={
            "project_id": assignment.project_id,
            "project_item_id": assignment.project_item_id,
            "assignee_user_id": assignment.assignee_user_id,
            "status": assignment.status,
            "cancelled_reason": cancelled_reason,
        },
    )
    await db.commit()
    await db.refresh(assignment)
    return assignment


async def delete_procurement_assignment(
    db: AsyncSession, actor: User, assignment_id: int
) -> ProcurementAssignment:
    """Soft-delete via cancel for active rows; idempotent for already terminal rows."""
    assignment = await get_procurement_assignment(db, actor, assignment_id)
    await _assert_can_manage_project(db, actor, assignment.project_id)

    if assignment.status == "active":
        return await cancel_procurement_assignment(
            db, actor, assignment_id, cancelled_reason="Deleted via assignment delete endpoint"
        )

    await log_audit(
        db,
        user_id=actor.id,
        action="PROCUREMENT_ASSIGNMENT_DELETE_OR_DEACTIVATE",
        entity_type="procurement_assignment",
        entity_id=assignment.id,
        details={
            "project_id": assignment.project_id,
            "project_item_id": assignment.project_item_id,
            "assignee_user_id": assignment.assignee_user_id,
            "status": assignment.status,
        },
    )
    await db.commit()
    await db.refresh(assignment)
    return assignment
