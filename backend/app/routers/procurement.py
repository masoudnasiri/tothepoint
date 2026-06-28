"""
Procurement options management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth import get_current_user
from app.crud import (
    create_procurement_option, get_procurement_option, update_procurement_option, delete_procurement_option, log_audit
)
from app.models import (
    DeliveryOption,
    FinalizedDecision,
    ProcurementOption as ProcurementOptionModel,
    ProcurementPackage,
    ProjectItem,
    User,
)
from app.schemas import ProcurementOption, ProcurementOptionCreate, ProcurementOptionUpdate, ProcurementOptionWithSupplier, SupplierSummary
from app.services.package_service import get_project_item_sent_state
from app.services.procurement_assignment_scope_service import (
    filter_procurement_options_by_scope,
    resolve_procurement_option_project_item_id,
    resolve_procurement_scope_access,
)

router = APIRouter(prefix="/procurement", tags=["procurement"])


async def _resolve_option_project_item_id(db: AsyncSession, option_payload: ProcurementOptionCreate) -> Optional[int]:
    if option_payload.project_item_id is not None:
        return option_payload.project_item_id
    if option_payload.package_id is not None:
        result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == option_payload.package_id
            )
        )
        return result.scalar_one_or_none()
    return None


async def _ensure_item_is_finalized(db: AsyncSession, project_item_id: int) -> None:
    item = await db.get(ProjectItem, project_item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project item not found",
        )
    if not bool(item.is_finalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Procurement options require finalized project items",
        )


def _enforce_item_scope(
    *,
    allowed_project_item_ids: set[int],
    project_item_id: Optional[int],
    denied_detail: str,
) -> None:
    if project_item_id is None or int(project_item_id) not in allowed_project_item_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=denied_detail,
        )


@router.get("/item-codes", response_model=List[str])
async def list_unique_item_codes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique item codes that are available for procurement
    
    Excludes items with LOCKED or PROPOSED finalized decisions.
    Includes items with REVERTED decisions (can add new options).
    """
    from sqlalchemy import and_, distinct

    access = await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.assignments.view",
            "procurement.view",
            "procurement.options.view",
            "project_items.view",
        },
    )

    blocking_decision_subquery = (
        select(FinalizedDecision.project_item_id).where(
            FinalizedDecision.status.in_(["LOCKED", "PROPOSED"])
        )
    )
    query = select(distinct(ProjectItem.item_code)).where(
        ProjectItem.is_finalized == True,  # noqa: E712
        ProjectItem.id.notin_(blocking_decision_subquery),
    )
    if access.assigned_only_scope:
        allowed_item_ids = access.active_scope.finalized_project_item_ids
        if not allowed_item_ids:
            return []
        query = query.where(ProjectItem.id.in_(allowed_item_ids))

    result = await db.execute(query.order_by(ProjectItem.item_code))
    return [str(row[0]) for row in result.fetchall() if row[0]]


@router.get("/items-with-details")
async def list_items_with_details(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of unique items with their names and descriptions (OPTIMIZED!)
    
    Returns items that are available for procurement:
    - Items from projects where the specific project_item has NO LOCKED or PROPOSED decision
    - Uses a single optimized SQL query instead of N+1 queries
    """
    from sqlalchemy import and_

    access = await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.assignments.view",
            "procurement.view",
            "procurement.options.view",
            "project_items.view",
        },
    )

    blocking_decision_subquery = (
        select(FinalizedDecision.project_item_id).where(
            FinalizedDecision.status.in_(["LOCKED", "PROPOSED"])
        )
    )
    query = (
        select(ProjectItem)
        .where(
            ProjectItem.is_finalized == True,  # noqa: E712
            ProjectItem.id.notin_(blocking_decision_subquery),
        )
        .order_by(ProjectItem.item_code, ProjectItem.created_at.desc())
    )
    if access.assigned_only_scope:
        allowed_item_ids = access.active_scope.finalized_project_item_ids
        if not allowed_item_ids:
            return []
        query = query.where(ProjectItem.id.in_(allowed_item_ids))

    rows = (await db.execute(query)).scalars().all()
    by_item_code: dict[str, ProjectItem] = {}
    for item in rows:
        code = item.item_code or ""
        existing = by_item_code.get(code)
        if existing is None:
            by_item_code[code] = item
            continue
        if not existing.description and item.description:
            by_item_code[code] = item

    return [
        {
            "item_code": code,
            "item_name": item.item_name or "",
            "description": item.description or "",
            "project_id": item.project_id,
            "project_item_id": item.id,
        }
        for code, item in sorted(by_item_code.items(), key=lambda entry: entry[0])
    ]


@router.get("/suppliers", response_model=List[SupplierSummary])
async def list_suppliers_for_procurement(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of active suppliers for procurement option creation"""
    import logging
    await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.assignments.view",
            "procurement.view",
            "procurement.options.create",
            "procurement.options.view",
        },
    )
    
    try:
        # --- START of original code ---
        from sqlalchemy import select
        from app.models import Supplier, SupplierStatus
        
        logging.info(f"DEBUG: About to query suppliers with SupplierStatus.ACTIVE = {SupplierStatus.ACTIVE}")
        logging.info(f"DEBUG: SupplierStatus enum values: {[e.value for e in SupplierStatus]}")
        
        result = await db.execute(
            select(Supplier)
            .where(Supplier.status == SupplierStatus.ACTIVE.value)
            .order_by(Supplier.company_name)
        )
        suppliers = result.scalars().all()
        logging.info(f"DEBUG: Successfully retrieved {len(suppliers)} suppliers")
        return suppliers
        # --- END of original code ---

    except Exception as e:
        # Log the full error traceback to the console
        logging.error(f"CRASH in GET /procurement/suppliers: {e}", exc_info=True)
        
        # Re-raise the error as a standard HTTP 500 error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred while fetching suppliers: {str(e)}"
        )


