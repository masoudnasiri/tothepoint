"""
Project items management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user, require_pm, get_user_projects
from app.crud import (
    create_project_item, get_project_item, get_project_items,
    update_project_item, delete_project_item
)
from app.models import User
from app.schemas import ProjectItem, ProjectItemCreate, ProjectItemUpdate

router = APIRouter(prefix="/items", tags=["project-items"])


@router.get("/project/{project_id}", response_model=List[ProjectItem])
async def list_project_items(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project items for a specific project"""
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    items = await get_project_items(db, project_id, skip=skip, limit=limit)
    return items


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
    """Update project item (PM only)"""
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
    
    updated_item = await update_project_item(db, item_id, item_update)
    return updated_item


@router.delete("/{item_id}")
async def delete_project_item_by_id(
    item_id: int,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Delete project item (PM only)"""
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
    
    success = await delete_project_item(db, item_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    return {"message": "Project item deleted successfully"}
