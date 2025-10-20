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
    
    Returns items that are available for procurement:
    - Items from projects where the specific project_item has NO LOCKED decision
    - This allows same item_code to be available in one project but locked in another
    
    For items with same item_code across multiple projects:
    - Prioritizes items WITH descriptions
    - Uses most recent item if multiple have descriptions
    """
    from sqlalchemy import select, distinct, and_, or_, func, case
    from sqlalchemy.orm import joinedload
    from app.models import ProjectItem, FinalizedDecision
    
    # Get all project items (not just unique codes)
    stmt = select(ProjectItem)
    result = await db.execute(stmt)
    all_items = result.scalars().all()
    
    # For each project item, check if it's available for procurement
    available_items_dict = {}  # Use dict to deduplicate by item_code
    
    for item in all_items:
        # Check for LOCKED decisions for this specific project_item_id
        locked_check = await db.execute(
            select(FinalizedDecision)
            .where(
                FinalizedDecision.project_item_id == item.id,
                FinalizedDecision.status == 'LOCKED'
            )
            .limit(1)
        )
        has_locked = locked_check.scalar_one_or_none() is not None
        
        # If this project_item is not locked, it's available
        if not has_locked:
            # Add to dict (will keep best one if multiple projects have same code)
            if item.item_code not in available_items_dict:
                available_items_dict[item.item_code] = item
            else:
                # Keep the one with better data (description > name > recent)
                existing = available_items_dict[item.item_code]
                if item.description and not existing.description:
                    available_items_dict[item.item_code] = item
                elif item.item_name and not existing.item_name:
                    available_items_dict[item.item_code] = item
                elif item.created_at > existing.created_at:
                    available_items_dict[item.item_code] = item
    
    # Convert to list
    available_items = []
    for item_code, best_item in available_items_dict.items():
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
