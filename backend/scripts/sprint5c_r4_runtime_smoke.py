#!/usr/bin/env python3
"""Sprint 5C-R4 runtime smoke — run inside demo backend container."""

from __future__ import annotations

import os
import sys

import httpx

BACKEND = os.environ.get("SMOKE_BACKEND_URL", "http://127.0.0.1:8000")
ADMIN_USER = os.environ.get("VERIFY_USERNAME", "admin")
ADMIN_PASS = os.environ.get("VERIFY_PASSWORD", "admin123")


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"OK: {msg}")


def login(client: httpx.Client, username: str, password: str) -> str:
    r = client.post(f"{BACKEND}/auth/login", json={"username": username, "password": password})
    if r.status_code != 200:
        fail(f"login {username} -> {r.status_code}")
    return r.json()["access_token"]


def ensure_role(client: httpx.Client, admin_headers: dict, code: str, display_name: str) -> int:
    roles = client.get(f"{BACKEND}/access-control/roles", headers=admin_headers)
    if roles.status_code != 200:
        fail("list roles failed")
    existing = next((r for r in roles.json() if r["code"] == code), None)
    if existing:
        return existing["id"]
    created = client.post(
        f"{BACKEND}/access-control/roles",
        headers=admin_headers,
        json={"code": code, "display_name": display_name, "description": "Sprint 5C-R4 audit role"},
    )
    if created.status_code not in (200, 201):
        fail(f"create role {code} -> {created.status_code}")
    return created.json()["id"]


def ensure_user(client: httpx.Client, admin_headers: dict, username: str, password: str) -> int:
    users = client.get(f"{BACKEND}/users/", headers=admin_headers)
    if users.status_code != 200:
        fail("list users failed")
    existing = next((u for u in users.json() if u["username"] == username), None)
    if existing:
        return existing["id"]
    created = client.post(
        f"{BACKEND}/users/",
        headers=admin_headers,
        json={"username": username, "password": password, "role": "pm", "is_active": True},
    )
    if created.status_code not in (200, 201):
        fail(f"create user {username} -> {created.status_code}")
    return created.json()["id"]


