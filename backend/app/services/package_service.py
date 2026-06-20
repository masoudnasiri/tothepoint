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
from app.models import (
    ProjectItem,
    ProjectItemSubItem,
    ProcurementPackage,
    PackageSubItem,
    FinalizedDecision,
)
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
    
    subitem_ids = [subitem.id for subitem in subitems]
    covered_by_subitem_id: Dict[int, int] = {}
    if subitem_ids:
        covered_result = await db.execute(
            select(
                PackageSubItem.project_item_subitem_id,
                func.coalesce(func.sum(PackageSubItem.quantity_covered), 0)
            )
            .join(ProcurementPackage, ProcurementPackage.id == PackageSubItem.package_id)
            .where(PackageSubItem.project_item_subitem_id.in_(subitem_ids))
            .where(ProcurementPackage.is_active == True)
            .group_by(PackageSubItem.project_item_subitem_id)
        )
        covered_by_subitem_id = {
            int(row[0]): int(row[1] or 0) for row in covered_result.all()
        }

    subitem_coverage = {}
    for subitem in subitems:
        covered = covered_by_subitem_id.get(subitem.id, 0)
        subitem_coverage[subitem.id] = {
            "required": subitem.quantity,
            "covered": covered,
            "remaining": max(0, subitem.quantity - covered)
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


async def validate_main_item_quantity(
    db: AsyncSession,
    project_item_id: int,
    main_item_quantity: Optional[int]
) -> None:
    """
    Validate package main-item quantity against project item demand.

    Rules:
    - quantity must be >= 0
    - quantity cannot exceed project_item.quantity
    """
    if main_item_quantity is None:
        return

    if main_item_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="main_item_quantity must be greater than or equal to 0"
        )

    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == project_item_id)
    )
    project_item = result.scalar_one_or_none()
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )

    required_quantity = int(project_item.quantity or 0)
    if main_item_quantity > required_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"main_item_quantity ({main_item_quantity}) cannot exceed required project item "
                f"quantity ({required_quantity})"
            )
        )


