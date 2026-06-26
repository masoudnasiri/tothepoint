"""
Sprint 5D — Procurement Assignment Backend tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import (
    AuditLog,
    Permission,
    ProcurementAssignment,
    Project,
    ProjectAssignment,
    ProjectItem,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.security.permission_registry import (
    ACCESS_CONTROL_ADMIN_PERMISSIONS,
    PROCUREMENT_ASSIGNMENT_MANAGE_PERMISSIONS,
)
from app.services.procurement_assignment_scope_service import (
    get_assigned_project_ids_for_user,
    get_assigned_project_item_ids_for_user,
    get_user_procurement_assignment_scope,
    user_has_active_procurement_assignment,
)
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


async def _create_project(db_session) -> Project:
    project = Project(project_code="PA-5D-001", name="Procurement Assignment Project", is_active=True)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _create_project_item(db_session, project: Project) -> ProjectItem:
    item = ProjectItem(
        project_id=project.id,
        item_code="PA-ITEM-001",
        item_name="Assignment Item",
        quantity=1,
        delivery_options=[],
        status="PENDING",
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _assign_system_role(db_session, user: User, role_code: str, admin: User) -> None:
    role = (
        await db_session.execute(select(Role).where(Role.code == role_code))
    ).scalar_one()
    await db_session.execute(delete(UserRole).where(UserRole.user_id == user.id))
    db_session.add(UserRole(user_id=user.id, role_id=role.id, assigned_by_id=admin.id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_procurement_assignment_permissions_seeded_idempotently(db_session):
    await ensure_rbac_seeded(db_session)
    keys = {
        "procurement.assignments.view",
        "procurement.assignments.create",
        "procurement.assignments.edit",
        "procurement.assignments.delete",
        "procurement.assignments.complete",
        "procurement.assignments.cancel",
    }
    result = await db_session.execute(
        select(Permission.permission_key).where(Permission.permission_key.in_(keys))
    )
    found = set(result.scalars().all())
    assert keys == found
    await ensure_rbac_seeded(db_session)
    result2 = await db_session.execute(
        select(Permission.permission_key).where(Permission.permission_key.in_(keys))
    )
    assert set(result2.scalars().all()) == found


@pytest.mark.asyncio
async def test_system_role_grants_for_procurement_assignments(db_session):
    await ensure_rbac_seeded(db_session)
    pmo_role = (await db_session.execute(select(Role).where(Role.code == "pmo"))).scalar_one()
    pm_role = (await db_session.execute(select(Role).where(Role.code == "project_manager"))).scalar_one()
    proc_role = (
        await db_session.execute(select(Role).where(Role.code == "procurement_specialist"))
    ).scalar_one()
    ac_role = (
        await db_session.execute(select(Role).where(Role.code == "access_control_admin"))
    ).scalar_one()

    async def role_keys(role_id: int) -> set[str]:
        rows = await db_session.execute(
            select(Permission.permission_key)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == role_id)
        )
        return set(rows.scalars().all())

    assert PROCUREMENT_ASSIGNMENT_MANAGE_PERMISSIONS.issubset(await role_keys(pmo_role.id))
    pm_keys = await role_keys(pm_role.id)
    assert "procurement.assignments.view" in pm_keys
    assert "procurement.assignments.create" in pm_keys
    assert "procurement.assignments.edit" in pm_keys
    assert "procurement.assignments.cancel" in pm_keys
    assert "procurement.assignments.delete" not in pm_keys

    proc_keys = await role_keys(proc_role.id)
    assert "procurement.assignments.view" in proc_keys
    assert "procurement.assignments.create" not in proc_keys

    ac_keys = await role_keys(ac_role.id)
    assert not any(k.startswith("procurement.assignments.") for k in ac_keys)
    assert not any(k.startswith("master_data") for k in ACCESS_CONTROL_ADMIN_PERMISSIONS)


@pytest.mark.asyncio
async def test_procurement_assignment_table_exists(db_session):
    result = await db_session.execute(
        select(ProcurementAssignment.id).limit(1)
    )
    assert result.fetchall() == []


@pytest.mark.asyncio
async def test_create_project_and_item_level_assignments(db_session, override_db):
    admin = await _create_user(db_session, "pa_admin", "admin")
    assignee = await _create_user(db_session, "pa_proc_user", "procurement")
    project = await _create_project(db_session)
    item = await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h = _auth_header(admin)
        project_resp = await client.post(
            "/procurement-assignments",
            headers=h,
            json={
                "project_id": project.id,
                "assignee_user_id": assignee.id,
                "note": "Project scope",
            },
        )
        assert project_resp.status_code == 201
        body = project_resp.json()
        assert body["assignment_scope"] == "project"
        assert body["project_item_id"] is None
        assert body["status"] == "active"

        item_resp = await client.post(
            "/procurement-assignments",
            headers=h,
            json={
                "project_id": project.id,
                "project_item_id": item.id,
                "assignee_user_id": assignee.id,
                "note": "Item scope",
            },
        )
        assert item_resp.status_code == 201
        item_body = item_resp.json()
        assert item_body["assignment_scope"] == "project_item"
        assert item_body["project_item_id"] == item.id


@pytest.mark.asyncio
async def test_bulk_assignment_and_duplicate_blocked(db_session, override_db):
    admin = await _create_user(db_session, "pa_bulk_admin", "admin")
    u1 = await _create_user(db_session, "pa_bulk_u1", "procurement")
    u2 = await _create_user(db_session, "pa_bulk_u2", "procurement")
    project = await _create_project(db_session)
    item = await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h = _auth_header(admin)
        bulk = await client.post(
            "/procurement-assignments/bulk",
            headers=h,
            json={
                "project_id": project.id,
                "assignee_user_ids": [u1.id, u2.id],
                "project_item_ids": [item.id],
                "note": "Bulk item assign",
            },
        )
        assert bulk.status_code == 201
        assert len(bulk.json()) == 2

        dup = await client.post(
            "/procurement-assignments",
            headers=h,
            json={
                "project_id": project.id,
                "project_item_id": item.id,
                "assignee_user_id": u1.id,
            },
        )
        assert dup.status_code == 409


@pytest.mark.asyncio
async def test_item_must_belong_to_project(db_session, override_db):
    admin = await _create_user(db_session, "pa_val_admin", "admin")
    assignee = await _create_user(db_session, "pa_val_proc", "procurement")
    project_a = await _create_project(db_session)
    project_b = Project(project_code="PA-5D-002", name="Other", is_active=True)
    db_session.add(project_b)
    await db_session.commit()
    await db_session.refresh(project_b)
    item_b = await _create_project_item(db_session, project_b)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project_a.id,
                "project_item_id": item_b.id,
                "assignee_user_id": assignee.id,
            },
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_inactive_assignee_rejected(db_session, override_db):
    admin = await _create_user(db_session, "pa_inact_admin", "admin")
    inactive = await _create_user(db_session, "pa_inact_user", "procurement")
    inactive.is_active = False
    await db_session.commit()
    project = await _create_project(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={"project_id": project.id, "assignee_user_id": inactive.id},
        )
        assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_filters_and_complete_cancel(db_session, override_db):
    admin = await _create_user(db_session, "pa_flow_admin", "admin")
    assignee = await _create_user(db_session, "pa_flow_proc", "procurement")
    project = await _create_project(db_session)
    item = await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h = _auth_header(admin)
        created = await client.post(
            "/procurement-assignments",
            headers=h,
            json={"project_id": project.id, "project_item_id": item.id, "assignee_user_id": assignee.id},
        )
        assignment_id = created.json()["id"]

        by_project = await client.get(f"/procurement-assignments?project_id={project.id}", headers=h)
        assert by_project.status_code == 200
        assert len(by_project.json()) >= 1

        by_item = await client.get(f"/project-items/{item.id}/procurement-assignments", headers=h)
        assert by_item.status_code == 200

        by_user = await client.get(f"/users/{assignee.id}/procurement-assignments", headers=h)
        assert by_user.status_code == 200

        complete = await client.post(f"/procurement-assignments/{assignment_id}/complete", headers=h)
        assert complete.status_code == 200
        assert complete.json()["status"] == "completed"

        created2 = await client.post(
            "/procurement-assignments",
            headers=h,
            json={"project_id": project.id, "assignee_user_id": assignee.id},
        )
        aid2 = created2.json()["id"]
        cancel = await client.post(
            f"/procurement-assignments/{aid2}/cancel",
            headers=h,
            json={"cancelled_reason": "No longer needed"},
        )
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_permission_checks(db_session, override_db):
    admin = await _create_user(db_session, "pa_perm_admin", "admin")
    ac_user = await _create_user(db_session, "pa_perm_ac", "pm")
    proc_user = await _create_user(db_session, "pa_perm_proc", "procurement")
    no_perm = await _create_user(db_session, "pa_perm_none", "finance")
    project = await _create_project(db_session)

    await _assign_system_role(db_session, ac_user, "access_control_admin", admin)
    await _assign_system_role(db_session, proc_user, "procurement_specialist", admin)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unauth = await client.get("/procurement-assignments")
        assert unauth.status_code in (401, 403)

        assert (await client.get("/procurement-assignments", headers=_auth_header(no_perm))).status_code == 403

        ac_create = await client.post(
            "/procurement-assignments",
            headers=_auth_header(ac_user),
            json={"project_id": project.id, "assignee_user_id": proc_user.id},
        )
        assert ac_create.status_code == 403

        admin_list = await client.get("/procurement-assignments", headers=_auth_header(admin))
        assert admin_list.status_code == 200

        admin_create = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={"project_id": project.id, "assignee_user_id": proc_user.id},
        )
        assert admin_create.status_code == 201

        proc_list = await client.get(
            f"/procurement-assignments?assignee_user_id={proc_user.id}",
            headers=_auth_header(proc_user),
        )
        assert proc_list.status_code == 200
        assert len(proc_list.json()) >= 1

        proc_other = await client.get(
            f"/procurement-assignments?assignee_user_id={admin.id}",
            headers=_auth_header(proc_user),
        )
        assert proc_other.status_code == 403


@pytest.mark.asyncio
async def test_audit_log_on_create(db_session, override_db):
    admin = await _create_user(db_session, "pa_audit_admin", "admin")
    assignee = await _create_user(db_session, "pa_audit_proc", "procurement")
    project = await _create_project(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={"project_id": project.id, "assignee_user_id": assignee.id},
        )

    logs = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "PROCUREMENT_ASSIGNMENT_CREATE")
    )
    assert logs.scalars().first() is not None


@pytest.mark.asyncio
async def test_scope_helpers(db_session, override_db):
    admin = await _create_user(db_session, "pa_scope_admin", "admin")
    assignee = await _create_user(db_session, "pa_scope_proc", "procurement")
    project = await _create_project(db_session)
    item = await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h = _auth_header(admin)
        await client.post(
            "/procurement-assignments",
            headers=h,
            json={"project_id": project.id, "assignee_user_id": assignee.id},
        )
        await client.post(
            "/procurement-assignments",
            headers=h,
            json={
                "project_id": project.id,
                "project_item_id": item.id,
                "assignee_user_id": assignee.id,
            },
        )

    assert project.id in await get_assigned_project_ids_for_user(db_session, assignee.id)
    assert item.id in await get_assigned_project_item_ids_for_user(db_session, assignee.id)
    scope = await get_user_procurement_assignment_scope(db_session, assignee.id)
    assert project.id in scope["project_ids"]
    assert item.id in scope["project_item_ids"]
    assert await user_has_active_procurement_assignment(db_session, assignee.id, project.id)
    assert await user_has_active_procurement_assignment(
        db_session, assignee.id, project.id, item.id
    )


@pytest.mark.asyncio
async def test_master_data_regression_ac_only_denied(db_session, override_db):
    """Regression: access_control_admin still denied master data."""
    admin = await _create_user(db_session, "pa_reg_admin", "admin")
    ac_user = await _create_user(db_session, "pa_reg_ac", "pm")
    await _assign_system_role(db_session, ac_user, "access_control_admin", admin)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        h = _auth_header(ac_user)
        assert (await client.get("/payment-methods", headers=h)).status_code == 403
        assert (await client.get("/users/", headers=h)).status_code == 200


@pytest.mark.asyncio
async def test_users_view_regression(db_session, override_db):
    admin = await _create_user(db_session, "pa_users_admin", "admin")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/users/", headers=_auth_header(admin))
        assert resp.status_code == 200
