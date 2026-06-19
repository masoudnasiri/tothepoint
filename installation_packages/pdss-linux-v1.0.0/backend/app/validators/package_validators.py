"""
Validation helpers for dual-mode package and legacy project-item operations.
Phase 3: Transition/Dual Mode Operation support.
"""

from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.config import settings
from app.models import ProcurementOption, DeliveryOption, FinalizedDecision, ProjectItem

logger = logging.getLogger(__name__)


def validate_package_or_legacy_reference(
    package_id: Optional[int] = None,
    project_item_id: Optional[int] = None,
    item_code: Optional[str] = None,
    context: str = "record"
) -> dict:
    """
    Validate that at least one reference (package_id, project_item_id, or item_code) is present.
    Returns dict with normalized reference information.
    
    Args:
        package_id: Package ID (new)
        project_item_id: Project item ID (legacy)
        item_code: Item code (legacy)
        context: Context for error messages (e.g., "procurement option")
    
    Returns:
        dict with keys: package_id, project_item_id, item_code, reference_type
        
    Raises:
        HTTPException if no valid reference provided
    """
    # Check if package_id is provided (preferred)
    # Accept package_id even if flag is off (flag only controls auto-resolution)
    if package_id is not None:
        if not settings.enable_package_procurement:
            logger.warning(f"package_id provided but ENABLE_PACKAGE_PROCUREMENT is disabled")
        return {
            "package_id": package_id,
            "project_item_id": project_item_id,  # Preserve if also provided
            "item_code": item_code,  # Preserve if also provided
            "reference_type": "package"
        }
    
    # Check legacy references
    if project_item_id is not None:
        if settings.legacy_project_item_fallback:
            return {
                "package_id": None,
                "project_item_id": project_item_id,
                "item_code": item_code,
                "reference_type": "project_item"
            }
    
    if item_code is not None:
        if settings.legacy_project_item_fallback:
            return {
                "package_id": None,
                "project_item_id": None,
                "item_code": item_code,
                "reference_type": "item_code"
            }
    
    # No valid reference found
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{context} must have at least one of: package_id, project_item_id, or item_code"
    )


async def validate_supplier_reference(
    db: AsyncSession,
    supplier_id: Optional[int] = None,
    supplier_name: Optional[str] = None,
    context: str = "record"
) -> dict:
    """
    Validate supplier reference, enforcing supplier_id when flag is enabled.
    
    Args:
        db: Database session
        supplier_id: Supplier ID (preferred)
        supplier_name: Supplier name (legacy)
        context: Context for error messages
    
    Returns:
        dict with supplier_id and supplier_name
    
    Raises:
        HTTPException if supplier validation fails
    """
    # If supplier_normalization_enforced is True, require supplier_id for new records
    if settings.supplier_normalization_enforced:
        if supplier_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{context} must have supplier_id when SUPPLIER_NORMALIZATION_ENFORCED is enabled"
            )
        
        # Verify supplier exists
        from app.models import Supplier
        result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
        supplier = result.scalar_one_or_none()
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {supplier_id} not found"
            )
        
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.company_name if supplier else None
        }
    
    # Legacy mode: allow supplier_name
    if supplier_id is not None:
        from app.models import Supplier
        result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
        supplier = result.scalar_one_or_none()
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.company_name if supplier else supplier_name
        }
    
    if supplier_name:
        return {
            "supplier_id": None,
            "supplier_name": supplier_name
        }
    
    # No supplier reference provided
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"{context} must have either supplier_id or supplier_name"
    )


async def resolve_package_from_project_item(
    db: AsyncSession,
    project_item_id: int,
    create_if_missing: bool = False
) -> Optional[int]:
    """
    Resolve package_id from project_item_id.
    If package_id is enabled and create_if_missing is True, creates FULL package if missing.
    
    Args:
        db: Database session
        project_item_id: Project item ID
        create_if_missing: If True and no FULL package exists, create one
    
    Returns:
        package_id if found/created, None otherwise
    """
    if not settings.enable_package_procurement:
        return None
    
    # Check if procurement_packages table exists (Phase 1 migration)
    from sqlalchemy import inspect
    from app.models import Base
    
    # Try to query for existing package
    try:
        from sqlalchemy import text
        result = await db.execute(
            text("""
                SELECT id FROM procurement_packages 
                WHERE project_item_id = :project_item_id 
                AND package_type = 'FULL' 
                LIMIT 1
            """),
            {"project_item_id": project_item_id}
        )
        row = result.fetchone()
        if row:
            return row[0]
        
        # Create if missing and flag is set
        if create_if_missing:
            # Create FULL package
            # Use SQLite-compatible syntax for test database
            try:
                dialect = db.bind.dialect.name if hasattr(db, 'bind') and db.bind else None
            except:
                dialect = None
            
            if dialect == 'sqlite':
                # SQLite doesn't support RETURNING, use lastrowid instead
                result = await db.execute(
                    text("""
                        INSERT INTO procurement_packages 
                        (project_item_id, package_name, package_type, is_active, created_at)
                        SELECT 
                            :project_item_id,
                            COALESCE(pi.item_code, 'ITEM-' || CAST(pi.id AS TEXT)) || ' - Full Package',
                            'FULL',
                            1,
                            CURRENT_TIMESTAMP
                        FROM project_items pi
                        WHERE pi.id = :project_item_id
                    """),
                    {"project_item_id": project_item_id}
                )
                await db.commit()
                # Get the last inserted ID
                result = await db.execute(
                    text("SELECT id FROM procurement_packages WHERE project_item_id = :project_item_id AND package_type = 'FULL' ORDER BY id DESC LIMIT 1"),
                    {"project_item_id": project_item_id}
                )
                row = result.fetchone()
                if row:
                    package_id = row[0]
                    logger.info(f"Created FULL package {package_id} for project_item_id {project_item_id}")
                    return package_id
            else:
                # PostgreSQL with RETURNING
                result = await db.execute(
                    text("""
                        INSERT INTO procurement_packages 
                        (project_item_id, package_name, package_type, is_active, created_at)
                        SELECT 
                            :project_item_id,
                            COALESCE(pi.item_code, 'ITEM-' || pi.id::text) || ' - Full Package',
                            'FULL',
                            TRUE,
                            NOW()
                        FROM project_items pi
                        WHERE pi.id = :project_item_id
                        RETURNING id
                    """),
                    {"project_item_id": project_item_id}
                )
                row = result.fetchone()
                if row:
                    await db.commit()
                    logger.info(f"Created FULL package {row[0]} for project_item_id {project_item_id}")
                    return row[0]
    except Exception as e:
        logger.warning(f"Could not resolve package from project_item_id {project_item_id}: {e}")
        return None
    
    return None


def log_feature_flag_usage(
    flag_name: str,
    value: bool,
    context: str = "",
    user_id: Optional[int] = None
):
    """
    Log feature flag evaluation for telemetry/auditing.
    
    Args:
        flag_name: Name of the feature flag
        value: Flag value (True/False)
        context: Additional context (e.g., endpoint name)
        user_id: User ID if available
    """
    logger.info(
        f"Feature flag evaluation: {flag_name}={value} "
        f"(context={context}, user_id={user_id})"
    )

