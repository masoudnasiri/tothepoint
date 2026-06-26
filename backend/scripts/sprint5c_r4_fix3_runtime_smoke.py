#!/usr/bin/env python3
"""Sprint 5C-R4-Fix-3 runtime smoke — master data backend enforcement closure."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import httpx

BASE = os.environ.get("RIVAR_SMOKE_BASE", "http://127.0.0.1:8000").rstrip("/")
ADMIN_USER = os.environ.get("RIVAR_SMOKE_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("RIVAR_SMOKE_ADMIN_PASS", "admin123")
AC_ONLY_USER = os.environ.get("RIVAR_SMOKE_AC_ONLY_USER", "sprint5c_r4_fix3_ac_only_user")
AC_ONLY_PASS = os.environ.get("RIVAR_SMOKE_AC_ONLY_PASS", "AuditTest!5cFix3Ac")
AC_ONLY_ROLE = "sprint5c_r4_fix3_ac_only_role"
PM_VIEW_USER = os.environ.get("RIVAR_SMOKE_PM_VIEW_USER", "sprint5c_r4_fix3_pm_view_user")
PM_VIEW_PASS = os.environ.get("RIVAR_SMOKE_PM_VIEW_PASS", "AuditTest!5cFix3PmView")
PM_VIEW_ROLE = "sprint5c_r4_fix3_pm_view_role"


def login(client: httpx.Client, username: str, password: str) -> str:
    resp = client.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def classify(status: int, allowed: bool) -> str:
    ok = (200 <= status < 300) if allowed else status in (401, 403)
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
        json={"code": code, "display_name": display_name, "description": "Fix3 smoke role"},
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
        json={"username": username, "password": password, "role": "pm", "is_active": True},
    )
    created.raise_for_status()
    return created.json()["id"]


def ensure_ac_only_user(client: httpx.Client, admin_h: dict) -> None:
    source = next(
        r
        for r in client.get(f"{BASE}/access-control/roles", headers=admin_h).json()
        if r["code"] == "access_control_admin"
    )
    keys = client.get(
        f"{BASE}/access-control/roles/{source['id']}/permissions", headers=admin_h
    ).json()["permission_keys"]
    role_id = ensure_role(client, admin_h, AC_ONLY_ROLE, "Fix3 Access Control Admin Copy")
    client.put(
        f"{BASE}/access-control/roles/{role_id}/permissions",
        headers=admin_h,
        json={"permission_keys": keys},
    ).raise_for_status()
    user_id = ensure_user(client, admin_h, AC_ONLY_USER, AC_ONLY_PASS)
    client.put(
        f"{BASE}/access-control/users/{user_id}/roles",
        headers=admin_h,
        json={"role_ids": [role_id]},
    ).raise_for_status()


def ensure_pm_view_user(client: httpx.Client, admin_h: dict) -> None:
    role_id = ensure_role(client, admin_h, PM_VIEW_ROLE, "Fix3 Payment Methods View")
    client.put(
        f"{BASE}/access-control/roles/{role_id}/permissions",
        headers=admin_h,
        json={"permission_keys": ["master_data.payment_methods.view"]},
    ).raise_for_status()
    user_id = ensure_user(client, admin_h, PM_VIEW_USER, PM_VIEW_PASS)
    client.put(
        f"{BASE}/access-control/users/{user_id}/roles",
        headers=admin_h,
        json={"role_ids": [role_id]},
    ).raise_for_status()


def main() -> int:
    results: Dict[str, Any] = {"base": BASE, "checks": []}
    failures = 0

    with httpx.Client(timeout=30.0) as client:
        admin_token = login(client, ADMIN_USER, ADMIN_PASS)
        admin_h = auth_headers(admin_token)

        ensure_ac_only_user(client, admin_h)
        ensure_pm_view_user(client, admin_h)

        ac_token = login(client, AC_ONLY_USER, AC_ONLY_PASS)
        ac_h = auth_headers(ac_token)
        pm_token = login(client, PM_VIEW_USER, PM_VIEW_PASS)
        pm_h = auth_headers(pm_token)

        ac_me = client.get(f"{BASE}/auth/me", headers=ac_h).json()
        master_data = sorted(p for p in ac_me.get("permissions") or [] if p.startswith("master_data"))
        results["ac_only_user"] = {
            "username": ac_me.get("username"),
            "legacy_role": ac_me.get("role"),
            "master_data_permissions": master_data,
        }
        if master_data:
            failures += 1

        matrix = [
            ("AC GET /users/", client.get(f"{BASE}/users/", headers=ac_h), True),
            ("AC GET /payment-methods", client.get(f"{BASE}/payment-methods", headers=ac_h), False),
            (
                "AC POST /payment-methods",
                client.post(
                    f"{BASE}/payment-methods",
                    headers=ac_h,
                    json={
                        "code": "DENYFIX3",
                        "name_en": "Deny",
                        "name_fa": "Deny",
                        "settlement_delay_days": 0,
                        "is_active": True,
                    },
                ),
                False,
            ),
            ("AC GET /items-master/", client.get(f"{BASE}/items-master/", headers=ac_h), False),
            ("AC GET /suppliers/", client.get(f"{BASE}/suppliers/", headers=ac_h), False),
            ("PM-view GET /payment-methods", client.get(f"{BASE}/payment-methods", headers=pm_h), True),
            ("admin GET /payment-methods", client.get(f"{BASE}/payment-methods", headers=admin_h), True),
            ("unauth GET /payment-methods", client.get(f"{BASE}/payment-methods"), False),
        ]

        for label, resp, expected_allowed in matrix:
            entry = {
                "route": label,
                "status": resp.status_code,
                "expected": "allow" if expected_allowed else "deny",
                "classification": classify(resp.status_code, expected_allowed),
            }
            if entry["classification"].startswith("incorrectly"):
                failures += 1
            results["checks"].append(entry)

    results["failures"] = failures
    results["pass"] = failures == 0
    print(json.dumps(results, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
