#!/usr/bin/env python3
"""Sprint 5D runtime smoke — procurement assignment backend."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

import httpx

BASE = os.environ.get("RIVAR_SMOKE_BASE", "http://127.0.0.1:8000").rstrip("/")
ADMIN_USER = os.environ.get("RIVAR_SMOKE_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("RIVAR_SMOKE_ADMIN_PASS", "admin123")
AC_ONLY_USER = os.environ.get("RIVAR_SMOKE_AC_ONLY_USER", "sprint5c_r4_fix3_ac_only_user")
AC_ONLY_PASS = os.environ.get("RIVAR_SMOKE_AC_ONLY_PASS", "AuditTest!5cFix3Ac")
PROC_USER = os.environ.get("RIVAR_SMOKE_PROC_USER", "sprint5d_proc_view_user")
PROC_PASS = os.environ.get("RIVAR_SMOKE_PROC_PASS", "AuditTest!5dProcView")
PROC_ROLE = "sprint5d_proc_view_role"


def login(client: httpx.Client, username: str, password: str) -> str:
    resp = client.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def classify(status: int, allowed: bool, *, conflict_ok: bool = False) -> str:
    if conflict_ok and status == 409:
        return "correctly_denied"
    ok = (200 <= status < 300) if allowed else status in (401, 403, 409)
    if ok:
        return "correctly_allowed" if allowed else "correctly_denied"
    return "incorrectly_allowed" if allowed else "incorrectly_denied"


def ensure_role(client: httpx.Client, admin_h: dict, code: str, display_name: str) -> int:
    roles = client.get(f"{BASE}/access-control/roles", headers=admin_h)
    roles.raise_for_status()
    existing = next((r for r in roles.json() if r["code"] == code), None)
    if existing:
        return existing["id"]
    created = client.post(
        f"{BASE}/access-control/roles",
        headers=admin_h,
        json={"code": code, "display_name": display_name, "description": "5D smoke role"},
    )
    created.raise_for_status()
    return created.json()["id"]


def ensure_user(client: httpx.Client, admin_h: dict, username: str, password: str) -> int:
    users = client.get(f"{BASE}/users/", headers=admin_h)
    users.raise_for_status()
    existing = next((u for u in users.json() if u["username"] == username), None)
    if existing:
        return existing["id"]
    created = client.post(
        f"{BASE}/users/",
        headers=admin_h,
        json={"username": username, "password": password, "role": "procurement", "is_active": True},
    )
    created.raise_for_status()
    return created.json()["id"]


def ensure_proc_view_user(client: httpx.Client, admin_h: dict) -> int:
    role_id = ensure_role(client, admin_h, PROC_ROLE, "5D Procurement View")
    client.put(
        f"{BASE}/access-control/roles/{role_id}/permissions",
        headers=admin_h,
        json={"permission_keys": ["procurement.assignments.view"]},
    ).raise_for_status()
    user_id = ensure_user(client, admin_h, PROC_USER, PROC_PASS)
    client.put(
        f"{BASE}/access-control/users/{user_id}/roles",
        headers=admin_h,
        json={"role_ids": [role_id]},
    ).raise_for_status()
    return user_id


def pick_project(client: httpx.Client, admin_h: dict) -> int:
    projects = client.get(f"{BASE}/projects/", headers=admin_h)
    projects.raise_for_status()
    data = projects.json()
    if not data:
        raise RuntimeError("No projects available for assignment smoke")
    return data[0]["id"]


def pick_project_item(client: httpx.Client, admin_h: dict, project_id: int) -> int | None:
    items = client.get(f"{BASE}/projects/{project_id}/items", headers=admin_h)
    if items.status_code != 200:
        return None
    data = items.json()
    if not data:
        return None
    return data[0]["id"]


def main() -> int:
    results: Dict[str, Any] = {"base": BASE, "checks": []}
    failures = 0

    with httpx.Client(timeout=30.0) as client:
        health = client.get(f"{BASE}/health")
        openapi = client.get(f"{BASE}/openapi.json")
        results["checks"].append({"route": "GET /health", "status": health.status_code, "expected": "allow"})
        results["checks"].append({"route": "GET /openapi.json", "status": openapi.status_code, "expected": "allow"})
        if health.status_code != 200 or openapi.status_code != 200:
            failures += 1

        admin_token = login(client, ADMIN_USER, ADMIN_PASS)
        admin_h = auth_headers(admin_token)
        me = client.get(f"{BASE}/auth/me", headers=admin_h)
        results["checks"].append({"route": "GET /auth/me admin", "status": me.status_code, "expected": "allow"})
        if me.status_code != 200:
            failures += 1

        proc_user_id = ensure_proc_view_user(client, admin_h)
        proc_token = login(client, PROC_USER, PROC_PASS)
        proc_h = auth_headers(proc_token)

        try:
            ac_token = login(client, AC_ONLY_USER, AC_ONLY_PASS)
            ac_h = auth_headers(ac_token)
        except Exception:
            ac_h = admin_h
            results["ac_only_user_fallback"] = True

        project_id = pick_project(client, admin_h)
        project_item_id = pick_project_item(client, admin_h, project_id)

        unauth_list = client.get(f"{BASE}/procurement-assignments")
        admin_list = client.get(f"{BASE}/procurement-assignments", headers=admin_h)
        ac_create = client.post(
            f"{BASE}/procurement-assignments",
            headers=ac_h,
            json={"project_id": project_id, "assignee_user_id": proc_user_id},
        )

        project_create = client.post(
            f"{BASE}/procurement-assignments",
            headers=admin_h,
            json={"project_id": project_id, "assignee_user_id": proc_user_id, "note": "5D smoke project"},
        )
        assignment_id = project_create.json().get("id") if project_create.status_code in (200, 201) else None

        dup = client.post(
            f"{BASE}/procurement-assignments",
            headers=admin_h,
            json={"project_id": project_id, "assignee_user_id": proc_user_id},
        )

        item_create_status = None
        if project_item_id:
            item_create = client.post(
                f"{BASE}/procurement-assignments",
                headers=admin_h,
                json={
                    "project_id": project_id,
                    "project_item_id": project_item_id,
                    "assignee_user_id": proc_user_id,
                    "note": "5D smoke item",
                },
            )
            item_create_status = item_create.status_code

        complete_status = cancel_status = None
        if assignment_id:
            complete = client.post(
                f"{BASE}/procurement-assignments/{assignment_id}/complete",
                headers=admin_h,
            )
            complete_status = complete.status_code
            create2 = client.post(
                f"{BASE}/procurement-assignments",
                headers=admin_h,
                json={"project_id": project_id, "assignee_user_id": proc_user_id},
            )
            if create2.status_code in (200, 201):
                cancel = client.post(
                    f"{BASE}/procurement-assignments/{create2.json()['id']}/cancel",
                    headers=admin_h,
                    json={"cancelled_reason": "5D smoke cancel"},
                )
                cancel_status = cancel.status_code

        proc_own = client.get(
            f"{BASE}/procurement-assignments?assignee_user_id={proc_user_id}",
            headers=proc_h,
        )

        matrix = [
            ("unauth GET /procurement-assignments", unauth_list, False),
            ("admin GET /procurement-assignments", admin_list, True),
            ("AC POST /procurement-assignments", ac_create, False),
            ("admin POST project assignment", project_create, True),
            ("admin duplicate active assignment", dup, False),
            ("proc view own assignments", proc_own, True),
            ("AC GET /payment-methods", client.get(f"{BASE}/payment-methods", headers=ac_h), False),
            ("admin GET /users/", client.get(f"{BASE}/users/", headers=admin_h), True),
        ]

        for label, resp, expected_allowed in matrix:
            entry = {
                "route": label,
                "status": resp.status_code,
                "expected": "allow" if expected_allowed else "deny",
                "classification": classify(
                    resp.status_code,
                    expected_allowed,
                    conflict_ok=("duplicate" in label.lower()),
                ),
            }
            if entry["classification"].startswith("incorrectly"):
                failures += 1
            results["checks"].append(entry)

        if item_create_status is not None:
            ok = item_create_status in (200, 201, 409)
            results["checks"].append(
                {"route": "admin POST item assignment", "status": item_create_status, "expected": "allow", "classification": "correctly_allowed" if ok else "incorrectly_denied"}
            )
            if not ok:
                failures += 1

        for label, status in [("complete assignment", complete_status), ("cancel assignment", cancel_status)]:
            if status is not None:
                ok = 200 <= status < 300
                results["checks"].append({"route": label, "status": status, "expected": "allow", "classification": "correctly_allowed" if ok else "incorrectly_denied"})
                if not ok:
                    failures += 1

    results["failures"] = failures
    results["pass"] = failures == 0
    print(json.dumps(results, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
