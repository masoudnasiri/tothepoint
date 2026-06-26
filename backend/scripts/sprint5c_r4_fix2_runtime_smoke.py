#!/usr/bin/env python3
"""Sprint 5C-R4-Fix-2 runtime smoke — access-control-only user + master data denial."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List

import httpx

BASE = os.environ.get("RIVAR_SMOKE_BASE", "http://127.0.0.1:8000").rstrip("/")
ADMIN_USER = os.environ.get("RIVAR_SMOKE_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("RIVAR_SMOKE_ADMIN_PASS", "admin123")
AC_ONLY_USER = os.environ.get("RIVAR_SMOKE_AC_ONLY_USER", "sprint5c_r4_fix2_ac_only_user")
AC_ONLY_PASS = os.environ.get("RIVAR_SMOKE_AC_ONLY_PASS", "AuditTest!5cFix2Ac")
AC_ONLY_ROLE = "sprint5c_r4_fix2_ac_only_role"


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
        json={"code": code, "display_name": display_name, "description": "Fix2 AC-only smoke role"},
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
    roles = client.get(f"{BASE}/access-control/roles", headers=admin_h)
    roles.raise_for_status()
    source = next((r for r in roles.json() if r["code"] == "access_control_admin"), None)
    if not source:
        raise RuntimeError("access_control_admin system role missing")

    source_perms = client.get(
        f"{BASE}/access-control/roles/{source['id']}/permissions", headers=admin_h
    )
    source_perms.raise_for_status()
    permission_keys = source_perms.json().get("permission_keys") or []

    role_id = ensure_role(client, admin_h, AC_ONLY_ROLE, "Fix2 Access Control Admin Copy")
    client.put(
        f"{BASE}/access-control/roles/{role_id}/permissions",
        headers=admin_h,
        json={"permission_keys": permission_keys},
    ).raise_for_status()

    user_id = ensure_user(client, admin_h, AC_ONLY_USER, AC_ONLY_PASS)
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

        me = client.get(f"{BASE}/auth/me", headers=admin_h)
        me.raise_for_status()
        results["admin_me_ok"] = me.status_code == 200

        perms_resp = client.get(f"{BASE}/access-control/permissions", headers=admin_h)
        perms_resp.raise_for_status()
        permissions = perms_resp.json()
        ac_features = sorted(
            {p["feature_key"] for p in permissions if p["feature_key"].startswith("access_control")}
        )
        results["access_control_features"] = ac_features

        try:
            ensure_ac_only_user(client, admin_h)
            test_token = login(client, AC_ONLY_USER, AC_ONLY_PASS)
            test_h = auth_headers(test_token)
            test_me = client.get(f"{BASE}/auth/me", headers=test_h)
            test_me.raise_for_status()
            test_body = test_me.json()
            test_perms: List[str] = test_body.get("permissions") or []
            master_data = sorted(p for p in test_perms if p.startswith("master_data"))
            results["test_user"] = {
                "username": test_body.get("username"),
                "legacy_role": test_body.get("role"),
                "roles": test_body.get("roles"),
                "permission_count": len(test_perms),
                "master_data_permissions": master_data,
                "access_control_only": bool(test_perms)
                and not master_data
                and any(p.startswith("access_control") for p in test_perms),
            }

            matrix = [
                ("GET /users/", client.get(f"{BASE}/users/", headers=test_h), True),
                ("GET /access-control/roles", client.get(f"{BASE}/access-control/roles", headers=test_h), True),
                ("GET /items-master/", client.get(f"{BASE}/items-master/", headers=test_h), False),
                ("GET /suppliers/", client.get(f"{BASE}/suppliers/", headers=test_h), False),
                ("GET /payment-methods", client.get(f"{BASE}/payment-methods", headers=test_h), None),
                (
                    "GET /procurement-options/1/cost-components",
                    client.get(f"{BASE}/procurement-options/1/cost-components", headers=test_h),
                    None,
                ),
            ]
            for label, resp, expected_allowed in matrix:
                if expected_allowed is None:
                    entry = {"route": label, "status": resp.status_code, "note": "legacy_auth_only"}
                else:
                    entry = {
                        "route": label,
                        "status": resp.status_code,
                        "expected": "allow" if expected_allowed else "deny",
                        "classification": classify(resp.status_code, expected_allowed),
                    }
                    if entry["classification"].startswith("incorrectly"):
                        failures += 1
                results["checks"].append(entry)

            if master_data:
                results["master_data_leak_in_me"] = True
                failures += 1
            else:
                results["master_data_leak_in_me"] = False

            if not results["test_user"]["access_control_only"]:
                failures += 1

        except httpx.HTTPError as exc:
            results["test_user_error"] = str(exc)
            failures += 1

    results["failures"] = failures
    results["pass"] = failures == 0
    print(json.dumps(results, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
