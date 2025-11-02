"""
Cash Flow Synchronization Service
Integrates payments in/out data with the existing cash flow system
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import date
from decimal import Decimal
from app.models import CashflowEvent, FinalizedDecision, SupplierPayment
from app.schemas import PaymentResponse, InvoiceResponse
import logging

logger = logging.getLogger(__name__)


class CashflowSyncService:
    """Service to synchronize payments in/out with cash flow events"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_payment_in(self, payment: PaymentResponse) -> Optional[CashflowEvent]:
        """
        Create or update INFLOW cash flow event for payment received
        """
        try:
            # Find the related decision
            decision_result = await self.db.execute(
                select(FinalizedDecision).where(FinalizedDecision.id == payment.decision_id)
            )
            decision = decision_result.scalar_one_or_none()
            
            if not decision:
                logger.warning(f"Decision {payment.decision_id} not found for payment {payment.id}")
                return None
            
            # Check if cash flow event already exists for this payment
            existing_event = await self.db.execute(
                select(CashflowEvent).where(
                    CashflowEvent.related_decision_id == payment.decision_id,
                    CashflowEvent.event_type == 'INFLOW',
                    CashflowEvent.forecast_type == 'ACTUAL',
                    CashflowEvent.event_date == payment.payment_date,
                    CashflowEvent.amount_value == payment.payment_amount
                )
            )
            existing = existing_event.scalar_one_or_none()
            
            if existing:
                # Update existing event
                existing.amount_value = payment.payment_amount
                existing.amount_currency = payment.currency
                existing.description = f"Payment received for {decision.item_code} - Invoice {payment.invoice_number}"
                await self.db.commit()
                return existing
            
            # Create new INFLOW event
            inflow_event = CashflowEvent(
                related_decision_id=payment.decision_id,
                event_type='INFLOW',
                forecast_type='ACTUAL',
                event_date=payment.payment_date,
                amount_value=payment.payment_amount,
                amount_currency=payment.currency,
                amount=payment.payment_amount,  # Legacy field
                description=f"Payment received for {decision.item_code} - Invoice {payment.invoice_number}"
            )
            
            self.db.add(inflow_event)
            await self.db.commit()
            await self.db.refresh(inflow_event)
            
            logger.info(f"Created INFLOW event for payment {payment.id}: {payment.payment_amount} {payment.currency}")
            return inflow_event
            
        except Exception as e:
            logger.error(f"Error syncing payment in {payment.id}: {str(e)}")
            await self.db.rollback()
            return None
    
    async def sync_payment_in_simple(self, payment_data: dict) -> Optional[CashflowEvent]:
        """
        Create or update INFLOW cash flow event for payment received (simplified version)
        """
        try:
            # Use the item_code from payment_data instead of querying the decision
            item_code = payment_data.get('item_code', 'Unknown Item')
            invoice_number = payment_data.get('invoice_number', 'N/A')
            
            # Check if cash flow event already exists for this payment
            existing_event = await self.db.execute(
                select(CashflowEvent).where(
                    CashflowEvent.related_decision_id == payment_data['decision_id'],
                    CashflowEvent.event_type == 'INFLOW',
                    CashflowEvent.forecast_type == 'ACTUAL',
                    CashflowEvent.event_date == payment_data['payment_date'],
                    CashflowEvent.amount_value == payment_data['payment_amount']
                )
            )
            existing = existing_event.scalar_one_or_none()
            
            if existing:
                # Update existing event
                existing.amount_value = payment_data['payment_amount']
                existing.amount_currency = payment_data['currency']
                existing.description = f"Payment received for {item_code} - Invoice {invoice_number}"
                await self.db.commit()
                return existing
            
            # Create new INFLOW event
            inflow_event = CashflowEvent(
                related_decision_id=payment_data['decision_id'],
                event_type='INFLOW',
                forecast_type='ACTUAL',
                event_date=payment_data['payment_date'],
                amount_value=payment_data['payment_amount'],
                amount_currency=payment_data['currency'],
                amount=payment_data['payment_amount'],  # Legacy field
                description=f"Payment received for {item_code} - Invoice {invoice_number}"
            )
            
            self.db.add(inflow_event)
            await self.db.commit()
            await self.db.refresh(inflow_event)
            
            logger.info(f"Created INFLOW event for payment {payment_data['id']}: {payment_data['payment_amount']} {payment_data['currency']}")
            return inflow_event
            
        except Exception as e:
            logger.error(f"Error syncing payment in {payment_data['id']}: {str(e)}")
            await self.db.rollback()
            return None
    
    async def sync_payment_out(self, supplier_payment: SupplierPayment) -> Optional[CashflowEvent]:
        """
        Create or update OUTFLOW cash flow event for supplier payment
        """
        try:
            # Check if cash flow event already exists for this supplier payment
            existing_event = await self.db.execute(
                select(CashflowEvent).where(
                    CashflowEvent.related_decision_id == supplier_payment.decision_id,
                    CashflowEvent.event_type == 'OUTFLOW',
                    CashflowEvent.forecast_type == 'ACTUAL',
                    CashflowEvent.event_date == supplier_payment.payment_date,
                    CashflowEvent.amount_value == supplier_payment.payment_amount
                )
            )
            existing = existing_event.scalar_one_or_none()
            
            if existing:
                # Update existing event
                existing.amount_value = supplier_payment.payment_amount
                existing.amount_currency = supplier_payment.currency
                existing.description = f"Payment to {supplier_payment.supplier_name} for {supplier_payment.item_code}"
                await self.db.commit()
                return existing
            
            # Create new OUTFLOW event
            outflow_event = CashflowEvent(
                related_decision_id=supplier_payment.decision_id,
                event_type='OUTFLOW',
                forecast_type='ACTUAL',
                event_date=supplier_payment.payment_date,
                amount_value=supplier_payment.payment_amount,
                amount_currency=supplier_payment.currency,
                amount=supplier_payment.payment_amount,  # Legacy field
                description=f"Payment to {supplier_payment.supplier_name} for {supplier_payment.item_code}"
            )
            
            self.db.add(outflow_event)
            await self.db.commit()
            await self.db.refresh(outflow_event)
            
            logger.info(f"Created OUTFLOW event for supplier payment {supplier_payment.id}: {supplier_payment.payment_amount} {supplier_payment.currency}")
            return outflow_event
            
        except Exception as e:
            logger.error(f"Error syncing supplier payment {supplier_payment.id}: {str(e)}")
            await self.db.rollback()
            return None
    
    async def sync_invoice_received(self, invoice: InvoiceResponse) -> Optional[CashflowEvent]:
        """
        Create INFLOW cash flow event when invoice is received
        """
        try:
            # Find the related decision
            decision_result = await self.db.execute(
                select(FinalizedDecision).where(FinalizedDecision.id == invoice.decision_id)
            )
            decision = decision_result.scalar_one_or_none()
            
            if not decision:
                logger.warning(f"Decision {invoice.decision_id} not found for invoice {invoice.id}")
                return None
            
            # Check if cash flow event already exists for this invoice
            existing_event = await self.db.execute(
                select(CashflowEvent).where(
                    CashflowEvent.related_decision_id == invoice.decision_id,
                    CashflowEvent.event_type == 'INFLOW',
                    CashflowEvent.forecast_type == 'ACTUAL',
                    CashflowEvent.event_date == invoice.invoice_date,
                    CashflowEvent.amount_value == invoice.invoice_amount
                )
            )
            existing = existing_event.scalar_one_or_none()
            
            if existing:
                # Update existing event
                existing.amount_value = invoice.invoice_amount
                existing.amount_currency = invoice.currency
                existing.description = f"Invoice received for {decision.item_code} - {invoice.invoice_number}"
                await self.db.commit()
                return existing
            
            # Create new INFLOW event for invoice received
            inflow_event = CashflowEvent(
                related_decision_id=invoice.decision_id,
                event_type='INFLOW',
                forecast_type='ACTUAL',
                event_date=invoice.invoice_date,
                amount_value=invoice.invoice_amount,
                amount_currency=invoice.currency,
                amount=invoice.invoice_amount,  # Legacy field
                description=f"Invoice received for {decision.item_code} - {invoice.invoice_number}"
            )
            
            self.db.add(inflow_event)
            await self.db.commit()
            await self.db.refresh(inflow_event)
            
            logger.info(f"Created INFLOW event for invoice {invoice.id}: {invoice.invoice_amount} {invoice.currency}")
            return inflow_event
            
        except Exception as e:
            logger.error(f"Error syncing invoice {invoice.id}: {str(e)}")
            await self.db.rollback()
            return None
    
    async def remove_payment_sync(self, payment_id: int, payment_type: str = 'in') -> bool:
        """
        Remove cash flow events when payments are deleted
        """
        try:
            if payment_type == 'in':
                # Remove INFLOW events for payment in
                await self.db.execute(
                    delete(CashflowEvent).where(
                        CashflowEvent.description.like(f"%Payment received%"),
                        CashflowEvent.event_type == 'INFLOW',
                        CashflowEvent.forecast_type == 'ACTUAL'
                    )
                )
            else:
                # Remove OUTFLOW events for payment out
                await self.db.execute(
                    delete(CashflowEvent).where(
                        CashflowEvent.description.like(f"%Payment to%"),
                        CashflowEvent.event_type == 'OUTFLOW',
                        CashflowEvent.forecast_type == 'ACTUAL'
                    )
                )
            
            await self.db.commit()
            logger.info(f"Removed cash flow events for {payment_type} payment {payment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing cash flow sync for payment {payment_id}: {str(e)}")
            await self.db.rollback()
            return False
    
    async def sync_all_payments(self) -> dict:
        """
        Sync all existing payments with cash flow events
        """
        try:
            # Get all payments in (from FinalizedDecision with payment data)
            payments_in_result = await self.db.execute(
                select(FinalizedDecision).where(
                    FinalizedDecision.actual_payment_date.isnot(None),
                    FinalizedDecision.actual_payment_amount_value.isnot(None)
                )
            )
            payments_in = payments_in_result.scalars().all()
            
            # Get all supplier payments
            supplier_payments_result = await self.db.execute(
                select(SupplierPayment)
            )
            supplier_payments = supplier_payments_result.scalars().all()
            
            # Get all invoices (from FinalizedDecision with invoice data)
            invoices_result = await self.db.execute(
                select(FinalizedDecision).where(
                    FinalizedDecision.actual_invoice_issue_date.isnot(None),
                    FinalizedDecision.actual_invoice_amount_value.isnot(None)
                )
            )
            invoices = invoices_result.scalars().all()
            
            synced_count = 0
            errors = []
            
            # Sync payments in
            for decision in payments_in:
                try:
                    # Create PaymentResponse-like object from FinalizedDecision
                    payment_data = PaymentResponse(
                        id=decision.id,
                        invoice_id=decision.id,
                        decision_id=decision.id,
                        payment_date=decision.actual_payment_date.isoformat() if decision.actual_payment_date else "",
                        payment_amount=float(decision.actual_payment_amount_value) if decision.actual_payment_amount_value else 0.0,
                        currency=decision.actual_payment_amount_currency or "IRR",
                        payment_method=decision.actual_payment_method or "bank_transfer",
                        reference_number=decision.actual_payment_reference or f"PAY-{decision.id:06d}",
                        notes=decision.actual_payment_notes or "",
                        item_code=decision.item_code,
                        project_name=f"Project {decision.project_id}",
                        supplier_name="Unknown Supplier",
                        status="completed" if decision.actual_payment_date else "pending",
                        created_at=decision.created_at,
                        updated_at=decision.updated_at
                    )
                    await self.sync_payment_in(payment_data)
                    synced_count += 1
                except Exception as e:
                    errors.append(f"Payment in {decision.id}: {str(e)}")
            
            # Sync supplier payments
            for supplier_payment in supplier_payments:
                try:
                    await self.sync_payment_out(supplier_payment)
                    synced_count += 1
                except Exception as e:
                    errors.append(f"Supplier payment {supplier_payment.id}: {str(e)}")
            
            # Sync invoices
            for decision in invoices:
                try:
                    # Create InvoiceResponse-like object from FinalizedDecision
                    invoice_data = InvoiceResponse(
                        id=decision.id,
                        decision_id=decision.id,
                        invoice_number=f"INV-{decision.id:06d}",  # Use decision ID as invoice number
                        invoice_date=decision.actual_invoice_issue_date.isoformat() if decision.actual_invoice_issue_date else "",
                        invoice_amount=float(decision.actual_invoice_amount_value) if decision.actual_invoice_amount_value else 0.0,
                        currency=decision.actual_invoice_amount_currency or "IRR",
                        due_date=decision.actual_invoice_received_date.isoformat() if decision.actual_invoice_received_date else "",
                        item_code=decision.item_code,
                        project_name=f"Project {decision.project_id}",
                        supplier_name="Unknown Supplier",
                        status="received" if decision.actual_invoice_received_date else "pending",
                        created_at=decision.created_at,
                        updated_at=decision.updated_at
                    )
                    await self.sync_invoice_received(invoice_data)
                    synced_count += 1
                except Exception as e:
                    errors.append(f"Invoice {decision.id}: {str(e)}")
            
            return {
                'synced_count': synced_count,
                'errors': errors,
                'success': len(errors) == 0
            }
            
        except Exception as e:
            logger.error(f"Error syncing all payments: {str(e)}")
            return {
                'synced_count': 0,
                'errors': [str(e)],
                'success': False
            }