@router.get("/options", response_model=List[ProcurementOptionWithSupplier])
async def list_procurement_options(
    skip: int = 0,
    limit: int = 50000,  # Increased default limit to handle large datasets
    item_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get procurement options with optional filtering by item_code"""
    from sqlalchemy.orm import selectinload

    access = await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.assignments.view",
            "procurement.view",
            "procurement.options.view",
        },
    )
    query = (
        select(ProcurementOptionModel)
        .where(ProcurementOptionModel.is_active == True)  # noqa: E712
        .options(selectinload(ProcurementOptionModel.supplier))
        .order_by(ProcurementOptionModel.created_at.desc())
    )
    if item_code:
        query = query.where(ProcurementOptionModel.item_code == item_code)

    if access.assigned_only_scope:
        query = filter_procurement_options_by_scope(
            query,
            allowed_project_item_ids=access.active_scope.finalized_project_item_ids,
        )

    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.get("/options/{item_code}", response_model=List[ProcurementOptionWithSupplier])
async def list_procurement_options_by_item_code(
    item_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all procurement options for a specific item code"""
    return await list_procurement_options(
        skip=0,
        limit=50000,
        item_code=item_code,
        current_user=current_user,
        db=db,
    )


@router.post("/options", response_model=ProcurementOption)
async def create_new_procurement_option(
    option: ProcurementOptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """Create a new procurement option with Phase 3 dual-mode support (procurement specialist only)"""
    import logging
    from app.config import settings
    from app.services.package_service import get_package_for_project_item
    from app.services.audit_service import log_feature_flag_event
    
    logger = logging.getLogger(__name__)
    
    try:
        access = await resolve_procurement_scope_access(
            db,
            current_user,
            required_any_permissions={
                "procurement.options.create",
                "procurement.create",
            },
        )
        project_item_id = await _resolve_option_project_item_id(db, option)
        if project_item_id is not None:
            await _ensure_item_is_finalized(db, int(project_item_id))
        if access.assigned_only_scope:
            if project_item_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Assigned procurement scope requires a scoped project item",
                )
            _enforce_item_scope(
                allowed_project_item_ids=access.active_scope.finalized_project_item_ids,
                project_item_id=int(project_item_id),
                denied_detail="Project item is outside your active procurement assignment scope",
            )
        if project_item_id is not None and await get_project_item_sent_state(db, project_item_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Item has been sent to optimization. "
                    "Rollback is required before changing procurement options."
                ),
            )

        # Phase 3: Log feature flag usage
        await log_feature_flag_event(
            db, "ENABLE_PACKAGE_PROCUREMENT", settings.enable_package_procurement,
            context="create_procurement_option", user_id=current_user.id
        )
        
        logger.info(f"Creating new procurement option (package_mode={settings.enable_package_procurement})")
        
        result = await create_procurement_option(db, option)
        
        # Phase 3: Enrich response with package context if available
        if result.package_id:
            package_info = await get_package_for_project_item(
                db, result.project_item_id if result.project_item_id else None
            )
            if package_info:
                result.package_name = package_info.get('package_name')
                result.package_type = package_info.get('package_type')

        # Materialize response while session is active to prevent MissingGreenlet
        response_payload = ProcurementOption.model_validate(result)

        # Audit
        try:
            client_host = request.client.host if request and request.client else None
            ua = request.headers.get("user-agent") if request else None
            await log_audit(
                db,
                user_id=current_user.id,
                action="PROCUREMENT_OPTION_CREATE",
                entity_type="procurement_option",
                entity_id=result.id,
                details={
                    "item_code": response_payload.item_code,
                    "supplier_name": response_payload.supplier_name,
                    "package_id": response_payload.package_id,
                    "project_item_id": response_payload.project_item_id
                },
                ip_address=client_host,
                user_agent=ua,
            )
        except Exception:
            pass
        
        logger.info(f"Successfully created procurement option with ID: {result.id}")
        return response_payload
        
    except ValueError as e:
        logger.warning(f"Validation error creating procurement option: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create procurement option: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create procurement option: {str(e)}"
        )


