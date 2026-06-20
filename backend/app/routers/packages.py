"""
Procurement Packages API endpoints
Phase 3: Package-based procurement management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from typing import Dict, List, Optional

from app.database import get_db
from app.auth import get_current_user
from app.crud import log_audit
from app.models import (
    PackageSubItem,
    ProcurementOption,
    ProcurementPackage,
    ProjectItem,
    User,
)
from app.schemas import (
    OptimizationSubmissionRequest,
    OptimizationSubmissionRollbackRequest,
    PackageSubItemResponse,
    PackageSubItemCreate,
    PackageSubItemUpdate,
    ProcurementPackageCreate,
    ProcurementPackageResponse,
    ProcurementPackageUpdate,
)
from app.services.package_service import (
    get_package_finalization_status,
    get_project_item_sent_state,
    validate_main_item_quantity,
    validate_and_compute_subitem_coverage,
)
from app.services.package_combination_service import (
    analyze_project_item_package_combinations,
    mark_project_item_sent_to_optimization,
    rollback_project_item_optimization_submission,
)
from app.services.optimization_rollback_service import (
    build_bulk_rollback_preview,
    execute_bulk_rollback,
)

router = APIRouter(prefix="/packages", tags=["packages"])


async def _ensure_item_editable_for_packages(db: AsyncSession, project_item_id: int) -> None:
    if await get_project_item_sent_state(db, project_item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Item has been sent to optimization. "
                "Rollback is required before package changes."
            ),
        )


def _derive_package_status(
    *, is_active: bool, is_finalized: bool, is_locked_for_optimization: bool
) -> str:
    if is_locked_for_optimization:
        return "SENT_TO_OPTIMIZATION"
    if not is_active:
        return "INACTIVE"
    if is_finalized:
        return "FINALIZED"
    return "DRAFT"


async def _enrich_packages_runtime_state(
    db: AsyncSession, packages: List[ProcurementPackage]
) -> List[ProcurementPackage]:
    if not packages:
        return packages

    package_ids = [int(p.id) for p in packages]
    finalization_map = await get_package_finalization_status(db, package_ids)

    project_item_ids = sorted({int(p.project_item_id) for p in packages})
    lock_map: Dict[int, bool] = {}
    for project_item_id in project_item_ids:
        lock_map[project_item_id] = await get_project_item_sent_state(db, project_item_id)

    for package in packages:
        is_finalized = bool(finalization_map.get(int(package.id), False))
        is_locked = bool(lock_map.get(int(package.project_item_id), False))
        setattr(package, "is_finalized", is_finalized)
        setattr(package, "is_locked_for_optimization", is_locked)
        setattr(
            package,
            "status",
            _derive_package_status(
                is_active=bool(package.is_active),
                is_finalized=is_finalized,
                is_locked_for_optimization=is_locked,
            ),
        )
    return packages


async def _resolve_target_project_item_ids(
    db: AsyncSession, request: OptimizationSubmissionRequest
) -> List[int]:
    if request.send_all_finalized:
        result = await db.execute(
            select(ProjectItem.id).where(ProjectItem.is_finalized == True)  # noqa: E712
        )
        return sorted({int(row[0]) for row in result.all()})

    ids: List[int] = []
    if request.project_item_id is not None:
        ids.append(int(request.project_item_id))
    if request.project_item_ids:
        ids.extend([int(v) for v in request.project_item_ids])
    return sorted(set(ids))


class OptimizationRollbackFilterRequest(BaseModel):
    include_full_package_items: bool = True
    include_partial_package_items: bool = True
    include_complete_coverage_items: bool = True
    include_incomplete_coverage_items: bool = True
    include_over_covered_items: bool = True
    include_domestic_suppliers: bool = True
    include_foreign_suppliers: bool = True
    include_single_supplier_items: bool = True
    include_multiple_supplier_items: bool = True
    include_warning_incomplete_submissions: bool = True
    min_total_cost_irr: Optional[float] = Field(
        None, description="Minimum IRR-equivalent procurement cost"
    )
    max_total_cost_irr: Optional[float] = Field(
        None, description="Maximum IRR-equivalent procurement cost"
    )
    date_from: Optional[str] = Field(None, description="YYYY-MM-DD")
    date_to: Optional[str] = Field(None, description="YYYY-MM-DD")
    date_field: str = Field(
        "submitted_at",
        pattern="^(submitted_at|delivery_date|purchase_date|project_need_date)$",
    )
    project_ids: List[int] = Field(default_factory=list)
    supplier_ids: List[int] = Field(default_factory=list)


class OptimizationRollbackPreviewRequest(BaseModel):
    filters: OptimizationRollbackFilterRequest = Field(
        default_factory=OptimizationRollbackFilterRequest
    )


class OptimizationRollbackExecuteRequest(BaseModel):
    filters: OptimizationRollbackFilterRequest = Field(
        default_factory=OptimizationRollbackFilterRequest
    )
    selected_item_ids: List[int] = Field(default_factory=list)
    confirmed: bool = Field(
        False, description="Must be true to execute rollback"
    )
    notes: Optional[str] = None


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

    await _ensure_item_editable_for_packages(db, project_item.id)

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
        payload = package_data.model_dump(exclude={"is_finalized"})
        package = ProcurementPackage(
            **payload,
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
        await _enrich_packages_runtime_state(db, [package])
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

    await _ensure_item_editable_for_packages(db, package.project_item_id)

    # Validate duplicate name when package_name is changed
    update_data = package_data.model_dump(exclude_unset=True)
    requested_finalization = update_data.pop("is_finalized", None)
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

    if requested_finalization is not None:
        await db.execute(
            update(ProcurementOption)
            .where(
                ProcurementOption.package_id == package.id,
                ProcurementOption.is_active == True,  # noqa: E712
            )
            .values(is_finalized=bool(requested_finalization))
        )

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
    await _enrich_packages_runtime_state(db, [package])
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

    await _ensure_item_editable_for_packages(db, package.project_item_id)

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
        await _enrich_packages_runtime_state(db, packages)
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
    await _enrich_packages_runtime_state(db, [package])
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
    package_result = await db.execute(
        select(ProcurementPackage).where(ProcurementPackage.id == subitem_data.package_id)
    )
    package = package_result.scalar_one_or_none()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    await _ensure_item_editable_for_packages(db, package.project_item_id)

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

    package_result = await db.execute(
        select(ProcurementPackage).where(ProcurementPackage.id == subitem.package_id)
    )
    package = package_result.scalar_one_or_none()
    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Package not found"
        )
    await _ensure_item_editable_for_packages(db, package.project_item_id)

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

    package_result = await db.execute(
        select(ProcurementPackage).where(ProcurementPackage.id == subitem.package_id)
    )
    package = package_result.scalar_one_or_none()
    if package:
        await _ensure_item_editable_for_packages(db, package.project_item_id)

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


@router.post("/optimization-submission")
async def submit_packages_to_optimization(
    request: OptimizationSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit finalized package combinations to optimization gate.
    Supports single item, multiple items, or all finalized items.
    """
    if current_user.role not in ["procurement", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement/admin users can submit packages to optimization",
        )

    target_item_ids = await _resolve_target_project_item_ids(db, request)
    if not target_item_ids:
        return {
            "submitted_items": [],
            "skipped_items": [],
            "warnings": ["No eligible project items found for submission"],
            "incomplete_items_requiring_confirmation": [],
            "generated_combinations": [],
            "errors": [],
        }

    submitted_items = []
    skipped_items = []
    warnings: List[str] = []
    incomplete_items_requiring_confirmation = []
    generated_combinations = []
    errors = []

    confirmed_incomplete_ids = set(int(v) for v in request.confirmed_incomplete_item_ids)

    for project_item_id in target_item_ids:
        try:
            if await get_project_item_sent_state(db, project_item_id):
                skipped_items.append(
                    {
                        "project_item_id": project_item_id,
                        "reason": "already_sent_to_optimization",
                    }
                )
                continue

            analysis = await analyze_project_item_package_combinations(
                db,
                project_item_id=project_item_id,
                max_combinations=request.max_combinations,
            )
            warnings.extend(analysis.get("warnings", []))

            finalized_packages = analysis.get("finalized_packages", [])
            if not finalized_packages:
                skipped_items.append(
                    {
                        "project_item_id": project_item_id,
                        "item_code": analysis.get("item_code"),
                        "reason": "no_finalized_packages",
                    }
                )
                continue

            full_combinations = analysis.get("full_coverage_combinations", [])
            aggregate = analysis.get("aggregate_finalized_coverage", {})
            is_incomplete = len(full_combinations) == 0
            is_confirmed_incomplete = (
                request.include_incomplete_with_confirmation
                and project_item_id in confirmed_incomplete_ids
            )

            if is_incomplete and not is_confirmed_incomplete:
                incomplete_items_requiring_confirmation.append(
                    {
                        "project_item_id": project_item_id,
                        "item_code": analysis.get("item_code"),
                        "coverage_percentage": aggregate.get("coverage_percentage", 0),
                        "missing_components": aggregate.get("missing_components", []),
                        "warning": (
                            "These finalized partial packages do not fully cover required demand. "
                            "Explicit confirmation is required to submit incomplete coverage."
                        ),
                    }
                )
                skipped_items.append(
                    {
                        "project_item_id": project_item_id,
                        "item_code": analysis.get("item_code"),
                        "reason": "incomplete_requires_confirmation",
                    }
                )
                continue

            selected_combination = (
                full_combinations[0]
                if full_combinations
                else {
                    "package_ids": aggregate.get("package_ids", []),
                    "option_ids": aggregate.get("option_ids", []),
                    "coverage_percentage": aggregate.get("coverage_percentage", 0),
                    "missing_components": aggregate.get("missing_components", []),
                    "coverage_classification": aggregate.get("coverage_classification"),
                    "is_over_coverage": aggregate.get("is_over_coverage", False),
                }
            )

            submission_payload = {
                "item_code": analysis.get("item_code"),
                "item_name": analysis.get("item_name"),
                "selected_combination": selected_combination,
                "full_coverage_combinations_count": len(full_combinations),
                "generated_combinations_count": len(analysis.get("generated_combinations", [])),
                "combination_threshold": analysis.get("combination_threshold"),
                "threshold_exceeded": analysis.get("threshold_exceeded"),
            }

            await mark_project_item_sent_to_optimization(
                db,
                project_item_id=project_item_id,
                user_id=current_user.id,
                partial_coverage_acknowledged=is_incomplete,
                summary_payload=submission_payload,
                notes=(
                    "Submitted with partial coverage acknowledgement"
                    if is_incomplete
                    else "Submitted with full coverage combinations"
                ),
            )

            submitted_items.append(
                {
                    "project_item_id": project_item_id,
                    "item_code": analysis.get("item_code"),
                    "item_name": analysis.get("item_name"),
                    "partial_coverage_acknowledged": is_incomplete,
                    "selected_combination": selected_combination,
                }
            )
            generated_combinations.append(
                {
                    "project_item_id": project_item_id,
                    "item_code": analysis.get("item_code"),
                    "combinations": analysis.get("generated_combinations", []),
                }
            )
        except HTTPException as exc:
            errors.append(
                {
                    "project_item_id": project_item_id,
                    "detail": exc.detail,
                    "status_code": exc.status_code,
                }
            )
        except Exception as exc:
            errors.append(
                {
                    "project_item_id": project_item_id,
                    "detail": str(exc),
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                }
            )

    await db.commit()

    for item in submitted_items:
        try:
            await log_audit(
                db,
                user_id=current_user.id,
                action="PACKAGE_SENT_TO_OPTIMIZATION",
                entity_type="project_item",
                entity_id=item["project_item_id"],
                details={
                    "item_code": item.get("item_code"),
                    "partial_coverage_acknowledged": item.get(
                        "partial_coverage_acknowledged", False
                    ),
                },
            )
        except Exception:
            pass

    return {
        "submitted_items": submitted_items,
        "skipped_items": skipped_items,
        "warnings": sorted(set(warnings)),
        "incomplete_items_requiring_confirmation": incomplete_items_requiring_confirmation,
        "generated_combinations": generated_combinations,
        "errors": errors,
    }


