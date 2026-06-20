"""
Procurement options management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth import get_current_user, require_procurement
from app.crud import (
    create_procurement_option, get_procurement_option, get_procurement_options,
    update_procurement_option, delete_procurement_option, get_unique_item_codes, log_audit
)
from app.models import User, ProcurementOption as ProcurementOptionModel, ProcurementPackage
from app.schemas import ProcurementOption, ProcurementOptionCreate, ProcurementOptionUpdate, ProcurementOptionWithSupplier, SupplierSummary
from app.services.package_service import get_project_item_sent_state

router = APIRouter(prefix="/procurement", tags=["procurement"])


async def _resolve_option_project_item_id(db: AsyncSession, option_payload: ProcurementOptionCreate) -> Optional[int]:
    if option_payload.project_item_id is not None:
        return option_payload.project_item_id
    if option_payload.package_id is not None:
        result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == option_payload.package_id
            )
        )
        return result.scalar_one_or_none()
    return None


@router.get("/item-codes", response_model=List[str])
async def list_unique_item_codes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique item codes that are available for procurement
    
    Excludes items with LOCKED or PROPOSED finalized decisions.
    Includes items with REVERTED decisions (can add new options).
    """
    from sqlalchemy import select
    from app.models import ProjectItem, FinalizedDecision
    
    # Get all unique item codes
    all_codes = await get_unique_item_codes(db)
    
    # Filter out items with LOCKED or PROPOSED decisions
    available_codes = []
    
    for code in all_codes:
        # Check if item has LOCKED or PROPOSED decisions
        finalized_check = await db.execute(
            select(FinalizedDecision)
            .where(
                FinalizedDecision.item_code == code,
                FinalizedDecision.status.in_(['LOCKED', 'PROPOSED'])
            )
            .limit(1)
        )
        has_finalized = finalized_check.scalar_one_or_none() is not None
        
        # Only include if not finalized (LOCKED or PROPOSED)
        if not has_finalized:
            available_codes.append(code)
    
    return available_codes


@router.get("/items-with-details")
async def list_items_with_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique items with their names and descriptions (OPTIMIZED!)
    
    Returns items that are available for procurement:
    - Items from projects where the specific project_item has NO LOCKED or PROPOSED decision
    - Uses a single optimized SQL query instead of N+1 queries
    """
    from sqlalchemy import select, distinct, and_, or_, func, case, text
    from app.models import ProjectItem, FinalizedDecision
    
    # OPTIMIZED: Single SQL query using LEFT JOIN and aggregation
    # Excludes items with LOCKED or PROPOSED finalized decisions
    query = text("""
        SELECT DISTINCT ON (pi.item_code)
            pi.item_code,
            pi.item_name,
            pi.description,
            pi.project_id,
            pi.id as project_item_id
        FROM project_items pi
        LEFT JOIN finalized_decisions fd ON pi.id = fd.project_item_id AND fd.status IN ('LOCKED', 'PROPOSED')
        WHERE fd.id IS NULL  -- Only items without LOCKED or PROPOSED decisions
          AND pi.is_finalized = true  -- Only finalized project items
        ORDER BY pi.item_code, 
                 CASE WHEN pi.description IS NOT NULL AND pi.description != '' THEN 1 ELSE 2 END,
                 pi.created_at DESC
    """)
    
    result = await db.execute(query)
    rows = result.fetchall()
    
    # Convert to list of dicts
    available_items = []
    for row in rows:
        available_items.append({
            "item_code": row.item_code,
            "item_name": row.item_name or "",
            "description": row.description or "",
            "project_id": row.project_id,
            "project_item_id": row.project_item_id
        })
    
    return available_items


@router.get("/suppliers", response_model=List[SupplierSummary])
async def list_suppliers_for_procurement(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of active suppliers for procurement option creation"""
    import logging
    
    try:
        # --- START of original code ---
        from sqlalchemy import select
        from app.models import Supplier, SupplierStatus
        
        logging.info(f"DEBUG: About to query suppliers with SupplierStatus.ACTIVE = {SupplierStatus.ACTIVE}")
        logging.info(f"DEBUG: SupplierStatus enum values: {[e.value for e in SupplierStatus]}")
        
        result = await db.execute(
            select(Supplier)
            .where(Supplier.status == SupplierStatus.ACTIVE.value)
            .order_by(Supplier.company_name)
        )
        suppliers = result.scalars().all()
        logging.info(f"DEBUG: Successfully retrieved {len(suppliers)} suppliers")
        return suppliers
        # --- END of original code ---

    except Exception as e:
        # Log the full error traceback to the console
        logging.error(f"CRASH in GET /procurement/suppliers: {e}", exc_info=True)
        
        # Re-raise the error as a standard HTTP 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while fetching suppliers: {str(e)}"
        )


