"""
RBAC seeding, effective permissions, and lockout protection (ADR-011 / Sprint 5B).
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Permission, Role, RolePermission, User, UserRole
from app.security.permission_registry import (
    ACCESS_CONTROL_MANAGE_KEYS,
    ALL_PERMISSION_KEYS,
    LEGACY_ROLE_PRECEDENCE,
    LEGACY_ROLE_TO_SYSTEM_ROLE,
    PERMISSION_DEFINITIONS,
    SYSTEM_ROLE_DEFINITIONS,
    SYSTEM_ROLE_PERMISSION_KEYS,
    SYSTEM_ROLE_TO_LEGACY_ROLE,
)

logger = logging.getLogger(__name__)


class AccessControlLockoutError(Exception):
    """Raised when an operation would remove the last access-control manager."""


async def ensure_rbac_seeded(db: AsyncSession) -> None:
    """Idempotent RBAC seed: permissions, system roles, grants, user_roles backfill."""
    await _seed_permissions(db)
    await _seed_system_roles(db)
    await _seed_system_role_permissions(db)
    await backfill_user_roles_from_legacy(db)
    await db.commit()


async def _seed_permissions(db: AsyncSession) -> None:
    result = await db.execute(select(Permission))
    existing = {row.permission_key: row for row in result.scalars().all()}
    for definition in PERMISSION_DEFINITIONS:
        if definition.permission_key in existing:
            row = existing[definition.permission_key]
            row.feature_key = definition.feature_key
            row.action = definition.action
            row.description = definition.description
            row.sort_order = definition.sort_order
            row.is_system = True
        else:
            db.add(
                Permission(
                    permission_key=definition.permission_key,
                    feature_key=definition.feature_key,
                    action=definition.action,
                    description=definition.description,
                    sort_order=definition.sort_order,
                    is_system=True,
                )
            )
    await db.flush()


async def _seed_system_roles(db: AsyncSession) -> None:
    result = await db.execute(select(Role))
    existing = {row.code: row for row in result.scalars().all()}
    for code, display_name, description, is_system in SYSTEM_ROLE_DEFINITIONS:
        if code in existing:
            row = existing[code]
            row.display_name = display_name
            row.description = description
            row.is_system = is_system
            row.is_active = True
        else:
            db.add(
                Role(
                    code=code,
                    display_name=display_name,
                    description=description,
                    is_system=is_system,
                    is_active=True,
                )
            )
    await db.flush()


async def _seed_system_role_permissions(db: AsyncSession) -> None:
    perm_result = await db.execute(select(Permission))
    permissions_by_key = {p.permission_key: p for p in perm_result.scalars().all()}
    role_result = await db.execute(select(Role))
    roles_by_code = {r.code: r for r in role_result.scalars().all()}

    for role_code, permission_keys in SYSTEM_ROLE_PERMISSION_KEYS.items():
        role = roles_by_code.get(role_code)
        if not role:
            continue
        existing_result = await db.execute(
            select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
        )
        existing_permission_ids = set(existing_result.scalars().all())
        for key in permission_keys:
            permission = permissions_by_key.get(key)
            if not permission:
                logger.warning("Missing permission key during seed: %s", key)
                continue
            if permission.id in existing_permission_ids:
                continue
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))
    await db.flush()


async def backfill_user_roles_from_legacy(db: AsyncSession) -> None:
    users_result = await db.execute(select(User))
    users = users_result.scalars().all()
    roles_result = await db.execute(select(Role))
    roles_by_code = {r.code: r for r in roles_result.scalars().all()}

    for user in users:
        system_role_code = LEGACY_ROLE_TO_SYSTEM_ROLE.get(user.role)
        if not system_role_code:
            continue
        role = roles_by_code.get(system_role_code)
        if not role:
            continue
        existing = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )
        if existing.scalar_one_or_none() is None:
            db.add(UserRole(user_id=user.id, role_id=role.id))
    await db.flush()


async def sync_legacy_role_for_user(db: AsyncSession, user_id: int) -> None:
    """Mirror users.role from assigned system roles (highest precedence wins)."""
    result = await db.execute(
        select(User, Role)
        .join(UserRole, UserRole.user_id == User.id)
        .join(Role, Role.id == UserRole.role_id)
        .where(User.id == user_id, Role.is_active == True)  # noqa: E712
    )
    rows = result.all()
    if not rows:
        return
    user = rows[0][0]
    legacy_roles = []
    for _, role in rows:
        legacy = SYSTEM_ROLE_TO_LEGACY_ROLE.get(role.code)
        if legacy:
            legacy_roles.append(legacy)
    if not legacy_roles:
        return
    chosen = None
    for candidate in LEGACY_ROLE_PRECEDENCE:
        if candidate in legacy_roles:
            chosen = candidate
            break
    if chosen and user.role != chosen:
        user.role = chosen
        await db.flush()


async def assign_user_system_role_for_legacy(
    db: AsyncSession,
    user: User,
    *,
    assigned_by_id: Optional[int] = None,
) -> None:
    """Ensure user_roles row exists for the user's legacy role."""
    system_role_code = LEGACY_ROLE_TO_SYSTEM_ROLE.get(user.role)
    if not system_role_code:
        return
    role_result = await db.execute(select(Role).where(Role.code == system_role_code))
    role = role_result.scalar_one_or_none()
    if not role:
        return
    existing = await db.execute(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
    )
    if existing.scalar_one_or_none() is None:
        db.add(
            UserRole(
                user_id=user.id,
                role_id=role.id,
                assigned_by_id=assigned_by_id,
            )
        )
        await db.flush()


