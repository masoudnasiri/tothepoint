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
from app.schemas import ProcurementOption, ProcurementOptionCreate, ProcurementOptionUpdate

router = APIRouter(prefix="/procurement", tags=["procurement"])


@router.get("/item-codes", response_model=List[str])
async def list_unique_item_codes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique item codes that are available for procurement
    
    Excludes items with LOCKED finalized decisions.
    Includes items with REVERTED decisions (can add new options).
    """
    from sqlalchemy import select
    from app.models import ProjectItem, FinalizedDecision
    
    # Get all unique item codes
    all_codes = await get_unique_item_codes(db)
    
    # Filter out items with LOCKED decisions
    available_codes = []
    
    for code in all_codes:
        # Check if item has LOCKED decisions
        locked_check = await db.execute(
            select(FinalizedDecision)
            .where(
                FinalizedDecision.item_code == code,
                FinalizedDecision.status == 'LOCKED'
            )
            .limit(1)
        )
        has_locked = locked_check.scalar_one_or_none() is not None
        
        # Only include if not locked
        if not has_locked:
            available_codes.append(code)
    
    return available_codes


@router.get("/items-with-details")
async def list_items_with_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique items with their names and descriptions
    
    Only returns items that:
    - Have NO finalized decisions, OR
    - Have only REVERTED or PROPOSED finalized decisions (not LOCKED)
    
    For items with same item_code across multiple projects:
    - Prioritizes items WITH descriptions
    - Uses most recent item if multiple have descriptions
    
    This ensures procurement users don't add options for already-locked items.
    """
    from sqlalchemy import select, distinct, and_, or_, func, case
    from sqlalchemy.orm import joinedload
    from app.models import ProjectItem, FinalizedDecision
    
    # Get all unique item codes first
    stmt = select(ProjectItem.item_code).distinct()
    result = await db.execute(stmt)
    unique_codes = [row[0] for row in result.all()]
    
    # For each unique item code, get the best item with details
    available_items = []
    
    for item_code in unique_codes:
        # Check for LOCKED decisions for this item_code
        locked_check = await db.execute(
            select(FinalizedDecision)
            .where(
                FinalizedDecision.item_code == item_code,
                FinalizedDecision.status == 'LOCKED'
            )
            .limit(1)
        )
        has_locked = locked_check.scalar_one_or_none() is not None
        
        # Skip if locked
        if has_locked:
            continue
        
        # Get all project items with this code
        items_query = await db.execute(
            select(ProjectItem)
            .where(ProjectItem.item_code == item_code)
            .order_by(
                # Priority 1: Items with description
                case((ProjectItem.description.isnot(None), 1), else_=0).desc(),
                # Priority 2: Items with name
                case((ProjectItem.item_name.isnot(None), 1), else_=0).desc(),
                # Priority 3: Most recent
                ProjectItem.created_at.desc()
            )
            .limit(1)
        )
        best_item = items_query.scalar_one_or_none()
        
        if best_item:
            available_items.append({
                "item_code": best_item.item_code,
                "item_name": best_item.item_name or "",
                "description": best_item.description or ""
            })
    
    return available_items


@router.get("/options", response_model=List[ProcurementOption])
async def list_procurement_options(
    skip: int = 0,
    limit: int = 100,
    item_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get procurement options with optional filtering by item_code"""
    options = await get_procurement_options(db, skip=skip, limit=limit, item_code=item_code)
    return options


@router.get("/options/{item_code}", response_model=List[ProcurementOption])
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
    return await create_procurement_option(db, option)


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
