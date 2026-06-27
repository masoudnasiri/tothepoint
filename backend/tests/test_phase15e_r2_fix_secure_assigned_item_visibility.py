"""
Sprint 5E-R2-Fix — secure assigned item visibility tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import (
    Permission,
    ProcurementAssignment,
    Project,
    ProjectItem,
    Role,
    RolePermission,
    User,
    UserRole,
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
    project = Project(project_code="PA-5E-FIX-001", name="Secure Visibility Project", is_active=True)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _create_project_item(
    db_session,
    project: Project,
    code: str = "PA-FIX-ITEM",
    *,
    is_finalized: bool = True,
) -> ProjectItem:
    item = ProjectItem(
        project_id=project.id,
        item_code=code,
        item_name="Secure Item",
        quantity=3,
        delivery_options=["2026-07-01"],
        status="PENDING",
        invoice_submission_date=None,
        payment_date=None,
        expected_cash_in_date=None,
        actual_cash_in_date=None,
        description="Procurement-safe description",
        is_finalized=is_finalized,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _assign_role_with_permissions(
    db_session, user: User, role_code: str, permission_keys: set[str], admin: User
) -> None:
    role = Role(
        code=role_code,
        display_name=role_code,
        description="test role",
        is_active=True,
        is_system=False,
    )
    db_session.add(role)
    await db_session.flush()
    await db_session.execute(delete(UserRole).where(UserRole.user_id == user.id))
    db_session.add(UserRole(user_id=user.id, role_id=role.id, assigned_by_id=admin.id))
    for key in permission_keys:
        perm = (
            await db_session.execute(select(Permission).where(Permission.permission_key == key))
        ).scalar_one()
        db_session.add(RolePermission(role_id=role.id, permission_id=perm.id))
    await db_session.commit()


@pytest.mark.asyncio
async def test_assigned_items_endpoint_returns_allowlisted_fields_only(db_session, override_db):
    admin = await _create_user(db_session, "fix_admin", "admin")
    assignee = await _create_user(db_session, "fix_proc_user", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "proc_view_only_fix",
        {"procurement.assignments.view"},
        admin,
    )
    project = await _create_project(db_session)
    item = await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project.id,
                "project_item_id": item.id,
                "assignee_user_id": assignee.id,
                "note": "Item assignee",
            },
        )
        assert create_resp.status_code == 201

        my_items = await client.get(
            "/procurement-assignments/my-assigned-items",
            headers=_auth_header(assignee),
        )
        assert my_items.status_code == 200
        rows = my_items.json()
        assert len(rows) == 1
        row = rows[0]
        assert row["project_item_id"] == item.id
        assert row["item_code"] == item.item_code
        assert row["quantity"] == 3
        assert "invoice_submission_date" not in row
        assert "payment_date" not in row
        assert "expected_cash_in_date" not in row
        assert "actual_cash_in_date" not in row
        assert "sale_price" not in row
        assert row["assignments"][0]["assignment_scope"] == "project_item"


@pytest.mark.asyncio
async def test_assigned_items_denies_unassigned_procurement_user(db_session, override_db):
    admin = await _create_user(db_session, "fix_admin2", "admin")
    assignee = await _create_user(db_session, "fix_proc_user2", "procurement")
    other = await _create_user(db_session, "fix_proc_user3", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "proc_view_only_fix2",
        {"procurement.assignments.view"},
        admin,
    )
    await _assign_role_with_permissions(
        db_session,
        other,
        "proc_view_only_fix3",
        {"procurement.assignments.view"},
        admin,
    )
    project = await _create_project(db_session)
    item = await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project.id,
                "project_item_id": item.id,
                "assignee_user_id": assignee.id,
            },
        )
        denied = await client.get(
            f"/procurement-assignments/projects/{project.id}/assigned-items",
            headers=_auth_header(other),
        )
        assert denied.status_code == 200
        assert denied.json() == []


@pytest.mark.asyncio
async def test_project_items_list_denied_for_procurement_view_only_user(db_session, override_db):
    admin = await _create_user(db_session, "fix_admin3", "admin")
    assignee = await _create_user(db_session, "fix_proc_user4", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "proc_view_only_fix4",
        {"procurement.assignments.view"},
        admin,
    )
    project = await _create_project(db_session)
    await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.get(
            f"/items/project/{project.id}",
            headers=_auth_header(assignee),
        )
        assert denied.status_code == 403


@pytest.mark.asyncio
async def test_project_items_list_allowed_for_pmo_user(db_session, override_db):
    pmo = await _create_user(db_session, "fix_pmo_user", "pmo")
    project = await _create_project(db_session)
    await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        allowed = await client.get(
            f"/items/project/{project.id}",
            headers=_auth_header(pmo),
        )
        assert allowed.status_code == 200


@pytest.mark.asyncio
async def test_manager_can_view_project_assigned_items(db_session, override_db):
    admin = await _create_user(db_session, "fix_admin4", "admin")
    manager = await _create_user(db_session, "fix_pmo_mgr", "pmo")
    assignee = await _create_user(db_session, "fix_proc_user5", "procurement")
    project = await _create_project(db_session)
    item = await _create_project_item(db_session, project)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project.id,
                "project_item_id": item.id,
                "assignee_user_id": assignee.id,
            },
        )
        manager_view = await client.get(
            f"/procurement-assignments/projects/{project.id}/assigned-items",
            headers=_auth_header(manager),
        )
        assert manager_view.status_code == 200
        assert len(manager_view.json()) == 1


@pytest.mark.asyncio
async def test_project_level_assignment_expands_to_all_items(db_session, override_db):
    admin = await _create_user(db_session, "fix_admin5", "admin")
    assignee = await _create_user(db_session, "fix_proc_user6", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "proc_view_only_fix5",
        {"procurement.assignments.view"},
        admin,
    )
    project = await _create_project(db_session)
    await _create_project_item(db_session, project, "ITEM-A", is_finalized=True)
    await _create_project_item(db_session, project, "ITEM-B", is_finalized=False)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project.id,
                "assignee_user_id": assignee.id,
                "note": "Whole project",
            },
        )
        rows = (
            await client.get(
                "/procurement-assignments/my-assigned-items",
                headers=_auth_header(assignee),
            )
        ).json()
        assert len(rows) == 1
        assert all(row["covered_by_project_assignment"] for row in rows)
        assert rows[0]["is_finalized"] is True


@pytest.mark.asyncio
async def test_project_level_assignment_shows_newly_finalized_items(db_session, override_db):
    admin = await _create_user(db_session, "fix_admin6", "admin")
    assignee = await _create_user(db_session, "fix_proc_user7", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "proc_view_only_fix6",
        {"procurement.assignments.view"},
        admin,
    )
    project = await _create_project(db_session)
    await _create_project_item(db_session, project, "ITEM-C", is_finalized=True)
    later_finalized = await _create_project_item(
        db_session, project, "ITEM-D", is_finalized=False
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project.id,
                "assignee_user_id": assignee.id,
                "note": "Whole project",
            },
        )
        assert create_resp.status_code == 201

        first_rows = (
            await client.get(
                "/procurement-assignments/my-assigned-items",
                headers=_auth_header(assignee),
            )
        ).json()
        assert len(first_rows) == 1

        later_finalized.is_finalized = True
        await db_session.commit()

        second_rows = (
            await client.get(
                "/procurement-assignments/my-assigned-items",
                headers=_auth_header(assignee),
            )
        ).json()
        assert len(second_rows) == 2
        assert all(row["is_finalized"] for row in second_rows)
