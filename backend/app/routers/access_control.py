"""
Access control APIs — roles, permissions, user role assignments (Sprint 5B).
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_access_control_manager
from app.crud import log_audit
from app.database import get_db
from app.models import Permission, Role, RolePermission, User, UserRole
from app.schemas import (
    PermissionResponse,
    RoleCreate,
    RolePermissionsResponse,
    RolePermissionsUpdate,
    RoleResponse,
    RoleUpdate,
    UserRoleSummary,
    UserRolesResponse,
    UserRolesUpdate,
)
from app.security.permission_registry import ALL_PERMISSION_KEYS
from app.services.rbac_service import (
    AccessControlLockoutError,
    assert_role_may_lose_access_control_permissions,
    assert_system_role_mutation_allowed,
    get_role_with_permissions,
    get_user_role_summaries,
    sync_legacy_role_for_user,
)

router = APIRouter(prefix="/access-control", tags=["access-control"])


@router.get("/permissions", response_model=List[PermissionResponse])
async def list_permissions(
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Permission).order_by(Permission.sort_order.asc(), Permission.permission_key.asc())
    )
    return list(result.scalars().all())


@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Role).order_by(Role.is_system.desc(), Role.code.asc()))
    return list(result.scalars().all())


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    payload: RoleCreate,
    request: Request,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Role).where(Role.code == payload.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role code already exists")

    role = Role(
        code=payload.code,
        display_name=payload.display_name,
        description=payload.description,
        is_system=False,
        is_active=True,
        created_by_id=current_user.id,
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)

    await log_audit(
        db,
        user_id=current_user.id,
        action="ROLE_CREATE",
        entity_type="role",
        entity_id=role.id,
        details={"code": role.code, "display_name": role.display_name},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return role


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    payload: RoleUpdate,
    request: Request,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    if payload.is_active is False and role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System roles cannot be deactivated",
        )

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    await db.commit()
    await db.refresh(role)

    action = "ROLE_DEACTIVATE" if payload.is_active is False else "ROLE_UPDATE"
    await log_audit(
        db,
        user_id=current_user.id,
        action=action,
        entity_type="role",
        entity_id=role.id,
        details=update_data,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return role


@router.delete("/roles/{role_id}")
async def deactivate_role(
    role_id: int,
    request: Request,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    assert_system_role_mutation_allowed(role, deleting=True)
    if role.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System roles cannot be deleted")

    role.is_active = False
    await db.commit()

    await log_audit(
        db,
        user_id=current_user.id,
        action="ROLE_DEACTIVATE",
        entity_type="role",
        entity_id=role.id,
        details={"code": role.code},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return {"message": "Role deactivated successfully"}


@router.get("/roles/{role_id}/permissions", response_model=RolePermissionsResponse)
async def get_role_permissions(
    role_id: int,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    role = await get_role_with_permissions(db, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    keys = sorted(rp.permission.permission_key for rp in role.role_permissions if rp.permission)
    return RolePermissionsResponse(role_id=role.id, permission_keys=keys)


@router.put("/roles/{role_id}/permissions", response_model=RolePermissionsResponse)
async def update_role_permissions(
    role_id: int,
    payload: RolePermissionsUpdate,
    request: Request,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    role = await db.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    assert_system_role_mutation_allowed(role)
    if role.code == "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="system_admin permissions cannot be modified",
        )

    requested = set(payload.permission_keys)
    unknown = requested - set(ALL_PERMISSION_KEYS)
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown permission keys: {sorted(unknown)}",
        )

    try:
        await assert_role_may_lose_access_control_permissions(db, role_id, requested)
    except AccessControlLockoutError as exc:
        await log_audit(
            db,
            user_id=current_user.id,
            action="USER_DELETE_BLOCKED_LAST_ADMIN",
            entity_type="role",
            entity_id=role_id,
            details={"reason": str(exc), "attempted_permission_keys": sorted(requested)},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    perm_result = await db.execute(
        select(Permission).where(Permission.permission_key.in_(requested or ["__none__"]))
    )
    permissions = {p.permission_key: p for p in perm_result.scalars().all()}

    await db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    for key in sorted(requested):
        permission = permissions.get(key)
        if permission:
            db.add(
                RolePermission(
                    role_id=role_id,
                    permission_id=permission.id,
                    granted_by_id=current_user.id,
                )
            )
    await db.commit()

    await log_audit(
        db,
        user_id=current_user.id,
        action="ROLE_PERMISSION_UPDATE",
        entity_type="role",
        entity_id=role_id,
        details={"permission_keys": sorted(requested)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return RolePermissionsResponse(role_id=role_id, permission_keys=sorted(requested))


@router.get("/users/{user_id}/roles", response_model=UserRolesResponse)
async def get_user_roles(
    user_id: int,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(
        select(UserRole.role_id).where(UserRole.user_id == user_id)
    )
    role_ids = list(result.scalars().all())
    summaries = await get_user_role_summaries(db, user_id)
    return UserRolesResponse(user_id=user_id, role_ids=role_ids, roles=summaries)


@router.put("/users/{user_id}/roles", response_model=UserRolesResponse)
async def update_user_roles(
    user_id: int,
    payload: UserRolesUpdate,
    request: Request,
    current_user: User = Depends(require_access_control_manager),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_result = await db.execute(
        select(Role).where(Role.id.in_(payload.role_ids or [-1]), Role.is_active == True)  # noqa: E712
    )
    roles = list(role_result.scalars().all())
    if len(roles) != len(set(payload.role_ids)):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more roles are invalid")

    await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
    for role in roles:
        db.add(
            UserRole(
                user_id=user_id,
                role_id=role.id,
                assigned_by_id=current_user.id,
            )
        )
    await sync_legacy_role_for_user(db, user_id)
    await db.commit()

    summaries = await get_user_role_summaries(db, user_id)
    await log_audit(
        db,
        user_id=current_user.id,
        action="USER_ROLE_UPDATE",
        entity_type="user",
        entity_id=user_id,
        details={"role_ids": payload.role_ids, "legacy_role": user.role},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()
    return UserRolesResponse(
        user_id=user_id,
        role_ids=payload.role_ids,
        roles=[UserRoleSummary(**item) for item in summaries],
    )
