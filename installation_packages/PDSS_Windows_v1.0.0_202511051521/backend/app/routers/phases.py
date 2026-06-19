"""
Project phases management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth import get_current_user, require_pm, get_user_projects
from app.crud import (
    create_project_phase, get_project_phase, get_project_phases,
    update_project_phase, delete_project_phase, get_project
)
from app.models import User
from app.schemas import ProjectPhase, ProjectPhaseCreate, ProjectPhaseUpdate

router = APIRouter(prefix="/phases", tags=["project-phases"])


@router.get("/project/{project_id}", response_model=List[ProjectPhase])
async def list_project_phases(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all phases for a specific project"""
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # Verify project exists
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    phases = await get_project_phases(db, project_id)
    return phases


@router.post("/project/{project_id}", response_model=ProjectPhase)
async def create_new_project_phase(
    project_id: int,
    phase: ProjectPhaseCreate,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project phase (PM and admin only)"""
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # Verify project exists
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Override project_id from URL
    phase.project_id = project_id
    
    return await create_project_phase(db, phase)


@router.get("/{phase_id}", response_model=ProjectPhase)
async def get_phase_by_id(
    phase_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project phase by ID"""
    phase = await get_project_phase(db, phase_id)
    if not phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project phase not found"
        )
    
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and phase.project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project phase"
        )
    
    return phase


@router.put("/{phase_id}", response_model=ProjectPhase)
async def update_phase_by_id(
    phase_id: int,
    phase_update: ProjectPhaseUpdate,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Update project phase (PM and admin only)"""
    # Get existing phase to check project access
    existing_phase = await get_project_phase(db, phase_id)
    if not existing_phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project phase not found"
        )
    
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and existing_phase.project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project phase"
        )
    
    updated_phase = await update_project_phase(db, phase_id, phase_update)
    return updated_phase


@router.delete("/{phase_id}")
async def delete_phase_by_id(
    phase_id: int,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Delete project phase (PM and admin only)"""
    # Get existing phase to check project access
    existing_phase = await get_project_phase(db, phase_id)
    if not existing_phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project phase not found"
        )
    
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and existing_phase.project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project phase"
        )
    
    success = await delete_project_phase(db, phase_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project phase not found"
        )
    return {"message": "Project phase deleted successfully"}