@router.post("/optimization-submission/{project_item_id}/rollback")
async def rollback_packages_from_optimization(
    project_item_id: int,
    request: OptimizationSubmissionRollbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Roll back optimization submission lock for a project item (when safe).
    """
    if current_user.role not in ["procurement", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement/admin users can rollback optimization submission",
        )

    record = await rollback_project_item_optimization_submission(
        db,
        project_item_id=project_item_id,
        user_id=current_user.id,
        notes=request.notes,
    )
    await db.commit()

    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="ITEM_OPTIMIZATION_ROLLBACK",
            entity_type="project_item",
            entity_id=project_item_id,
            details={"notes": request.notes},
        )
    except Exception:
        pass

    return {
        "project_item_id": project_item_id,
        "status": record.status,
        "rolled_back_at": record.rolled_back_at.isoformat() if record.rolled_back_at else None,
    }


@router.post("/optimization-rollback-preview")
async def preview_bulk_optimization_rollback(
    request: OptimizationRollbackPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Preview rollback eligibility for sent-to-optimization items using checklist/range filters.
    This endpoint is read-only and does not mutate data.
    """
    if current_user.role not in ["procurement", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement/admin users can preview optimization rollback",
        )

    preview = await build_bulk_rollback_preview(
        db,
        filters=request.filters.model_dump(),
    )
    return preview


@router.post("/optimization-rollback")
async def execute_bulk_optimization_rollback(
    request: OptimizationRollbackExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute controlled bulk rollback for safe sent-to-optimization items.
    """
    if current_user.role not in ["procurement", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only procurement/admin users can execute optimization rollback",
        )

    result = await execute_bulk_rollback(
        db,
        filters=request.filters.model_dump(),
        selected_item_ids=request.selected_item_ids,
        confirmed=request.confirmed,
        user_id=current_user.id,
        notes=request.notes,
    )
    await db.commit()

    for row in result.get("rolled_back_items", []):
        try:
            await log_audit(
                db,
                user_id=current_user.id,
                action="ITEM_OPTIMIZATION_BULK_ROLLBACK",
                entity_type="project_item",
                entity_id=row.get("project_item_id"),
                details={
                    "item_code": row.get("item_code"),
                    "rolled_back_at": row.get("rolled_back_at"),
                },
            )
        except Exception:
            pass

    for row in result.get("skipped_items", []):
        try:
            await log_audit(
                db,
                user_id=current_user.id,
                action="ITEM_OPTIMIZATION_BULK_ROLLBACK_SKIPPED",
                entity_type="project_item",
                entity_id=row.get("project_item_id"),
                details=row,
            )
        except Exception:
            pass

    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="ITEM_OPTIMIZATION_BULK_ROLLBACK_SUMMARY",
            entity_type="optimization_submission",
            entity_id=None,
            details={
                "rolled_back_count": len(result.get("rolled_back_items", [])),
                "skipped_count": len(result.get("skipped_items", [])),
                "error_count": len(result.get("errors", [])),
                "preview_summary": result.get("preview_summary", {}),
            },
        )
    except Exception:
        pass

    return result

