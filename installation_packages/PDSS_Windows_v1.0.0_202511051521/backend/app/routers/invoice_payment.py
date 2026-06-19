from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, desc, asc, select
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import io

from app.database import get_db
from app.models_invoice_payment import Invoice, Payment, InvoiceStatus, PaymentStatus, PaymentMethod
from app.models import FinalizedDecision
from app.schemas import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    PaymentCreate, PaymentUpdate, PaymentResponse,
    InvoicePaymentSummary
)

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
    query = select(Invoice).join(FinalizedDecision)
    
    # Apply filters
    if search:
        query = query.where(
            or_(
                Invoice.invoice_number.ilike(f"%{search}%"),
                Invoice.notes.ilike(f"%{search}%")
            )
        )
    
    if status:
        query = query.where(Invoice.status == status)
    
    if project_id:
        query = query.where(FinalizedDecision.project_id == project_id)
    
    if start_date:
        query = query.where(Invoice.invoice_date >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.where(Invoice.invoice_date <= datetime.fromisoformat(end_date))
    
    # Apply pagination
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    invoices = result.scalars().all()
    
    return invoices

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get a specific invoice by ID"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate, db: Session = Depends(get_db)):
    """Create a new invoice"""
    # Verify decision exists
    decision = db.query(FinalizedDecision).filter(FinalizedDecision.id == invoice_data.decision_id).first()
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    
    # Check if invoice number already exists
    existing_invoice = db.query(Invoice).filter(Invoice.invoice_number == invoice_data.invoice_number).first()
    if existing_invoice:
        raise HTTPException(status_code=400, detail="Invoice number already exists")
    
    # Create invoice
    invoice = Invoice(
        decision_id=invoice_data.decision_id,
        invoice_number=invoice_data.invoice_number,
        invoice_date=datetime.fromisoformat(invoice_data.invoice_date),
        invoice_amount=invoice_data.invoice_amount,
        currency=invoice_data.currency,
        due_date=datetime.fromisoformat(invoice_data.due_date),
        payment_terms=invoice_data.payment_terms,
        notes=invoice_data.notes
    )
    
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice

@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int, 
    invoice_data: InvoiceUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update fields
    for field, value in invoice_data.dict(exclude_unset=True).items():
        if field in ['invoice_date', 'due_date'] and value:
            setattr(invoice, field, datetime.fromisoformat(value))
        else:
            setattr(invoice, field, value)
    
    db.commit()
    db.refresh(invoice)
    
    return invoice

@router.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Delete an invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Check if invoice has payments
    payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).count()
    if payments > 0:
        raise HTTPException(status_code=400, detail="Cannot delete invoice with existing payments")
    
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}

@router.post("/invoices/{invoice_id}/mark-sent")
async def mark_invoice_as_sent(invoice_id: int, db: Session = Depends(get_db)):
    """Mark invoice as sent"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = InvoiceStatus.SENT
    db.commit()
    
    return {"message": "Invoice marked as sent"}

@router.post("/invoices/{invoice_id}/mark-paid")
async def mark_invoice_as_paid(invoice_id: int, db: Session = Depends(get_db)):
    """Mark invoice as paid"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice.status = InvoiceStatus.PAID
    db.commit()
    
    return {"message": "Invoice marked as paid"}

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
    db: Session = Depends(get_db)
):
    """List payments with filtering and pagination"""
    query = db.query(Payment).join(FinalizedDecision)
    
    # Apply filters
    if search:
        query = query.filter(
            or_(
                Payment.reference_number.ilike(f"%{search}%"),
                Payment.notes.ilike(f"%{search}%")
            )
        )
    
    if status:
        query = query.filter(Payment.status == status)
    
    if project_id:
        query = query.filter(FinalizedDecision.project_id == project_id)
    
    if start_date:
        query = query.filter(Payment.payment_date >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Payment.payment_date <= datetime.fromisoformat(end_date))
    
    # Apply pagination
    offset = (page - 1) * limit
    payments = query.offset(offset).limit(limit).all()
    
    return payments

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get a specific payment by ID"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment

