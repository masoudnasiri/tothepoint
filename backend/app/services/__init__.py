"""
Service layer for package-aware procurement operations.
"""

from app.services.package_service import (
    get_package_for_project_item,
    get_package_subitems,
    normalize_procurement_reference,
    calculate_coverage_summary,
    validate_main_item_quantity,
    validate_and_compute_subitem_coverage,
    validate_package_coverage_for_lock,
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
    "validate_main_item_quantity",
    "validate_and_compute_subitem_coverage",
    "validate_package_coverage_for_lock",
    "log_feature_flag_event",
    "log_phase3_operation"
]