def main() -> None:
    with httpx.Client(timeout=30.0) as client:
        health = client.get(f"{BACKEND}/health")
        if health.status_code != 200:
            fail(f"/health -> {health.status_code}")
        ok("/health 200")

        openapi = client.get(f"{BACKEND}/openapi.json")
        if openapi.status_code != 200:
            fail(f"/openapi.json -> {openapi.status_code}")
        ok("/openapi.json 200")

        admin_token = login(client, ADMIN_USER, ADMIN_PASS)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        me = client.get(f"{BACKEND}/auth/me", headers=admin_headers)
        if me.status_code != 200 or "permissions" not in me.json():
            fail("/auth/me missing permissions")
        ok("/auth/me returns permissions")

        users_view_role = ensure_role(
            client, admin_headers, "sprint5c_r4_users_view_only", "Sprint 5C-R4 Users View Only"
        )
        perm_put = client.put(
            f"{BACKEND}/access-control/roles/{users_view_role}/permissions",
            headers=admin_headers,
            json={"permission_keys": ["users.view"]},
        )
        if perm_put.status_code != 200:
            fail("set users.view role permissions failed")

        users_view_user_id = ensure_user(
            client, admin_headers, "sprint5c_r4_users_view_only_user", "AuditTest!5cR4View"
        )
        assign = client.put(
            f"{BACKEND}/access-control/users/{users_view_user_id}/roles",
            headers=admin_headers,
            json={"role_ids": [users_view_role]},
        )
        if assign.status_code != 200:
            fail("assign users.view role failed")

        view_token = login(client, "sprint5c_r4_users_view_only_user", "AuditTest!5cR4View")
        view_headers = {"Authorization": f"Bearer {view_token}"}

        view_me = client.get(f"{BACKEND}/auth/me", headers=view_headers)
        if view_me.status_code != 200:
            fail("users.view user /auth/me failed")
        perms = view_me.json().get("permissions") or []
        if "users.view" not in perms:
            fail("users.view not in effective permissions")
        ok("users.view user has users.view permission")

        users_list = client.get(f"{BACKEND}/users/", headers=view_headers)
        if users_list.status_code != 200:
            fail(f"users.view user list users expected 200 got {users_list.status_code}")
        ok("users.view user can GET /users/")

        users_create = client.post(
            f"{BACKEND}/users/",
            headers=view_headers,
            json={"username": "r4_should_fail", "password": "x", "role": "pm", "is_active": True},
        )
        if users_create.status_code != 403:
            fail(f"users.view user create expected 403 got {users_create.status_code}")
        ok("users.view user cannot POST /users/")

        ac_roles = client.get(f"{BACKEND}/access-control/roles", headers=view_headers)
        if ac_roles.status_code != 403:
            fail(f"users.view user access-control roles expected 403 got {ac_roles.status_code}")
        ok("users.view user cannot GET /access-control/roles")

        manager_role = ensure_role(
            client, admin_headers, "sprint5c_r4_users_manager", "Sprint 5C-R4 Users Manager"
        )
        manager_perms = client.put(
            f"{BACKEND}/access-control/roles/{manager_role}/permissions",
            headers=admin_headers,
            json={
                "permission_keys": [
                    "users.view",
                    "users.create",
                    "users.edit",
                    "users.delete",
                ]
            },
        )
        if manager_perms.status_code != 200:
            fail("set users manager role permissions failed")

        manager_user_id = ensure_user(
            client, admin_headers, "sprint5c_r4_users_manager_user", "AuditTest!5cR4Mgr"
        )
        mgr_assign = client.put(
            f"{BACKEND}/access-control/users/{manager_user_id}/roles",
            headers=admin_headers,
            json={"role_ids": [manager_role]},
        )
        if mgr_assign.status_code != 200:
            fail("assign users manager role failed")

        mgr_token = login(client, "sprint5c_r4_users_manager_user", "AuditTest!5cR4Mgr")
        mgr_headers = {"Authorization": f"Bearer {mgr_token}"}
        mgr_list = client.get(f"{BACKEND}/users/", headers=mgr_headers)
        if mgr_list.status_code != 200:
            fail(f"users manager list expected 200 got {mgr_list.status_code}")
        ok("users manager can GET /users/")

        items_denied_role = ensure_role(
            client, admin_headers, "sprint5c_r4_masterdata_denied", "Sprint 5C-R4 Master Data Denied"
        )
        client.put(
            f"{BACKEND}/access-control/roles/{items_denied_role}/permissions",
            headers=admin_headers,
            json={"permission_keys": ["users.view"]},
        )
        denied_user_id = ensure_user(
            client, admin_headers, "sprint5c_r4_masterdata_denied_user", "AuditTest!5cR4Deny"
        )
        client.put(
            f"{BACKEND}/access-control/users/{denied_user_id}/roles",
            headers=admin_headers,
            json={"role_ids": [items_denied_role]},
        )
        denied_token = login(client, "sprint5c_r4_masterdata_denied_user", "AuditTest!5cR4Deny")
        denied_headers = {"Authorization": f"Bearer {denied_token}"}
        items_list = client.get(f"{BACKEND}/items-master/", headers=denied_headers)
        if items_list.status_code != 403:
            fail(f"masterdata denied items list expected 403 got {items_list.status_code}")
        ok("masterdata denied user cannot list items-master")

        pm = client.get(f"{BACKEND}/payment-methods", headers=admin_headers)
        if pm.status_code != 200:
            fail(f"admin payment-methods expected 200 got {pm.status_code}")
        ok("admin payment-methods 200")

    print("Sprint 5C-R4 runtime smoke PASS")


if __name__ == "__main__":
    main()
