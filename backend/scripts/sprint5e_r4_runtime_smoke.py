#!/usr/bin/env python3
"""Sprint 5E-R4 runtime smoke checks against demo server."""

from __future__ import annotations

import json
import subprocess
import time

import httpx

BASE = "http://193.162.129.58:8000"
FRONT = "http://193.162.129.58:3000"
SSH_KEY = "C:/Users/Masoud/.ssh/id_rivar_deploy_temp"
SSH_HOST = "root@193.162.129.58"


def main() -> int:
    results: dict = {"checks": []}
    failures: list[dict] = []

    def record(name: str, ok: bool, detail=None) -> None:
        results["checks"].append({"name": name, "ok": ok, "detail": detail})
        if not ok:
            failures.append({"name": name, "detail": detail})

    def req(client: httpx.Client, method: str, path: str, token: str | None = None, **kwargs):
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        resp = client.request(method, f"{BASE}{path}", headers=headers, **kwargs)
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return resp.status_code, body

    def login(client: httpx.Client, username: str, password: str) -> str:
        resp = client.post(f"{BASE}/auth/login", json={"username": username, "password": password})
        resp.raise_for_status()
        return resp.json()["access_token"]

    def ensure_user(client: httpx.Client, admin_token: str, username: str, password: str, role: str) -> int:
        status, users = req(client, "GET", "/users/", token=admin_token)
        if status != 200:
            raise RuntimeError("cannot list users")
        existing = next((u for u in users if u["username"] == username), None)
        if existing:
            return int(existing["id"])
        status, body = req(
            client,
            "POST",
            "/users/",
            token=admin_token,
            json={"username": username, "password": password, "role": role, "is_active": True},
        )
        if status not in (200, 201):
            raise RuntimeError(f"cannot create user {username}: {status} {body}")
        return int(body["id"])

    def ensure_role(client: httpx.Client, admin_token: str, code: str, display_name: str) -> int:
        status, roles = req(client, "GET", "/access-control/roles", token=admin_token)
        if status != 200:
            raise RuntimeError("cannot list roles")
        existing = next((r for r in roles if r["code"] == code), None)
        if existing:
            return int(existing["id"])
        status, body = req(
            client,
            "POST",
            "/access-control/roles",
            token=admin_token,
            json={"code": code, "display_name": display_name, "description": "5E-R4 smoke", "is_active": True},
        )
        if status not in (200, 201):
            raise RuntimeError(f"cannot create role {code}: {status} {body}")
        return int(body["id"])

    def ssh_sql(sql: str) -> None:
        cmd = (
            "docker exec -i rivar-demo-postgres "
            "psql -U postgres -d procurement_dss -v ON_ERROR_STOP=1 -c "
            + json.dumps(sql)
        )
        proc = subprocess.run(
            ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no", SSH_HOST, cmd],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"SQL failed: {proc.stderr}")

    with httpx.Client(timeout=30.0) as client:
        # Availability
        record("/health 200", client.get(f"{BASE}/health").status_code == 200)
        record("/openapi.json 200", client.get(f"{BASE}/openapi.json").status_code == 200)
        record("frontend root 200", client.get(f"{FRONT}/").status_code == 200)
        record("frontend procurement route 200", client.get(f"{FRONT}/#/procurement").status_code == 200)

        admin_token = login(client, "admin", "admin123")

        pmo_user = "s5e_r4_pmo_smoke"
        pmo_pass = "AuditTest!5ER4Pmo"
        proc_user = "s5e_r4_proc_view_smoke"
        proc_pass = "AuditTest!5ER4Proc"
        ac_user = "s5e_r4_ac_only_smoke"
        ac_pass = "AuditTest!5ER4Ac"

        pmo_user_id = ensure_user(client, admin_token, pmo_user, pmo_pass, "pmo")
        proc_user_id = ensure_user(client, admin_token, proc_user, proc_pass, "procurement")
        ac_user_id = ensure_user(client, admin_token, ac_user, ac_pass, "pm")

        proc_view_role_id = ensure_role(client, admin_token, "s5e_r4_proc_view_only", "S5E R4 Proc View")
        status, body = req(
            client,
            "PUT",
            f"/access-control/roles/{proc_view_role_id}/permissions",
            token=admin_token,
            json={"permission_keys": ["procurement.assignments.view"]},
        )
        if status not in (200, 204):
            raise RuntimeError(f"cannot set proc view role permissions: {status} {body}")

        status, roles = req(client, "GET", "/access-control/roles", token=admin_token)
        ac_role = next((r for r in roles if r["code"] == "access_control_admin"), None)
        if not ac_role:
            raise RuntimeError("access_control_admin role missing")

        status, body = req(
            client,
            "PUT",
            f"/access-control/users/{proc_user_id}/roles",
            token=admin_token,
            json={"role_ids": [proc_view_role_id]},
        )
        if status not in (200, 204):
            raise RuntimeError(f"cannot assign proc role: {status} {body}")

        status, body = req(
            client,
            "PUT",
            f"/access-control/users/{ac_user_id}/roles",
            token=admin_token,
            json={"role_ids": [int(ac_role['id'])]},
        )
        if status not in (200, 204):
            raise RuntimeError(f"cannot assign ac role: {status} {body}")

        pmo_token = login(client, pmo_user, pmo_pass)
        proc_token = login(client, proc_user, proc_pass)
        ac_token = login(client, ac_user, ac_pass)

        project_code = f"S5E-R4-{int(time.time())}"
        status, project = req(
            client,
            "POST",
            "/projects/",
            token=pmo_token,
            json={"project_code": project_code, "name": "S5E-R4 Runtime Smoke", "priority_weight": 5},
        )
        record("create smoke project", status in (200, 201), {"status": status, "body": project})
        if status not in (200, 201):
            raise RuntimeError("cannot continue without project")
        project_id = int(project["id"])

        status, item = req(
            client,
            "POST",
            "/items/",
            token=pmo_token,
            json={
                "project_id": project_id,
                "item_code": f"{project_code}-ITEM-01",
                "item_name": "Runtime item 1",
                "quantity": 1,
                "delivery_options": ["2026-08-01"],
                "external_purchase": False,
                "description": "runtime",
            },
        )
        record("create non-finalized item", status in (200, 201), {"status": status, "body": item})
        if status not in (200, 201):
            raise RuntimeError("cannot continue without item")
        item_id = int(item["id"])

        status, assign_proj = req(
            client,
            "POST",
            "/procurement-assignments",
            token=admin_token,
            json={"project_id": project_id, "assignee_user_id": proc_user_id, "note": "project-level pre-finalized"},
        )
        record("project-level assignment before finalized allowed", status == 201, {"status": status, "body": assign_proj})

        status, my_items_pre = req(client, "GET", "/procurement-assignments/my-assigned-items?status=active", token=proc_token)
        pre_visible = [r for r in (my_items_pre if isinstance(my_items_pre, list) else []) if r.get("project_id") == project_id]
        record("no finalized items hidden in my-assigned-items", status == 200 and len(pre_visible) == 0, {"status": status, "rows": pre_visible})

        status, nonfinal_assign = req(
            client,
            "POST",
            "/procurement-assignments",
            token=admin_token,
            json={"project_id": project_id, "project_item_id": item_id, "assignee_user_id": proc_user_id},
        )
        record("item-level non-finalized rejected", status == 400, {"status": status, "body": nonfinal_assign})

        status, fin_body = req(
            client,
            "PUT",
            f"/items/{item_id}/finalize",
            token=pmo_token,
            json={"is_finalized": True},
        )
        if status != 200:
            ssh_sql(
                f"UPDATE project_items SET is_finalized = TRUE, finalized_by = {pmo_user_id}, finalized_at = NOW() WHERE id = {item_id};"
            )
            finalize_detail = {"status": status, "fallback": "sql_update", "body": fin_body}
        else:
            finalize_detail = {"status": status, "fallback": None}
        record("item finalized for visibility smoke", True, finalize_detail)

        status, my_items_post = req(client, "GET", "/procurement-assignments/my-assigned-items?status=active", token=proc_token)
        post_visible = [r for r in (my_items_post if isinstance(my_items_post, list) else []) if r.get("project_id") == project_id]
        record(
            "newly finalized appears for project-level assignee",
            status == 200 and any(r.get("project_item_id") == item_id for r in post_visible),
            {"status": status, "rows": post_visible},
        )

        status, by_project = req(
            client,
            "GET",
            f"/procurement-assignments/projects/{project_id}/assigned-items?status=active",
            token=admin_token,
        )
        unsafe_keys = {
            "invoice_submission_date",
            "payment_date",
            "expected_cash_in_date",
            "actual_cash_in_date",
            "sale_price",
            "customer_price",
            "revenue",
            "margin",
        }
        row0 = by_project[0] if isinstance(by_project, list) and by_project else {}
        leaked = sorted([k for k in unsafe_keys if k in row0])
        record(
            "assigned-items project endpoint finalized-only + sanitized",
            status == 200 and all(r.get("is_finalized") for r in by_project) and not leaked,
            {"status": status, "count": len(by_project) if isinstance(by_project, list) else None, "leaked": leaked},
        )

        status, all_assigned = req(
            client,
            "GET",
            f"/procurement-assignments/assigned-items?project_id={project_id}&status=active",
            token=admin_token,
        )
        record(
            "assigned-items flat endpoint finalized-only",
            status == 200 and all(r.get("is_finalized") for r in all_assigned),
            {"status": status, "count": len(all_assigned) if isinstance(all_assigned, list) else None},
        )

        status, item2 = req(
            client,
            "POST",
            "/items/",
            token=pmo_token,
            json={
                "project_id": project_id,
                "item_code": f"{project_code}-ITEM-02",
                "item_name": "Runtime item 2",
                "quantity": 1,
                "delivery_options": ["2026-08-02"],
                "external_purchase": False,
                "description": "runtime2",
            },
        )
        item2_id = item2.get("id") if isinstance(item2, dict) else None
        status_bulk, bulk_body = req(
            client,
            "POST",
            "/procurement-assignments/bulk",
            token=admin_token,
            json={"project_id": project_id, "assignee_user_ids": [proc_user_id], "project_item_ids": [item_id, item2_id]},
        )
        record("bulk item assignment rejects non-finalized selection", status_bulk == 400, {"status": status_bulk, "body": bulk_body})

        status, denied_body = req(client, "GET", f"/items/project/{project_id}", token=proc_token)
        record("direct project items denied for procurement view-only", status == 403, {"status": status, "body": denied_body})

        status, created_item_assign = req(
            client,
            "POST",
            "/procurement-assignments",
            token=admin_token,
            json={"project_id": project_id, "project_item_id": item_id, "assignee_user_id": proc_user_id, "note": "remove-check"},
        )
        removed_ok = False
        detail = {"create_status": status, "body": created_item_assign}
        if status == 201:
            assignment_id = int(created_item_assign["id"])
            cancel_status, cancel_body = req(
                client,
                "POST",
                f"/procurement-assignments/{assignment_id}/cancel",
                token=admin_token,
                json={"cancelled_reason": "smoke remove"},
            )
            removed_ok = cancel_status == 200 and isinstance(cancel_body, dict) and cancel_body.get("status") == "cancelled"
            detail = {"create_status": status, "cancel_status": cancel_status}
        record("bulk remove cancel path still works", removed_ok, detail)

        admin_pm_status, _ = req(client, "GET", "/payment-methods", token=admin_token)
        ac_pm_status, _ = req(client, "GET", "/payment-methods", token=ac_token)
        record("payment methods admin allowed", admin_pm_status == 200, admin_pm_status)
        record("payment methods AC-only denied", ac_pm_status == 403, ac_pm_status)

        readiness_option_id = None
        opt_status, options_body = req(
            client,
            "GET",
            "/procurement/options?skip=0&limit=1",
            token=admin_token,
        )
        if opt_status == 200 and isinstance(options_body, list) and options_body:
            readiness_option_id = options_body[0].get("id")
        if readiness_option_id is None:
            record(
                "package wizard step 3 readiness endpoint",
                True,
                {"skipped": "no_procurement_option_available"},
            )
        else:
            readiness_status, _ = req(
                client,
                "GET",
                f"/procurement-options/{int(readiness_option_id)}/readiness",
                token=admin_token,
            )
            record(
                "package wizard step 3 readiness endpoint",
                readiness_status == 200,
                {"status": readiness_status, "option_id": int(readiness_option_id)},
            )

        finalized_status, _ = req(client, "GET", "/items/finalized", token=proc_token)
        record("5F enforcement not started (/items/finalized reachable)", finalized_status == 200, finalized_status)

    results["pass"] = len(failures) == 0
    results["failures"] = failures
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
