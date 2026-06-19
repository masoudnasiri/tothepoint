"""
Procurement Packages API endpoints
Phase 3: Package-based procurement management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.database import get_db
from app.auth import get_current_user
from app.models import User, ProcurementPackage, ProjectItem, PackageSubItem
from app.schemas import (
    ProcurementPackageResponse,
    ProcurementPackageCreate,
    ProcurementPackageUpdate,
    PackageSubItemResponse,
    PackageSubItemCreate,
    PackageSubItemUpdate
)
from app.services.package_service import (
    validate_main_item_quantity,
    validate_and_compute_subitem_coverage
)

router = APIRouter(prefix="/packages", tags=["packages"])


@router.post("/", response_model=ProcurementPackageResponse, status_code=status.HTTP_201_CREATED)
async def create_package(
    package_data: ProcurementPackageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new procurement package.
    """
    # Verify project item exists
    result = await db.execute(
        select(ProjectItem).where(ProjectItem.id == package_data.project_item_id)
    )
    project_item = result.scalar_one_or_none()
    if not project_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found"
        )
    
    # Check for duplicate package name for this project item
    if package_data.package_name:
        result = await db.execute(
            select(ProcurementPackage).where(
                ProcurementPackage.project_item_id == package_data.project_item_id,
                ProcurementPackage.package_name == package_data.package_name,
                ProcurementPackage.is_active == True
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A package with the name '{package_data.package_name}' already exists for this project item. Please choose a different name."
            )
    
    # Validate package quantity boundaries for main item
    await validate_main_item_quantity(
        db,
        project_item_id=package_data.project_item_id,
        main_item_quantity=package_data.main_item_quantity
    )

    # Create package
    try:
        package = ProcurementPackage(
            **package_data.model_dump(),
            created_by_id=current_user.id
        )
        db.add(package)
        await db.commit()
        await db.refresh(package)
        
        # Re-query with supplier and subitems relationships loaded for response serialization
        result = await db.execute(
            select(ProcurementPackage)
            .options(
                selectinload(ProcurementPackage.supplier),
                selectinload(ProcurementPackage.subitems)  # Load subitems for serialization
            )
            .where(ProcurementPackage.id == package.id)
        )
        package = result.scalar_one()
        
        return package
    except Exception as e:
        await db.rollback()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating package: {str(e)}", exc_info=True)
        
        # Check for unique constraint violation
        error_str = str(e)
        if "unique constraint" in error_str.lower() or "duplicate key" in error_str.lower():
            if "package_name" in error_str:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"A package with the name '{package_data.package_name}' already exists for this project item. Please choose a different name."
                )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create package: {str(e)}"
        )


