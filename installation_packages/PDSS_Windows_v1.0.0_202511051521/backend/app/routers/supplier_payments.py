from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime

from app.database import get_db
from app.models import SupplierPayment as SupplierPaymentModel, FinalizedDecision, Project, User
from app.schemas import (
    SupplierPaymentCreate, 
    SupplierPaymentUpdate, 
    SupplierPaymentResponse,
    SupplierPayment
)
from app.auth import get_current_user
from app.schemas import User as UserSchema
from app.cashflow_sync_service import CashflowSyncService

router = APIRouter(prefix="/supplier-payments", tags=["supplier-payments"])


@router.get("/", response_model=List[SupplierPaymentResponse])
async def list_supplier_payments(
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    supplier_name: Optional[str] = Query(None, description="Filter by supplier name"),
    item_code: Optional[str] = Query(None, description="Filter by item code"),
    status: Optional[str] = Query(None, description="Filter by payment status"),
    start_date: Optional[date] = Query(None, description="Filter by start date"),
    end_date: Optional[date] = Query(None, description="Filter by end date")
):
    """
    Get list of supplier payments with filtering and pagination.
    """
    # Base query
    stmt = select(SupplierPaymentModel).options(
        selectinload(SupplierPaymentModel.decision),
        selectinload(SupplierPaymentModel.project),
        selectinload(SupplierPaymentModel.created_by)
    )
    
    # Apply filters
    filters = []
    
    if project_id:
        filters.append(SupplierPaymentModel.project_id == project_id)
    
    if supplier_name:
        filters.append(SupplierPaymentModel.supplier_name.ilike(f"%{supplier_name}%"))
    
    if item_code:
        filters.append(SupplierPaymentModel.item_code.ilike(f"%{item_code}%"))
    
    if status:
        filters.append(SupplierPaymentModel.status == status)
    
    if start_date:
        filters.append(SupplierPaymentModel.payment_date >= start_date)
    
    if end_date:
        filters.append(SupplierPaymentModel.payment_date <= end_date)
    
    # Apply role-based filtering for project managers
    if current_user.role == 'pm':
        # Get projects assigned to this user
        from app.models import ProjectAssignment
        assigned_projects_stmt = select(ProjectAssignment.project_id).where(
            ProjectAssignment.user_id == current_user.id
        )
        assigned_projects_result = await db.execute(assigned_projects_stmt)
        assigned_project_ids = [row[0] for row in assigned_projects_result.fetchall()]
        
        if not assigned_project_ids:
            return []
        
        filters.append(SupplierPaymentModel.project_id.in_(assigned_project_ids))
    
    if filters:
        stmt = stmt.where(and_(*filters))
    
    # Order by payment date descending
    stmt = stmt.order_by(desc(SupplierPaymentModel.payment_date))
    
    # Apply pagination
    stmt = stmt.offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    payments = result.scalars().all()
    
    # Convert to response format
    response_data = []
    for payment in payments:
        payment_dict = {
            "id": payment.id,
            "decision_id": payment.decision_id,
            "supplier_name": payment.supplier_name,
            "item_code": payment.item_code,
            "project_id": payment.project_id,
            "project_name": payment.project.name if payment.project else None,
            "payment_date": payment.payment_date,
            "payment_amount": payment.payment_amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "reference_number": payment.reference_number,
            "notes": payment.notes,
            "status": payment.status,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "created_by_id": payment.created_by_id
        }
        response_data.append(payment_dict)
    
    return response_data