async def validate_and_compute_subitem_coverage(
    db: AsyncSession,
    package_id: int,
    project_item_subitem_id: int,
    quantity_covered: int,
    *,
    exclude_package_subitem_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Validate package sub-item mapping and compute normalized coverage fields.

    Rules:
    - package and project_item_subitem must exist
    - project_item_subitem must belong to package.project_item_id
    - quantity_covered cannot exceed required sub-item quantity
    - total coverage across ACTIVE packages for this sub-item cannot exceed requirement
    """
    package_result = await db.execute(
        select(ProcurementPackage).where(ProcurementPackage.id == package_id)
    )
    package = package_result.scalar_one_or_none()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )

    subitem_result = await db.execute(
        select(ProjectItemSubItem).where(ProjectItemSubItem.id == project_item_subitem_id)
    )
    project_subitem = subitem_result.scalar_one_or_none()
    if not project_subitem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item sub-item not found"
        )

    if project_subitem.project_item_id != package.project_item_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sub-item does not belong to the same project item as the package"
        )

    required_quantity = int(project_subitem.quantity or 0)
    if quantity_covered > required_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"quantity_covered ({quantity_covered}) cannot exceed required sub-item "
                f"quantity ({required_quantity})"
            )
        )

    total_query = (
        select(func.coalesce(func.sum(PackageSubItem.quantity_covered), 0))
        .select_from(PackageSubItem)
        .join(ProcurementPackage, ProcurementPackage.id == PackageSubItem.package_id)
        .where(PackageSubItem.project_item_subitem_id == project_item_subitem_id)
        .where(ProcurementPackage.is_active == True)
    )
    if exclude_package_subitem_id is not None:
        total_query = total_query.where(PackageSubItem.id != exclude_package_subitem_id)

    total_result = await db.execute(total_query)
    existing_coverage = int(total_result.scalar() or 0)
    total_after = existing_coverage + int(quantity_covered)
    if total_after > required_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Coverage overflow for this sub-item: existing active coverage ({existing_coverage}) + "
                f"new quantity ({quantity_covered}) exceeds required quantity ({required_quantity})"
            )
        )

    coverage_percentage = None
    if required_quantity > 0:
        coverage_percentage = round((float(quantity_covered) / float(required_quantity)) * 100, 2)
    else:
        coverage_percentage = 100.0 if quantity_covered == 0 else 0.0

    return {
        "required_quantity": required_quantity,
        "is_fully_covered": quantity_covered >= required_quantity,
        "coverage_percentage": coverage_percentage,
    }


async def validate_package_coverage_for_lock(
    db: AsyncSession,
    decision_ids: List[int],
) -> None:
    """
    Enforce package/sub-item coverage before decisions are locked.

    Policy:
    - active only when both package procurement and lock enforcement flags are enabled
    - checks project items that have sub-item requirements and package-based decisions
    - uses union of existing LOCKED packages + currently locking package decisions
    - blocks lock if any required sub-item remains uncovered
    """
    if not decision_ids:
        return

    if not (settings.enable_package_procurement and settings.enforce_package_coverage_on_lock):
        return

    target_result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id.in_(decision_ids))
    )
    target_decisions = target_result.scalars().all()
    if not target_decisions:
        return

    # Only project-items that are actually using package decisions are validated.
    project_item_ids = {
        d.project_item_id
        for d in target_decisions
        if d.project_item_id is not None and d.package_id is not None
    }

    for project_item_id in project_item_ids:
        target_package_ids = {
            d.package_id
            for d in target_decisions
            if d.project_item_id == project_item_id and d.package_id is not None
        }
        if not target_package_ids:
            continue

        locked_result = await db.execute(
            select(FinalizedDecision.package_id).where(
                FinalizedDecision.project_item_id == project_item_id,
                FinalizedDecision.status == "LOCKED",
                FinalizedDecision.package_id.isnot(None),
            )
        )
        locked_package_ids = {row[0] for row in locked_result.all() if row[0] is not None}
        package_ids_to_validate = target_package_ids | locked_package_ids

        await _validate_project_item_subitem_coverage_for_packages(
            db,
            project_item_id=project_item_id,
            package_ids=package_ids_to_validate,
        )


async def _validate_project_item_subitem_coverage_for_packages(
    db: AsyncSession,
    *,
    project_item_id: int,
    package_ids: set,
) -> None:
    """Validate aggregate sub-item coverage for selected packages of one project item."""
    if not package_ids:
        return

    requirements_result = await db.execute(
        select(ProjectItemSubItem).where(ProjectItemSubItem.project_item_id == project_item_id)
    )
    requirements = requirements_result.scalars().all()
    if not requirements:
        # No sub-item breakdown -> skip enforcement for this project item.
        return

    active_packages_result = await db.execute(
        select(ProcurementPackage.id).where(
            ProcurementPackage.project_item_id == project_item_id,
            ProcurementPackage.is_active == True,
            ProcurementPackage.id.in_(list(package_ids)),
        )
    )
    active_package_ids = {row[0] for row in active_packages_result.all()}
    if not active_package_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot lock package decisions: no active packages found for coverage validation "
                f"(project_item_id={project_item_id})."
            ),
        )

    coverage_result = await db.execute(
        select(
            PackageSubItem.project_item_subitem_id,
            func.coalesce(func.sum(PackageSubItem.quantity_covered), 0),
        )
        .where(PackageSubItem.package_id.in_(list(active_package_ids)))
        .group_by(PackageSubItem.project_item_subitem_id)
    )
    covered_by_subitem = {row[0]: int(row[1] or 0) for row in coverage_result.all()}

    uncovered = []
    for requirement in requirements:
        required = int(requirement.quantity or 0)
        covered = int(covered_by_subitem.get(requirement.id, 0))
        if covered < required:
            uncovered.append(
                {
                    "project_item_subitem_id": requirement.id,
                    "required": required,
                    "covered": covered,
                    "remaining": required - covered,
                }
            )

    if uncovered:
        preview = ", ".join(
            [
                f"subitem {row['project_item_subitem_id']}: {row['covered']}/{row['required']}"
                for row in uncovered[:5]
            ]
        )
        if len(uncovered) > 5:
            preview += ", ..."

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Cannot lock decisions: package coverage is incomplete for required sub-items "
                f"(project_item_id={project_item_id}; {preview})."
            ),
        )


async def get_project_item_sent_state(db: AsyncSession, project_item_id: int) -> bool:
    """
    Returns True when project item is currently sent to optimization.
    """
    from app.services.package_combination_service import is_project_item_sent_to_optimization

    return await is_project_item_sent_to_optimization(db, project_item_id)


async def get_package_finalization_status(
    db: AsyncSession, package_ids: List[int]
) -> Dict[int, bool]:
    """
    Compute package finalized state from active linked procurement options.

    Rule:
    - package is finalized iff it has at least one active option and all active options are finalized.
    """
    if not package_ids:
        return {}

    from app.services.package_combination_service import get_package_finalization_map

    return await get_package_finalization_map(db, package_ids)

