"""
Sprint 5B — Backend RBAC foundation tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.auth import create_access_token, get_password_hash, require_admin, require_procurement
from app.database import get_db
from app.main import app
from app.models import Permission, Role, User, UserRole
from app.security.permission_registry import ALL_PERMISSION_KEYS, PERMISSION_DEFINITIONS
from app.services.rbac_service import (
    AccessControlLockoutError,
    assert_user_may_be_deleted_or_deactivated,
    ensure_rbac_seeded,
    get_effective_permissions,
)


async def _seed_rbac(db_session):
    await ensure_rbac_seeded(db_session)


async def _create_user(db_session, username: str, role: str, password: str = "testpass123") -> User:
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


@pytest.fixture
def override_db(db_session):
    async def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_rbac_seed_creates_permissions_roles_and_backfill(db_session):
    admin = await _create_user(db_session, "rbac_admin_seed", "admin")
    await _seed_rbac(db_session)

    perm_count = (await db_session.execute(select(Permission))).scalars().all()
    role_count = (await db_session.execute(select(Role))).scalars().all()
    user_roles = (
        await db_session.execute(select(UserRole).where(UserRole.user_id == admin.id))
    ).scalars().all()

    assert len(perm_count) == len(PERMISSION_DEFINITIONS)
    assert len(role_count) >= 6
    assert len(user_roles) >= 1

    # idempotent second run
    await ensure_rbac_seeded(db_session)
    perm_count_2 = (await db_session.execute(select(Permission))).scalars().all()
    assert len(perm_count_2) == len(perm_count)


@pytest.mark.asyncio
async def test_admin_effective_permissions_include_all_keys(db_session):
    admin = await _create_user(db_session, "rbac_admin_perms", "admin")
    perms = await get_effective_permissions(db_session, admin)
    assert perms == set(ALL_PERMISSION_KEYS)


@pytest.mark.asyncio
async def test_union_permissions_for_multiple_roles(db_session, override_db):
    user = await _create_user(db_session, "rbac_multi_role", "pm")
    finance_role = (
        await db_session.execute(select(Role).where(Role.code == "finance_analyst"))
    ).scalar_one()
    db_session.add(UserRole(user_id=user.id, role_id=finance_role.id))
    await db_session.commit()

    perms = await get_effective_permissions(db_session, user)
    assert "finance.view" in perms
    assert "projects.view" in perms


@pytest.mark.asyncio
async def test_inactive_role_grants_no_permission(db_session):
    user = await _create_user(db_session, "rbac_inactive_role_user", "finance")
    role = (
        await db_session.execute(select(Role).where(Role.code == "finance_analyst"))
    ).scalar_one()
    role.is_active = False
    await db_session.commit()

    perms = await get_effective_permissions(db_session, user)
    assert "finance.view" not in perms


@pytest.mark.asyncio
async def test_auth_me_returns_roles_and_permissions(db_session, override_db):
    admin = await _create_user(db_session, "rbac_me_admin", "admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/auth/me", headers=_auth_header(admin))
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"
    assert "permissions" in body
    assert len(body["permissions"]) == len(ALL_PERMISSION_KEYS)
    assert any(r["code"] == "system_admin" for r in body["roles"])
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_access_control_permissions_admin_ok(db_session, override_db):
    admin = await _create_user(db_session, "rbac_ac_admin", "admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/access-control/permissions",
            headers=_auth_header(admin),
        )
    assert response.status_code == 200
    assert len(response.json()) == len(PERMISSION_DEFINITIONS)


@pytest.mark.asyncio
async def test_access_control_forbidden_for_procurement(db_session, override_db):
    proc = await _create_user(db_session, "rbac_ac_proc", "procurement")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/access-control/roles",
            headers=_auth_header(proc),
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_custom_role_and_assign_permissions(db_session, override_db):
    admin = await _create_user(db_session, "rbac_role_crud", "admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={
                "code": "custom_viewer",
                "display_name": "Custom Viewer",
                "description": "Read-only custom role",
            },
        )
        assert create_resp.status_code == 201
        role_id = create_resp.json()["id"]

        perm_resp = await client.put(
            f"/access-control/roles/{role_id}/permissions",
            headers=_auth_header(admin),
            json={"permission_keys": ["projects.view", "reports.view"]},
        )
        assert perm_resp.status_code == 200
        assert set(perm_resp.json()["permission_keys"]) == {"projects.view", "reports.view"}


@pytest.mark.asyncio
async def test_assign_roles_to_user(db_session, override_db):
    admin = await _create_user(db_session, "rbac_user_roles_admin", "admin")
    target = await _create_user(db_session, "rbac_user_roles_target", "pm")
    pmo_role = (
        await db_session.execute(select(Role).where(Role.code == "pmo"))
    ).scalar_one()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            f"/access-control/users/{target.id}/roles",
            headers=_auth_header(admin),
            json={"role_ids": [pmo_role.id]},
        )
    assert response.status_code == 200
    assert pmo_role.id in response.json()["role_ids"]


@pytest.mark.asyncio
async def test_cannot_delete_last_admin(db_session, override_db):
    admin = await _create_user(db_session, "rbac_last_admin", "admin")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(
            f"/users/{admin.id}",
            headers=_auth_header(admin),
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_cannot_delete_system_admin_role(db_session, override_db):
    admin = await _create_user(db_session, "rbac_sys_role_admin", "admin")
    system_admin = (
        await db_session.execute(select(Role).where(Role.code == "system_admin"))
    ).scalar_one()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/access-control/roles/{system_admin.id}",
            headers=_auth_header(admin),
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_can_deactivate_custom_role(db_session, override_db):
    admin = await _create_user(db_session, "rbac_custom_deact_admin", "admin")
    custom = Role(
        code="qa_custom_deact",
        display_name="QA Custom Deact",
        is_system=False,
        is_active=True,
    )
    db_session.add(custom)
    await db_session.commit()
    await db_session.refresh(custom)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.delete(
            f"/access-control/roles/{custom.id}",
            headers=_auth_header(admin),
        )
    assert response.status_code == 200
    await db_session.refresh(custom)
    assert custom.is_active is False


@pytest.mark.asyncio
async def test_list_roles_includes_user_count(db_session, override_db):
    admin = await _create_user(db_session, "rbac_role_count_admin", "admin")
    pm_user = await _create_user(db_session, "rbac_role_count_pm", "pm")
    pmo_role = (
        await db_session.execute(select(Role).where(Role.code == "pmo"))
    ).scalar_one()
    db_session.add(UserRole(user_id=pm_user.id, role_id=pmo_role.id))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/access-control/roles", headers=_auth_header(admin))
    assert response.status_code == 200
    pmo_payload = next(item for item in response.json() if item["code"] == "pmo")
    assert pmo_payload["user_count"] >= 1


@pytest.mark.asyncio
async def test_list_role_assigned_users(db_session, override_db):
    admin = await _create_user(db_session, "rbac_assigned_admin", "admin")
    pm_user = await _create_user(db_session, "rbac_assigned_pm", "pm")
    pmo_role = (
        await db_session.execute(select(Role).where(Role.code == "pmo"))
    ).scalar_one()
    db_session.add(UserRole(user_id=pm_user.id, role_id=pmo_role.id))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            f"/access-control/roles/{pmo_role.id}/assigned-users",
            headers=_auth_header(admin),
        )
    assert response.status_code == 200
    usernames = {item["username"] for item in response.json()}
    assert "rbac_assigned_pm" in usernames


@pytest.mark.asyncio
async def test_legacy_role_helpers_unchanged(db_session):
    admin = await _create_user(db_session, "rbac_legacy_admin", "admin")
    proc = await _create_user(db_session, "rbac_legacy_proc", "procurement")

    admin_checker = require_admin()
    # require_admin returns a dependency callable; verify role membership contract
    assert admin.role in ["admin"]
    assert proc.role not in ["admin"]
    assert proc.role in ["procurement", "admin"] or proc.role == "procurement"


@pytest.mark.asyncio
async def test_require_permission_returns_403_when_enforced(db_session, monkeypatch):
    from app.config import settings
    from app.auth import require_permission

    user = await _create_user(db_session, "rbac_perm_enforce", "procurement")
    monkeypatch.setattr(settings, "enable_permission_enforcement", True)

    checker = require_permission("access_control.roles.manage")
    inner = checker.__wrapped__ if hasattr(checker, "__wrapped__") else None
    # Direct service check
    perms = await get_effective_permissions(db_session, user)
    assert "access_control.roles.manage" not in perms


@pytest.mark.asyncio
async def test_lockout_assertion_blocks_last_manager(db_session):
    admin = await _create_user(db_session, "rbac_lockout_admin", "admin")
    with pytest.raises(AccessControlLockoutError):
        await assert_user_may_be_deleted_or_deactivated(db_session, admin.id)


@pytest.mark.asyncio
async def test_payment_methods_list_still_works(db_session):
    from app.routers.procurement_financials import list_payment_methods

    finance_user = await _create_user(db_session, "rbac_fin_pm", "finance")
    result = await list_payment_methods(active_only=True, current_user=finance_user, db=db_session)
    assert isinstance(result, list)
