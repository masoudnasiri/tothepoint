"""
Sprint 5C-R4-Fix-3 — Master Data backend enforcement for Payment Methods and Cost Components.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import Permission, Role, RolePermission, User, UserRole
from app.security.permission_registry import ACCESS_CONTROL_ADMIN_PERMISSIONS
from app.services.rbac_service import ensure_rbac_seeded


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


async def _assign_role_permissions(db_session, role_id: int, permission_keys: list[str]) -> None:
    await db_session.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    perms = await db_session.execute(
        select(Permission).where(Permission.permission_key.in_(permission_keys))
    )
    for perm in perms.scalars().all():
        db_session.add(RolePermission(role_id=role_id, permission_id=perm.id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_access_control_admin_has_no_master_data_permissions():
    assert not any(key.startswith("master_data") for key in ACCESS_CONTROL_ADMIN_PERMISSIONS)


@pytest.mark.asyncio
async def test_ac_only_user_denied_payment_methods_and_cost_components(db_session, override_db):
    admin = await _create_user(db_session, "fix3_admin", "admin")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        role_resp = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={
                "code": "fix3_ac_only",
                "display_name": "Fix3 AC Only",
                "description": "Access control only",
            },
        )
        assert role_resp.status_code == 201
        role_id = role_resp.json()["id"]

        source = await db_session.execute(
            select(Role).where(Role.code == "access_control_admin")
        )
        source_role = source.scalar_one()
        links = await db_session.execute(
            select(RolePermission).where(RolePermission.role_id == source_role.id)
        )
        for row in links.scalars().all():
            db_session.add(RolePermission(role_id=role_id, permission_id=row.permission_id))
        await db_session.commit()

        ac_user = await _create_user(db_session, "fix3_ac_only_user", "pm")
        await db_session.execute(delete(UserRole).where(UserRole.user_id == ac_user.id))
        db_session.add(UserRole(user_id=ac_user.id, role_id=role_id, assigned_by_id=admin.id))
        await db_session.commit()

        h = _auth_header(ac_user)
        assert (await client.get("/payment-methods", headers=h)).status_code == 403
        assert (
            await client.post(
                "/payment-methods",
                headers=h,
                json={
                    "code": "DENY",
                    "name_en": "Deny",
                    "name_fa": "Deny",
                    "settlement_delay_days": 0,
                    "is_active": True,
                },
            )
        ).status_code == 403
        assert (await client.get("/items-master/", headers=h)).status_code == 403
        assert (await client.get("/suppliers/", headers=h)).status_code == 403


@pytest.mark.asyncio
async def test_payment_methods_view_and_write_permissions(db_session, override_db):
    admin = await _create_user(db_session, "fix3_pm_admin", "admin")
    viewer = await _create_user(db_session, "fix3_pm_viewer", "finance")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        view_role = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={"code": "fix3_pm_view", "display_name": "PM View", "description": "view only"},
        )
        manage_role = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={"code": "fix3_pm_manage", "display_name": "PM Manage", "description": "manage"},
        )
        view_role_id = view_role.json()["id"]
        manage_role_id = manage_role.json()["id"]

        await _assign_role_permissions(
            db_session, view_role_id, ["master_data.payment_methods.view"]
        )
        await _assign_role_permissions(
            db_session,
            manage_role_id,
            [
                "master_data.payment_methods.view",
                "master_data.payment_methods.create",
                "master_data.payment_methods.edit",
                "master_data.payment_methods.delete",
            ],
        )

        await db_session.execute(delete(UserRole).where(UserRole.user_id == viewer.id))
        db_session.add(
            UserRole(user_id=viewer.id, role_id=view_role_id, assigned_by_id=admin.id)
        )
        await db_session.commit()

        vh = _auth_header(viewer)
        assert (await client.get("/payment-methods", headers=vh)).status_code == 200
        assert (
            await client.post(
                "/payment-methods",
                headers=vh,
                json={
                    "code": "NOCREATE",
                    "name_en": "No",
                    "name_fa": "No",
                    "settlement_delay_days": 0,
                    "is_active": True,
                },
            )
        ).status_code == 403

        manager = await _create_user(db_session, "fix3_pm_manager", "finance")
        await db_session.execute(delete(UserRole).where(UserRole.user_id == manager.id))
        db_session.add(
            UserRole(user_id=manager.id, role_id=manage_role_id, assigned_by_id=admin.id)
        )
        await db_session.commit()
        mh = _auth_header(manager)
        create_resp = await client.post(
            "/payment-methods",
            headers=mh,
            json={
                "code": "FIX3QA",
                "name_en": "Fix3 QA",
                "name_fa": "Fix3 QA",
                "settlement_delay_days": 0,
                "is_active": True,
            },
        )
        assert create_resp.status_code == 201
        pm_id = create_resp.json()["id"]
        assert (
            await client.put(
                f"/payment-methods/{pm_id}",
                headers=mh,
                json={"name_en": "Fix3 QA Updated"},
            )
        ).status_code == 200
        assert (await client.delete(f"/payment-methods/{pm_id}", headers=mh)).status_code == 200


@pytest.mark.asyncio
async def test_cost_components_view_requires_permission(db_session, override_db):
    admin = await _create_user(db_session, "fix3_cc_admin", "admin")
    denied = await _create_user(db_session, "fix3_cc_denied", "procurement")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied_role = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={"code": "fix3_cc_none", "display_name": "No CC", "description": "none"},
        )
        role_id = denied_role.json()["id"]
        await _assign_role_permissions(db_session, role_id, ["procurement.view"])

        await db_session.execute(delete(UserRole).where(UserRole.user_id == denied.id))
        db_session.add(UserRole(user_id=denied.id, role_id=role_id, assigned_by_id=admin.id))
        await db_session.commit()

        assert (
            await client.get("/procurement-options/1/cost-components", headers=_auth_header(denied))
        ).status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_payment_methods_returns_401(override_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/payment-methods")).status_code == 401
