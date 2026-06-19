"""
Configuration and feature flags endpoint
Exposes feature flags for Phase 3 dual-mode procurement
"""

from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models import User
from app.config import settings

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/feature-flags")
async def get_feature_flags(
    current_user: User = Depends(get_current_user)
):
    """
    Get current feature flag states for Phase 3 dual-mode procurement.
    Frontend uses this to determine UI behavior (package mode vs legacy mode).
    """
    return {
        "enable_package_procurement": settings.enable_package_procurement,
        "legacy_project_item_fallback": settings.legacy_project_item_fallback,
        "supplier_normalization_enforced": settings.supplier_normalization_enforced,
        "enable_package_based_optimization": settings.enable_package_based_optimization,
        "require_package_id_for_new_options": settings.require_package_id_for_new_options
    }

