"""
Items Master Catalog Management
Centralized catalog of all items used across projects
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.exc import IntegrityError
import re
import logging

from app.database import get_db
from app.crud import log_audit
from app.auth import get_current_user, require_role
from app.models import User, ItemMaster, ItemSubItem
from app.schemas import (
    ItemMaster as ItemMasterSchema,
    ItemMasterCreate,
    ItemMasterUpdate,
    ItemSubItem as ItemSubItemSchema,
    ItemSubItemCreate,
    ItemSubItemUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/items-master", tags=["items-master"])


def generate_item_code(company: str, item_name: str, model: str = "") -> str:
    """
    Generate unique item code from company, name, and model
    
    Format: COMPANY-NAME-MODEL
    Example: ACME-STEEL-BEAM-A36
    """
    # Clean and uppercase company
    company_clean = re.sub(r'[^A-Z0-9]+', '', company.upper())
    
    # Clean name - keep hyphens for readability
    name_clean = re.sub(r'[^A-Z0-9\s]+', '', item_name.upper())
    name_clean = re.sub(r'\s+', '-', name_clean.strip())
    
    # Clean model
    model_clean = re.sub(r'[^A-Z0-9]+', '', model.upper()) if model else ""
    
    # Combine
    if model_clean:
        code = f"{company_clean}-{name_clean}-{model_clean}"
    else:
        code = f"{company_clean}-{name_clean}"
    
    # Limit length and clean up multiple hyphens
    code = re.sub(r'-+', '-', code)  # Replace multiple hyphens with single
    code = code[:100]  # Limit to 100 chars
    
    return code


@router.get("/", response_model=List[ItemMasterSchema])
async def list_items_master(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    category: Optional[str] = None,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all master items with optional filtering
    
    All authenticated users can view items master
    """
    query = select(ItemMaster)
    
    # Filter by active status
    if active_only:
        query = query.where(ItemMaster.is_active == True)
    
    # Filter by category
    if category:
        query = query.where(ItemMaster.category == category)
    
    # Search by code, company, or name
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                ItemMaster.item_code.ilike(search_term),
                ItemMaster.company.ilike(search_term),
                ItemMaster.item_name.ilike(search_term),
                ItemMaster.model.ilike(search_term)
            )
        )
    
    # Order and paginate
    query = query.order_by(ItemMaster.company, ItemMaster.item_name).offset(skip).limit(limit)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return items


@router.get("/{item_id}", response_model=ItemMasterSchema)
async def get_item_master(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific master item by ID"""
    result = await db.execute(
        select(ItemMaster).where(ItemMaster.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Master item #{item_id} not found"
        )
    
    return item


@router.post("/", response_model=ItemMasterSchema, status_code=status.HTTP_201_CREATED)
async def create_item_master(
    item_data: ItemMasterCreate,
    request: Request,
    current_user: User = Depends(require_role(["admin", "pm", "pmo", "finance"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new master item
    
    Allowed roles: admin, pm, pmo, finance
    Item code is auto-generated from company + name + model
    """
    # Generate item code
    item_code = generate_item_code(
        item_data.company,
        item_data.item_name,
        item_data.model or ""
    )
    
    # Check if code already exists
    existing = await db.execute(
        select(ItemMaster).where(ItemMaster.item_code == item_code)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item with code '{item_code}' already exists. Please use different company, name, or model combination."
        )
    
    # Create master item
    master_item = ItemMaster(
        item_code=item_code,
        company=item_data.company,
        item_name=item_data.item_name,
        model=item_data.model,
        part_number=item_data.part_number,
        specifications=item_data.specifications,
        category=item_data.category,
        unit=item_data.unit,
        created_by_id=current_user.id
    )
    
    db.add(master_item)
    
    try:
        await db.commit()
        await db.refresh(master_item)
        logger.info(f"Created master item: {item_code} by user {current_user.username}")
        # Audit
        try:
            client_host = request.client.host if request and request.client else None
            ua = request.headers.get("user-agent") if request else None
            await log_audit(
                db,
                user_id=current_user.id,
                action="ITEM_MASTER_CREATE",
                entity_type="item_master",
                entity_id=master_item.id,
                details={"item_code": master_item.item_code, "company": master_item.company, "item_name": master_item.item_name},
                ip_address=client_host,
                user_agent=ua,
            )
        except Exception:
            pass
        return master_item
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Error creating master item: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item with this code already exists or invalid data"
        )


