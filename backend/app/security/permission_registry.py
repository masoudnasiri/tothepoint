"""
Versioned permission registry for Rivar RBAC (ADR-011).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Set, Tuple


@dataclass(frozen=True)
class PermissionDefinition:
    permission_key: str
    feature_key: str
    action: str
    description: str
    sort_order: int


def _p(feature: str, action: str, description: str, sort_order: int) -> PermissionDefinition:
    return PermissionDefinition(
        permission_key=f"{feature}.{action}",
        feature_key=feature,
        action=action,
        description=description,
        sort_order=sort_order,
    )


# fmt: off
PERMISSION_DEFINITIONS: Tuple[PermissionDefinition, ...] = (
    # access_control
    _p("access_control.roles", "view", "View roles", 10),
    _p("access_control.roles", "create", "Create custom roles", 11),
    _p("access_control.roles", "edit", "Edit roles", 12),
    _p("access_control.roles", "delete", "Deactivate/delete custom roles", 13),
    _p("access_control.roles", "manage", "Manage roles and role assignments", 14),
    _p("access_control.permissions", "view", "View permission registry", 20),
    _p("access_control.permissions", "manage", "Assign permissions to roles", 21),
    _p("access_control.user_roles", "view", "View user role assignments", 30),
    _p("access_control.user_roles", "edit", "Assign roles to users", 31),
    # users
    _p("users", "view", "View users", 100),
    _p("users", "create", "Create users", 101),
    _p("users", "edit", "Edit users", 102),
    _p("users", "delete", "Delete users", 103),
    # projects
    _p("projects", "view", "View projects", 200),
    _p("projects", "create", "Create projects", 201),
    _p("projects", "edit", "Edit projects", 202),
    _p("projects", "delete", "Delete projects", 203),
    # project_items
    _p("project_items", "view", "View project items", 210),
    _p("project_items", "create", "Create project items", 211),
    _p("project_items", "edit", "Edit project items", 212),
    _p("project_items", "delete", "Delete project items", 213),
    _p("project_items", "finalize", "Finalize project items", 214),
    # procurement (general)
    _p("procurement", "view", "View procurement workspace", 300),
    _p("procurement", "create", "Create procurement records", 301),
    _p("procurement", "edit", "Edit procurement records", 302),
    _p("procurement", "delete", "Delete procurement records", 303),
    # procurement packages
    _p("procurement.packages", "view", "View procurement packages", 310),
    _p("procurement.packages", "create", "Create procurement packages", 311),
    _p("procurement.packages", "edit", "Edit procurement packages", 312),
    _p("procurement.packages", "delete", "Delete procurement packages", 313),
    # procurement options
    _p("procurement.options", "view", "View procurement options", 320),
    _p("procurement.options", "create", "Create procurement options", 321),
    _p("procurement.options", "edit", "Edit procurement options", 322),
    _p("procurement.options", "delete", "Delete procurement options", 323),
    _p("procurement.options", "submit", "Submit procurement options", 324),
    # procurement assignments (Sprint 5D)
    _p("procurement.assignments", "view", "View procurement assignments", 330),
    _p("procurement.assignments", "create", "Create procurement assignments", 331),
    _p("procurement.assignments", "edit", "Edit procurement assignments", 332),
    _p("procurement.assignments", "delete", "Delete/deactivate procurement assignments", 333),
    _p("procurement.assignments", "complete", "Complete procurement assignments", 334),
    _p("procurement.assignments", "cancel", "Cancel procurement assignments", 335),
    # master_data
    _p("master_data", "view", "View master data", 400),
    _p("master_data.payment_methods", "view", "View payment methods", 410),
    _p("master_data.payment_methods", "create", "Create payment methods", 411),
    _p("master_data.payment_methods", "edit", "Edit payment methods", 412),
    _p("master_data.payment_methods", "delete", "Deactivate payment methods", 413),
    _p("master_data.cost_components", "view", "View cost components", 420),
    _p("master_data.cost_components", "create", "Create cost components", 421),
    _p("master_data.cost_components", "edit", "Edit cost components", 422),
    _p("master_data.cost_components", "delete", "Delete cost components", 423),
    _p("master_data.items", "view", "View items master catalog", 430),
    _p("master_data.items", "create", "Create items master records", 431),
    _p("master_data.items", "edit", "Edit items master records", 432),
    _p("master_data.items", "delete", "Delete items master records", 433),
    _p("master_data.suppliers", "view", "View suppliers", 440),
    _p("master_data.suppliers", "create", "Create suppliers", 441),
    _p("master_data.suppliers", "edit", "Edit suppliers", 442),
    _p("master_data.suppliers", "delete", "Delete suppliers", 443),
    # audit
    _p("audit_logs", "view", "View audit logs", 500),
    # finance / cashflow
    _p("finance", "view", "View finance module", 600),
    _p("finance", "edit", "Edit finance records", 601),
    _p("cashflow", "view", "View cashflow", 610),
    _p("cashflow", "edit", "Edit cashflow", 611),
    # optimization
    _p("optimization", "view", "View optimization", 700),
    _p("optimization", "run", "Run optimization", 701),
    _p("optimization", "review", "Review optimization results", 702),
    _p("optimization", "approve", "Approve optimization outcomes", 703),
    # reports
    _p("reports", "view", "View reports", 800),
    _p("reports", "export", "Export reports", 801),
    # decisions
    _p("decisions", "view", "View decisions", 900),
    _p("decisions", "approve", "Approve decisions", 901),
    _p("decisions", "lock", "Lock decisions", 902),
    _p("decisions", "review", "Review decisions", 903),
)
# fmt: on

ALL_PERMISSION_KEYS: FrozenSet[str] = frozenset(p.permission_key for p in PERMISSION_DEFINITIONS)

ACCESS_CONTROL_MANAGE_KEYS: FrozenSet[str] = frozenset(
    {
        "access_control.roles.manage",
        "access_control.permissions.manage",
        "access_control.user_roles.edit",
    }
)

LEGACY_ROLE_TO_SYSTEM_ROLE: Dict[str, str] = {
    "admin": "system_admin",
    "pmo": "pmo",
    "pm": "project_manager",
    "procurement": "procurement_specialist",
    "finance": "finance_analyst",
}

SYSTEM_ROLE_TO_LEGACY_ROLE: Dict[str, str] = {v: k for k, v in LEGACY_ROLE_TO_SYSTEM_ROLE.items()}

# Precedence when mirroring legacy users.role from multiple assigned roles
LEGACY_ROLE_PRECEDENCE: Tuple[str, ...] = (
    "admin",
    "pmo",
    "finance",
    "procurement",
    "pm",
)

SYSTEM_ROLE_DEFINITIONS: Tuple[Tuple[str, str, str, bool], ...] = (
    ("system_admin", "System Administrator", "Full platform access (legacy admin)", True),
    ("access_control_admin", "Access Control Administrator", "Manage roles and permissions", True),
    ("pmo", "PMO", "Project management office oversight", True),
    ("project_manager", "Project Manager", "Assigned project delivery", True),
    ("procurement_specialist", "Procurement Specialist", "Procurement operations", True),
    ("finance_analyst", "Finance Analyst", "Finance and cashflow operations", True),
)


def _keys(*keys: str) -> Set[str]:
    return set(keys)


def _feature_actions(feature: str, actions: List[str]) -> Set[str]:
    return {f"{feature}.{action}" for action in actions}


PROCUREMENT_ASSIGNMENT_MANAGE_PERMISSIONS = _keys(
    "procurement.assignments.view",
    "procurement.assignments.create",
    "procurement.assignments.edit",
    "procurement.assignments.delete",
    "procurement.assignments.complete",
    "procurement.assignments.cancel",
)

PMO_PERMISSIONS = (
    _keys(
        "projects.view", "projects.create", "projects.edit",
        "project_items.view", "project_items.create", "project_items.edit", "project_items.finalize",
        "procurement.view", "procurement.packages.view", "procurement.options.view",
    )
    | PROCUREMENT_ASSIGNMENT_MANAGE_PERMISSIONS
    | _keys(
        "master_data.view", "master_data.payment_methods.view", "master_data.cost_components.view",
        "master_data.items.view", "master_data.items.create", "master_data.items.edit",
        "master_data.suppliers.view", "master_data.suppliers.create", "master_data.suppliers.edit",
        "decisions.view", "decisions.review",
        "reports.view",
        "users.view",
    )
)

PROJECT_MANAGER_PERMISSIONS = (
    _keys(
        "projects.view",
        "project_items.view", "project_items.create", "project_items.edit",
        "procurement.view", "procurement.packages.view", "procurement.options.view",
        "procurement.assignments.view",
        "procurement.assignments.create",
        "procurement.assignments.edit",
        "procurement.assignments.cancel",
        "master_data.view",
        "master_data.items.view", "master_data.items.create", "master_data.items.edit",
        "master_data.suppliers.view", "master_data.suppliers.create", "master_data.suppliers.edit",
        "decisions.view", "decisions.review",
        "reports.view",
    )
)

PROCUREMENT_SPECIALIST_PERMISSIONS = (
    _keys(
        "procurement.assignments.view",
        "procurement.view", "procurement.create", "procurement.edit",
        "procurement.packages.view", "procurement.packages.create", "procurement.packages.edit",
        "procurement.options.view", "procurement.options.create", "procurement.options.edit",
        "procurement.options.submit",
        "master_data.view", "master_data.payment_methods.view",
        "master_data.cost_components.view", "master_data.cost_components.create",
        "master_data.cost_components.edit", "master_data.cost_components.delete",
        "master_data.items.view",
        "master_data.suppliers.view",
        "reports.view",
    )
)

FINANCE_ANALYST_PERMISSIONS = (
    _keys(
        "finance.view", "finance.edit",
        "cashflow.view", "cashflow.edit",
        "master_data.view", "master_data.payment_methods.view",
        "master_data.payment_methods.create", "master_data.payment_methods.edit",
        "master_data.payment_methods.delete",
        "master_data.items.view", "master_data.items.create", "master_data.items.edit",
        "master_data.suppliers.view", "master_data.suppliers.create", "master_data.suppliers.edit",
        "procurement.view", "procurement.options.view",
        "optimization.view", "optimization.run", "optimization.review", "optimization.approve",
        "decisions.view", "decisions.approve", "decisions.lock",
        "reports.view", "reports.export",
        "audit_logs.view",
    )
)

ACCESS_CONTROL_ADMIN_PERMISSIONS = _feature_actions(
    "access_control.roles", ["view", "create", "edit", "delete", "manage"]
) | _feature_actions(
    "access_control.permissions", ["view", "manage"]
) | _feature_actions(
    "access_control.user_roles", ["view", "edit"]
) | _keys("users.view", "users.create", "users.edit", "users.delete")

# Sprint 5C-R1/R4-Fix-3: RBAC-enforced master data prefixes (ignore legacy role except admin bypass).
PILOT_PERMISSION_PREFIXES: Tuple[str, ...] = (
    "master_data.items.",
    "master_data.suppliers.",
    "master_data.payment_methods.",
    "master_data.cost_components.",
)

# Sprint 5D: RBAC-enforced procurement assignment API prefix.
PROCUREMENT_ASSIGNMENT_PERMISSION_PREFIX = "procurement.assignments."

SYSTEM_ROLE_PERMISSION_KEYS: Dict[str, Set[str]] = {
    "system_admin": set(ALL_PERMISSION_KEYS),
    "access_control_admin": ACCESS_CONTROL_ADMIN_PERMISSIONS,
    "pmo": PMO_PERMISSIONS,
    "project_manager": PROJECT_MANAGER_PERMISSIONS,
    "procurement_specialist": PROCUREMENT_SPECIALIST_PERMISSIONS,
    "finance_analyst": FINANCE_ANALYST_PERMISSIONS,
}