@router.get("/option/{option_id}", response_model=ProcurementOption)
async def get_procurement_option_by_id(
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get procurement option by ID"""
    access = await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.assignments.view",
            "procurement.view",
            "procurement.options.view",
        },
    )
    option = await get_procurement_option(db, option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )
    if access.assigned_only_scope:
        project_item_id = await resolve_procurement_option_project_item_id(db, option)
        _enforce_item_scope(
            allowed_project_item_ids=access.active_scope.finalized_project_item_ids,
            project_item_id=project_item_id,
            denied_detail="Procurement option is outside your active procurement assignment scope",
        )
    return option


@router.get("/options/by-project-item/{project_item_id}", response_model=List[ProcurementOptionWithSupplier])
async def list_procurement_options_by_project_item(
    project_item_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetch procurement options for a project item with package/legacy compatibility."""
    from sqlalchemy import select, and_, or_
    from sqlalchemy.orm import selectinload
    from app.models import ProcurementOption

    access = await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.assignments.view",
            "procurement.view",
            "procurement.options.view",
        },
    )
    if access.assigned_only_scope:
        _enforce_item_scope(
            allowed_project_item_ids=access.active_scope.finalized_project_item_ids,
            project_item_id=project_item_id,
            denied_detail="Project item is outside your active procurement assignment scope",
        )

    try:
        delivery_option_ids_subquery = (
            select(DeliveryOption.id)
            .where(DeliveryOption.project_item_id == project_item_id)
        )

        # Prefer direct project_item_id filtering, with a legacy fallback through delivery_option_id.
        result = await db.execute(
            select(ProcurementOption)
            .where(ProcurementOption.is_active == True)
            .where(
                or_(
                    ProcurementOption.project_item_id == project_item_id,
                    ProcurementOption.package_id.in_(
                        select(ProcurementPackage.id).where(
                            ProcurementPackage.project_item_id == project_item_id
                        )
                    ),
                    and_(
                        ProcurementOption.project_item_id.is_(None),
                        ProcurementOption.delivery_option_id.in_(delivery_option_ids_subquery)
                    )
                )
            )
            .options(selectinload(ProcurementOption.supplier))
            .order_by(ProcurementOption.created_at.desc())
        )
        options = result.scalars().all()
        return options if options is not None else []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch procurement options: {str(e)}"
        )


@router.put("/option/{option_id}", response_model=ProcurementOption)
async def update_procurement_option_by_id(
    option_id: int,
    option_update: ProcurementOptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update procurement option (procurement specialist only)"""
    access = await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.options.edit",
            "procurement.edit",
        },
    )

    existing = await db.execute(
        select(ProcurementOptionModel).where(ProcurementOptionModel.id == option_id)
    )
    existing_option = existing.scalar_one_or_none()
    if not existing_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )

    project_item_id = existing_option.project_item_id
    if project_item_id is None and existing_option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == existing_option.package_id
            )
        )
        project_item_id = package_result.scalar_one_or_none()

    if access.assigned_only_scope:
        _enforce_item_scope(
            allowed_project_item_ids=access.active_scope.finalized_project_item_ids,
            project_item_id=project_item_id,
            denied_detail="Procurement option is outside your active procurement assignment scope",
        )
    if project_item_id is not None and await get_project_item_sent_state(db, project_item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Item has been sent to optimization. "
                "Rollback is required before changing procurement options."
            ),
        )

    try:
        option = await update_procurement_option(db, option_id, option_update)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if not option:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Procurement option not found")
    response_payload = ProcurementOption.model_validate(option)
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="PROCUREMENT_OPTION_UPDATE",
            entity_type="procurement_option",
            entity_id=option_id,
            details=jsonable_encoder(option_update.model_dump(exclude_unset=True)),
        )
    except Exception:
        pass
    return response_payload


@router.delete("/option/{option_id}")
async def delete_procurement_option_by_id(
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete procurement option (procurement specialist only)"""
    access = await resolve_procurement_scope_access(
        db,
        current_user,
        required_any_permissions={
            "procurement.options.delete",
            "procurement.delete",
        },
    )

    existing = await db.execute(
        select(ProcurementOptionModel).where(ProcurementOptionModel.id == option_id)
    )
    existing_option = existing.scalar_one_or_none()
    if not existing_option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )

    project_item_id = existing_option.project_item_id
    if project_item_id is None and existing_option.package_id is not None:
        package_result = await db.execute(
            select(ProcurementPackage.project_item_id).where(
                ProcurementPackage.id == existing_option.package_id
            )
        )
        project_item_id = package_result.scalar_one_or_none()

    if access.assigned_only_scope:
        _enforce_item_scope(
            allowed_project_item_ids=access.active_scope.finalized_project_item_ids,
            project_item_id=project_item_id,
            denied_detail="Procurement option is outside your active procurement assignment scope",
        )
    if project_item_id is not None and await get_project_item_sent_state(db, project_item_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Item has been sent to optimization. "
                "Rollback is required before changing procurement options."
            ),
        )

    success = await delete_procurement_option(db, option_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement option not found"
        )
    try:
        await log_audit(
            db,
            user_id=current_user.id,
            action="PROCUREMENT_OPTION_DELETE",
            entity_type="procurement_option",
            entity_id=option_id,
        )
    except Exception:
        pass
    return {"message": "Procurement option deleted successfully"}
