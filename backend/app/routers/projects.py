"""
Project management endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.auth import get_current_user, require_admin, require_pmo, get_user_projects
from app.crud import (
    create_project, get_projects, get_project, update_project, delete_project,
    assign_user_to_project, remove_user_from_project, get_user_project_assignments,
    get_project_summaries, log_audit
)
from app.models import User, ProcurementPackage, ProjectItem
from app.schemas import (
    Project, ProjectCreate, ProjectUpdate, ProjectAssignmentCreate,
    ProjectAssignment, ProjectSummary, ProcurementPackageResponse
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectSummary])
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of projects with summaries"""
    user_projects = await get_user_projects(db, current_user)
    projects = await get_projects(db, skip=skip, limit=limit, user_projects=user_projects)
    
    # Get summaries for the projects
    summaries = await get_project_summaries(db, user_projects)
    return summaries


@router.post("/", response_model=Project)
async def create_new_project(
    project: ProjectCreate,
    request: Request,
    current_user: User = Depends(require_pmo()),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project (PMO or admin only)"""
    created = await create_project(db, project)
    # Audit
    try:
        client_host = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        await log_audit(
            db,
            user_id=current_user.id,
            action="PROJECT_CREATE",
            entity_type="project",
            entity_id=created.id,
            details={"project_code": created.project_code, "name": created.name},
            ip_address=client_host,
            user_agent=ua,
        )
    except Exception:
        pass
    return created


@router.get("/{project_id}", response_model=Project)
async def get_project_by_id(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get project by ID"""
    user_projects = await get_user_projects(db, current_user)
    
    # Check if user can access this project
    if current_user.role == "pm" and project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    project = await get_project(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    return project


@router.put("/{project_id}", response_model=Project)
async def update_project_by_id(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Update project (admin only)"""
    project = await update_project(db, project_id, project_update)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="PROJECT_UPDATE",
            entity_type="project",
            entity_id=project_id,
            details=project_update.dict(exclude_unset=True),
        )
    except Exception:
        pass
    return project


@router.delete("/{project_id}")
async def delete_project_by_id(
    project_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Delete project (admin only)"""
    success = await delete_project(db, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="PROJECT_DELETE",
            entity_type="project",
            entity_id=project_id,
        )
    except Exception:
        pass
    return {"message": "Project deleted successfully"}


@router.post("/assignments", response_model=ProjectAssignment)
async def assign_user_to_project_endpoint(
    assignment: ProjectAssignmentCreate,
    current_user: User = Depends(require_pmo()),
    db: AsyncSession = Depends(get_db)
):
    """Assign user to project (PMO or admin only)"""
    return await assign_user_to_project(db, assignment.user_id, assignment.project_id)


@router.delete("/assignments/{user_id}/{project_id}")
async def remove_user_from_project_endpoint(
    user_id: int,
    project_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Remove user from project (admin only)"""
    success = await remove_user_from_project(db, user_id, project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    return {"message": "User removed from project successfully"}


@router.get("/assignments/{user_id}", response_model=List[ProjectAssignment])
async def get_user_project_assignments_endpoint(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: AsyncSession = Depends(get_db)
):
    """Get user's project assignments (admin only)"""
    return await get_user_project_assignments(db, user_id)


@router.get("/{project_id}/assignments", response_model=List[ProjectAssignment])
async def get_project_assignments_endpoint(
    project_id: int,
    current_user: User = Depends(require_pmo()),
    db: AsyncSession = Depends(get_db)
):
    """Get all users assigned to a specific project (PMO or admin only)"""
    from sqlalchemy import select
    from app.models import ProjectAssignment
    result = await db.execute(
        select(ProjectAssignment)
        .where(ProjectAssignment.project_id == project_id)
        .order_by(ProjectAssignment.assigned_at)
    )
    return result.scalars().all()


@router.get("/{project_id}/packages", response_model=List[ProcurementPackageResponse])
async def list_packages_by_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True, description="Filter to active packages only")
):
    """
    List all procurement packages for a project.
    """
    # Verify project exists and user has access
    user_projects = await get_user_projects(db, current_user)
    if current_user.role == "pm" and project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    query = select(ProcurementPackage).options(
        selectinload(ProcurementPackage.supplier),
        selectinload(ProcurementPackage.subitems),
    ).join(ProjectItem).where(
        ProjectItem.project_id == project_id
    )
    
    if active_only:
        query = query.where(ProcurementPackage.is_active == True)
    
    query = query.order_by(
        ProcurementPackage.package_type,
        ProcurementPackage.id
    )
    
    result = await db.execute(query)
    packages = result.scalars().all()
    
    return packages


@router.get("/{project_id}/coverage-summary")
async def get_project_coverage_summary(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get coverage summary for all items in a project.
    """
    # Verify project exists and user has access
    user_projects = await get_user_projects(db, current_user)
    if current_user.role == "pm" and project_id not in user_projects:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    # Import helper function from package service
    from app.services.package_service import calculate_coverage_summary
    
    # Get all project items
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.project_id == project_id)
    )
    project_items = result.scalars().all()
    
    coverage_summaries = []
    for item in project_items:
        # Get coverage for this item
        try:
            coverage_result = await calculate_coverage_summary(db, item.id)
            coverage_summaries.append(coverage_result)
        except Exception as e:
            # Skip items with errors
            continue
    
    return {
        "project_id": project_id,
        "items": coverage_summaries,
        "total_items": len(project_items),
        "fully_covered_items": sum(1 for c in coverage_summaries if c.get("is_fully_covered", False))
    }
