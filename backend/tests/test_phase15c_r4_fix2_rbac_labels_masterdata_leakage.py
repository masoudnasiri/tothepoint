"""
Sprint 5C-R4-Fix-2 — Access Control role must not grant master_data; pilot denial tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import Permission, Role, RolePermission, User, UserRole
from app.security.permission_registry import (
    ACCESS_CONTROL_ADMIN_PERMISSIONS,
    SYSTEM_ROLE_PERMISSION_KEYS,
)
from app.services.rbac_service import ensure_rbac_seeded, get_effective_permissions


async def _create_user(db_session, username: str, role: str) -> User:
    user = User(username=username, password_hash="test-hash", role=role, is_active=True)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    await ensure_rbac_seeded(db_session)
    return user


def _auth_header(user: User) -> dict:
    token = create_access_token(data={"sub": user.username})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def override_db(db_session):
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_access_control_admin_system_role_has_no_master_data_permissions():
    keys = ACCESS_CONTROL_ADMIN_PERMISSIONS
    assert keys
    assert not any(key.startswith("master_data") for key in keys)
    registry = SYSTEM_ROLE_PERMISSION_KEYS["access_control_admin"]
    assert not any(key.startswith("master_data") for key in registry)


@pytest.mark.asyncio
async def test_copied_access_control_admin_role_grants_no_master_data(db_session, override_db):
    admin = await _create_user(db_session, "fix2_admin", "admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={
                "code": "access_control_admin_copy_fix2",
                "display_name": "Access Control Admin Copy Fix2",
                "description": "Copied from access control administrator",
            },
        )
        assert create_resp.status_code == 201
        role_id = create_resp.json()["id"]

        ac_admin = await db_session.execute(
            select(Role).where(Role.code == "access_control_admin")
        )
        source_role = ac_admin.scalar_one()
        source_links = await db_session.execute(
            select(RolePermission).where(RolePermission.role_id == source_role.id)
        )
        source_perm_ids = [row.permission_id for row in source_links.scalars().all()]
        perm_rows = await db_session.execute(
            select(Permission).where(Permission.id.in_(source_perm_ids))
        )
        source_keys = {p.permission_key for p in perm_rows.scalars().all()}
        assert not any(key.startswith("master_data") for key in source_keys)

        for perm_id in source_perm_ids:
            db_session.add(RolePermission(role_id=role_id, permission_id=perm_id))
        await db_session.commit()

        ac_user = await _create_user(db_session, "fix2_ac_only", "pm")
        await db_session.execute(delete(UserRole).where(UserRole.user_id == ac_user.id))
        db_session.add(
            UserRole(user_id=ac_user.id, role_id=role_id, assigned_by_id=admin.id)
        )
        await db_session.commit()
        await db_session.refresh(ac_user)

        effective = await get_effective_permissions(db_session, ac_user)
        assert not any(key.startswith("master_data") for key in effective)
        assert "access_control.roles.view" in effective
        assert "users.view" in effective

        items_resp = await client.get("/items-master/", headers=_auth_header(ac_user))
        assert items_resp.status_code == 403

        suppliers_resp = await client.get("/suppliers/", headers=_auth_header(ac_user))
        assert suppliers_resp.status_code == 403

        users_resp = await client.get("/users/", headers=_auth_header(ac_user))
        assert users_resp.status_code == 200