@router.post("/payments", response_model=PaymentResponse)
async def create_payment(payment_data: PaymentCreate, db: Session = Depends(get_db)):
    """Create a new payment"""
    # Verify invoice exists
    invoice = db.query(Invoice).filter(Invoice.id == payment_data.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Create payment
    payment = Payment(
        invoice_id=payment_data.invoice_id,
        decision_id=invoice.decision_id,
        payment_date=datetime.fromisoformat(payment_data.payment_date),
        payment_amount=payment_data.payment_amount,
        currency=payment_data.currency,
        payment_method=payment_data.payment_method,
        reference_number=payment_data.reference_number,
        notes=payment_data.notes
    )
    
    db.add(payment)
    db.commit()
    db.refresh(payment)
    
    return payment

@router.put("/payments/{payment_id}", response_model=PaymentResponse)
async def update_payment(
    payment_id: int, 
    payment_data: PaymentUpdate, 
    db: Session = Depends(get_db)
):
    """Update an existing payment"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Update fields
    for field, value in payment_data.dict(exclude_unset=True).items():
        if field == 'payment_date' and value:
            setattr(payment, field, datetime.fromisoformat(value))
        else:
            setattr(payment, field, value)
    
    db.commit()
    db.refresh(payment)
    
    return payment

@router.delete("/payments/{payment_id}")
async def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    """Delete a payment"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    db.delete(payment)
    db.commit()
    
    return {"message": "Payment deleted successfully"}

@router.post("/payments/{payment_id}/mark-completed")
async def mark_payment_as_completed(payment_id: int, db: Session = Depends(get_db)):
    """Mark payment as completed"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment.status = PaymentStatus.COMPLETED
    db.commit()
    
    return {"message": "Payment marked as completed"}

@router.post("/payments/{payment_id}/mark-failed")
async def mark_payment_as_failed(payment_id: int, db: Session = Depends(get_db)):
    """Mark payment as failed"""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    payment.status = PaymentStatus.FAILED
    db.commit()
    
    return {"message": "Payment marked as failed"}

# Summary and Analytics
@router.get("/summary", response_model=InvoicePaymentSummary)
async def get_summary(db: Session = Depends(get_db)):
    """Get invoice and payment summary statistics"""
    total_invoices = db.query(Invoice).count()
    total_payments = db.query(Payment).count()
    paid_invoices = db.query(Invoice).filter(Invoice.status == InvoiceStatus.PAID).count()
    pending_invoices = db.query(Invoice).filter(Invoice.status == InvoiceStatus.SENT).count()
    overdue_invoices = db.query(Invoice).filter(Invoice.status == InvoiceStatus.OVERDUE).count()
    
    # Calculate amounts
    total_invoice_amount = db.query(Invoice).with_entities(
        db.func.sum(Invoice.invoice_amount)
    ).scalar() or 0
    
    total_payment_amount = db.query(Payment).filter(
        Payment.status == PaymentStatus.COMPLETED
    ).with_entities(
        db.func.sum(Payment.payment_amount)
    ).scalar() or 0
    
    pending_payment_amount = db.query(Payment).filter(
        Payment.status == PaymentStatus.PENDING
    ).with_entities(
        db.func.sum(Payment.payment_amount)
    ).scalar() or 0
    
    return InvoicePaymentSummary(
        total_invoices=total_invoices,
        total_payments=total_payments,
        paid_invoices=paid_invoices,
        pending_invoices=pending_invoices,
        overdue_invoices=overdue_invoices,
        total_invoice_amount=float(total_invoice_amount),
        total_payment_amount=float(total_payment_amount),
        pending_payment_amount=float(pending_payment_amount)
    )

# Export functionality
@router.get("/invoices/export")
async def export_invoices(
    format: str = Query("excel", regex="^(excel|csv)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Export invoices to Excel or CSV"""
    query = db.query(Invoice).join(FinalizedDecision)
    
    if start_date:
        query = query.filter(Invoice.invoice_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Invoice.invoice_date <= datetime.fromisoformat(end_date))
    
    invoices = query.all()
    
    # Convert to DataFrame
    data = []
    for invoice in invoices:
        data.append({
            'Invoice Number': invoice.invoice_number,
            'Decision ID': invoice.decision_id,
            'Invoice Date': invoice.invoice_date.strftime('%Y-%m-%d'),
            'Amount': float(invoice.invoice_amount),
            'Currency': invoice.currency,
            'Due Date': invoice.due_date.strftime('%Y-%m-%d'),
            'Status': invoice.status.value,
            'Payment Terms': invoice.payment_terms,
            'Notes': invoice.notes
        })
    
    df = pd.DataFrame(data)
    
    if format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Invoices', index=False)
        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=invoices.xlsx"}
        )
    else:  # CSV
        csv_data = df.to_csv(index=False)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=invoices.csv"}
        )

@router.get("/payments/export")
async def export_payments(
    format: str = Query("excel", regex="^(excel|csv)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Export payments to Excel or CSV"""
    query = db.query(Payment).join(FinalizedDecision)
    
    if start_date:
        query = query.filter(Payment.payment_date >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Payment.payment_date <= datetime.fromisoformat(end_date))
    
    payments = query.all()
    
    # Convert to DataFrame
    data = []
    for payment in payments:
        data.append({
            'Reference Number': payment.reference_number,
            'Invoice ID': payment.invoice_id,
            'Decision ID': payment.decision_id,
            'Payment Date': payment.payment_date.strftime('%Y-%m-%d'),
            'Amount': float(payment.payment_amount),
            'Currency': payment.currency,
            'Payment Method': payment.payment_method.value,
            'Status': payment.status.value,
            'Notes': payment.notes
        })
    
    df = pd.DataFrame(data)
    
    if format == "excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Payments', index=False)
        output.seek(0)
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=payments.xlsx"}
        )
    else:  # CSV
        csv_data = df.to_csv(index=False)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=payments.csv"}
        )