@router.put("/{package_id}", response_model=ProcurementPackageResponse)
async def update_package(
    package_id: int,
    package_data: ProcurementPackageUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a procurement package.
    """
    result = await db.execute(
        select(ProcurementPackage).where(ProcurementPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement package not found"
        )

    # Validate duplicate name when package_name is changed
    update_data = package_data.model_dump(exclude_unset=True)
    new_package_name = update_data.get("package_name")
    if new_package_name and new_package_name != package.package_name:
        result = await db.execute(
            select(ProcurementPackage).where(
                ProcurementPackage.project_item_id == package.project_item_id,
                ProcurementPackage.package_name == new_package_name,
                ProcurementPackage.is_active == True,
                ProcurementPackage.id != package_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A package with the name '{new_package_name}' already exists for this project item. Please choose a different name."
            )

    # Validate main-item quantity if provided
    if "main_item_quantity" in update_data:
        await validate_main_item_quantity(
            db,
            project_item_id=package.project_item_id,
            main_item_quantity=update_data.get("main_item_quantity")
        )

    # Update fields
    for field, value in update_data.items():
        setattr(package, field, value)
    
    await db.commit()
    await db.refresh(package)
    
    # Re-query with supplier and subitems relationships loaded for response serialization
    result = await db.execute(
        select(ProcurementPackage)
        .options(
            selectinload(ProcurementPackage.supplier),
            selectinload(ProcurementPackage.subitems)  # Load subitems for serialization
        )
        .where(ProcurementPackage.id == package.id)
    )
    package = result.scalar_one()
    
    return package


@router.delete("/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package(
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a procurement package (soft delete by setting is_active=False).
    """
    result = await db.execute(
        select(ProcurementPackage).where(ProcurementPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement package not found"
        )
    
    # Soft delete
    package.is_active = False
    await db.commit()
    
    return None


@router.get("/by-project-item/{project_item_id}", response_model=List[ProcurementPackageResponse])
async def list_packages_by_project_item(
    project_item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True, description="Filter to active packages only")
):
    """
    List all procurement packages for a specific project item.
    Returns packages ordered by type (FULL first, then PARTIAL, then CUSTOM).
    Includes supplier relationship for efficient data loading.
    """
    try:
        query = select(ProcurementPackage).options(
            selectinload(ProcurementPackage.supplier),
            selectinload(ProcurementPackage.subitems)  # Load subitems for serialization
        ).where(
            ProcurementPackage.project_item_id == project_item_id
        )
        
        if active_only:
            query = query.where(ProcurementPackage.is_active == True)
        
        query = query.order_by(
            ProcurementPackage.package_type,  # FULL < PARTIAL < CUSTOM
            ProcurementPackage.id
        )
        
        result = await db.execute(query)
        packages = result.scalars().all()
        
        # Relationships should already be loaded via selectinload
        # But ensure they're accessible for serialization
        # Note: subitems will be an empty list if none exist, which is fine
        
        return packages
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching packages for project_item_id {project_item_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching packages: {str(e)}"
        )


@router.get("/{package_id}", response_model=ProcurementPackageResponse)
async def get_package(
    package_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific procurement package by ID.
    """
    result = await db.execute(
        select(ProcurementPackage)
        .options(
            selectinload(ProcurementPackage.project_item),
            selectinload(ProcurementPackage.supplier),
            selectinload(ProcurementPackage.subitems)  # Load subitems for count
        )
        .where(ProcurementPackage.id == package_id)
    )
    package = result.scalar_one_or_none()
    
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement package not found"
        )
    
    return package


# Package SubItems endpoints
@router.post("/subitems/", response_model=PackageSubItemResponse, status_code=status.HTTP_201_CREATED)
async def create_package_subitem(
    subitem_data: PackageSubItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new package sub-item mapping.
    """
    # Check for duplicate
    result = await db.execute(
        select(PackageSubItem).where(
            PackageSubItem.package_id == subitem_data.package_id,
            PackageSubItem.project_item_subitem_id == subitem_data.project_item_subitem_id
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Package sub-item mapping already exists"
        )

    coverage_info = await validate_and_compute_subitem_coverage(
        db,
        package_id=subitem_data.package_id,
        project_item_subitem_id=subitem_data.project_item_subitem_id,
        quantity_covered=subitem_data.quantity_covered
    )

    # Create subitem
    payload = subitem_data.model_dump()
    payload["is_fully_covered"] = coverage_info["is_fully_covered"]
    payload["coverage_percentage"] = coverage_info["coverage_percentage"]

    subitem = PackageSubItem(**payload)
    db.add(subitem)
    await db.commit()
    await db.refresh(subitem)
    
    return subitem


@router.put("/subitems/{subitem_id}", response_model=PackageSubItemResponse)
async def update_package_subitem(
    subitem_id: int,
    subitem_data: PackageSubItemUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a package sub-item mapping.
    """
    result = await db.execute(
        select(PackageSubItem).where(PackageSubItem.id == subitem_id)
    )
    subitem = result.scalar_one_or_none()
    
    if not subitem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package sub-item not found"
        )

    # Update fields
    update_data = subitem_data.model_dump(exclude_unset=True)
    next_quantity = update_data.get("quantity_covered", subitem.quantity_covered)
    next_package_id = update_data.get("package_id", subitem.package_id)
    next_project_item_subitem_id = update_data.get("project_item_subitem_id", subitem.project_item_subitem_id)

    coverage_info = await validate_and_compute_subitem_coverage(
        db,
        package_id=next_package_id,
        project_item_subitem_id=next_project_item_subitem_id,
        quantity_covered=next_quantity,
        exclude_package_subitem_id=subitem.id
    )
    update_data["is_fully_covered"] = coverage_info["is_fully_covered"]
    update_data["coverage_percentage"] = coverage_info["coverage_percentage"]

    for field, value in update_data.items():
        setattr(subitem, field, value)
    
    await db.commit()
    await db.refresh(subitem)
    
    return subitem


@router.delete("/subitems/{subitem_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_package_subitem(
    subitem_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a package sub-item mapping.
    """
    result = await db.execute(
        select(PackageSubItem).where(PackageSubItem.id == subitem_id)
    )
    subitem = result.scalar_one_or_none()
    
    if not subitem:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package sub-item not found"
        )
    
    await db.delete(subitem)
    await db.commit()
    
    return None


# Coverage summary endpoints
@router.get("/coverage/{project_item_id}")
async def get_coverage_summary(
    project_item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get coverage summary for a project item showing how much is covered by packages.
    """
    from app.services.package_service import calculate_coverage_summary
    return await calculate_coverage_summary(db, project_item_id)

