"""
Sprint 5F — procurement assignment scope enforcement tests.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import get_db
from app.main import app
from app.models import (
    Currency,
    Permission,
    Project,
    ProjectItem,
    Role,
    RolePermission,
    Supplier,
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


async def _create_project(db_session, code: str) -> Project:
    project = Project(project_code=code, name=code, is_active=True)
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def _create_project_item(
    db_session,
    project: Project,
    code: str,
    *,
    is_finalized: bool,
) -> ProjectItem:
    item = ProjectItem(
        project_id=project.id,
        item_code=code,
        item_name=code,
        quantity=2,
        delivery_options=["2026-08-01"],
        status="PENDING",
        description=f"item {code}",
        is_finalized=is_finalized,
    )
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


async def _ensure_supplier_and_currency(db_session) -> tuple[Supplier, Currency]:
    supplier = Supplier(supplier_id="SUP-5F-001", company_name="Scope Supplier", status="ACTIVE")
    currency = Currency(
        code="USD",
        name="US Dollar",
        symbol="$",
        is_base_currency=True,
        is_active=True,
        decimal_places=2,
    )
    db_session.add(supplier)
    db_session.add(currency)
    await db_session.commit()
    await db_session.refresh(supplier)
    await db_session.refresh(currency)
    return supplier, currency


def _option_payload(*, item: ProjectItem, supplier_id: int, currency_id: int) -> dict:
    return {
        "project_item_id": item.id,
        "item_code": item.item_code,
        "supplier_name": "Scope Supplier",
        "supplier_id": supplier_id,
        "base_cost": 1200,
        "currency_id": currency_id,
        "shipping_cost": 0,
        "payment_terms": {"type": "cash", "discount_percent": 0},
    }


@pytest.mark.asyncio
async def test_assigned_only_items_finalized_scoped_and_sanitized(db_session, override_db):
    admin = await _create_user(db_session, "s5f_admin_a", "admin")
    assignee = await _create_user(db_session, "s5f_proc_a", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "s5f_assigned_only_view",
        {"procurement.assignments.view"},
        admin,
    )

    project_assigned = await _create_project(db_session, "S5F-ASSIGNED")
    project_other = await _create_project(db_session, "S5F-OTHER")

    assigned_finalized = await _create_project_item(
        db_session, project_assigned, "S5F-ITEM-A", is_finalized=True
    )
    await _create_project_item(db_session, project_assigned, "S5F-ITEM-B", is_finalized=False)
    unassigned_finalized = await _create_project_item(
        db_session, project_other, "S5F-ITEM-C", is_finalized=True
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_assignment = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project_assigned.id,
                "assignee_user_id": assignee.id,
                "note": "project scope",
            },
        )
        assert create_assignment.status_code == 201

        response = await client.get("/items/finalized", headers=_auth_header(assignee))
        assert response.status_code == 200
        rows = response.json()
        assert {int(r["id"]) for r in rows} == {int(assigned_finalized.id)}
        assert all(bool(r.get("is_finalized")) for r in rows)
        assert all(int(r.get("project_id")) == int(project_assigned.id) for r in rows)
        assert all(int(r["id"]) != int(unassigned_finalized.id) for r in rows)
        # Sensitive fields must not be present for assigned-only scope.
        for row in rows:
            assert "payment_date" not in row
            assert "invoice_submission_date" not in row
            assert "expected_cash_in_date" not in row
            assert "actual_cash_in_date" not in row
            assert "decision_date" not in row


@pytest.mark.asyncio
async def test_cancelled_assignment_removes_items_finalized_scope(db_session, override_db):
    admin = await _create_user(db_session, "s5f_admin_b", "admin")
    assignee = await _create_user(db_session, "s5f_proc_b", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "s5f_assigned_only_view_b",
        {"procurement.assignments.view"},
        admin,
    )
    project = await _create_project(db_session, "S5F-CANCEL")
    item = await _create_project_item(db_session, project, "S5F-CANCEL-ITEM", is_finalized=True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_assignment = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project.id,
                "project_item_id": item.id,
                "assignee_user_id": assignee.id,
                "note": "item scope",
            },
        )
        assert create_assignment.status_code == 201
        assignment_id = int(create_assignment.json()["id"])

        cancel = await client.post(
            f"/procurement-assignments/{assignment_id}/cancel",
            headers=_auth_header(admin),
            json={"cancelled_reason": "scope closed"},
        )
        assert cancel.status_code == 200

        response = await client.get("/items/finalized", headers=_auth_header(assignee))
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
async def test_procurement_option_scope_enforced_for_assigned_only(db_session, override_db):
    admin = await _create_user(db_session, "s5f_admin_c", "admin")
    assignee = await _create_user(db_session, "s5f_proc_c", "procurement")
    await _assign_role_with_permissions(
        db_session,
        assignee,
        "s5f_assigned_only_ops",
        {
            "procurement.assignments.view",
            "procurement.options.view",
            "procurement.options.create",
            "procurement.options.edit",
            "procurement.options.delete",
        },
        admin,
    )

    project = await _create_project(db_session, "S5F-OPTIONS")
    assigned_item = await _create_project_item(db_session, project, "S5F-OPT-A", is_finalized=True)
    unassigned_item = await _create_project_item(db_session, project, "S5F-OPT-B", is_finalized=True)
    non_finalized_item = await _create_project_item(
        db_session, project, "S5F-OPT-C", is_finalized=False
    )
    supplier, currency = await _ensure_supplier_and_currency(db_session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        seeded_option_resp = await client.post(
            "/procurement/options",
            headers=_auth_header(admin),
            json=_option_payload(
                item=unassigned_item,
                supplier_id=supplier.id,
                currency_id=currency.id,
            ),
        )
        assert seeded_option_resp.status_code == 200
        seeded_option_id = int(seeded_option_resp.json()["id"])

        create_assignment = await client.post(
            "/procurement-assignments",
            headers=_auth_header(admin),
            json={
                "project_id": project.id,
                "project_item_id": assigned_item.id,
                "assignee_user_id": assignee.id,
                "note": "item scope",
            },
        )
        assert create_assignment.status_code == 201

        unassigned_create = await client.post(
            "/procurement/options",
            headers=_auth_header(assignee),
            json=_option_payload(item=unassigned_item, supplier_id=supplier.id, currency_id=currency.id),
        )
        assert unassigned_create.status_code == 403

        non_finalized_create = await client.post(
            "/procurement/options",
            headers=_auth_header(assignee),
            json=_option_payload(
                item=non_finalized_item, supplier_id=supplier.id, currency_id=currency.id
            ),
        )
        assert non_finalized_create.status_code == 400

        assigned_create = await client.post(
            "/procurement/options",
            headers=_auth_header(assignee),
            json=_option_payload(item=assigned_item, supplier_id=supplier.id, currency_id=currency.id),
        )
        assert assigned_create.status_code == 200
        assigned_option_id = int(assigned_create.json()["id"])

        scoped_list = await client.get("/procurement/options", headers=_auth_header(assignee))
        assert scoped_list.status_code == 200
        visible_ids = {int(row["id"]) for row in scoped_list.json()}
        assert assigned_option_id in visible_ids
        assert seeded_option_id not in visible_ids

        deny_update = await client.put(
            f"/procurement/option/{seeded_option_id}",
            headers=_auth_header(assignee),
            json={"base_cost": 2000},
        )
        assert deny_update.status_code == 403

        deny_delete = await client.delete(
            f"/procurement/option/{seeded_option_id}",
            headers=_auth_header(assignee),
        )
        assert deny_delete.status_code == 403


@pytest.mark.asyncio
async def test_access_control_admin_role_denied_procurement_scope_endpoints(db_session, override_db):
    admin = await _create_user(db_session, "s5f_admin_d", "admin")
    ac_user = await _create_user(db_session, "s5f_ac_only", "pm")
    role = (
        await db_session.execute(select(Role).where(Role.code == "access_control_admin"))
    ).scalar_one()
    await db_session.execute(delete(UserRole).where(UserRole.user_id == ac_user.id))
    db_session.add(UserRole(user_id=ac_user.id, role_id=role.id, assigned_by_id=admin.id))
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        finalized_resp = await client.get("/items/finalized", headers=_auth_header(ac_user))
        assert finalized_resp.status_code == 403
        options_resp = await client.get("/procurement/options", headers=_auth_header(ac_user))
        assert options_resp.status_code == 403
