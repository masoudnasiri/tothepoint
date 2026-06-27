"""
Sanitized assigned-item summaries for procurement assignment viewers (Sprint 5E-R2-Fix).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ProcurementAssignment, Project, ProjectItem, User
from app.schemas import (
    ProcurementAssignedItemAssignmentInfo,
    ProcurementAssignedItemSummary,
)
from app.services.procurement_assignment_scope_service import user_can_view_all_assignments
from app.services.rbac_service import get_effective_permissions, user_has_system_admin_role


def _sanitize_item_row(
    project: Project,
    item: ProjectItem,
    *,
    covered_by_project_assignment: bool,
    assignments: List[ProcurementAssignedItemAssignmentInfo],
) -> ProcurementAssignedItemSummary:
    delivery_options = item.delivery_options if isinstance(item.delivery_options, list) else []
    item_status = item.status.value if hasattr(item.status, "value") else str(item.status)
    return ProcurementAssignedItemSummary(
        project_id=project.id,
        project_code=project.project_code,
        project_name=project.name,
        project_item_id=item.id,
        item_code=item.item_code,
        item_name=item.item_name,
        description=item.description,
        quantity=item.quantity,
        delivery_options=[str(d) for d in delivery_options],
        item_status=item_status,
        external_purchase=bool(item.external_purchase),
        is_finalized=bool(item.is_finalized),
        covered_by_project_assignment=covered_by_project_assignment,
        assignments=assignments,
    )


async def _load_usernames(db: AsyncSession, user_ids: Set[int]) -> Dict[int, str]:
    if not user_ids:
        return {}
    result = await db.execute(select(User.id, User.username).where(User.id.in_(user_ids)))
    return {row[0]: row[1] for row in result.fetchall()}


async def list_assigned_item_summaries(
    db: AsyncSession,
    actor: User,
    *,
    project_id: Optional[int] = None,
    status_filter: Optional[str] = "active",
    assignee_user_id: Optional[int] = None,
    restrict_to_actor: bool = False,
) -> List[ProcurementAssignedItemSummary]:
    """
    Return sanitized item rows visible through procurement assignments.

    View-only users see only their own assignments. Managers may filter by assignee.
    """
    perms = await get_effective_permissions(db, actor)
    if "procurement.assignments.view" not in perms and actor.role != "admin":
        if not await user_has_system_admin_role(db, actor):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    can_view_all = (
        actor.role == "admin"
        or await user_has_system_admin_role(db, actor)
        or user_can_view_all_assignments(perms)
    )

    if restrict_to_actor:
        assignee_user_id = actor.id
    elif not can_view_all:
        if assignee_user_id is not None and assignee_user_id != actor.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view assigned items for other users",
            )
        assignee_user_id = actor.id

    query = select(ProcurementAssignment)
    if project_id is not None:
        query = query.where(ProcurementAssignment.project_id == project_id)
    if status_filter is not None:
        query = query.where(ProcurementAssignment.status == status_filter)
    if assignee_user_id is not None:
        query = query.where(ProcurementAssignment.assignee_user_id == assignee_user_id)

    result = await db.execute(query)
    assignments = list(result.scalars().all())
    if not assignments:
        return []

    project_ids = sorted({a.project_id for a in assignments})
    projects_result = await db.execute(select(Project).where(Project.id.in_(project_ids)))
    projects_by_id = {p.id: p for p in projects_result.scalars().all()}

    usernames = await _load_usernames(db, {a.assignee_user_id for a in assignments})

    project_level_by_project: Dict[int, List[ProcurementAssignment]] = {}
    item_level_by_item: Dict[int, List[ProcurementAssignment]] = {}
    for assignment in assignments:
        if assignment.assignment_scope == "project":
            project_level_by_project.setdefault(assignment.project_id, []).append(assignment)
        elif assignment.project_item_id is not None:
            item_level_by_item.setdefault(assignment.project_item_id, []).append(assignment)

    item_ids_needed: Set[int] = set(item_level_by_item.keys())
    projects_needing_all_items: Set[int] = set(project_level_by_project.keys())
    if projects_needing_all_items:
        all_items_result = await db.execute(
            select(ProjectItem).where(
                ProjectItem.project_id.in_(projects_needing_all_items),
                ProjectItem.is_finalized == True,  # noqa: E712
            )
        )
        for item in all_items_result.scalars().all():
            item_ids_needed.add(item.id)

    if not item_ids_needed:
        return []

    items_result = await db.execute(
        select(ProjectItem).where(
            ProjectItem.id.in_(item_ids_needed),
            ProjectItem.is_finalized == True,  # noqa: E712
        )
    )
    items_by_id = {item.id: item for item in items_result.scalars().all()}

    summaries: List[ProcurementAssignedItemSummary] = []
    for item_id, item in sorted(items_by_id.items(), key=lambda pair: (pair[1].project_id, pair[0])):
        project = projects_by_id.get(item.project_id)
        if project is None:
            continue

        project_level = project_level_by_project.get(item.project_id, [])
        item_level = item_level_by_item.get(item_id, [])
        if not project_level and not item_level:
            continue

        assignment_infos: List[ProcurementAssignedItemAssignmentInfo] = []
        for source in project_level + item_level:
            assignment_infos.append(
                ProcurementAssignedItemAssignmentInfo(
                    assignment_id=source.id,
                    assignment_scope=source.assignment_scope,
                    assignment_status=source.status,
                    assignee_user_id=source.assignee_user_id,
                    assignee_username=usernames.get(source.assignee_user_id),
                )
            )

        summaries.append(
            _sanitize_item_row(
                project,
                item,
                covered_by_project_assignment=bool(project_level),
                assignments=assignment_infos,
            )
        )

    return summaries
