"""
Sprint 3A-R3 scoped runtime verification for /opt/rivar-demo.

Checks procurement_financials endpoints only (payment methods, cost components,
readiness). Does not require Sprint 3C/4A atomic/coverage/projection/scenario paths.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.request
from typing import Dict, Optional, Tuple

from sqlalchemy import text

from app.database import AsyncSessionLocal

FIXTURE_PREFIX = "RIVAR_DEMO_ACCEPTED_BASELINE"
R3_REQUIRED_OPENAPI_PATHS = [
    "/payment-methods",
    "/payment-methods/{payment_method_id}",
    "/procurement-options/{option_id}/cost-components",
    "/procurement-options/{option_id}/readiness",
    "/procurement-cost-components/{component_id}",
]
READ_ONLY_SIDE_EFFECT_TABLES = [
    "optimization_results",
    "finalized_decisions",
    "decision_rounds",
    "cashflow_events",
    "invoices",
    "payments",
    "receipts",
]


def _http_json(
    method: str,
    url: str,
    *,
    payload: Optional[dict] = None,
    headers: Optional[dict] = None,
) -> Tuple[int, dict]:
    data = None
    all_headers = {"Content-Type": "application/json"}
    if headers:
        all_headers.update(headers)
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url=url,
        method=method.upper(),
        data=data,
        headers=all_headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            if not body:
                return int(response.status), {}
            parsed = json.loads(body)
            if isinstance(parsed, list):
                return int(response.status), {"items": parsed}
            return int(response.status), parsed
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload_json = json.loads(body) if body else {}
        except Exception:
            payload_json = {"raw": body}
        return int(exc.code), payload_json


async def _table_counts(tables: list[str]) -> Dict[str, Optional[int]]:
    counts: Dict[str, Optional[int]] = {}
    async with AsyncSessionLocal() as db:
        for table_name in tables:
            reg = await db.execute(
                text("SELECT to_regclass(:table_name)"),
                {"table_name": table_name},
            )
            exists = reg.scalar_one_or_none()
            if not exists:
                counts[table_name] = None
                continue
            result = await db.execute(text(f"SELECT COUNT(*)::bigint FROM {table_name}"))
            counts[table_name] = int(result.scalar_one())
    return counts


async def _discover_fixture_ids() -> dict:
    async with AsyncSessionLocal() as db:
        project_row = (
            await db.execute(
                text(
                    """
                    SELECT id, project_code
                    FROM projects
                    WHERE project_code LIKE :prefix
                    ORDER BY id ASC
                    LIMIT 1
                    """
                ),
                {"prefix": f"{FIXTURE_PREFIX}%"},
            )
        ).first()
        if not project_row:
            raise RuntimeError("Fixture project not found")

        item_row = (
            await db.execute(
                text(
                    """
                    SELECT id
                    FROM project_items
                    WHERE project_id = :project_id
                    ORDER BY id ASC
                    LIMIT 1
                    """
                ),
                {"project_id": int(project_row.id)},
            )
        ).first()
        if not item_row:
            raise RuntimeError("Fixture project item not found")

        option_rows = (
            await db.execute(
                text(
                    """
                    SELECT id
                    FROM procurement_options
                    WHERE project_item_id = :project_item_id
                    ORDER BY id ASC
                    """
                ),
                {"project_item_id": int(item_row.id)},
            )
        ).all()
        if not option_rows:
            raise RuntimeError("Fixture procurement options not found")

    return {
        "project_id": int(project_row.id),
        "project_code": str(project_row.project_code),
        "project_item_id": int(item_row.id),
        "option_ids": [int(row.id) for row in option_rows],
    }


async def verify_runtime_r3(backend_url: str, username: str, password: str) -> dict:
    report: Dict[str, object] = {"checks": [], "mode": "sprint3a-r3"}
    fixture = await _discover_fixture_ids()

    status, login_payload = _http_json(
        "POST",
        f"{backend_url}/auth/login",
        payload={"username": username, "password": password},
    )
    if status != 200 or "access_token" not in login_payload:
        raise RuntimeError(f"Login failed for verify user (status={status})")
    token = login_payload["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}
    report["checks"].append("auth_login")

    status, openapi = _http_json("GET", f"{backend_url}/openapi.json")
    if status != 200:
        raise RuntimeError(f"OpenAPI fetch failed (status={status})")
    openapi_paths = set((openapi.get("paths") or {}).keys())
    missing_paths = [path for path in R3_REQUIRED_OPENAPI_PATHS if path not in openapi_paths]
    if missing_paths:
        raise RuntimeError(f"Missing required R3 OpenAPI paths: {missing_paths}")
    report["checks"].append("r3_openapi_paths_present")

    status, payment_methods_payload = _http_json(
        "GET",
        f"{backend_url}/payment-methods",
        headers=auth_headers,
    )
    payment_methods = payment_methods_payload.get("items", payment_methods_payload)
    if status != 200 or not isinstance(payment_methods, list) or len(payment_methods) < 1:
        raise RuntimeError("payment-methods endpoint failed or returned empty list")
    report["checks"].append("payment_methods_list")

    ready_option_id: Optional[int] = None
    not_ready_option_id: Optional[int] = None
    for option_id in fixture["option_ids"]:
        status, readiness = _http_json(
            "GET",
            f"{backend_url}/procurement-options/{option_id}/readiness",
            headers=auth_headers,
        )
        if status != 200:
            raise RuntimeError(
                f"Readiness endpoint failed for option {option_id} (status={status})"
            )
        if readiness.get("is_ready_for_candidate_builder") is True and ready_option_id is None:
            ready_option_id = option_id
        if (
            readiness.get("is_ready_for_candidate_builder") is False
            and not_ready_option_id is None
        ):
            not_ready_option_id = option_id

    if ready_option_id is None:
        raise RuntimeError("No ready procurement option found in fixture")
    if not_ready_option_id is None:
        raise RuntimeError("No not-ready procurement option found in fixture")
    report["checks"].append("readiness_ready_and_not_ready_detected")

    before_read_counts = await _table_counts(READ_ONLY_SIDE_EFFECT_TABLES)

    status, components_payload = _http_json(
        "GET",
        f"{backend_url}/procurement-options/{ready_option_id}/cost-components",
        headers=auth_headers,
    )
    components = components_payload.get("items", components_payload)
    if status != 200 or not isinstance(components, list) or len(components) < 1:
        raise RuntimeError("cost-components list failed or empty for ready option")
    report["checks"].append("cost_components_list")

    base_component = next(
        (row for row in components if row.get("component_type") == "BASE_PRICE"),
        None,
    )
    if not base_component:
        raise RuntimeError("BASE_PRICE cost component missing on ready option")

    component_id = int(base_component["id"])
    payment_method_id = int(payment_methods[0]["id"])
    toggle_payload = {
        "payment_metadata": {
            "inherit_option_payment_schedule": False,
            "payee_type": "SUPPLIER",
            "payment_method_id": payment_method_id,
            "payment_type": "CASH",
            "planned_payment_date": "2026-07-05",
        }
    }
    status, updated = _http_json(
        "PUT",
        f"{backend_url}/procurement-cost-components/{component_id}",
        payload=toggle_payload,
        headers=auth_headers,
    )
    if status != 200:
        raise RuntimeError(
            f"cost component payment_metadata update failed (status={status})"
        )

    status, reread_payload = _http_json(
        "GET",
        f"{backend_url}/procurement-options/{ready_option_id}/cost-components",
        headers=auth_headers,
    )
    reread = reread_payload.get("items", reread_payload)
    reread_base = next(
        (row for row in reread if int(row.get("id", -1)) == component_id),
        None,
    )
    if status != 200 or not reread_base:
        raise RuntimeError("cost component re-read after update failed")
    metadata = reread_base.get("payment_metadata") or {}
    if metadata.get("inherit_option_payment_schedule") is not False:
        raise RuntimeError("component payment schedule save/reopen did not persist")
    report["checks"].append("component_payment_schedule_save_reopen")

    after_read_counts = await _table_counts(READ_ONLY_SIDE_EFFECT_TABLES)
    side_effect_deltas = {}
    for table_name, before_value in before_read_counts.items():
        after_value = after_read_counts.get(table_name)
        if before_value is None or after_value is None:
            continue
        if before_value != after_value:
            side_effect_deltas[table_name] = {"before": before_value, "after": after_value}
    if side_effect_deltas:
        raise RuntimeError(f"Read-only side-effect check failed: {side_effect_deltas}")
    report["checks"].append("read_only_side_effects_unchanged")

    report["fixture"] = fixture
    report["ready_option_id"] = ready_option_id
    report["not_ready_option_id"] = not_ready_option_id
    report["updated_component_id"] = component_id
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sprint 3A-R3 runtime verification for clean installer",
    )
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    args = parser.parse_args()

    try:
        report = asyncio.run(
            verify_runtime_r3(
                backend_url=args.backend_url.rstrip("/"),
                username=args.username,
                password=args.password,
            )
        )
        print(json.dumps({"status": "PASS", "report": report}, indent=2, default=str))
        return 0
    except Exception as exc:
        print(
            json.dumps(
                {"status": "FAIL", "error": str(exc)},
                indent=2,
                default=str,
            )
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