async def get_effective_permissions(db: AsyncSession, user: User) -> Set[str]:
    if not user.is_active:
        return set()

    if settings.enable_super_admin_bypass and user.role == "admin":
        return set(ALL_PERMISSION_KEYS)

    result = await db.execute(
        select(Permission.permission_key)
        .select_from(UserRole)
        .join(Role, Role.id == UserRole.role_id)
        .join(RolePermission, RolePermission.role_id == Role.id)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(
            UserRole.user_id == user.id,
            Role.is_active == True,  # noqa: E712
        )
    )
    return set(result.scalars().all())


async def user_has_permission(db: AsyncSession, user: User, permission_key: str) -> bool:
    permissions = await get_effective_permissions(db, user)
    return permission_key in permissions


async def user_has_system_admin_role(db: AsyncSession, user: User) -> bool:
    result = await db.execute(
        select(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user.id, Role.is_active == True, Role.code == "system_admin")  # noqa: E712
    )
    return result.scalar_one_or_none() is not None


async def user_has_pilot_permission(db: AsyncSession, user: User, permission_key: str) -> bool:
    """RBAC-only check for pilot-enforced master data routes (ignores legacy role except admin bypass)."""
    if not user.is_active:
        return False
    if settings.enable_super_admin_bypass and user.role == "admin":
        return True
    if await user_has_system_admin_role(db, user):
        return True
    return await user_has_permission(db, user, permission_key)


async def user_has_users_permission(db: AsyncSession, user: User, permission_key: str) -> bool:
    """RBAC-only check for Users module routes (ignores legacy role except admin bypass)."""
    if not permission_key.startswith("users."):
        raise ValueError(f"Expected users.* permission key, got {permission_key!r}")
    if not user.is_active:
        return False
    if settings.enable_super_admin_bypass and user.role == "admin":
        return True
    if await user_has_system_admin_role(db, user):
        return True
    return await user_has_permission(db, user, permission_key)


async def user_has_procurement_assignment_permission(
    db: AsyncSession, user: User, permission_key: str
) -> bool:
    """RBAC-only check for procurement assignment routes (ignores legacy role except admin bypass)."""
    if not permission_key.startswith("procurement.assignments."):
        raise ValueError(
            f"Expected procurement.assignments.* permission key, got {permission_key!r}"
        )
    if not user.is_active:
        return False
    if settings.enable_super_admin_bypass and user.role == "admin":
        return True
    if await user_has_system_admin_role(db, user):
        return True
    return await user_has_permission(db, user, permission_key)