@router.get("/{payment_id}", response_model=SupplierPaymentResponse)
async def get_supplier_payment(
    payment_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific supplier payment by ID.
    """
    stmt = select(SupplierPaymentModel).where(SupplierPaymentModel.id == payment_id).options(
        selectinload(SupplierPaymentModel.decision),
        selectinload(SupplierPaymentModel.project),
        selectinload(SupplierPaymentModel.created_by)
    )
    
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Supplier payment not found")
    
    # Check if user has access to this payment's project
    if current_user.role == 'pm':
        from app.models import ProjectAssignment
        assigned_projects_stmt = select(ProjectAssignment.project_id).where(
            ProjectAssignment.user_id == current_user.id
        )
        assigned_projects_result = await db.execute(assigned_projects_stmt)
        assigned_project_ids = [row[0] for row in assigned_projects_result.fetchall()]
        
        if payment.project_id not in assigned_project_ids:
            raise HTTPException(status_code=403, detail="Access denied to this payment")
    
    return {
        "id": payment.id,
        "decision_id": payment.decision_id,
        "supplier_name": payment.supplier_name,
        "item_code": payment.item_code,
        "project_id": payment.project_id,
        "project_name": payment.project.name if payment.project else None,
        "payment_date": payment.payment_date,
        "payment_amount": payment.payment_amount,
        "currency": payment.currency,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "status": payment.status,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
        "created_by_id": payment.created_by_id
    }


@router.post("/", response_model=SupplierPaymentResponse)
async def create_supplier_payment(
    payment_data: SupplierPaymentCreate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new supplier payment.
    """
    # Verify the decision exists and user has access
    decision_stmt = select(FinalizedDecision).where(
        FinalizedDecision.id == payment_data.decision_id
    ).options(selectinload(FinalizedDecision.project))
    
    decision_result = await db.execute(decision_stmt)
    decision = decision_result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    # Check if user has access to this decision's project
    if current_user.role == 'pm':
        from app.models import ProjectAssignment
        assigned_projects_stmt = select(ProjectAssignment.project_id).where(
            ProjectAssignment.user_id == current_user.id
        )
        assigned_projects_result = await db.execute(assigned_projects_stmt)
        assigned_project_ids = [row[0] for row in assigned_projects_result.fetchall()]
        
        if decision.project_id not in assigned_project_ids:
            raise HTTPException(status_code=403, detail="Access denied to this decision")
    
    # Create the supplier payment
    supplier_payment = SupplierPaymentModel(
        decision_id=payment_data.decision_id,
        supplier_name=payment_data.supplier_name,
        item_code=payment_data.item_code,
        project_id=payment_data.project_id,
        payment_date=payment_data.payment_date,
        payment_amount=payment_data.payment_amount,
        currency=payment_data.currency,
        payment_method=payment_data.payment_method,
        reference_number=payment_data.reference_number,
        notes=payment_data.notes,
        status=payment_data.status,
        created_by_id=current_user.id
    )
    
    db.add(supplier_payment)
    await db.commit()
    await db.refresh(supplier_payment)
    
    # Sync with cash flow system
    try:
        cashflow_service = CashflowSyncService(db)
        await cashflow_service.sync_payment_out(supplier_payment)
    except Exception as e:
        # Log error but don't fail the payment creation
        print(f"Warning: Failed to sync supplier payment with cash flow: {str(e)}")
    
    # Get project name for response
    project_stmt = select(Project).where(Project.id == supplier_payment.project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    
    return {
        "id": supplier_payment.id,
        "decision_id": supplier_payment.decision_id,
        "supplier_name": supplier_payment.supplier_name,
        "item_code": supplier_payment.item_code,
        "project_id": supplier_payment.project_id,
        "project_name": project.name if project else None,
        "payment_date": supplier_payment.payment_date,
        "payment_amount": supplier_payment.payment_amount,
        "currency": supplier_payment.currency,
        "payment_method": supplier_payment.payment_method,
        "reference_number": supplier_payment.reference_number,
        "notes": supplier_payment.notes,
        "status": supplier_payment.status,
        "created_at": supplier_payment.created_at,
        "updated_at": supplier_payment.updated_at,
        "created_by_id": supplier_payment.created_by_id
    }


@router.put("/{payment_id}", response_model=SupplierPaymentResponse)
async def update_supplier_payment(
    payment_id: int,
    payment_data: SupplierPaymentUpdate,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a supplier payment.
    """
    stmt = select(SupplierPayment).where(SupplierPaymentModel.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Supplier payment not found")
    
    # Check if user has access to this payment's project
    if current_user.role == 'pm':
        from app.models import ProjectAssignment
        assigned_projects_stmt = select(ProjectAssignment.project_id).where(
            ProjectAssignment.user_id == current_user.id
        )
        assigned_projects_result = await db.execute(assigned_projects_stmt)
        assigned_project_ids = [row[0] for row in assigned_projects_result.fetchall()]
        
        if payment.project_id not in assigned_project_ids:
            raise HTTPException(status_code=403, detail="Access denied to this payment")
    
    # Update fields
    update_data = payment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(payment, field, value)
    
    payment.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(payment)
    
    # Get project name for response
    project_stmt = select(Project).where(Project.id == payment.project_id)
    project_result = await db.execute(project_stmt)
    project = project_result.scalar_one_or_none()
    
    return {
        "id": payment.id,
        "decision_id": payment.decision_id,
        "supplier_name": payment.supplier_name,
        "item_code": payment.item_code,
        "project_id": payment.project_id,
        "project_name": project.name if project else None,
        "payment_date": payment.payment_date,
        "payment_amount": payment.payment_amount,
        "currency": payment.currency,
        "payment_method": payment.payment_method,
        "reference_number": payment.reference_number,
        "notes": payment.notes,
        "status": payment.status,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
        "created_by_id": payment.created_by_id
    }


@router.delete("/{payment_id}")
async def delete_supplier_payment(
    payment_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a supplier payment.
    """
    stmt = select(SupplierPaymentModel).where(SupplierPaymentModel.id == payment_id)
    result = await db.execute(stmt)
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Supplier payment not found")
    
    # Check if user has access to this payment's project
    if current_user.role == 'pm':
        from app.models import ProjectAssignment
        assigned_projects_stmt = select(ProjectAssignment.project_id).where(
            ProjectAssignment.user_id == current_user.id
        )
        assigned_projects_result = await db.execute(assigned_projects_stmt)
        assigned_project_ids = [row[0] for row in assigned_projects_result.fetchall()]
        
        if payment.project_id not in assigned_project_ids:
            raise HTTPException(status_code=403, detail="Access denied to this payment")
    
    await db.delete(payment)
    await db.commit()
    
    # Remove from cash flow system
    try:
        cashflow_service = CashflowSyncService(db)
        await cashflow_service.remove_payment_sync(payment_id, 'out')
    except Exception as e:
        # Log error but don't fail the payment deletion
        print(f"Warning: Failed to remove supplier payment from cash flow: {str(e)}")
    
    return {"message": "Supplier payment deleted successfully"}


@router.get("/decisions/{decision_id}/payments", response_model=List[SupplierPaymentResponse])
async def get_decision_supplier_payments(
    decision_id: int,
    current_user: UserSchema = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all supplier payments for a specific decision.
    """
    # First verify the decision exists and user has access
    decision_stmt = select(FinalizedDecision).where(
        FinalizedDecision.id == decision_id
    )
    decision_result = await db.execute(decision_stmt)
    decision = decision_result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    # Check if user has access to this decision's project
    if current_user.role == 'pm':
        from app.models import ProjectAssignment
        assigned_projects_stmt = select(ProjectAssignment.project_id).where(
            ProjectAssignment.user_id == current_user.id
        )
        assigned_projects_result = await db.execute(assigned_projects_stmt)
        assigned_project_ids = [row[0] for row in assigned_projects_result.fetchall()]
        
        if decision.project_id not in assigned_project_ids:
            raise HTTPException(status_code=403, detail="Access denied to this decision")
    
    # Get supplier payments for this decision
    stmt = select(SupplierPayment).where(
        SupplierPaymentModel.decision_id == decision_id
    ).options(
        selectinload(SupplierPaymentModel.project),
        selectinload(SupplierPaymentModel.created_by)
    ).order_by(desc(SupplierPaymentModel.payment_date))
    
    result = await db.execute(stmt)
    payments = result.scalars().all()
    
    # Convert to response format
    response_data = []
    for payment in payments:
        payment_dict = {
            "id": payment.id,
            "decision_id": payment.decision_id,
            "supplier_name": payment.supplier_name,
            "item_code": payment.item_code,
            "project_id": payment.project_id,
            "project_name": payment.project.name if payment.project else None,
            "payment_date": payment.payment_date,
            "payment_amount": payment.payment_amount,
            "currency": payment.currency,
            "payment_method": payment.payment_method,
            "reference_number": payment.reference_number,
            "notes": payment.notes,
            "status": payment.status,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "created_by_id": payment.created_by_id
        }
        response_data.append(payment_dict)
    
    return response_data
