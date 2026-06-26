#!/usr/bin/env python3
"""Extract frontend routes, backend endpoints, and permission registry for Sprint 5C-R4 audit."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend" / "src"
BACKEND_ROUTERS = ROOT / "backend" / "app" / "routers"
PERM_REGISTRY = ROOT / "backend" / "app" / "security" / "permission_registry.py"


def extract_app_routes() -> List[Dict[str, str]]:
    app_tsx = (FRONTEND / "App.tsx").read_text(encoding="utf-8")
    routes: List[Dict[str, str]] = []
    for m in re.finditer(r'<Route path="([^"]+)" element=\{([^}]+)\}', app_tsx):
        path, element = m.group(1), m.group(2).strip()
        routes.append({"path": path, "element": element})
    return routes


def extract_layout_nav() -> List[Dict[str, Any]]:
    layout = (FRONTEND / "components" / "Layout.tsx").read_text(encoding="utf-8")
    items: List[Dict[str, Any]] = []
    for m in re.finditer(
        r"\{\s*textKey:\s*'([^']+)',\s*icon:\s*<[^>]+>,\s*(?:path:\s*'([^']*)',)?\s*roles:\s*\[([^\]]+)\]"
        r"(?:,\s*usersAccessControlOnly:\s*(true))?",
        layout,
    ):
        items.append(
            {
                "textKey": m.group(1),
                "path": m.group(2) or "",
                "roles": [r.strip().strip("'") for r in m.group(3).split(",")],
                "usersAccessControlOnly": bool(m.group(4)),
            }
        )
    return items


def extract_pages() -> List[str]:
    pages_dir = FRONTEND / "pages"
    return sorted(
        p.name
        for p in pages_dir.glob("*.tsx")
        if not p.name.endswith(".test.tsx") and not p.name.endswith(".smoke.test.tsx")
    )


def extract_router_endpoints() -> List[Dict[str, str]]:
    endpoints: List[Dict[str, str]] = []
    guard_patterns = [
        "require_pilot_permission",
        "require_users_permission",
        "require_permission",
        "require_admin",
        "require_pmo",
        "require_pm",
        "require_finance",
        "require_procurement",
        "require_role",
        "require_access_control_manager",
        "get_current_user",
    ]
    route_re = re.compile(
        r'@router\.(get|post|put|patch|delete)\(\s*["\']([^"\']*)["\']',
        re.MULTILINE,
    )
    for router_file in sorted(BACKEND_ROUTERS.glob("*.py")):
        if router_file.name == "__init__.py":
            continue
        text = router_file.read_text(encoding="utf-8")
        prefix_m = re.search(r'APIRouter\(prefix="([^"]+)"', text)
        prefix = prefix_m.group(1) if prefix_m else ""
        for m in route_re.finditer(text):
            method, subpath = m.group(1).upper(), m.group(2)
            full_path = f"{prefix}{subpath}" if subpath else prefix
            chunk = text[m.end() : m.end() + 600]
            guard = "unknown"
            for gp in guard_patterns:
                if gp in chunk:
                    guard = gp
                    break
            if guard == "unknown" and "Depends(" not in chunk:
                guard = "no auth dependency found"
            endpoints.append(
                {
                    "router": router_file.name,
                    "method": method,
                    "path": full_path,
                    "guard": guard,
                }
            )
    return endpoints


def extract_permissions() -> List[Dict[str, Any]]:
    text = PERM_REGISTRY.read_text(encoding="utf-8")
    perms: List[Dict[str, Any]] = []
    for m in re.finditer(
        r'_p\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*(\d+)\)',
        text,
    ):
        feature, action, description, sort_order = m.groups()
        perms.append(
            {
                "permission_key": f"{feature}.{action}",
                "feature_key": feature,
                "action": action,
                "description": description,
                "sort_order": int(sort_order),
            }
        )
    return perms


def main() -> None:
    inventory = {
        "routes": extract_app_routes(),
        "navigation": extract_layout_nav(),
        "pages": extract_pages(),
        "endpoints": extract_router_endpoints(),
        "permissions": extract_permissions(),
    }
    out = ROOT / "docs" / "restart-audit" / "64_sprint5c_r4_inventory_extract.json"
    out.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    print(f"  routes: {len(inventory['routes'])}")
    print(f"  nav items: {len(inventory['navigation'])}")
    print(f"  pages: {len(inventory['pages'])}")
    print(f"  endpoints: {len(inventory['endpoints'])}")
    print(f"  permissions: {len(inventory['permissions'])}")


if __name__ == "__main__":
    main()
