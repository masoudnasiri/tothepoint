"""
Delivery options management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete as sql_delete
from app.database import get_db
from app.crud import log_audit
from app.auth import get_current_user
from app.models import User, DeliveryOption, ProjectItem
from app.schemas import (
    DeliveryOption as DeliveryOptionSchema,
    DeliveryOptionCreate,
    DeliveryOptionUpdate
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/delivery-options", tags=["delivery-options"])


@router.get("/item/{project_item_id}", response_model=List[DeliveryOptionSchema])
async def get_delivery_options_by_project_item(
    project_item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all delivery options for a specific project item"""
    result = await db.execute(
        select(DeliveryOption)
        .where(DeliveryOption.project_item_id == project_item_id)
        .where(DeliveryOption.is_active == True)
        .order_by(DeliveryOption.delivery_date)
    )
    delivery_options = result.scalars().all()
    
    # ✅ Auto-assign slots based on date order
    for index, option in enumerate(delivery_options, start=1):
        if option.delivery_slot != index:
            option.delivery_slot = index
    
    await db.commit()
    
    return delivery_options


@router.get("/by-item-code/{item_code}", response_model=List[DeliveryOptionSchema])
async def get_delivery_options_by_item_code(
    item_code: str,
    project_id: Optional[int] = Query(None, description="Filter by specific project"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get delivery options for a specific item code.
    If project_id is provided, returns options only for that project.
    Otherwise, returns options across all projects (legacy behavior).
    """
    # Build query for project items
    project_items_query = select(ProjectItem).where(ProjectItem.item_code == item_code)
    
    # Filter by project if specified
    if project_id:
        project_items_query = project_items_query.where(ProjectItem.project_id == project_id)
    
    result = await db.execute(project_items_query)
    project_items = result.scalars().all()
    
    if not project_items:
        return []
    
    # Get all delivery options for these project items
    project_item_ids = [item.id for item in project_items]
    result = await db.execute(
        select(DeliveryOption)
        .where(DeliveryOption.project_item_id.in_(project_item_ids))
        .where(DeliveryOption.is_active == True)
        .order_by(DeliveryOption.delivery_date)
    )
    delivery_options = result.scalars().all()
    
    return delivery_options


@router.get("/{option_id}", response_model=DeliveryOptionSchema)
async def get_delivery_option(
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific delivery option by ID"""
    result = await db.execute(
        select(DeliveryOption).where(DeliveryOption.id == option_id)
    )
    option = result.scalar_one_or_none()
    
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery option not found"
        )
    
    return option


@router.post("/", response_model=DeliveryOptionSchema)
async def create_delivery_option(
    option_data: DeliveryOptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new delivery option"""
    # ✅ Auto-calculate slot based on existing options for this item
    existing_result = await db.execute(
        select(DeliveryOption)
        .where(DeliveryOption.project_item_id == option_data.project_item_id)
        .where(DeliveryOption.is_active == True)
        .order_by(DeliveryOption.delivery_date)
    )
    existing_options = existing_result.scalars().all()
    
    # Calculate slot: count existing + 1, or use provided slot
    if option_data.delivery_slot is None:
        calculated_slot = len(existing_options) + 1
    else:
        calculated_slot = option_data.delivery_slot
    
    # Create option with data
    option_dict = option_data.dict()
    option_dict['delivery_slot'] = calculated_slot
    
    new_option = DeliveryOption(**option_dict)
    db.add(new_option)
    await db.commit()
    await db.refresh(new_option)
    
    logger.info(f"Created delivery option for item {option_data.project_item_id}, slot {calculated_slot}")
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="DELIVERY_OPTION_CREATE",
            entity_type="delivery_option",
            entity_id=new_option.id,
            details=option_dict,
        )
    except Exception:
        pass
    
    return new_option


@router.put("/{option_id}", response_model=DeliveryOptionSchema)
async def update_delivery_option(
    option_id: int,
    option_update: DeliveryOptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a delivery option"""
    # Check if exists
    result = await db.execute(
        select(DeliveryOption).where(DeliveryOption.id == option_id)
    )
    existing_option = result.scalar_one_or_none()
    
    if not existing_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery option not found"
        )
    
    # Update fields
    update_data = option_update.dict(exclude_unset=True)
    
    if update_data:
        await db.execute(
            update(DeliveryOption)
            .where(DeliveryOption.id == option_id)
            .values(**update_data)
        )
        await db.commit()
        try:
            await log_audit(
                db,
                user_id=current_user.id,
                action="DELIVERY_OPTION_UPDATE",
                entity_type="delivery_option",
                entity_id=option_id,
                details=update_data,
            )
        except Exception:
            pass
    
    # Fetch and return updated option
    result = await db.execute(
        select(DeliveryOption).where(DeliveryOption.id == option_id)
    )
    return result.scalar_one()


@router.delete("/{option_id}")
async def delete_delivery_option(
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a delivery option"""
    result = await db.execute(
        sql_delete(DeliveryOption).where(DeliveryOption.id == option_id)
    )
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery option not found"
        )
    
    await db.commit()
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="DELIVERY_OPTION_DELETE",
            entity_type="delivery_option",
            entity_id=option_id,
        )
    except Exception:
        pass
    
    return {"message": "Delivery option deleted successfully"}
