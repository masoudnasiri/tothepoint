"""
Sprint 5C-R1 — Master data RBAC pilot enforcement tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import Role, User, UserRole
from app.security.permission_registry import PERMISSION_DEFINITIONS
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


@pytest.mark.asyncio
async def test_master_data_permission_keys_exist_in_registry():
    keys = {d.permission_key for d in PERMISSION_DEFINITIONS}
    for key in [
        "master_data.items.view",
        "master_data.items.create",
        "master_data.items.edit",
        "master_data.items.delete",
        "master_data.suppliers.view",
        "master_data.suppliers.create",
        "master_data.suppliers.edit",
        "master_data.suppliers.delete",
    ]:
        assert key in keys


@pytest.mark.asyncio
async def test_restricted_role_cannot_write_items_or_suppliers(db_session, override_db):
    admin = await _create_user(db_session, "pilot_admin", "admin")
    restricted = await _create_user(db_session, "pilot_restricted", "pm")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        role_resp = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={
                "code": "users_view_only_pilot",
                "display_name": "Users View Only Pilot",
                "description": "Sprint 5C-R1 restricted role",
            },
        )
        assert role_resp.status_code == 201
        role_id = role_resp.json()["id"]

        from sqlalchemy import delete

        await db_session.execute(delete(UserRole).where(UserRole.user_id == restricted.id))
        await db_session.commit()

        perm_resp = await client.put(
            f"/access-control/roles/{role_id}/permissions",
            headers=_auth_header(admin),
            json={"permission_keys": ["users.view"]},
        )
        assert perm_resp.status_code == 200

        assign_resp = await client.put(
            f"/access-control/users/{restricted.id}/roles",
            headers=_auth_header(admin),
            json={"role_ids": [role_id]},
        )
        assert assign_resp.status_code == 200

        items_list = await client.get("/items-master/", headers=_auth_header(restricted))
        assert items_list.status_code == 403

        items_create = await client.post(
            "/items-master/",
            headers=_auth_header(restricted),
            json={
                "company": "ACME",
                "item_name": "Widget",
                "model": "X1",
                "unit": "piece",
            },
        )
        assert items_create.status_code == 403

        suppliers_list = await client.get("/suppliers/", headers=_auth_header(restricted))
        assert suppliers_list.status_code == 403

        suppliers_create = await client.post(
            "/suppliers/",
            headers=_auth_header(restricted),
            json={"company_name": "Pilot Supplier Co"},
        )
        assert suppliers_create.status_code == 403


@pytest.mark.asyncio
async def test_view_only_role_can_list_but_not_create_items(db_session, override_db):
    admin = await _create_user(db_session, "pilot_admin_view", "admin")
    viewer = await _create_user(db_session, "pilot_items_viewer", "procurement")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        role_resp = await client.post(
            "/access-control/roles",
            headers=_auth_header(admin),
            json={
                "code": "items_view_only_pilot",
                "display_name": "Items View Only",
            },
        )
        role_id = role_resp.json()["id"]

        from sqlalchemy import delete

        await db_session.execute(delete(UserRole).where(UserRole.user_id == viewer.id))
        await db_session.commit()

        await client.put(
            f"/access-control/roles/{role_id}/permissions",
            headers=_auth_header(admin),
            json={"permission_keys": ["master_data.items.view"]},
        )
        await client.put(
            f"/access-control/users/{viewer.id}/roles",
            headers=_auth_header(admin),
            json={"role_ids": [role_id]},
        )

        list_resp = await client.get("/items-master/", headers=_auth_header(viewer))
        assert list_resp.status_code == 200

        create_resp = await client.post(
            "/items-master/",
            headers=_auth_header(viewer),
            json={
                "company": "ACME",
                "item_name": "Widget",
                "model": "X1",
                "unit": "piece",
            },
        )
        assert create_resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_items_master_returns_401(override_db):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/items-master/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_procurement_legacy_role_does_not_grant_items_write_without_rbac(db_session, override_db):
    """Legacy procurement could not create items; pilot must not grant write via users.role alone."""
    proc = await _create_user(db_session, "pilot_proc_legacy", "procurement")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        from sqlalchemy import delete

        await db_session.execute(delete(UserRole).where(UserRole.user_id == proc.id))
        await db_session.commit()

        create_resp = await client.post(
            "/items-master/",
            headers=_auth_header(proc),
            json={
                "company": "ACME",
                "item_name": "Widget",
                "model": "X1",
                "unit": "piece",
            },
        )
        assert create_resp.status_code == 403
