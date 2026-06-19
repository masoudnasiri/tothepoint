"""
Service layer for package-aware procurement operations.
"""

from app.services.package_service import (
    get_package_for_project_item,
    get_package_subitems,
    normalize_procurement_reference,
    calculate_coverage_summary
)

from app.services.audit_service import (
    log_feature_flag_event,
    log_phase3_operation
)

__all__ = [
    "get_package_for_project_item",
    "get_package_subitems",
    "normalize_procurement_reference",
    "calculate_coverage_summary",
    "log_feature_flag_event",
    "log_phase3_operation"
]

