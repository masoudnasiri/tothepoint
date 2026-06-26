"""
Payment methods and procurement cost components foundation endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, require_pilot_permission
from app.database import get_db
from app.models import PaymentMethod, ProcurementCostComponent, ProcurementOption, User
from app.schemas import (
    PaymentMethod as PaymentMethodSchema,
    PaymentMethodCreate,
    PaymentMethodUpdate,
    ProcurementCostComponent as ProcurementCostComponentSchema,
    ProcurementCostComponentCreate,
    ProcurementCostComponentUpdate,
    ProcurementOptionDeliveryFinancialPreview,
    ProcurementOptionDeliveryFinancialPreviewRequest,
    ProcurementOptionLandedCostPreview,
    ProcurementOptionReadinessSummary,
)
from app.services.procurement_financials_service import (
    apply_procurement_option_persistence_contract,
    calculate_procurement_option_delivery_financial_preview,
    calculate_procurement_option_landed_cost,
    get_procurement_option_readiness,
    synchronize_procurement_option_legacy_pricing_fields,
)

router = APIRouter(tags=["procurement-financials"])


@router.get("/payment-methods", response_model=List[PaymentMethodSchema])
async def list_payment_methods(
    active_only: bool = Query(True),
    current_user: User = Depends(require_pilot_permission("master_data.payment_methods.view")),
    db: AsyncSession = Depends(get_db),
):
    query = select(PaymentMethod).order_by(PaymentMethod.code.asc())
    if active_only:
        query = query.where(PaymentMethod.is_active == True)  # noqa: E712
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/payment-methods/{payment_method_id}", response_model=PaymentMethodSchema)
async def get_payment_method(
    payment_method_id: int,
    current_user: User = Depends(require_pilot_permission("master_data.payment_methods.view")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
    )
    payment_method = result.scalar_one_or_none()
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found"
        )
    return payment_method


@router.post(
    "/payment-methods",
    response_model=PaymentMethodSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_method(
    payload: PaymentMethodCreate,
    current_user: User = Depends(require_pilot_permission("master_data.payment_methods.create")),
    db: AsyncSession = Depends(get_db),
):
    normalized_code = payload.code.strip().upper()
    existing_result = await db.execute(
        select(PaymentMethod).where(func.upper(PaymentMethod.code) == normalized_code)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment method code '{normalized_code}' already exists",
        )

    payment_method = PaymentMethod(
        code=normalized_code,
        name_en=payload.name_en.strip(),
        name_fa=payload.name_fa.strip(),
        description=payload.description,
        settlement_delay_days=payload.settlement_delay_days,
        is_active=payload.is_active,
    )
    db.add(payment_method)
    await db.commit()
    await db.refresh(payment_method)
    return payment_method


@router.put("/payment-methods/{payment_method_id}", response_model=PaymentMethodSchema)
async def update_payment_method(
    payment_method_id: int,
    payload: PaymentMethodUpdate,
    current_user: User = Depends(require_pilot_permission("master_data.payment_methods.edit")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
    )
    payment_method = result.scalar_one_or_none()
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found"
        )

    update_data = payload.model_dump(exclude_unset=True)
    if "code" in update_data:
        normalized_code = update_data["code"].strip().upper()
        existing_result = await db.execute(
            select(PaymentMethod).where(
                func.upper(PaymentMethod.code) == normalized_code,
                PaymentMethod.id != payment_method_id,
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment method code '{normalized_code}' already exists",
            )
        update_data["code"] = normalized_code

    for field, value in update_data.items():
        if field in {"name_en", "name_fa"} and isinstance(value, str):
            setattr(payment_method, field, value.strip())
        else:
            setattr(payment_method, field, value)

    await db.commit()
    await db.refresh(payment_method)
    return payment_method


@router.delete("/payment-methods/{payment_method_id}")
async def deactivate_payment_method(
    payment_method_id: int,
    current_user: User = Depends(require_pilot_permission("master_data.payment_methods.delete")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PaymentMethod).where(PaymentMethod.id == payment_method_id)
    )
    payment_method = result.scalar_one_or_none()
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Payment method not found"
        )

    payment_method.is_active = False
    await db.commit()
    return {"message": "Payment method deactivated"}


@router.get(
    "/procurement-options/{option_id}/cost-components",
    response_model=List[ProcurementCostComponentSchema],
)
async def list_procurement_option_cost_components(
    option_id: int,
    active_only: bool = Query(True),
    current_user: User = Depends(require_pilot_permission("master_data.cost_components.view")),
    db: AsyncSession = Depends(get_db),
):
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    if not option_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Procurement option not found"
        )

    query = (
        select(ProcurementCostComponent)
        .where(ProcurementCostComponent.procurement_option_id == option_id)
        .order_by(ProcurementCostComponent.id.asc())
    )
    if active_only:
        query = query.where(ProcurementCostComponent.is_active == True)  # noqa: E712
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post(
    "/procurement-options/{option_id}/cost-components",
    response_model=ProcurementCostComponentSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_procurement_option_cost_component(
    option_id: int,
    payload: ProcurementCostComponentCreate,
    current_user: User = Depends(require_pilot_permission("master_data.cost_components.create")),
    db: AsyncSession = Depends(get_db),
):
    option_result = await db.execute(
        select(ProcurementOption).where(ProcurementOption.id == option_id)
    )
    if not option_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Procurement option not found"
        )

    # TODO (Sprint 2B/2C): enforce VAT/CUSTOMS purchase-type constraints once
    # supplier/domestic-vs-foreign purchase_type semantics are canonicalized.
    component = ProcurementCostComponent(
        procurement_option_id=option_id,
        component_type=payload.component_type.value,
        description=payload.description,
        amount_value=payload.amount_value,
        amount_currency=payload.amount_currency.strip().upper(),
        amount_irr=payload.amount_irr,
        exchange_rate_date=payload.exchange_rate_date,
        payment_metadata=(
            jsonable_encoder(payload.payment_metadata, exclude_none=True)
            if payload.payment_metadata is not None
            else None
        ),
        is_active=payload.is_active,
    )
    db.add(component)
    await db.flush()
    try:
        await synchronize_procurement_option_legacy_pricing_fields(
            option_id=option_id,
            db=db,
            require_base_price=False,
        )
        await apply_procurement_option_persistence_contract(option_id=option_id, db=db)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await db.commit()
    await db.refresh(component)
    return component


@router.put(
    "/procurement-cost-components/{component_id}",
    response_model=ProcurementCostComponentSchema,
)
async def update_procurement_cost_component(
    component_id: int,
    payload: ProcurementCostComponentUpdate,
    current_user: User = Depends(require_pilot_permission("master_data.cost_components.edit")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcurementCostComponent).where(ProcurementCostComponent.id == component_id)
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement cost component not found",
        )

    update_data = payload.model_dump(exclude_unset=True)
    next_component_type = update_data.get("component_type")
    next_description = (
        update_data.get("description")
        if "description" in update_data
        else component.description
    )
    if next_component_type is not None and next_component_type.value == "OTHER" and not (
        (next_description or "").strip()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="description is required when component_type is OTHER",
        )

    for field, value in update_data.items():
        if field == "component_type" and value is not None:
            setattr(component, field, value.value)
        elif field == "amount_currency" and isinstance(value, str):
            setattr(component, field, value.strip().upper())
        elif field == "payment_metadata":
            setattr(
                component,
                field,
                (
                    jsonable_encoder(value, exclude_none=True)
                    if value is not None
                    else None
                ),
            )
        else:
            setattr(component, field, value)
    try:
        await synchronize_procurement_option_legacy_pricing_fields(
            option_id=component.procurement_option_id,
            db=db,
            require_base_price=False,
        )
        await apply_procurement_option_persistence_contract(
            option_id=component.procurement_option_id,
            db=db,
        )
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await db.commit()
    await db.refresh(component)
    return component


@router.delete("/procurement-cost-components/{component_id}")
async def deactivate_procurement_cost_component(
    component_id: int,
    current_user: User = Depends(require_pilot_permission("master_data.cost_components.delete")),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcurementCostComponent).where(ProcurementCostComponent.id == component_id)
    )
    component = result.scalar_one_or_none()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Procurement cost component not found",
        )

    component.is_active = False
    try:
        await synchronize_procurement_option_legacy_pricing_fields(
            option_id=component.procurement_option_id,
            db=db,
            require_base_price=False,
        )
        await apply_procurement_option_persistence_contract(
            option_id=component.procurement_option_id,
            db=db,
        )
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    await db.commit()
    return {"message": "Procurement cost component deactivated"}


@router.get(
    "/procurement-options/{option_id}/landed-cost-preview",
    response_model=ProcurementOptionLandedCostPreview,
)
async def get_procurement_option_landed_cost_preview(
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        preview = await calculate_procurement_option_landed_cost(option_id=option_id, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return preview


@router.post(
    "/procurement-options/{option_id}/delivery-financial-preview",
    response_model=ProcurementOptionDeliveryFinancialPreview,
)
async def get_procurement_option_delivery_financial_preview(
    option_id: int,
    payload: ProcurementOptionDeliveryFinancialPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        preview = await calculate_procurement_option_delivery_financial_preview(
            option_id=option_id,
            db=db,
            overrides=payload.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return preview


@router.get(
    "/procurement-options/{option_id}/readiness",
    response_model=ProcurementOptionReadinessSummary,
)
async def get_procurement_option_candidate_readiness(
    option_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        readiness = await get_procurement_option_readiness(option_id=option_id, db=db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return readiness
