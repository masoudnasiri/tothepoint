"""
Sprint 5C-R4 — Users module RBAC enforcement tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import Permission, Role, RolePermission, User, UserRole
from app.services.rbac_service import ensure_rbac_seeded


async def _create_user(db_session, username: str, role: str = "pm") -> User:
    user = User(
        username=username,
        password_hash="test-hash",
        role=role,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    await ensure_rbac_seeded(db_session)
    return user


def _auth_header(user: User) -> dict:
    token = create_access_token(data={"sub": user.username})
    return {"Authorization": f"Bearer {token}"}


async def _assign_role_permissions(db_session, role_code: str, permission_keys: list[str]) -> Role:
    role = (
        await db_session.execute(select(Role).where(Role.code == role_code))
    ).scalar_one()
    perm_ids = (
        await db_session.execute(
            select(Permission.id).where(Permission.permission_key.in_(permission_keys))
        )
    ).scalars().all()
    for perm_id in perm_ids:
        db_session.add(RolePermission(role_id=role.id, permission_id=perm_id))
    await db_session.commit()
    return role


@pytest.fixture
def override_db(db_session):
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_users_view_only_can_list_but_not_create(db_session, override_db):
    admin = await _create_user(db_session, "r4_admin_users", "admin")
    viewer = await _create_user(db_session, "r4_users_viewer", "pm")

    custom_role = Role(
        code="sprint5c_r4_users_view_only",
        display_name="R4 Users View Only",
        description="Test role",
        is_system=False,
        is_active=True,
    )
    db_session.add(custom_role)
    await db_session.commit()
    await db_session.refresh(custom_role)

    perm = (
        await db_session.execute(select(Permission).where(Permission.permission_key == "users.view"))
    ).scalar_one()
    db_session.add(RolePermission(role_id=custom_role.id, permission_id=perm.id))
    db_session.add(UserRole(user_id=viewer.id, role_id=custom_role.id, assigned_by_id=admin.id))
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        list_resp = await client.get("/users/", headers=_auth_header(viewer))
        assert list_resp.status_code == 200

        create_resp = await client.post(
            "/users/",
            headers=_auth_header(viewer),
            json={"username": "r4_new_user", "password": "TestPass!123", "role": "pm", "is_active": True},
        )
        assert create_resp.status_code == 403


@pytest.mark.asyncio
async def test_users_edit_delete_permissions_respected(db_session, override_db):
    admin = await _create_user(db_session, "r4_admin_full", "admin")
    manager = await _create_user(db_session, "r4_users_manager", "pm")
    target = await _create_user(db_session, "r4_target_for_mgr", "pm")

    custom_role = Role(
        code="sprint5c_r4_users_manager",
        display_name="R4 Users Manager",
        description="Test role",
        is_system=False,
        is_active=True,
    )
    db_session.add(custom_role)
    await db_session.commit()
    await db_session.refresh(custom_role)

    keys = ["users.view", "users.create", "users.edit", "users.delete"]
    perm_ids = (
        await db_session.execute(select(Permission.id).where(Permission.permission_key.in_(keys)))
    ).scalars().all()
    for perm_id in perm_ids:
        db_session.add(RolePermission(role_id=custom_role.id, permission_id=perm_id))
    db_session.add(UserRole(user_id=manager.id, role_id=custom_role.id, assigned_by_id=admin.id))
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_resp = await client.post(
            "/users/",
            headers=_auth_header(manager),
            json={"username": "r4_should_not_403", "password": "TestPass!123", "role": "pm", "is_active": True},
        )
        assert create_resp.status_code != 403

        update_resp = await client.put(
            f"/users/{target.id}",
            headers=_auth_header(manager),
            json={"is_active": False},
        )
        assert update_resp.status_code == 200

        delete_resp = await client.delete(f"/users/{target.id}", headers=_auth_header(manager))
        assert delete_resp.status_code == 200


@pytest.mark.asyncio
async def test_legacy_pm_without_users_view_denied(db_session, override_db):
    viewer = await _create_user(db_session, "r4_legacy_pm", "pm")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        list_resp = await client.get("/users/", headers=_auth_header(viewer))
        assert list_resp.status_code == 403
