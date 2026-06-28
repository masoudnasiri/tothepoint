"""
Procurement assignment scope helpers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set, Union

from fastapi import HTTPException, status
from sqlalchemy import false, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.models import (
    DeliveryOption,
    ProcurementAssignment,
    ProcurementOption,
    ProcurementPackage,
    ProjectItem,
    User,
)
from app.services.rbac_service import get_effective_permissions, user_has_system_admin_role

GLOBAL_PROCUREMENT_SCOPE_PERMISSION_KEYS: Set[str] = {
    "procurement.assignments.create",
    "procurement.assignments.edit",
    "procurement.assignments.delete",
    "procurement.assignments.complete",
    "procurement.assignments.cancel",
    "project_items.view",
}

PROCUREMENT_SCOPE_BASE_PERMISSION_KEYS: Set[str] = {
    "procurement.assignments.view",
    "procurement.view",
    "procurement.create",
    "procurement.edit",
    "procurement.delete",
    "procurement.options.view",
    "procurement.options.create",
    "procurement.options.edit",
    "procurement.options.delete",
    "procurement.options.submit",
    "procurement.packages.view",
    "procurement.packages.create",
    "procurement.packages.edit",
    "procurement.packages.delete",
}


@dataclass
class ProcurementActiveScope:
    project_ids: Set[int] = field(default_factory=set)
    project_level_project_ids: Set[int] = field(default_factory=set)
    item_level_project_item_ids: Set[int] = field(default_factory=set)
    finalized_project_item_ids: Set[int] = field(default_factory=set)

    @classmethod
    def empty(cls) -> "ProcurementActiveScope":
        return cls()

    def to_dict(self) -> Dict[str, List[int]]:
        return {
            "project_ids": sorted(self.project_ids),
            "project_level_project_ids": sorted(self.project_level_project_ids),
            "item_level_project_item_ids": sorted(self.item_level_project_item_ids),
            "finalized_project_item_ids": sorted(self.finalized_project_item_ids),
        }


@dataclass
class ProcurementScopeAccess:
    permission_keys: Set[str]
    global_scope: bool
    assigned_only_scope: bool
    active_scope: ProcurementActiveScope
    admin_or_system_admin: bool


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
    """Compatibility helper retained from Sprint 5D."""
    return {
        "project_ids": await get_assigned_project_ids_for_user(db, user_id),
        "project_item_ids": await get_assigned_project_item_ids_for_user(db, user_id),
    }


async def get_active_procurement_scope_for_user(
    db: AsyncSession, user_id: int
) -> ProcurementActiveScope:
    result = await db.execute(
        select(
            ProcurementAssignment.project_id,
            ProcurementAssignment.assignment_scope,
            ProcurementAssignment.project_item_id,
        ).where(
            ProcurementAssignment.assignee_user_id == user_id,
            ProcurementAssignment.status == "active",
        )
    )
    rows = result.fetchall()
    if not rows:
        return ProcurementActiveScope.empty()

    project_ids: Set[int] = set()
    project_level_project_ids: Set[int] = set()
    item_level_project_item_ids: Set[int] = set()

    for project_id, assignment_scope, project_item_id in rows:
        project_ids.add(int(project_id))
        if assignment_scope == "project":
            project_level_project_ids.add(int(project_id))
        elif assignment_scope == "project_item" and project_item_id is not None:
            item_level_project_item_ids.add(int(project_item_id))

    finalized_project_item_ids: Set[int] = set()
    if project_level_project_ids:
        project_result = await db.execute(
            select(ProjectItem.id).where(
                ProjectItem.project_id.in_(project_level_project_ids),
                ProjectItem.is_finalized == True,  # noqa: E712
            )
        )
        finalized_project_item_ids.update(int(row[0]) for row in project_result.fetchall())

    if item_level_project_item_ids:
        item_result = await db.execute(
            select(ProjectItem.id).where(
                ProjectItem.id.in_(item_level_project_item_ids),
                ProjectItem.is_finalized == True,  # noqa: E712
            )
        )
        finalized_project_item_ids.update(int(row[0]) for row in item_result.fetchall())

    return ProcurementActiveScope(
        project_ids=project_ids,
        project_level_project_ids=project_level_project_ids,
        item_level_project_item_ids=item_level_project_item_ids,
        finalized_project_item_ids=finalized_project_item_ids,
    )


async def is_global_procurement_scope_user(
    db: AsyncSession,
    user: User,
    permission_keys: Optional[Set[str]] = None,
) -> bool:
    if user.role == "admin" or await user_has_system_admin_role(db, user):
        return True
    perms = permission_keys if permission_keys is not None else await get_effective_permissions(db, user)
    return bool(perms & GLOBAL_PROCUREMENT_SCOPE_PERMISSION_KEYS)


async def is_assigned_only_procurement_scope_user(
    db: AsyncSession,
    user: User,
    permission_keys: Optional[Set[str]] = None,
) -> bool:
    perms = permission_keys if permission_keys is not None else await get_effective_permissions(db, user)
    if not (perms & PROCUREMENT_SCOPE_BASE_PERMISSION_KEYS):
        return False
    return not await is_global_procurement_scope_user(db, user, perms)


async def resolve_procurement_scope_access(
    db: AsyncSession,
    user: User,
    *,
    required_any_permissions: Optional[Set[str]] = None,
) -> ProcurementScopeAccess:
    permission_keys = await get_effective_permissions(db, user)
    admin_or_system_admin = user.role == "admin" or await user_has_system_admin_role(db, user)

    required = required_any_permissions or set()
    if required and not admin_or_system_admin and not (required & permission_keys):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for procurement workflow",
        )

    global_scope = (
        admin_or_system_admin
        or bool(permission_keys & GLOBAL_PROCUREMENT_SCOPE_PERMISSION_KEYS)
    )
    assigned_only_scope = (
        not global_scope
        and bool(permission_keys & PROCUREMENT_SCOPE_BASE_PERMISSION_KEYS)
    )

    if not global_scope and not assigned_only_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for procurement workflow",
        )

    active_scope = (
        ProcurementActiveScope.empty()
        if global_scope
        else await get_active_procurement_scope_for_user(db, user.id)
    )
    return ProcurementScopeAccess(
        permission_keys=permission_keys,
        global_scope=global_scope,
        assigned_only_scope=assigned_only_scope,
        active_scope=active_scope,
        admin_or_system_admin=admin_or_system_admin,
    )


def _access_can_view_project(access: ProcurementScopeAccess, project_id: int) -> bool:
    if access.global_scope:
        return True
    return int(project_id) in access.active_scope.project_ids


def _access_can_view_item(access: ProcurementScopeAccess, project_item_id: int) -> bool:
    if access.global_scope:
        return True
    return int(project_item_id) in access.active_scope.finalized_project_item_ids


async def user_can_access_procurement_project(
    db: AsyncSession, user: User, project_id: int
) -> bool:
    access = await resolve_procurement_scope_access(db, user)
    return _access_can_view_project(access, project_id)


async def user_can_access_procurement_item(
    db: AsyncSession, user: User, project_item_id: int
) -> bool:
    access = await resolve_procurement_scope_access(db, user)
    return _access_can_view_item(access, project_item_id)


def filter_project_items_by_procurement_scope(
    items_or_query: Union[Sequence[ProjectItem], Select],
    *,
    allowed_project_item_ids: Set[int],
) -> Union[List[ProjectItem], Select]:
    if isinstance(items_or_query, Select):
        if not allowed_project_item_ids:
            return items_or_query.where(false())
        return items_or_query.where(ProjectItem.id.in_(allowed_project_item_ids))

    allowed = {int(v) for v in allowed_project_item_ids}
    return [item for item in items_or_query if int(item.id) in allowed]


def filter_procurement_options_by_scope(
    options_or_query: Union[Sequence[ProcurementOption], Select],
    *,
    allowed_project_item_ids: Set[int],
    package_project_item_by_id: Optional[Dict[int, int]] = None,
    delivery_option_project_item_by_id: Optional[Dict[int, int]] = None,
) -> Union[List[ProcurementOption], Select]:
    if isinstance(options_or_query, Select):
        if not allowed_project_item_ids:
            return options_or_query.where(false())
        package_scope = (
            select(ProcurementPackage.id).where(
                ProcurementPackage.project_item_id.in_(allowed_project_item_ids)
            )
        )
        delivery_scope = (
            select(DeliveryOption.id).where(
                DeliveryOption.project_item_id.in_(allowed_project_item_ids)
            )
        )
        return options_or_query.where(
            or_(
                ProcurementOption.project_item_id.in_(allowed_project_item_ids),
                ProcurementOption.package_id.in_(package_scope),
                ProcurementOption.delivery_option_id.in_(delivery_scope),
            )
        )

    allowed = {int(v) for v in allowed_project_item_ids}
    package_project_item_by_id = package_project_item_by_id or {}
    delivery_option_project_item_by_id = delivery_option_project_item_by_id or {}
    rows: List[ProcurementOption] = []
    for option in options_or_query:
        project_item_id = option.project_item_id
        if project_item_id is None and option.package_id is not None:
            project_item_id = package_project_item_by_id.get(int(option.package_id))
        if project_item_id is None and option.delivery_option_id is not None:
            project_item_id = delivery_option_project_item_by_id.get(int(option.delivery_option_id))
        if project_item_id is not None and int(project_item_id) in allowed:
            rows.append(option)
    return rows


async def resolve_procurement_option_project_item_id(
    db: AsyncSession, option: ProcurementOption
) -> Optional[int]:
    if option.project_item_id is not None:
        return int(option.project_item_id)
    if option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == option.package_id
            )
        )
        package_item_id = package_result.scalar_one_or_none()
        if package_item_id is not None:
            return int(package_item_id)
    if option.delivery_option_id is not None:
        delivery_result = await db.execute(
            select(DeliveryOption.project_item_id).where(
                DeliveryOption.id == option.delivery_option_id
            )
        )
        delivery_item_id = delivery_result.scalar_one_or_none()
        if delivery_item_id is not None:
            return int(delivery_item_id)
    return None


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