@router.get("/options", response_model=List[ProcurementOptionWithSupplier])
async def list_procurement_options(
    skip: int = 0,
    limit: int = 50000,  # Increased default limit to handle large datasets
    item_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get procurement options with optional filtering by item_code"""
    options = await get_procurement_options(db, skip=skip, limit=limit, item_code=item_code)
    return options


@router.get("/options/{item_code}", response_model=List[ProcurementOptionWithSupplier])
async def list_procurement_options_by_item_code(
    item_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all procurement options for a specific item code"""
    options = await get_procurement_options(db, item_code=item_code)
    return options


@router.post("/options", response_model=ProcurementOption)
async def create_new_procurement_option(
    option: ProcurementOptionCreate,
    current_user: User = Depends(require_procurement()),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Create a new procurement option with Phase 3 dual-mode support (procurement specialist only)"""
    import logging
    from app.config import settings
    from app.services.package_service import get_package_for_project_item
    from app.services.audit_service import log_feature_flag_event
    
    logger = logging.getLogger(__name__)
    
    try:
        project_item_id = await _resolve_option_project_item_id(db, option)
        if project_item_id is not None and await get_project_item_sent_state(db, project_item_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Item has been sent to optimization. "
                    "Rollback is required before changing procurement options."
                ),
            )

        # Phase 3: Log feature flag usage
        await log_feature_flag_event(
            db, "ENABLE_PACKAGE_PROCUREMENT", settings.enable_package_procurement,
            context="create_procurement_option", user_id=current_user.id
        )
        
        logger.info(f"Creating new procurement option (package_mode={settings.enable_package_procurement})")
        
        result = await create_procurement_option(db, option)
        
        # Phase 3: Enrich response with package context if available
        if result.package_id:
            package_info = await get_package_for_project_item(
                db, result.project_item_id if result.project_item_id else None
            )
            if package_info:
                result.package_name = package_info.get('package_name')
                result.package_type = package_info.get('package_type')
        
        # Audit
        try:
            client_host = request.client.host if request and request.client else None
            ua = request.headers.get("user-agent") if request else None
            await log_audit(
                db,
                user_id=current_user.id,
                action="PROCUREMENT_OPTION_CREATE",
                entity_type="procurement_option",
                entity_id=result.id,
                details={
                    "item_code": result.item_code,
                    "supplier_name": result.supplier_name,
                    "package_id": result.package_id,
                    "project_item_id": result.project_item_id
                },
                ip_address=client_host,
                user_agent=ua,
            )
        except Exception:
            pass
        
        logger.info(f"Successfully created procurement option with ID: {result.id}")
        return result
        
    except ValueError as e:
        logger.warning(f"Validation error creating procurement option: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to create procurement option: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create procurement option: {str(e)}"
        )


@router.get("/option/{option_id}", response_model=ProcurementOption)
async def get_procurement_option_by_id(
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get procurement option by ID"""
    option = await get_procurement_option(db, option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )
    return option


@router.get("/options/by-project-item/{project_item_id}", response_model=List[ProcurementOptionWithSupplier])
async def list_procurement_options_by_project_item(
    project_item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch procurement options for a project item with package/legacy compatibility."""
    from sqlalchemy import select, and_, or_
    from sqlalchemy.orm import selectinload
    from app.models import ProcurementOption, DeliveryOption, Supplier

    try:
        delivery_option_ids_subquery = (
            select(DeliveryOption.id)
            .where(DeliveryOption.project_item_id == project_item_id)
        )

        # Prefer direct project_item_id filtering, with a legacy fallback through delivery_option_id.
        result = await db.execute(
            select(ProcurementOption)
            .where(ProcurementOption.is_active == True)
            .where(
                or_(
                    ProcurementOption.project_item_id == project_item_id,
                    and_(
                        ProcurementOption.project_item_id.is_(None),
                        ProcurementOption.delivery_option_id.in_(delivery_option_ids_subquery)
                    )
                )
            )
            .options(selectinload(ProcurementOption.supplier))
            .order_by(ProcurementOption.created_at.desc())
        )
        options = result.scalars().all()
        return options if options is not None else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch procurement options: {str(e)}"
        )


@router.put("/option/{option_id}", response_model=ProcurementOption)
async def update_procurement_option_by_id(
    option_id: int,
    option_update: ProcurementOptionUpdate,
    current_user: User = Depends(require_procurement()),
    db: AsyncSession = Depends(get_db)
):
    """Update procurement option (procurement specialist only)"""
    existing = await db.execute(
        select(ProcurementOptionModel).where(ProcurementOptionModel.id == option_id)
    )
    existing_option = existing.scalar_one_or_none()
    if not existing_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )

    project_item_id = existing_option.project_item_id
    if project_item_id is None and existing_option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == existing_option.package_id
            )
        )
        project_item_id = package_result.scalar_one_or_none()

    if project_item_id is not None and await get_project_item_sent_state(db, project_item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Item has been sent to optimization. "
                "Rollback is required before changing procurement options."
            ),
        )

    option = await update_procurement_option(db, option_id, option_update)
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement option not found")
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="PROCUREMENT_OPTION_UPDATE",
            entity_type="procurement_option",
            entity_id=option_id,
            details=option_update.dict(exclude_unset=True),
        )
    except Exception:
        pass
    return option


@router.delete("/option/{option_id}")
async def delete_procurement_option_by_id(
    option_id: int,
    current_user: User = Depends(require_procurement()),
    db: AsyncSession = Depends(get_db)
):
    """Delete procurement option (procurement specialist only)"""
    existing = await db.execute(
        select(ProcurementOptionModel).where(ProcurementOptionModel.id == option_id)
    )
    existing_option = existing.scalar_one_or_none()
    if not existing_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )

    project_item_id = existing_option.project_item_id
    if project_item_id is None and existing_option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == existing_option.package_id
            )
        )
        project_item_id = package_result.scalar_one_or_none()

    if project_item_id is not None and await get_project_item_sent_state(db, project_item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Item has been sent to optimization. "
                "Rollback is required before changing procurement options."
            ),
        )

    success = await delete_procurement_option(db, option_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="PROCUREMENT_OPTION_DELETE",
            entity_type="procurement_option",
            entity_id=option_id,
        )
    except Exception:
        pass
    return {"message": "Procurement option deleted successfully"}
