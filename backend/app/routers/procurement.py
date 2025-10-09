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
    """Get list of unique item codes"""
    return await get_unique_item_codes(db)


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