@router.put("/{item_id}", response_model=ItemMasterSchema)
async def update_item_master(
    item_id: int,
    item_update: ItemMasterUpdate,
    request: Request,
    current_user: User = Depends(require_role(["admin", "pm", "pmo", "finance"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a master item
    
    Allowed roles: admin, pm, pmo, finance
    Item code will be regenerated if company/name/model changes
    """
    # Get existing item
    result = await db.execute(
        select(ItemMaster).where(ItemMaster.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Master item #{item_id} not found"
        )
    
    # Update fields
    update_data = item_update.dict(exclude_unset=True)
    
    # Regenerate item code if company/name/model changed
    if any(k in update_data for k in ['company', 'item_name', 'model']):
        new_company = update_data.get('company', item.company)
        new_name = update_data.get('item_name', item.item_name)
        new_model = update_data.get('model', item.model) or ""
        
        new_code = generate_item_code(new_company, new_name, new_model)
        
        # Check if new code conflicts with another item
        if new_code != item.item_code:
            existing = await db.execute(
                select(ItemMaster).where(
                    ItemMaster.item_code == new_code,
                    ItemMaster.id != item_id
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item with code '{new_code}' already exists"
                )
            update_data['item_code'] = new_code
    
    # Apply updates
    for key, value in update_data.items():
        setattr(item, key, value)
    
    try:
        await db.commit()
        await db.refresh(item)
        logger.info(f"Updated master item #{item_id}: {item.item_code}")
        # Audit
        try:
            client_host = request.client.host if request and request.client else None
            ua = request.headers.get("user-agent") if request else None
            await log_audit(
                db,
                user_id=current_user.id,
                action="ITEM_MASTER_UPDATE",
                entity_type="item_master",
                entity_id=item.id,
                details=item_update.dict(exclude_unset=True),
                ip_address=client_host,
                user_agent=ua,
            )
        except Exception:
            pass
        return item
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Error updating master item: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Update failed due to constraint violation"
        )


@router.delete("/{item_id}")
async def delete_item_master(
    item_id: int,
    request: Request,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a master item (Admin only)
    
    Cannot delete if item is referenced by project_items
    """
    from app.models import ProjectItem
    
    # Check if item exists
    result = await db.execute(
        select(ItemMaster).where(ItemMaster.id == item_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Master item #{item_id} not found"
        )
    
    # Check if item is used in any projects
    usage_check = await db.execute(
        select(func.count(ProjectItem.id))
        .where(ProjectItem.master_item_id == item_id)
    )
    usage_count = usage_check.scalar()
    
    if usage_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete item. It is used in {usage_count} project(s). Set to inactive instead."
        )
    
    # Delete item
    await db.delete(item)
    await db.commit()
    
    logger.info(f"Deleted master item #{item_id}: {item.item_code}")
    # Audit
    try:
        client_host = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        await log_audit(
            db,
            user_id=current_user.id,
            action="ITEM_MASTER_DELETE",
            entity_type="item_master",
            entity_id=item_id,
            details={"item_code": item.item_code},
            ip_address=client_host,
            user_agent=ua,
        )
    except Exception:
        pass
    
    return {"message": "Master item deleted successfully", "item_id": item_id}


@router.get("/preview/code")
async def preview_item_code(
    company: str,
    item_name: str,
    model: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Preview what item code will be generated for given inputs
    
    Useful for frontend to show live preview as user types
    """
    item_code = generate_item_code(company, item_name, model or "")
    
    # Check if code already exists
    existing = await db.execute(
        select(ItemMaster).where(ItemMaster.item_code == item_code)
    )
    exists = existing.scalar_one_or_none() is not None
    
    return {
        "item_code": item_code,
        "exists": exists,
        "available": not exists
    }


@router.get("/search/by-code/{item_code}", response_model=ItemMasterSchema)
async def get_item_by_code(
    item_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get master item by item code"""
    result = await db.execute(
        select(ItemMaster).where(ItemMaster.item_code == item_code)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with code '{item_code}' not found"
        )
    
    return item


# ----------------------
# Sub-Items CRUD (nested)
# ----------------------

@router.post("/{item_id}/subitems", response_model=ItemSubItemSchema, status_code=status.HTTP_201_CREATED)
async def create_sub_item(
    item_id: int,
    payload: ItemSubItemCreate,
    current_user: User = Depends(require_role(["admin", "pm", "pmo", "procurement"])),
    db: AsyncSession = Depends(get_db)
):
    """Create a sub-item under an items_master entry"""
    # Ensure parent exists
    result = await db.execute(select(ItemMaster).where(ItemMaster.id == item_id))
    master = result.scalar_one_or_none()
    if not master:
        raise HTTPException(status_code=404, detail="Master item not found")

    sub = ItemSubItem(
        item_master_id=item_id,
        name=payload.name,
        description=payload.description,
        part_number=payload.part_number,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.get("/{item_id}/subitems", response_model=List[ItemSubItemSchema])
async def list_sub_items(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List sub-items for a master item"""
    result = await db.execute(
        select(ItemSubItem).where(ItemSubItem.item_master_id == item_id).order_by(ItemSubItem.id)
    )
    return result.scalars().all()


@router.put("/{item_id}/subitems/{subitem_id}", response_model=ItemSubItemSchema)
async def update_sub_item(
    item_id: int,
    subitem_id: int,
    payload: ItemSubItemUpdate,
    current_user: User = Depends(require_role(["admin", "pm", "pmo", "procurement"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ItemSubItem).where(
            ItemSubItem.id == subitem_id,
            ItemSubItem.item_master_id == item_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Sub-item not found")

    update_data = payload.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(sub, k, v)
    await db.commit()
    await db.refresh(sub)
    return sub


@router.delete("/{item_id}/subitems/{subitem_id}")
async def delete_sub_item(
    item_id: int,
    subitem_id: int,
    current_user: User = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(ItemSubItem).where(
            ItemSubItem.id == subitem_id,
            ItemSubItem.item_master_id == item_id,
        )
    )
    sub = result.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Sub-item not found")
    await db.delete(sub)
    await db.commit()
    return {"message": "Sub-item deleted"}

