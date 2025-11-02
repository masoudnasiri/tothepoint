"""
Procurement options management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user, require_procurement
from app.crud import (
    create_procurement_option, get_procurement_option, get_procurement_options,
    update_procurement_option, delete_procurement_option, get_unique_item_codes
)
from app.models import User
from app.schemas import ProcurementOption, ProcurementOptionCreate, ProcurementOptionUpdate, ProcurementOptionWithSupplier, SupplierSummary

router = APIRouter(prefix="/procurement", tags=["procurement"])


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
    db: AsyncSession = Depends(get_db)
):
    """Create a new procurement option (procurement specialist only)"""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔍 DEBUG: Creating new procurement option")
        logger.info(f"🔍 DEBUG: Option data: {option}")
        logger.info(f"🔍 DEBUG: Current user: {current_user.username} (role: {current_user.role})")
        
        result = await create_procurement_option(db, option)
        logger.info(f"🔍 DEBUG: Successfully created procurement option with ID: {result.id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to create procurement option: {str(e)}")
        logger.error(f"❌ ERROR: Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ ERROR: Traceback: {traceback.format_exc()}")
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
    """Fetches procurement options filtered by the specific project_item_id."""
    from sqlalchemy import select
    from app.models import ProcurementOption, DeliveryOption, Supplier
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"🔍 DEBUG: Starting project-specific options fetch for project_item_id: {project_item_id}")
        
        # First, get all delivery option IDs for this project item
        logger.info(f"🔍 DEBUG: Querying delivery options for project_item_id: {project_item_id}")
        delivery_options_result = await db.execute(
            select(DeliveryOption.id)
            .where(DeliveryOption.project_item_id == project_item_id)
        )
        delivery_option_ids = [row[0] for row in delivery_options_result.all()]
        logger.info(f"🔍 DEBUG: Found {len(delivery_option_ids)} delivery options: {delivery_option_ids}")
        
        if not delivery_option_ids:
            logger.info(f"🔍 DEBUG: No delivery options found for project_item_id: {project_item_id}, returning empty list")
            return []
        
        # Now get all procurement options that reference these delivery options
        # Include supplier eager loading to avoid greenlet_spawn error
        logger.info(f"🔍 DEBUG: Querying procurement options for delivery_option_ids: {delivery_option_ids}")
        from sqlalchemy.orm import selectinload
        
        result = await db.execute(
            select(ProcurementOption)
            .where(ProcurementOption.delivery_option_id.in_(delivery_option_ids))
            .where(ProcurementOption.is_active == True)
            .options(selectinload(ProcurementOption.supplier))
            .order_by(ProcurementOption.created_at.desc())
        )
        options = result.scalars().all()
        logger.info(f"🔍 DEBUG: Found {len(options)} procurement options")
        
        # Log details about each option
        for i, option in enumerate(options):
            logger.info(f"🔍 DEBUG: Option {i+1}: id={option.id}, item_code={option.item_code}, supplier_id={option.supplier_id}, delivery_option_id={option.delivery_option_id}")
        
        logger.info(f"🔍 DEBUG: Successfully returning {len(options)} options")
        return options if options is not None else []
        
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to fetch options for project_item_id {project_item_id}: {str(e)}")
        logger.error(f"❌ ERROR: Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ ERROR: Traceback: {traceback.format_exc()}")
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
    option = await update_procurement_option(db, option_id, option_update)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )
    return option


@router.delete("/option/{option_id}")
async def delete_procurement_option_by_id(
    option_id: int,
    current_user: User = Depends(require_procurement()),
    db: AsyncSession = Depends(get_db)
):
    """Delete procurement option (procurement specialist only)"""
    success = await delete_procurement_option(db, option_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )
    return {"message": "Procurement option deleted successfully"}
