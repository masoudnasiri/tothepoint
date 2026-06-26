from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Dict, Optional, Tuple

from sqlalchemy import text

from app.database import AsyncSessionLocal


FIXTURE_PREFIX = "RIVAR_DEMO_ACCEPTED_BASELINE"
REQUIRED_OPENAPI_PATHS = [
    "/procurement-options/{option_id}/readiness",
    "/atomic-optimization-candidates/by-project/{project_id}",
    "/atomic-optimization-candidates/by-option/{option_id}",
    "/atomic-optimization-candidates/by-package/{package_id}",
    "/candidate-coverage-validation/by-project/{project_id}",
    "/candidate-coverage-validation/by-option/{option_id}",
    "/candidate-coverage-validation/by-package/{package_id}",
    "/financial-projections/by-project/{project_id}",
    "/financial-projections/by-option/{option_id}",
    "/financial-projections/by-package/{package_id}",
    "/optimization-scenario-preview/by-project/{project_id}",
    "/optimization-scenario-preview/by-package/{package_id}",
]
SIDE_EFFECT_TABLES = [
    "optimization_results",
    "finalized_decisions",
    "decision_rounds",
    "cashflow_events",
    "invoices",
    "payments",
    "receipts",
    "procurement_options",
    "procurement_cost_components",
    "project_items",
    "procurement_packages",
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
            return int(response.status), json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            payload_json = json.loads(body) if body else {}
        except Exception:
            payload_json = {"raw": body}
        return int(exc.code), payload_json


async def _table_counts() -> Dict[str, Optional[int]]:
    counts: Dict[str, Optional[int]] = {}
    async with AsyncSessionLocal() as db:
        for table_name in SIDE_EFFECT_TABLES:
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

        package_rows = (
            await db.execute(
                text(
                    """
                    SELECT id
                    FROM procurement_packages
                    WHERE project_item_id = :project_item_id
                    ORDER BY id ASC
                    """
                ),
                {"project_item_id": int(item_row.id)},
            )
        ).all()
        if not package_rows:
            raise RuntimeError("Fixture packages not found")

        option_rows = (
            await db.execute(
                text(
                    """
                    SELECT id, package_id
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
        "package_ids": [int(row.id) for row in package_rows],
        "option_ids": [int(row.id) for row in option_rows],
    }


async def verify_runtime(backend_url: str, username: str, password: str) -> dict:
    report: Dict[str, object] = {"checks": [], "errors": []}

    seed_time_counts = await _table_counts()
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

    status, openapi = _http_json("GET", f"{backend_url}/openapi.json")
    if status != 200:
        raise RuntimeError(f"OpenAPI fetch failed (status={status})")
    openapi_paths = set((openapi.get("paths") or {}).keys())
    missing_paths = [path for path in REQUIRED_OPENAPI_PATHS if path not in openapi_paths]
    if missing_paths:
        raise RuntimeError(f"Missing required OpenAPI paths: {missing_paths}")
    report["checks"].append("openapi_paths_present")

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

    ready_package_id = fixture["package_ids"][0]

    before_read_counts = await _table_counts()

    def _expect_ok(url: str) -> dict:
        status_code, payload = _http_json("GET", url, headers=auth_headers)
        if status_code != 200:
            raise RuntimeError(f"Endpoint failed {url} (status={status_code})")
        return payload

    _expect_ok(f"{backend_url}/atomic-optimization-candidates/by-project/{fixture['project_id']}")
    candidate_by_option = _expect_ok(
        f"{backend_url}/atomic-optimization-candidates/by-option/{ready_option_id}"
    )
    _expect_ok(f"{backend_url}/atomic-optimization-candidates/by-package/{ready_package_id}")

    coverage_project = _expect_ok(
        f"{backend_url}/candidate-coverage-validation/by-project/{fixture['project_id']}"
    )
    _expect_ok(f"{backend_url}/candidate-coverage-validation/by-option/{ready_option_id}")
    _expect_ok(f"{backend_url}/candidate-coverage-validation/by-package/{ready_package_id}")

    projection_project = _expect_ok(
        f"{backend_url}/financial-projections/by-project/{fixture['project_id']}"
    )
    _expect_ok(f"{backend_url}/financial-projections/by-option/{ready_option_id}")
    _expect_ok(f"{backend_url}/financial-projections/by-package/{ready_package_id}")

    scenario_project = _expect_ok(
        f"{backend_url}/optimization-scenario-preview/by-project/{fixture['project_id']}"
    )
    scenario_package = _expect_ok(
        f"{backend_url}/optimization-scenario-preview/by-package/{ready_package_id}"
    )
    scenario_filtered = _expect_ok(
        f"{backend_url}/optimization-scenario-preview/by-project/{fixture['project_id']}?"
        + urllib.parse.urlencode(
            [("scenario_types", "CHEAPEST"), ("scenario_types", "FASTEST_DELIVERY")]
        )
    )

    if coverage_project.get("is_valid_for_solver_input") is not True:
        raise RuntimeError("Coverage validation project scope is not solver-valid")

    if projection_project.get("is_projection_complete") is not True:
        raise RuntimeError("Financial projection is not complete for fixture project")
    if len(projection_project.get("projection_events", [])) <= 0:
        raise RuntimeError("Financial projection returned no projection events")
    if len(projection_project.get("period_summaries", [])) <= 0:
        raise RuntimeError("Financial projection returned no period summaries")
    if len(projection_project.get("candidate_summaries", [])) <= 0:
        raise RuntimeError("Financial projection returned no candidate summaries")

    if scenario_project.get("scenario_count", 0) <= 0:
        raise RuntimeError("Scenario preview returned zero scenarios")
    if scenario_project.get("feasible_scenario_count", 0) <= 0:
        raise RuntimeError("Scenario preview returned zero feasible scenarios")
    if scenario_package.get("scenario_count", 0) <= 0:
        raise RuntimeError("Package scope scenario preview returned zero scenarios")

    filtered_types = {row.get("scenario_type") for row in scenario_filtered.get("scenarios", [])}
    if not filtered_types:
        raise RuntimeError("Scenario filtering returned no scenarios")
    if not filtered_types.issubset({"CHEAPEST", "FASTEST_DELIVERY"}):
        raise RuntimeError(f"Scenario filtering returned unexpected types: {sorted(filtered_types)}")

    after_read_counts = await _table_counts()
    side_effect_deltas = {}
    for table_name, before_value in before_read_counts.items():
        after_value = after_read_counts.get(table_name)
        if before_value is None or after_value is None:
            continue
        if before_value != after_value:
            side_effect_deltas[table_name] = {"before": before_value, "after": after_value}
    if side_effect_deltas:
        raise RuntimeError(f"Read-only side-effect check failed: {side_effect_deltas}")

    report["fixture"] = fixture
    report["ready_option_id"] = ready_option_id
    report["not_ready_option_id"] = not_ready_option_id
    candidate_rows = candidate_by_option.get("candidates", []) or []
    candidate_id = candidate_rows[0].get("candidate_id") if candidate_rows else None
    report["discovered_ids"] = {
        "project_id": fixture["project_id"],
        "project_item_id": fixture["project_item_id"],
        "package_id": ready_package_id,
        "procurement_option_id": ready_option_id,
        "candidate_id": candidate_id,
    }
    report["seed_time_counts"] = seed_time_counts
    report["before_read_smoke_counts"] = before_read_counts
    report["after_read_smoke_counts"] = after_read_counts
    report["side_effect_deltas"] = side_effect_deltas
    report["projection_summary"] = {
        "is_projection_complete": projection_project.get("is_projection_complete"),
        "projection_events_count": len(projection_project.get("projection_events", [])),
        "period_summaries_count": len(projection_project.get("period_summaries", [])),
        "candidate_summaries_count": len(projection_project.get("candidate_summaries", [])),
    }
    report["scenario_summary"] = {
        "scenario_count": scenario_project.get("scenario_count"),
        "feasible_scenario_count": scenario_project.get("feasible_scenario_count"),
        "filtered_types": sorted(filtered_types),
    }
    report["checks"].append("runtime_read_only_smoke_passed")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Runtime verification for clean installer",
    )
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    args = parser.parse_args()

    try:
        report = asyncio.run(
            verify_runtime(
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