async def user_has_project_items_permission(
    db: AsyncSession, user: User, permission_key: str
) -> bool:
    """RBAC-first check for project item management routes (Sprint 5E-R2-Fix)."""
    if not permission_key.startswith("project_items."):
        raise ValueError(f"Expected project_items.* permission key, got {permission_key!r}")
    if not user.is_active:
        return False
    if settings.enable_super_admin_bypass and user.role == "admin":
        return True
    if await user_has_system_admin_role(db, user):
        return True

    perms = await get_effective_permissions(db, user)
    if perms:
        return permission_key in perms

    # Legacy role fallback when no RBAC roles are assigned.
    if permission_key == "project_items.view":
        return user.role in ("pmo", "pm")
    if permission_key in ("project_items.create", "project_items.edit"):
        return user.role in ("pmo", "pm")
    if permission_key == "project_items.delete":
        return user.role == "pmo"
    if permission_key == "project_items.finalize":
        return user.role == "pmo"
    return False


async def get_user_role_summaries(db: AsyncSession, user_id: int) -> List[Dict[str, object]]:
    result = await db.execute(
        select(Role)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id, Role.is_active == True)  # noqa: E712
        .order_by(Role.code.asc())
    )
    roles = result.scalars().all()
    return [
        {
            "code": role.code,
            "display_name": role.display_name,
            "is_system": role.is_system,
        }
        for role in roles
    ]


async def count_access_control_managers(
    db: AsyncSession,
    *,
    exclude_user_id: Optional[int] = None,
) -> int:
    users_result = await db.execute(select(User).where(User.is_active == True))  # noqa: E712
    count = 0
    for user in users_result.scalars().all():
        if exclude_user_id is not None and user.id == exclude_user_id:
            continue
        if await user_can_manage_access_control(db, user):
            count += 1
    return count


async def assert_user_may_be_deleted_or_deactivated(
    db: AsyncSession,
    target_user_id: int,
) -> None:
    target = await db.get(User, target_user_id)
    if not target or not target.is_active:
        return
    if not await user_can_manage_access_control(db, target):
        return
    remaining = await count_access_control_managers(db, exclude_user_id=target_user_id)
    if remaining == 0:
        raise AccessControlLockoutError(
            "Cannot remove or deactivate the last active access-control manager"
        )


async def user_can_manage_access_control(db: AsyncSession, user: User) -> bool:
    if not user.is_active:
        return False
    if settings.enable_super_admin_bypass and user.role == "admin":
        return True
    permissions = await get_effective_permissions(db, user)
    return bool(permissions & ACCESS_CONTROL_MANAGE_KEYS)


async def assert_role_may_lose_access_control_permissions(
    db: AsyncSession,
    role_id: int,
    new_permission_keys: Set[str],
) -> None:
    role = await db.get(Role, role_id)
    if not role:
        return

    losing_manage = bool(ACCESS_CONTROL_MANAGE_KEYS - new_permission_keys)
    if not losing_manage:
        return

    # Users who only had manage capability through this role
    users_result = await db.execute(
        select(User.id)
        .join(UserRole, UserRole.user_id == User.id)
        .where(UserRole.role_id == role_id, User.is_active == True)  # noqa: E712
    )
    user_ids = list(users_result.scalars().all())
    for user_id in user_ids:
        other_roles = await db.execute(
            select(Role.id, Permission.permission_key)
            .select_from(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .join(RolePermission, RolePermission.role_id == Role.id)
            .join(Permission, Permission.id == RolePermission.permission_id)
            .where(
                UserRole.user_id == user_id,
                UserRole.role_id != role_id,
                Role.is_active == True,  # noqa: E712
            )
        )
        other_keys = {row[1] for row in other_roles.all()}
        if settings.enable_super_admin_bypass:
            user = await db.get(User, user_id)
            if user and user.role == "admin":
                other_keys |= ACCESS_CONTROL_MANAGE_KEYS
        if not (other_keys & ACCESS_CONTROL_MANAGE_KEYS):
            remaining = await count_access_control_managers(db, exclude_user_id=user_id)
            if remaining == 0:
                raise AccessControlLockoutError(
                    "Cannot remove access-control manage permissions from the last manager role/user"
                )


def assert_system_role_mutation_allowed(role: Role, *, deleting: bool = False) -> None:
    if not role.is_system:
        return
    if role.code == "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="system_admin role cannot be modified or removed",
        )
    if deleting:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be deleted",
        )


async def get_role_with_permissions(db: AsyncSession, role_id: int) -> Optional[Role]:
    result = await db.execute(
        select(Role)
        .options(selectinload(Role.role_permissions).selectinload(RolePermission.permission))
        .where(Role.id == role_id)
    )
    return result.scalar_one_or_none()
