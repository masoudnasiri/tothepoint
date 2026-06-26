#!/usr/bin/env python3
"""Sprint 5C-R4-Fix-2 runtime smoke — RBAC labels context + master data denial."""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

import httpx

BASE = os.environ.get("RIVAR_SMOKE_BASE", "http://127.0.0.1:8000").rstrip("/")
ADMIN_USER = os.environ.get("RIVAR_SMOKE_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("RIVAR_SMOKE_ADMIN_PASS", "admin123")
TEST_USER = os.environ.get("RIVAR_SMOKE_TEST_USER", "testuser5")
TEST_PASS = os.environ.get("RIVAR_SMOKE_TEST_PASS", "Test1234!")


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
            test_token = login(client, TEST_USER, TEST_PASS)
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
                ("GET /users/", client.get(f"{BASE}/users/", headers=test_h), False),
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

        except httpx.HTTPError as exc:
            results["test_user_error"] = str(exc)
            failures += 1

    results["failures"] = failures
    results["pass"] = failures == 0
    print(json.dumps(results, indent=2))
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
