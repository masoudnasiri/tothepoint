"""
Procurement assignment API (Sprint 5D).
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_procurement_assignment_permission
from app.database import get_db
from app.models import User
from app.schemas import (
    ProcurementAssignedItemSummary,
    ProcurementAssignmentBulkCreate,
    ProcurementAssignmentCancel,
    ProcurementAssignmentCreate,
    ProcurementAssignmentRead,
    ProcurementAssignmentUpdate,
)
from app.services import procurement_assignment_service as svc
from app.services import procurement_assigned_items_service as assigned_items_svc

router = APIRouter(tags=["procurement-assignments"])


@router.get(
    "/procurement-assignments/my-assigned-items",
    response_model=List[ProcurementAssignedItemSummary],
)
async def list_my_assigned_items(
    status_filter: Optional[str] = Query("active", alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    return await assigned_items_svc.list_assigned_item_summaries(
        db,
        current_user,
        status_filter=status_filter,
        restrict_to_actor=True,
    )


@router.get(
    "/procurement-assignments/assigned-items",
    response_model=List[ProcurementAssignedItemSummary],
)
async def list_assigned_items(
    project_id: Optional[int] = Query(None),
    assignee_user_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query("active", alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    return await assigned_items_svc.list_assigned_item_summaries(
        db,
        current_user,
        project_id=project_id,
        status_filter=status_filter,
        assignee_user_id=assignee_user_id,
    )


@router.get(
    "/procurement-assignments/projects/{project_id}/assigned-items",
    response_model=List[ProcurementAssignedItemSummary],
)
async def list_project_assigned_items(
    project_id: int,
    assignee_user_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query("active", alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    return await assigned_items_svc.list_assigned_item_summaries(
        db,
        current_user,
        project_id=project_id,
        status_filter=status_filter,
        assignee_user_id=assignee_user_id,
    )


@router.get("/procurement-assignments", response_model=List[ProcurementAssignmentRead])
async def list_procurement_assignments(
    project_id: Optional[int] = Query(None),
    project_item_id: Optional[int] = Query(None),
    assignee_user_id: Optional[int] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    assignment_scope: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    rows = await svc.list_procurement_assignments(
        db,
        current_user,
        project_id=project_id,
        project_item_id=project_item_id,
        assignee_user_id=assignee_user_id,
        status_filter=status_filter,
        assignment_scope=assignment_scope,
    )
    return rows


@router.post(
    "/procurement-assignments",
    response_model=ProcurementAssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_procurement_assignment(
    payload: ProcurementAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.create")),
):
    return await svc.create_procurement_assignment(db, current_user, payload)


@router.post(
    "/procurement-assignments/bulk",
    response_model=List[ProcurementAssignmentRead],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_procurement_assignments(
    payload: ProcurementAssignmentBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.create")),
):
    return await svc.bulk_create_procurement_assignments(db, current_user, payload)


@router.get("/procurement-assignments/{assignment_id}", response_model=ProcurementAssignmentRead)
async def get_procurement_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    return await svc.get_procurement_assignment(db, current_user, assignment_id)


@router.put("/procurement-assignments/{assignment_id}", response_model=ProcurementAssignmentRead)
async def update_procurement_assignment(
    assignment_id: int,
    payload: ProcurementAssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.edit")),
):
    return await svc.update_procurement_assignment(db, current_user, assignment_id, payload)


@router.post(
    "/procurement-assignments/{assignment_id}/complete",
    response_model=ProcurementAssignmentRead,
)
async def complete_procurement_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.complete")),
):
    return await svc.complete_procurement_assignment(db, current_user, assignment_id)


@router.post(
    "/procurement-assignments/{assignment_id}/cancel",
    response_model=ProcurementAssignmentRead,
)
async def cancel_procurement_assignment(
    assignment_id: int,
    payload: ProcurementAssignmentCancel,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.cancel")),
):
    return await svc.cancel_procurement_assignment(
        db, current_user, assignment_id, payload.cancelled_reason
    )


@router.delete(
    "/procurement-assignments/{assignment_id}",
    response_model=ProcurementAssignmentRead,
)
async def delete_procurement_assignment(
    assignment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.delete")),
):
    return await svc.delete_procurement_assignment(db, current_user, assignment_id)


@router.get(
    "/projects/{project_id}/procurement-assignments",
    response_model=List[ProcurementAssignmentRead],
)
async def list_project_procurement_assignments(
    project_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    assignment_scope: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    return await svc.list_procurement_assignments(
        db,
        current_user,
        project_id=project_id,
        status_filter=status_filter,
        assignment_scope=assignment_scope,
    )


@router.get(
    "/project-items/{project_item_id}/procurement-assignments",
    response_model=List[ProcurementAssignmentRead],
)
async def list_project_item_procurement_assignments(
    project_item_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    return await svc.list_procurement_assignments(
        db,
        current_user,
        project_item_id=project_item_id,
        status_filter=status_filter,
    )


@router.get(
    "/users/{user_id}/procurement-assignments",
    response_model=List[ProcurementAssignmentRead],
)
async def list_user_procurement_assignments(
    user_id: int,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_procurement_assignment_permission("procurement.assignments.view")),
):
    return await svc.list_procurement_assignments(
        db,
        current_user,
        assignee_user_id=user_id,
        status_filter=status_filter,
    )
