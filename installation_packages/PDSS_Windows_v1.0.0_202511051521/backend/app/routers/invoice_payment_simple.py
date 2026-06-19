from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models import FinalizedDecision
from app.schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    PaymentCreate, PaymentUpdate, PaymentResponse,
    InvoicePaymentSummary
)
from app.cashflow_sync_service import CashflowSyncService

router = APIRouter(prefix="/api/invoice-payment", tags=["invoice-payment"])

# Invoice Management
@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List invoices with filtering and pagination"""
    # Query finalized decisions that have invoice data
    query = select(FinalizedDecision).where(
        FinalizedDecision.actual_invoice_issue_date.isnot(None)
    )
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                FinalizedDecision.item_code.ilike(f"%{search}%"),
                FinalizedDecision.notes.ilike(f"%{search}%")
            )
        )
    
    if project_id:
        query = query.where(FinalizedDecision.project_id == project_id)
    
    if start_date and isinstance(start_date, str) and start_date.strip():
        query = query.where(FinalizedDecision.actual_invoice_issue_date >= datetime.fromisoformat(start_date).date())
    
    if end_date and isinstance(end_date, str) and end_date.strip():
        query = query.where(FinalizedDecision.actual_invoice_issue_date <= datetime.fromisoformat(end_date).date())
    
    # Apply pagination
    page_num = page if isinstance(page, int) else 1
    limit_num = limit if isinstance(limit, int) else 50
    offset = (page_num - 1) * limit_num
    result = await db.execute(query.offset(offset).limit(limit_num))
    decisions = result.scalars().all()
    
    # Convert to InvoiceResponse format
    invoices = []
    for decision in decisions:
        invoice = InvoiceResponse(
            id=decision.id,
            decision_id=decision.id,
            invoice_number=f"INV-{decision.id:06d}",
            invoice_date=decision.actual_invoice_issue_date.isoformat() if decision.actual_invoice_issue_date else "",
            invoice_amount=float(decision.actual_invoice_amount) if decision.actual_invoice_amount else 0.0,
            currency=decision.actual_invoice_amount_currency or "IRR",
            due_date=decision.actual_invoice_received_date.isoformat() if decision.actual_invoice_received_date else "",
            payment_terms="",  # No payment_terms field in finalized_decisions
            notes=decision.notes or "",
            item_code=decision.item_code,
            project_name=f"Project {decision.project_id}",
            supplier_name="Unknown Supplier",
            status="sent" if decision.actual_invoice_issue_date else "draft",
            created_at=decision.created_at,
            updated_at=decision.updated_at
        )
        invoices.append(invoice)
    
    return invoices

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific invoice by ID"""
    raise HTTPException(status_code=404, detail="Invoice not found")

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    """Create a new invoice"""
    try:
        # Find the decision
        result = await db.execute(
            select(FinalizedDecision).where(FinalizedDecision.id == invoice.decision_id)
        )
        decision = result.scalar_one_or_none()
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Check if item is already fully paid
        final_cost = float(decision.final_cost)
        total_paid = float(decision.actual_payment_amount or 0)
        
        # Check if item is fully paid
        if total_paid >= final_cost - 0.01:
            raise HTTPException(
                status_code=400, 
                detail="This item is already fully paid. Cannot create additional invoices."
            )
        
        # Note: We removed the final invoice blocking logic to allow flexibility
        
        # Determine payment status based on invoice amount vs final cost
        invoice_amount = float(invoice.invoice_amount)
        
        # If invoice amount equals final cost, it's complete payment
        # If invoice amount is less than final cost, it's partial payment
        if invoice_amount >= final_cost - 0.01:  # Small tolerance for floating point
            payment_status = "Complete"
        else:
            payment_status = "Partial"
        
        # Calculate remaining amount that can be invoiced
        remaining_amount = 0
        if decision.actual_invoice_amount:
            total_invoiced = float(decision.actual_invoice_amount)
            total_paid = float(decision.actual_payment_amount or 0)
            remaining_amount = total_invoiced - total_paid
        
        # Set final invoice flag if specified (for both first and additional invoices)
        decision.is_final_invoice = invoice.is_final_invoice
        
        # If this is an additional invoice, add to existing amount
        if decision.actual_invoice_issue_date:
            # This is an additional invoice for partial payment
            existing_amount = float(decision.actual_invoice_amount or 0)
            new_total_amount = existing_amount + float(invoice.invoice_amount)
            decision.actual_invoice_amount = new_total_amount
        else:
            # This is the first invoice
            decision.actual_invoice_issue_date = datetime.fromisoformat(invoice.invoice_date).date()
            decision.actual_invoice_amount = float(invoice.invoice_amount)
            decision.actual_invoice_amount_currency = invoice.currency
            if invoice.due_date:
                decision.actual_invoice_received_date = datetime.fromisoformat(invoice.due_date).date()
            # Payment status is determined by amount vs final cost, not stored separately
            if invoice.notes:
                decision.notes = invoice.notes
        
        await db.commit()
        await db.refresh(decision)
        
        # Return the updated decision as an invoice response
        return InvoiceResponse(
            id=decision.id,
            decision_id=decision.id,
            invoice_number=invoice.invoice_number,
            invoice_date=decision.actual_invoice_issue_date.isoformat() if decision.actual_invoice_issue_date else "",
            invoice_amount=float(decision.actual_invoice_amount) if decision.actual_invoice_amount else 0.0,
            currency=decision.actual_invoice_amount_currency or "IRR",
            due_date=decision.actual_invoice_received_date.isoformat() if decision.actual_invoice_received_date else "",
            payment_terms=payment_status,
            notes=decision.notes or "",
            item_code=decision.item_code,
            project_name=f"Project {decision.project_id}",
            supplier_name="Unknown Supplier",
            status="sent" if decision.actual_invoice_issue_date else "draft",
            created_at=decision.created_at,
            updated_at=decision.updated_at
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create invoice: {str(e)}")

@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(invoice_id: int, invoice: InvoiceUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing invoice"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an invoice"""
    try:
        # Find the decision
        result = await db.execute(
            select(FinalizedDecision).where(FinalizedDecision.id == invoice_id)
        )
        decision = result.scalar_one_or_none()
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Clear invoice data from the decision
        decision.actual_invoice_issue_date = None
        decision.actual_invoice_amount = None
        decision.actual_invoice_amount_currency = None
        decision.actual_invoice_received_date = None
        decision.payment_terms = None
        
        await db.commit()
        
        return {"message": "Invoice deleted successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete invoice: {str(e)}")

# Payment Management
@router.get("/payments", response_model=List[PaymentResponse])
async def list_payments(
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List payments with filtering and pagination"""
    # Query finalized decisions that have payment data
    query = select(FinalizedDecision).where(
        FinalizedDecision.actual_payment_date.isnot(None)
    )
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                FinalizedDecision.item_code.ilike(f"%{search}%"),
                FinalizedDecision.notes.ilike(f"%{search}%")
            )
        )
    
    if project_id:
        query = query.where(FinalizedDecision.project_id == project_id)
    
    if start_date and isinstance(start_date, str) and start_date.strip():
        query = query.where(FinalizedDecision.actual_payment_date >= datetime.fromisoformat(start_date).date())
    
    if end_date and isinstance(end_date, str) and end_date.strip():
        query = query.where(FinalizedDecision.actual_payment_date <= datetime.fromisoformat(end_date).date())
    
    # Apply pagination
    page_num = page if isinstance(page, int) else 1
    limit_num = limit if isinstance(limit, int) else 50
    offset = (page_num - 1) * limit_num
    result = await db.execute(query.offset(offset).limit(limit_num))
    decisions = result.scalars().all()
    
    # Convert to PaymentResponse format
    payments = []
    for decision in decisions:
        payment = PaymentResponse(
            id=decision.id,
            invoice_id=decision.id,  # Using decision ID as invoice ID for now
            decision_id=decision.id,
            payment_date=decision.actual_payment_date.isoformat() if decision.actual_payment_date else "",
            payment_amount=float(decision.actual_payment_amount) if decision.actual_payment_amount else 0.0,
            currency=decision.actual_payment_amount_currency or "IRR",
            payment_method="bank_transfer",  # Default payment method
            reference_number=f"PAY-{decision.id:06d}",
            notes=decision.notes or "",
            item_code=decision.item_code,
            project_name=f"Project {decision.project_id}",
            supplier_name="Unknown Supplier",
            status="completed" if decision.actual_payment_date else "pending",
            created_at=decision.created_at,
            updated_at=decision.updated_at
        )
        payments.append(payment)
    
    return payments

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific payment by ID"""
    raise HTTPException(status_code=404, detail="Payment not found")

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(payment: PaymentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new payment"""
    try:
        # Find the decision (using invoice_id as decision_id for now)
        result = await db.execute(
            select(FinalizedDecision).where(FinalizedDecision.id == payment.invoice_id)
        )
        decision = result.scalar_one_or_none()
        
        if not decision:
            raise HTTPException(status_code=404, detail="Decision not found")
        
        # Update the decision with payment data
        decision.actual_payment_date = datetime.fromisoformat(payment.payment_date).date()
        decision.actual_payment_amount = payment.payment_amount
        decision.actual_payment_amount_currency = payment.currency
        if payment.reference_number:
            decision.notes = f"{decision.notes or ''}\nPayment Ref: {payment.reference_number}".strip()
        if payment.notes:
            decision.notes = f"{decision.notes or ''}\nPayment Notes: {payment.notes}".strip()
        
        await db.commit()
        await db.refresh(decision)
        
        # Create cash flow event directly without using the sync service
        try:
            from app.models import CashflowEvent
            
            # Create INFLOW event directly
            inflow_event = CashflowEvent(
                related_decision_id=decision.id,
                event_type='INFLOW',
                forecast_type='ACTUAL',
                event_date=decision.actual_payment_date,  # Use date object directly, not string
                amount_value=float(decision.actual_payment_amount) if decision.actual_payment_amount else 0.0,
                amount_currency=decision.actual_payment_amount_currency or "IRR",
                amount=float(decision.actual_payment_amount) if decision.actual_payment_amount else 0.0,  # Legacy field
                description=f"Payment received for {decision.item_code} - Invoice INV-{decision.id:06d}"
            )
            
            db.add(inflow_event)
            await db.commit()
            print(f"Created INFLOW event for payment {decision.id}: {decision.actual_payment_amount} {decision.actual_payment_amount_currency}")
            
        except Exception as e:
            # Log error but don't fail the payment creation
            print(f"Warning: Failed to create cash flow event: {str(e)}")
        
        # Return the updated decision as a payment response
        # Use current datetime to avoid async context issues
        current_time = datetime.now()
        
        return PaymentResponse(
            id=decision.id,
            invoice_id=decision.id,
            decision_id=decision.id,
            payment_date=decision.actual_payment_date.isoformat() if decision.actual_payment_date else "",
            payment_amount=float(decision.actual_payment_amount) if decision.actual_payment_amount else 0.0,
            currency=decision.actual_payment_amount_currency or "IRR",
            payment_method=payment.payment_method,
            reference_number=payment.reference_number or f"PAY-{decision.id:06d}",
            notes=payment.notes or "",
            item_code=decision.item_code,
            project_name=f"Project {decision.project_id}",
            supplier_name="Unknown Supplier",
            status="completed" if decision.actual_payment_date else "pending",
            created_at=current_time.isoformat(),
            updated_at=current_time.isoformat()
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {str(e)}")

@router.put("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(payment_id: int, payment: PaymentUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing payment"""
    raise HTTPException(status_code=501, detail="Not implemented yet")

@router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a payment by clearing payment data from the decision"""
    # Find the decision that has this payment
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == payment_id)
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Clear payment data from the decision
    decision.actual_payment_date = None
    decision.actual_payment_amount = None
    decision.actual_payment_currency = None
    decision.actual_payment_method = None
    decision.actual_payment_reference = None
    decision.actual_payment_notes = None
    
    await db.commit()
    
    # Remove from cash flow system
    try:
        cashflow_service = CashflowSyncService(db)
        await cashflow_service.remove_payment_sync(payment_id, 'in')
    except Exception as e:
        # Log error but don't fail the payment deletion
        print(f"Warning: Failed to remove payment from cash flow: {str(e)}")
    
    return {"message": "Payment deleted successfully"}

# Summary endpoints
@router.get("/summary", response_model=InvoicePaymentSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Get invoice and payment summary statistics"""
    # Count invoices (decisions with invoice data)
    invoice_query = select(FinalizedDecision).where(
        FinalizedDecision.actual_invoice_issue_date.isnot(None)
    )
    invoice_result = await db.execute(invoice_query)
    invoices = invoice_result.scalars().all()
    
    # Count payments (decisions with payment data)
    payment_query = select(FinalizedDecision).where(
        FinalizedDecision.actual_payment_date.isnot(None)
    )
    payment_result = await db.execute(payment_query)
    payments = payment_result.scalars().all()
    
    # Calculate totals
    total_invoices = len(invoices)
    total_payments = len(payments)
    total_invoice_amount = sum(float(inv.actual_invoice_amount or 0) for inv in invoices)
    total_payment_amount = sum(float(pay.actual_payment_amount or 0) for pay in payments)
    
    return InvoicePaymentSummary(
        total_invoices=total_invoices,
        total_payments=total_payments,
        paid_invoices=total_payments,  # Assuming all payments are for paid invoices
        pending_invoices=max(0, total_invoices - total_payments),
        overdue_invoices=0,  # Would need to check due dates
        total_invoice_amount=total_invoice_amount,
        total_payment_amount=total_payment_amount,
        pending_payment_amount=max(0, total_invoice_amount - total_payment_amount)
    )
