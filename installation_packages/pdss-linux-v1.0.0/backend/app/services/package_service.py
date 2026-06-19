"""
Package-aware procurement service layer.
Phase 3: Dual-mode operation support for package and legacy flows.
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from fastapi import HTTPException, status
import logging

from app.config import settings
from app.models import ProjectItem, ProjectItemSubItem
from app.validators.package_validators import (
    validate_package_or_legacy_reference,
    resolve_package_from_project_item,
    log_feature_flag_usage
)

logger = logging.getLogger(__name__)


async def get_package_for_project_item(
    db: AsyncSession,
    project_item_id: int,
    package_type: str = "FULL"
) -> Optional[Dict[str, Any]]:
    """
    Get package information for a project item.
    
    Args:
        db: Database session
        project_item_id: Project item ID
        package_type: Package type (FULL, PARTIAL, CUSTOM)
    
    Returns:
        Dict with package info or None
    """
    if not settings.enable_package_procurement:
        return None
    
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT 
                    id,
                    project_item_id,
                    package_name,
                    package_type,
                    supplier_id,
                    description,
                    is_active
                FROM procurement_packages
                WHERE project_item_id = :project_item_id
                AND package_type = :package_type
                AND is_active = TRUE
                LIMIT 1
            """),
            {"project_item_id": project_item_id, "package_type": package_type}
        )
        row = result.fetchone()
        if row:
            return {
                "id": row[0],
                "project_item_id": row[1],
                "package_name": row[2],
                "package_type": row[3],
                "supplier_id": row[4],
                "description": row[5],
                "is_active": row[6]
            }
    except Exception as e:
        logger.warning(f"Error fetching package for project_item_id {project_item_id}: {e}")
    
    return None


async def get_package_subitems(
    db: AsyncSession,
    package_id: int
) -> List[Dict[str, Any]]:
    """
    Get sub-items covered by a package.
    
    Args:
        db: Database session
        package_id: Package ID
    
    Returns:
        List of sub-item information
    """
    if not settings.enable_package_procurement:
        return []
    
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT 
                    psi.id,
                    psi.package_id,
                    psi.project_item_subitem_id,
                    psi.quantity_covered,
                    psi.is_fully_covered,
                    psi.coverage_percentage,
                    pis.quantity as required_quantity
                FROM package_subitems psi
                INNER JOIN project_item_subitems pis ON pis.id = psi.project_item_subitem_id
                WHERE psi.package_id = :package_id
            """),
            {"package_id": package_id}
        )
        rows = result.fetchall()
        return [
            {
                "id": row[0],
                "package_id": row[1],
                "project_item_subitem_id": row[2],
                "quantity_covered": row[3],
                "is_fully_covered": row[4],
                "coverage_percentage": float(row[5]) if row[5] else None,
                "required_quantity": row[6]
            }
            for row in rows
        ]
    except Exception as e:
        logger.warning(f"Error fetching package subitems for package_id {package_id}: {e}")
        return []


async def normalize_procurement_reference(
    db: AsyncSession,
    package_id: Optional[int] = None,
    project_item_id: Optional[int] = None,
    item_code: Optional[str] = None,
    context: str = "procurement_option"
) -> Dict[str, Any]:
    """
    Normalize procurement reference to prefer package_id when enabled.
    Resolves package_id from project_item_id if needed.
    
    Args:
        db: Database session
        package_id: Package ID (if provided)
        project_item_id: Project item ID (legacy)
        item_code: Item code (legacy)
        context: Context for logging
    
    Returns:
        Dict with normalized references (package_id, project_item_id, item_code, reference_type)
    """
    log_feature_flag_usage("ENABLE_PACKAGE_PROCUREMENT", settings.enable_package_procurement, context)
    
    # If package_id is provided, use it
    if package_id is not None:
        if settings.enable_package_procurement:
            return {
                "package_id": package_id,
                "project_item_id": project_item_id,
                "item_code": item_code,
                "reference_type": "package"
            }
    
    # Try to resolve package_id from project_item_id
    if project_item_id is not None and settings.enable_package_procurement:
        resolved_package_id = await resolve_package_from_project_item(
            db, project_item_id, create_if_missing=False
        )
        if resolved_package_id:
            return {
                "package_id": resolved_package_id,
                "project_item_id": project_item_id,
                "item_code": item_code,
                "reference_type": "package"
            }
    
    # Fall back to legacy references
    if settings.legacy_project_item_fallback:
        log_feature_flag_usage("LEGACY_PROJECT_ITEM_FALLBACK", True, context)
        return {
            "package_id": None,
            "project_item_id": project_item_id,
            "item_code": item_code,
            "reference_type": "legacy"
        }
    
    # No valid reference
    raise ValueError(
        f"{context} must have at least one of: package_id, project_item_id, or item_code"
    )


async def calculate_coverage_summary(
    db: AsyncSession,
    project_item_id: int
) -> Dict[str, Any]:
    """
    Calculate coverage summary for a project item showing how much is covered by packages.
    
    Args:
        db: Database session
        project_item_id: Project item ID
        
    Returns:
        Dict with coverage summary including main_item, subitems, packages, and is_fully_covered
    """
    # Verify project item exists
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == project_item_id)
    )
    project_item = result.scalar_one_or_none()
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    
    # Get required quantities
    result = await db.execute(
        select(ProjectItemSubItem).where(ProjectItemSubItem.project_item_id == project_item_id)
    )
    subitems = result.scalars().all()
    
    # Get packages and their coverage
    result = await db.execute(
        text("""
            SELECT 
                p.id,
                p.package_name,
                p.package_type,
                p.main_item_quantity,
                COALESCE(SUM(psi.quantity_covered), 0) as total_subitem_coverage
            FROM procurement_packages p
            LEFT JOIN package_subitems psi ON psi.package_id = p.id
            WHERE p.project_item_id = :project_item_id
            AND p.is_active = TRUE
            GROUP BY p.id, p.package_name, p.package_type, p.main_item_quantity
        """),
        {"project_item_id": project_item_id}
    )
    packages = result.fetchall()
    
    # Calculate coverage
    main_item_required = project_item.quantity or 0
    main_item_covered = sum(p[3] or 0 for p in packages)
    
    subitem_coverage = {}
    for subitem in subitems:
        result = await db.execute(
            text("""
                SELECT COALESCE(SUM(quantity_covered), 0)
                FROM package_subitems
                WHERE project_item_subitem_id = :subitem_id
            """),
            {"subitem_id": subitem.id}
        )
        covered = result.scalar() or 0
        subitem_coverage[subitem.id] = {
            "required": subitem.quantity,
            "covered": int(covered),
            "remaining": max(0, subitem.quantity - int(covered))
        }
    
    is_fully_covered = (
        main_item_covered >= main_item_required and
        all(cov["covered"] >= cov["required"] for cov in subitem_coverage.values())
    )
    
    return {
        "project_item_id": project_item_id,
        "main_item": {
            "required": main_item_required,
            "covered": main_item_covered,
            "remaining": max(0, main_item_required - main_item_covered)
        },
        "subitems": subitem_coverage,
        "is_fully_covered": is_fully_covered,
        "packages": [
            {
                "id": p[0],
                "package_name": p[1],
                "package_type": p[2],
                "main_item_quantity": p[3] or 0,
                "subitem_coverage": p[4]
            }
            for p in packages
        ]
    }

