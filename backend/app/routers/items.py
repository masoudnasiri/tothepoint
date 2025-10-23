"""
Project items management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user, require_pm, require_pmo, require_role, get_user_projects
from app.crud import (
    create_project_item, get_project_item, get_project_items,
    update_project_item, delete_project_item, finalize_project_item
)
from app.models import User, FinalizedDecision
from app.schemas import ProjectItem, ProjectItemCreate, ProjectItemUpdate, ProjectItemFinalize

router = APIRouter(prefix="/items", tags=["project-items"])


@router.get("/project/{project_id}")
async def list_project_items(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    status: str = None,
    is_finalized: bool = None,
    external_purchase: bool = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project items for a specific project with procurement status, search, and filters"""
    from sqlalchemy import select, func, or_, and_
    from app.models import ProjectItem as ProjectItemModel, ProcurementOption, FinalizedDecision
    
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # Build query with filters
    query = select(ProjectItemModel).where(ProjectItemModel.project_id == project_id)
    
    # Apply search filter
    if search:
        search_filter = or_(
            ProjectItemModel.item_code.ilike(f"%{search}%"),
            ProjectItemModel.item_name.ilike(f"%{search}%"),
            ProjectItemModel.description.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
    
    # Apply status filter
    if status:
        query = query.where(ProjectItemModel.status == status)
    
    # Apply finalized filter
    if is_finalized is not None:
        query = query.where(ProjectItemModel.is_finalized == is_finalized)
    
    # Apply external_purchase filter
    if external_purchase is not None:
        query = query.where(ProjectItemModel.external_purchase == external_purchase)
    
    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total_count = total_result.scalar() or 0
    
    # Apply ordering and pagination
    query = query.order_by(ProjectItemModel.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    items = result.scalars().all()
    
    # Enrich with procurement status
    enriched_items = []
    for item in items:
        # Count procurement options
        proc_count_query = await db.execute(
            select(func.count(ProcurementOption.id))
            .where(ProcurementOption.item_code == item.item_code)
        )
        procurement_options_count = proc_count_query.scalar() or 0
        
        # Check if has finalized decision
        finalized_decision_query = await db.execute(
            select(func.count(FinalizedDecision.id))
            .where(FinalizedDecision.project_item_id == item.id)
        )
        has_finalized_decision = (finalized_decision_query.scalar() or 0) > 0
        
        # Convert to dict and add extra fields
        item_dict = {
            "id": item.id,
            "project_id": item.project_id,
            "master_item_id": item.master_item_id,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "delivery_options": item.delivery_options,
            "status": item.status.value if hasattr(item.status, 'value') else item.status,
            "external_purchase": item.external_purchase,
            "description": item.description,
            "file_path": item.file_path,
            "file_name": item.file_name,
            "decision_date": item.decision_date.isoformat() if item.decision_date else None,
            "procurement_date": item.procurement_date.isoformat() if item.procurement_date else None,
            "payment_date": item.payment_date.isoformat() if item.payment_date else None,
            "invoice_submission_date": item.invoice_submission_date.isoformat() if item.invoice_submission_date else None,
            "expected_cash_in_date": item.expected_cash_in_date.isoformat() if item.expected_cash_in_date else None,
            "actual_cash_in_date": item.actual_cash_in_date.isoformat() if item.actual_cash_in_date else None,
            "is_finalized": item.is_finalized,
            "finalized_by": item.finalized_by,
            "finalized_at": item.finalized_at.isoformat() if item.finalized_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            # Extra fields for UI control
            "procurement_options_count": procurement_options_count,
            "has_finalized_decision": has_finalized_decision,
        }
        enriched_items.append(item_dict)
    
    return {
        "items": enriched_items,
        "total": total_count,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=ProjectItem)
async def create_new_project_item(
    item: ProjectItemCreate,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project item (PM only)"""
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and item.project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    return await create_project_item(db, item)


@router.get("/finalized")
async def list_finalized_items(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all finalized project items (visible in procurement) - excludes items with LOCKED or PROPOSED decisions"""
    from sqlalchemy import select, and_, not_, exists
    from app.models import ProjectItem as ProjectItemModel, FinalizedDecision
    
    # Only procurement and admin users can see finalized items
    if current_user.role not in ["procurement", "admin", "pmo", "pm"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - procurement role required"
        )
    
    # Get finalized items that DON'T have LOCKED or PROPOSED decisions
    # This ensures procurement only sees items that are ready for new options
    result = await db.execute(
        select(ProjectItemModel)
        .where(
            and_(
                ProjectItemModel.is_finalized == True,
                # Exclude items with LOCKED or PROPOSED decisions
                ~exists(
                    select(FinalizedDecision.id)
                    .where(
                        FinalizedDecision.project_item_id == ProjectItemModel.id,
                        FinalizedDecision.status.in_(['LOCKED', 'PROPOSED'])
                    )
                )
            )
        )
        .offset(skip)
        .limit(limit)
        .order_by(ProjectItemModel.finalized_at.desc())
    )
    items = result.scalars().all()
    
    # Manually serialize to avoid validation issues
    serialized_items = []
    for item in items:
        serialized_items.append({
            "id": item.id,
            "project_id": item.project_id,
            "master_item_id": item.master_item_id,
            "item_code": item.item_code,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "delivery_options": item.delivery_options,
            "status": item.status.value if hasattr(item.status, 'value') else item.status,
            "external_purchase": item.external_purchase,
            "description": item.description,
            "file_path": item.file_path,
            "file_name": item.file_name,
            "decision_date": item.decision_date.isoformat() if item.decision_date else None,
            "procurement_date": item.procurement_date.isoformat() if item.procurement_date else None,
            "payment_date": item.payment_date.isoformat() if item.payment_date else None,
            "invoice_submission_date": item.invoice_submission_date.isoformat() if item.invoice_submission_date else None,
            "expected_cash_in_date": item.expected_cash_in_date.isoformat() if item.expected_cash_in_date else None,
            "actual_cash_in_date": item.actual_cash_in_date.isoformat() if item.actual_cash_in_date else None,
            "is_finalized": item.is_finalized,
            "finalized_by": item.finalized_by,
            "finalized_at": item.finalized_at.isoformat() if item.finalized_at else None,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        })
    
    return serialized_items


@router.get("/{item_id}", response_model=ProjectItem)
async def get_project_item_by_id(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project item by ID"""
    item = await get_project_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and item.project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project item"
        )
    
    return item


@router.put("/{item_id}", response_model=ProjectItem)
async def update_project_item_by_id(
    item_id: int,
    item_update: ProjectItemUpdate,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Update project item (PM only) - only if no procurement options exist"""
    from sqlalchemy import select, func
    from app.models import ProcurementOption
    
    # Get existing item to check project access
    existing_item = await get_project_item(db, item_id)
    if not existing_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and existing_item.project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project item"
        )
    
    # Check if item has finalized decision in procurement
    finalized_decision_query = await db.execute(
        select(func.count(FinalizedDecision.id))
        .where(FinalizedDecision.project_item_id == item_id)
    )
    has_finalized_decision = (finalized_decision_query.scalar() or 0) > 0
    
    if has_finalized_decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit: Procurement has finalized decision for this item. Contact procurement team to revert their decision first."
        )
    
    updated_item = await update_project_item(db, item_id, item_update)
    return updated_item


@router.delete("/{item_id}")
async def delete_project_item_by_id(
    item_id: int,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Delete project item (PM only) - only if no procurement options exist"""
    from sqlalchemy import select, func
    from app.models import ProcurementOption
    
    # Get existing item to check project access
    existing_item = await get_project_item(db, item_id)
    if not existing_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and existing_item.project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project item"
        )
    
    # Check if item has finalized decision in procurement
    finalized_decision_query = await db.execute(
        select(func.count(FinalizedDecision.id))
        .where(FinalizedDecision.project_item_id == item_id)
    )
    has_finalized_decision = (finalized_decision_query.scalar() or 0) > 0
    
    if has_finalized_decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete: Procurement has finalized decision for this item. Contact procurement team to revert their decision first."
        )
    
    success = await delete_project_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    return {"message": "Project item deleted successfully"}


@router.put("/{item_id}/finalize", response_model=ProjectItem)
async def finalize_project_item_by_id(
    item_id: int,
    finalize_data: ProjectItemFinalize,
    current_user: User = Depends(require_role(["pmo", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Finalize a project item (PMO or Admin only) - makes it visible in procurement"""
    item = await finalize_project_item(db, item_id, current_user.id, finalize_data)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    return item


@router.put("/{item_id}/unfinalize", response_model=ProjectItem)
async def unfinalize_project_item_by_id(
    item_id: int,
    current_user: User = Depends(require_role(["pmo", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Unfinalize a project item (PMO or Admin only) - only if no procurement options or decisions exist"""
    from sqlalchemy import select, func
    from app.models import ProjectItem as ProjectItemModel, FinalizedDecision, ProcurementOption
    
    # Get the item
    item = await get_project_item(db, item_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    
    # Check if item has any procurement options
    procurement_options_query = await db.execute(
        select(func.count(ProcurementOption.id))
        .where(ProcurementOption.item_code == item.item_code)
    )
    has_procurement_options = (procurement_options_query.scalar() or 0) > 0
    
    if has_procurement_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unfinalize: Item has procurement options. Contact procurement team to remove options first."
        )
    
    # Check if item has finalized decision in procurement
    finalized_decision_query = await db.execute(
        select(func.count(FinalizedDecision.id))
        .where(FinalizedDecision.project_item_id == item_id)
    )
    has_finalized_decision = (finalized_decision_query.scalar() or 0) > 0
    
    if has_finalized_decision:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot unfinalize: Item has been finalized in procurement. Contact procurement team to revert their decision first."
        )
    
    # Unfinalize the item
    from app.schemas import ProjectItemFinalize
    unfinalize_data = ProjectItemFinalize(is_finalized=False, finalized_at=None)
    
    # Update the item
    from sqlalchemy import update
    await db.execute(
        update(ProjectItemModel)
        .where(ProjectItemModel.id == item_id)
        .values(is_finalized=False, finalized_by=None, finalized_at=None)
    )
    await db.commit()
    
    # Return updated item
    return await get_project_item(db, item_id)
