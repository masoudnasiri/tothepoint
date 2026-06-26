#!/usr/bin/env python3
"""Sprint 5C-R1 runtime smoke — run inside demo backend container."""

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
    r = client.post(
        f"{BACKEND}/auth/login",
        json={"username": username, "password": password},
    )
    if r.status_code != 200:
        fail(f"login {username} -> {r.status_code}")
    return r.json()["access_token"]


def main() -> None:
    with httpx.Client(timeout=30.0) as client:
        admin_token = login(client, ADMIN_USER, ADMIN_PASS)
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        me = client.get(f"{BACKEND}/auth/me", headers=admin_headers)
        if me.status_code != 200 or "permissions" not in me.json():
            fail("/auth/me missing permissions")
        ok("/auth/me returns roles and permissions")

        unauth_items = client.get(f"{BACKEND}/items-master/")
        if unauth_items.status_code not in (401, 403):
            fail(f"unauthenticated items-master expected 401/403 got {unauth_items.status_code}")
        ok(f"unauthenticated items-master denied ({unauth_items.status_code})")

        role_code = "sprint5c_r1_smoke_restricted"
        roles = client.get(f"{BACKEND}/access-control/roles", headers=admin_headers)
        if roles.status_code != 200:
            fail("list roles failed")
        existing = next((r for r in roles.json() if r["code"] == role_code), None)
        if existing:
            role_id = existing["id"]
        else:
            created = client.post(
                f"{BACKEND}/access-control/roles",
                headers=admin_headers,
                json={
                    "code": role_code,
                    "display_name": "Sprint 5C-R1 Smoke Restricted",
                    "description": "Temporary runtime smoke role",
                },
            )
            if created.status_code not in (200, 201):
                fail(f"create restricted role -> {created.status_code}")
            role_id = created.json()["id"]

        perm_put = client.put(
            f"{BACKEND}/access-control/roles/{role_id}/permissions",
            headers=admin_headers,
            json={"permission_keys": ["users.view"]},
        )
        if perm_put.status_code != 200:
            fail("set restricted role permissions failed")
        ok("restricted role has users.view only")

        smoke_username = "sprint5c_r1_smoke_user"
        users = client.get(f"{BACKEND}/users/", headers=admin_headers)
        smoke_user = next((u for u in users.json() if u["username"] == smoke_username), None)
        if not smoke_user:
            created_user = client.post(
                f"{BACKEND}/users/",
                headers=admin_headers,
                json={
                    "username": smoke_username,
                    "password": "SmokeTest!5cR1",
                    "role": "pm",
                    "is_active": True,
                },
            )
            if created_user.status_code not in (200, 201):
                fail(f"create smoke user -> {created_user.status_code}")
            smoke_user_id = created_user.json()["id"]
        else:
            smoke_user_id = smoke_user["id"]

        assign = client.put(
            f"{BACKEND}/access-control/users/{smoke_user_id}/roles",
            headers=admin_headers,
            json={"role_ids": [role_id]},
        )
        if assign.status_code != 200:
            fail("assign restricted role failed")
        ok("restricted role assigned to smoke user")

        restricted_token = login(client, smoke_username, "SmokeTest!5cR1")
        restricted_headers = {"Authorization": f"Bearer {restricted_token}"}

        items_list = client.get(f"{BACKEND}/items-master/", headers=restricted_headers)
        if items_list.status_code != 403:
            fail(f"restricted user items list expected 403 got {items_list.status_code}")
        ok("restricted user cannot list items-master")

        items_create = client.post(
            f"{BACKEND}/items-master/",
            headers=restricted_headers,
            json={"company": "Smoke", "item_name": "Item", "model": "X", "unit": "piece"},
        )
        if items_create.status_code != 403:
            fail(f"restricted user items create expected 403 got {items_create.status_code}")
        ok("restricted user cannot create items-master")

        suppliers_list = client.get(f"{BACKEND}/suppliers/", headers=restricted_headers)
        if suppliers_list.status_code != 403:
            fail(f"restricted user suppliers list expected 403 got {suppliers_list.status_code}")
        ok("restricted user cannot list suppliers")

        suppliers_create = client.post(
            f"{BACKEND}/suppliers/",
            headers=restricted_headers,
            json={"company_name": "Smoke Supplier Co"},
        )
        if suppliers_create.status_code != 403:
            fail(f"restricted user suppliers create expected 403 got {suppliers_create.status_code}")
        ok("restricted user cannot create suppliers")

        admin_items = client.get(f"{BACKEND}/items-master/", headers=admin_headers)
        if admin_items.status_code != 200:
            fail(f"admin items list expected 200 got {admin_items.status_code}")
        ok("admin can list items-master")

        pm = client.get(f"{BACKEND}/payment-methods", headers=admin_headers)
        if pm.status_code != 200:
            fail(f"admin payment-methods expected 200 got {pm.status_code}")
        ok("admin payment-methods 200")

        perm_role_code = "sprint5c_r1_smoke_permissioned"
        perm_existing = next((r for r in roles.json() if r["code"] == perm_role_code), None)
        if perm_existing:
            perm_role_id = perm_existing["id"]
        else:
            perm_created = client.post(
                f"{BACKEND}/access-control/roles",
                headers=admin_headers,
                json={
                    "code": perm_role_code,
                    "display_name": "Sprint 5C-R1 Smoke Permissioned (view only)",
                    "description": "Temporary runtime smoke role with master data view",
                },
            )
            if perm_created.status_code not in (200, 201):
                fail(f"create permissioned role -> {perm_created.status_code}")
            perm_role_id = perm_created.json()["id"]

        view_perms = [
            "master_data.items.view",
            "master_data.suppliers.view",
        ]
        perm_put = client.put(
            f"{BACKEND}/access-control/roles/{perm_role_id}/permissions",
            headers=admin_headers,
            json={"permission_keys": view_perms},
        )
        if perm_put.status_code != 200:
            fail("set permissioned role view permissions failed")
        ok("permissioned role has items/suppliers view only")

        perm_username = "sprint5c_r1_smoke_perm_user"
        users = client.get(f"{BACKEND}/users/", headers=admin_headers)
        perm_user = next((u for u in users.json() if u["username"] == perm_username), None)
        if not perm_user:
            created_perm_user = client.post(
                f"{BACKEND}/users/",
                headers=admin_headers,
                json={
                    "username": perm_username,
                    "password": "SmokeTest!5cR1Perm",
                    "role": "pm",
                    "is_active": True,
                },
            )
            if created_perm_user.status_code not in (200, 201):
                fail(f"create permissioned smoke user -> {created_perm_user.status_code}")
            perm_user_id = created_perm_user.json()["id"]
        else:
            perm_user_id = perm_user["id"]

        perm_assign = client.put(
            f"{BACKEND}/access-control/users/{perm_user_id}/roles",
            headers=admin_headers,
            json={"role_ids": [perm_role_id]},
        )
        if perm_assign.status_code != 200:
            fail("assign permissioned role failed")
        ok("permissioned role assigned to smoke user")

        perm_token = login(client, perm_username, "SmokeTest!5cR1Perm")
        perm_headers = {"Authorization": f"Bearer {perm_token}"}

        perm_items_list = client.get(f"{BACKEND}/items-master/", headers=perm_headers)
        if perm_items_list.status_code != 200:
            fail(f"permissioned user items list expected 200 got {perm_items_list.status_code}")
        ok("permissioned user can list items-master (view)")

        perm_items_create = client.post(
            f"{BACKEND}/items-master/",
            headers=perm_headers,
            json={"company": "SmokePerm", "item_name": "Item", "model": "Y", "unit": "piece"},
        )
        if perm_items_create.status_code != 403:
            fail(f"permissioned user items create expected 403 got {perm_items_create.status_code}")
        ok("permissioned user cannot create items-master without create perm")

        perm_suppliers_list = client.get(f"{BACKEND}/suppliers/", headers=perm_headers)
        if perm_suppliers_list.status_code != 200:
            fail(f"permissioned user suppliers list expected 200 got {perm_suppliers_list.status_code}")
        ok("permissioned user can list suppliers (view)")

        perm_suppliers_create = client.post(
            f"{BACKEND}/suppliers/",
            headers=perm_headers,
            json={"company_name": "Smoke Perm Supplier Co"},
        )
        if perm_suppliers_create.status_code != 403:
            fail(f"permissioned user suppliers create expected 403 got {perm_suppliers_create.status_code}")
        ok("permissioned user cannot create suppliers without create perm")

    print("Sprint 5C-R1 runtime smoke PASS")


if __name__ == "__main__":
    main()
