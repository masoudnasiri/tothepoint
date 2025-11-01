"""
Finalized decisions management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func as sql_func, or_
from sqlalchemy.orm import selectinload
from datetime import datetime, date, timedelta
import uuid
from app.database import get_db
from app.auth import get_current_user, require_pm, require_finance
from app.models import User, FinalizedDecision, ProjectItem, ProcurementOption, OptimizationRun, CashflowEvent, OptimizationResult, DeliveryOption
from app import schemas
from app.schemas import (
    FinalizedDecision as FinalizedDecisionSchema, 
    FinalizedDecisionCreate, 
    FinalizedDecisionUpdate, 
    CashflowEventCreate,
    FinalizeDecisionsRequest,
    BatchSaveDecisionsRequest,
    ActualInvoiceDataRequest,
    ActualPaymentDataRequest,
    DecisionStatusUpdate
)
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/decisions", tags=["finalized-decisions"])


@router.get("/", response_model=List[FinalizedDecisionSchema])
async def list_finalized_decisions(
    skip: int = 0,
    limit: int = 100,  # Default pagination size
    run_id: Optional[str] = None,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    hide_superseded: bool = True,
    search: Optional[str] = None,  # New search parameter
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all finalized decisions with optional filtering and search
    
    Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (default: 100, max: 1000)
    - hide_superseded: If True (default), hides REVERTED decisions that have been superseded by new decisions
    - status: Filter by status (PROPOSED, LOCKED, REVERTED)
    - search: Search in item_code, notes, and supplier information
    """
    query = select(FinalizedDecision)
    
    if run_id:
        query = query.where(FinalizedDecision.run_id == uuid.UUID(run_id))
    
    if project_id:
        query = query.join(ProjectItem).where(ProjectItem.project_id == project_id)
    
    if status:
        query = query.where(FinalizedDecision.status == status)
    
    # Add search functionality
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                FinalizedDecision.item_code.ilike(search_term),
                FinalizedDecision.notes.ilike(search_term),
                # Search in procurement option supplier name through join
                FinalizedDecision.procurement_option_id.in_(
                    select(ProcurementOption.id)
                    .where(ProcurementOption.supplier_name.ilike(search_term))
                )
            )
        )
    
    # ✅ FIX: Hide old superseded REVERTED decisions by default
    if hide_superseded:
        query = query.where(
            or_(
                FinalizedDecision.status != 'REVERTED',
                ~FinalizedDecision.notes.contains('[SUPERSEDED]')
            )
        )
    
    result = await db.execute(
        query.offset(skip).limit(limit).order_by(FinalizedDecision.decision_date.desc())
    )
    return result.scalars().all()


@router.get("/count")
async def count_finalized_decisions(
    run_id: Optional[str] = None,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    hide_superseded: bool = True,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get total count of finalized decisions for pagination"""
    query = select(sql_func.count(FinalizedDecision.id))
    
    if run_id:
        query = query.where(FinalizedDecision.run_id == uuid.UUID(run_id))
    
    if project_id:
        query = query.join(ProjectItem).where(ProjectItem.project_id == project_id)
    
    if status:
        query = query.where(FinalizedDecision.status == status)
    
    # Add search functionality
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                FinalizedDecision.item_code.ilike(search_term),
                FinalizedDecision.notes.ilike(search_term),
                # Search in procurement option supplier name through join
                FinalizedDecision.procurement_option_id.in_(
                    select(ProcurementOption.id)
                    .where(ProcurementOption.supplier_name.ilike(search_term))
                )
            )
        )
    
    # ✅ FIX: Hide old superseded REVERTED decisions by default
    if hide_superseded:
        query = query.where(
            or_(
                FinalizedDecision.status != 'REVERTED',
                ~FinalizedDecision.notes.contains('[SUPERSEDED]')
            )
        )
    
    result = await db.execute(query)
    return {"count": result.scalar()}


@router.get("/summary")
async def get_finalized_decisions_summary(
    run_id: Optional[str] = None,
    project_id: Optional[int] = None,
    hide_superseded: bool = True,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get summary statistics for all finalized decisions"""
    from sqlalchemy import case
    
    # Base query with filters
    base_query = select(FinalizedDecision)
    
    if run_id:
        base_query = base_query.where(FinalizedDecision.run_id == uuid.UUID(run_id))
    
    if project_id:
        base_query = base_query.join(ProjectItem).where(ProjectItem.project_id == project_id)
    
    # Add search functionality
    if search:
        search_term = f"%{search}%"
        base_query = base_query.where(
            or_(
                FinalizedDecision.item_code.ilike(search_term),
                FinalizedDecision.notes.ilike(search_term),
                # Search in procurement option supplier name through join
                FinalizedDecision.procurement_option_id.in_(
                    select(ProcurementOption.id)
                    .where(ProcurementOption.supplier_name.ilike(search_term))
                )
            )
        )
    
    # ✅ FIX: Hide old superseded REVERTED decisions by default
    if hide_superseded:
        base_query = base_query.where(
            or_(
                FinalizedDecision.status != 'REVERTED',
                ~FinalizedDecision.notes.contains('[SUPERSEDED]')
            )
        )
    
    # Get summary statistics
    summary_query = select(
        sql_func.count(FinalizedDecision.id).label('total'),
        sql_func.count(case((FinalizedDecision.status == 'LOCKED', 1))).label('locked'),
        sql_func.count(case((FinalizedDecision.status == 'PROPOSED', 1))).label('proposed'),
        sql_func.count(case((FinalizedDecision.status == 'REVERTED', 1))).label('reverted'),
        sql_func.count(case((FinalizedDecision.actual_invoice_amount > 0, 1))).label('invoiced'),
        sql_func.count(case((FinalizedDecision.actual_invoice_amount == 0, 1))).label('not_invoiced'),
        sql_func.count(case((FinalizedDecision.actual_payment_amount >= FinalizedDecision.final_cost, 1))).label('fully_paid'),
        sql_func.count(case((FinalizedDecision.actual_payment_amount == 0, 1))).label('not_paid')
    ).select_from(base_query.subquery())
    
    result = await db.execute(summary_query)
    row = result.first()
    
    return {
        "total": row.total,
        "locked": row.locked,
        "proposed": row.proposed,
        "reverted": row.reverted,
        "invoiced": row.invoiced,
        "not_invoiced": row.not_invoiced,
        "fully_paid": row.fully_paid,
        "not_paid": row.not_paid
    }


@router.post("/", response_model=dict)
async def save_optimization_results(
    decisions: List[FinalizedDecisionCreate],
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Save a list of finalized decisions from an optimization run and generate cash flow events"""
    saved_count = 0
    cashflow_events_count = 0
    
    try:
        for decision_data in decisions:
            # Create FinalizedDecision record with all fields
            decision = FinalizedDecision(
                run_id=decision_data.run_id,
                project_id=decision_data.project_id,
                project_item_id=decision_data.project_item_id,
                item_code=decision_data.item_code,
                procurement_option_id=decision_data.procurement_option_id,
                purchase_date=decision_data.purchase_date,
                delivery_date=decision_data.delivery_date,
                quantity=decision_data.quantity,
                final_cost=decision_data.final_cost,
                decision_maker_id=current_user.id,
                decision_date=decision_data.decision_date,
                status=decision_data.status or 'PROPOSED',
                is_manual_edit=decision_data.is_manual_edit,
                notes=decision_data.notes,
                # Forecast invoice fields
                delivery_option_id=decision_data.delivery_option_id,
                forecast_invoice_timing_type=decision_data.forecast_invoice_timing_type or 'RELATIVE',
                forecast_invoice_issue_date=decision_data.forecast_invoice_issue_date,
                forecast_invoice_days_after_delivery=decision_data.forecast_invoice_days_after_delivery or 30,
                forecast_invoice_amount=decision_data.forecast_invoice_amount
            )
            db.add(decision)
            await db.flush()  # Get the decision ID
            
            # Fetch the procurement option to get payment terms
            result = await db.execute(
                select(ProcurementOption).where(
                    ProcurementOption.id == decision_data.procurement_option_id
                )
            )
            proc_option = result.scalar_one_or_none()
            
            if proc_option:
                # Generate FORECAST cash outflow events based on payment_terms
                payment_terms = proc_option.payment_terms
                
                if isinstance(payment_terms, dict):
                    payment_type = payment_terms.get('type', 'cash')
                    
                    if payment_type == 'cash':
                        # Single outflow on purchase date
                        discount = payment_terms.get('discount_percent', 0)
                        amount = decision_data.final_cost * (1 - Decimal(discount) / 100)
                        
                        outflow = CashflowEvent(
                            related_decision_id=decision.id,
                            event_type='OUTFLOW',
                            forecast_type='FORECAST',
                            event_date=decision_data.purchase_date,
                            amount=amount,
                            description=f"Payment for {decision_data.item_code} (Cash, {discount}% discount)"
                        )
                        db.add(outflow)
                        cashflow_events_count += 1
                    
                    elif payment_type == 'installments':
                        # Multiple installments
                        schedule = payment_terms.get('schedule', [])
                        
                        for installment in schedule:
                            due_offset = installment.get('due_offset', 0)
                            percent = installment.get('percent', 0)
                            amount = decision_data.final_cost * Decimal(percent) / 100
                            installment_date = decision_data.purchase_date + timedelta(days=due_offset)
                            
                            outflow = CashflowEvent(
                                related_decision_id=decision.id,
                                event_type='OUTFLOW',
                                forecast_type='FORECAST',
                                event_date=installment_date,
                                amount=amount,
                                description=f"Payment for {decision_data.item_code} (Installment {percent}%)"
                            )
                            db.add(outflow)
                            cashflow_events_count += 1
                
                # Generate FORECAST cash inflow event
                # Calculate invoice date based on forecast settings
                if decision.forecast_invoice_timing_type == 'ABSOLUTE' and decision.forecast_invoice_issue_date:
                    invoice_date = decision.forecast_invoice_issue_date
                else:
                    # RELATIVE timing
                    days_after = decision.forecast_invoice_days_after_delivery or 30
                    invoice_date = decision_data.delivery_date + timedelta(days=days_after)
                
                invoice_amount = decision.forecast_invoice_amount or decision_data.final_cost
                
                inflow = CashflowEvent(
                    related_decision_id=decision.id,
                    event_type='INFLOW',
                    forecast_type='FORECAST',
                    event_date=invoice_date,
                    amount=invoice_amount,
                    description=f"Revenue from {decision_data.item_code}"
                )
                db.add(inflow)
                cashflow_events_count += 1
            
            saved_count += 1
        
        await db.commit()
        
        return {
            "message": "Decisions and cash flow events saved successfully",
            "saved_count": saved_count,
            "cashflow_events_created": cashflow_events_count,
            "decision_maker": current_user.username
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save decisions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save decisions: {str(e)}"
        )


@router.post("/save-proposal", response_model=dict)
async def save_proposal_as_decisions(
    proposal_data: dict,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """
    Save a proposal from enhanced optimization as finalized decisions.
    This endpoint handles proposals with full decision data.
    
    Requires: Finance or Admin role (PM cannot save proposals)
    """
    try:
        run_id_str = proposal_data.get('run_id')
        proposal_name = proposal_data.get('proposal_name', 'Unknown Proposal')
        decisions_data = proposal_data.get('decisions', [])
        
        if not run_id_str or not decisions_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing run_id or decisions data"
            )
        
        run_uuid = uuid.UUID(run_id_str)
        
        # Check if OptimizationRun exists, if not create it
        run_check = await db.execute(
            select(OptimizationRun).where(OptimizationRun.run_id == run_uuid)
        )
        optimization_run = run_check.scalars().first()
        
        if not optimization_run:
            # Create the optimization run record
            optimization_run = OptimizationRun(
                run_id=run_uuid,
                request_parameters={'proposal_name': proposal_name},
                status='SUCCESS'
            )
            db.add(optimization_run)
            await db.flush()
        
        saved_count = 0
        cashflow_count = 0
        
        for decision_data in decisions_data:
            # Find or create project item
            item_code = decision_data.get('item_code')
            project_id = decision_data.get('project_id')
            project_item_id = decision_data.get('project_item_id')  # Prefer project_item_id if provided
            
            # FIXED: Use project_item_id directly if provided (prevents wrong item selection when multiple items have same code)
            if project_item_id:
                item_result = await db.execute(
                    select(ProjectItem).where(ProjectItem.id == project_item_id)
                )
                project_item = item_result.scalars().first()
            else:
                # Fallback: Query by item_code + project_id (legacy behavior)
                item_result = await db.execute(
                    select(ProjectItem).where(
                        ProjectItem.item_code == item_code,
                        ProjectItem.project_id == project_id
                    )
                )
                project_item = item_result.scalars().first()
            
            if not project_item:
                if project_item_id:
                    logger.warning(f"Project item not found: project_item_id={project_item_id}")
                else:
                    logger.warning(f"Project item not found: {item_code} for project {project_id}")
                continue
            
            # Check if decision already exists
            existing_check = await db.execute(
                select(FinalizedDecision).where(
                    FinalizedDecision.run_id == run_uuid,
                    FinalizedDecision.project_item_id == project_item.id,
                    FinalizedDecision.item_code == item_code
                )
            )
            existing_decision = existing_check.scalars().first()
            
            if existing_decision:
                logger.info(f"Decision already exists for {item_code}, skipping")
                continue
            
            # ✅ FIX: Check for old REVERTED decisions for this item and mark them as superseded
            # This prevents confusion when same item is re-optimized
            old_reverted_check = await db.execute(
                select(FinalizedDecision).where(
                    FinalizedDecision.project_item_id == project_item.id,
                    FinalizedDecision.item_code == item_code,
                    FinalizedDecision.status == 'REVERTED'
                )
            )
            old_reverted_decisions = old_reverted_check.scalars().all()
            
            if old_reverted_decisions:
                # Add note to old reverted decisions that they're superseded
                for old_decision in old_reverted_decisions:
                    old_notes = old_decision.notes or ''
                    new_note = f"\n[SUPERSEDED] New decision created in run {run_uuid}"
                    old_decision.notes = (old_notes + new_note).strip()
                logger.info(f"Marked {len(old_reverted_decisions)} old reverted decision(s) as superseded for {item_code}")
            
            # Create finalized decision
            purchase_date = datetime.fromisoformat(decision_data['purchase_date'].replace('Z', '+00:00')).date() if isinstance(decision_data['purchase_date'], str) else decision_data['purchase_date']
            delivery_date = datetime.fromisoformat(decision_data['delivery_date'].replace('Z', '+00:00')).date() if isinstance(decision_data['delivery_date'], str) else decision_data['delivery_date']
            
            # Get procurement option to fetch currency information
            procurement_opt_result = await db.execute(
                select(ProcurementOption)
                .where(ProcurementOption.id == decision_data['procurement_option_id'])
            )
            procurement_opt = procurement_opt_result.scalars().first()
            
            if not procurement_opt:
                logger.warning(f"Procurement option not found: {decision_data['procurement_option_id']}")
                continue
            
            # Get currency (default to IRR if not found)
            from app.models import Currency
            if procurement_opt.currency_id:
                currency_id = procurement_opt.currency_id
                currency_code = procurement_opt.cost_currency or 'IRR'
            else:
                # Fallback: fetch IRR currency
                irr_currency_result = await db.execute(
                    select(Currency).where(Currency.code == 'IRR')
                )
                irr_currency = irr_currency_result.scalar_one()
                currency_id = irr_currency.id
                currency_code = 'IRR'
            
            # Get invoice amount from delivery options (20% markup fallback)
            delivery_opt_result = await db.execute(
                select(DeliveryOption)
                .where(DeliveryOption.project_item_id == project_item.id)
                .limit(1)
            )
            delivery_opt = delivery_opt_result.scalars().first()
            
            if delivery_opt and delivery_opt.invoice_amount_per_unit:
                # Use actual invoice amount from delivery option
                forecast_invoice_amount = delivery_opt.invoice_amount_per_unit * decision_data['quantity']
            else:
                # Fallback: Use 20% markup on cost
                forecast_invoice_amount = Decimal(str(decision_data['final_cost'])) * Decimal('1.20')
            
            final_cost_value = Decimal(str(decision_data['final_cost']))
            
            decision = FinalizedDecision(
                run_id=run_uuid,
                project_id=project_id,
                project_item_id=project_item.id,
                item_code=item_code,
                procurement_option_id=decision_data['procurement_option_id'],
                delivery_option_id=delivery_opt.id if delivery_opt else None,
                purchase_date=purchase_date,
                delivery_date=delivery_date,
                quantity=decision_data['quantity'],
                final_cost=final_cost_value,
                # Multi-currency fields
                currency_id=currency_id,
                final_cost_amount=final_cost_value,
                final_cost_currency=currency_code,
                forecast_invoice_amount_value=forecast_invoice_amount,
                forecast_invoice_amount_currency=currency_code,
                decision_maker_id=current_user.id,
                decision_date=datetime.utcnow(),
                status='PROPOSED',
                is_manual_edit=decision_data.get('is_manual_edit', False),
                notes=f"Saved from proposal: {proposal_name}",
                # Forecast invoice - use actual invoice amount from delivery options
                forecast_invoice_timing_type='RELATIVE',
                forecast_invoice_days_after_delivery=30,
                forecast_invoice_amount=forecast_invoice_amount
            )
            db.add(decision)
            await db.flush()
            
            # Create forecast cashflow events with multi-currency support
            # Outflow on purchase date
            outflow = CashflowEvent(
                related_decision_id=decision.id,
                event_type='OUTFLOW',
                forecast_type='FORECAST',
                event_date=purchase_date,
                amount=decision.final_cost,
                amount_value=final_cost_value,
                amount_currency=currency_code,
                description=f"Payment for {item_code}"
            )
            db.add(outflow)
            
            # Inflow 30 days after delivery
            invoice_date = delivery_date + timedelta(days=30)
            inflow = CashflowEvent(
                related_decision_id=decision.id,
                event_type='INFLOW',
                forecast_type='FORECAST',
                event_date=invoice_date,
                amount=decision.forecast_invoice_amount,
                amount_value=forecast_invoice_amount,
                amount_currency=currency_code,
                description=f"Revenue from {item_code}"
            )
            db.add(inflow)
            
            saved_count += 1
            cashflow_count += 2
        
        await db.commit()
        
        return {
            "message": f"Proposal '{proposal_name}' saved successfully",
            "saved_count": saved_count,
            "cashflow_events_created": cashflow_count,
            "run_id": str(run_uuid)
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save proposal: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save proposal: {str(e)}"
        )


@router.get("/budget-analysis")
async def get_budget_analysis(
    project_ids: Optional[str] = Query(None, description="Comma-separated project IDs"),
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze budget needs and identify gaps
    
    Returns detailed budget analysis including:
    - Budget needs by period and currency
    - Available budget by period and currency
    - Gaps and recommendations
    """
    from app.budget_analysis_service import BudgetAnalysisService
    
    # Parse project IDs
    project_id_list = None
    if project_ids:
        try:
            project_id_list = [int(pid.strip()) for pid in project_ids.split(',')]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project IDs format"
            )
    
    # Parse dates
    start_date_obj = None
    end_date_obj = None
    if start_date:
        try:
            start_date_obj = date.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use YYYY-MM-DD"
            )
    if end_date:
        try:
            end_date_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use YYYY-MM-DD"
            )
    
    # Create analysis service
    analysis_service = BudgetAnalysisService(db)
    
    # Run analysis
    try:
        result = await analysis_service.analyze_budget_needs(
            project_ids=project_id_list,
            start_date=start_date_obj,
            end_date=end_date_obj
        )
        
        # Convert to response format
        return {
            "status": result.status,
            "periods": result.periods,
            "total_needed_by_currency": {
                currency: float(amount)
                for currency, amount in result.total_needed_by_currency.items()
            },
            "total_available_by_currency": {
                currency: float(amount)
                for currency, amount in result.total_available_by_currency.items()
            },
            "gap_by_currency": {
                currency: float(amount)
                for currency, amount in result.gap_by_currency.items()
            },
            "recommendations": result.recommendations,
            "critical_months": result.critical_months
        }
    except Exception as e:
        logger.error(f"Budget analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Budget analysis failed: {str(e)}"
        )


@router.get("/{decision_id}", response_model=FinalizedDecisionSchema)
async def get_decision(
    decision_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific finalized decision by ID"""
    result = await db.execute(
        select(FinalizedDecision)
        .options(
            selectinload(FinalizedDecision.project_item),
            selectinload(FinalizedDecision.procurement_option)
        )
        .where(FinalizedDecision.id == decision_id)
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )
    
    return decision


@router.put("/{decision_id}", response_model=FinalizedDecisionSchema)
async def update_decision(
    decision_id: int,
    decision_update: FinalizedDecisionUpdate,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Update a finalized decision (allows manual edits)"""
    # Get existing decision
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    existing_decision = result.scalar_one_or_none()
    
    if not existing_decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )
    
    # Prepare update data
    update_data = decision_update.dict(exclude_unset=True)
    
    # Mark as manual edit if being modified
    if update_data:
        update_data['is_manual_edit'] = True
    
    # Update the decision
    await db.execute(
        update(FinalizedDecision)
        .where(FinalizedDecision.id == decision_id)
        .values(**update_data)
    )
    await db.commit()
    
    # Fetch and return updated decision
    result = await db.execute(
        select(FinalizedDecision)
        .options(
            selectinload(FinalizedDecision.project_item),
            selectinload(FinalizedDecision.procurement_option)
        )
        .where(FinalizedDecision.id == decision_id)
    )
    return result.scalar_one()


@router.delete("/{decision_id}")
async def delete_decision(
    decision_id: int,
    current_user: User = Depends(require_pm()),
    db: AsyncSession = Depends(get_db)
):
    """Delete a finalized decision"""
    result = await db.execute(
        delete(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    await db.commit()
    
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )
    
    return {"message": "Decision deleted successfully"}


@router.post("/batch", response_model=dict)
async def save_batch_decisions(
    request: schemas.BatchSaveDecisionsRequest,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """
    Save multiple decisions at once from optimization results
    
    Requires: Finance or Admin role (PM cannot save decisions)
    """
    if len(request.project_item_ids) != len(request.procurement_option_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mismatch between items and options count"
        )
    
    saved_count = 0
    run_uuid = uuid.UUID(request.run_id)
    
    # Check if OptimizationRun exists, if not create it
    run_check = await db.execute(
        select(OptimizationRun).where(OptimizationRun.run_id == run_uuid)
    )
    optimization_run = run_check.scalars().first()
    
    if not optimization_run:
        # Create the optimization run record
        optimization_run = OptimizationRun(
            run_id=run_uuid,
            request_parameters={},
            status='SUCCESS'
        )
        db.add(optimization_run)
        await db.flush()
    
    # First, fetch the optimization results to get the actual project_item mapping
    opt_results_query = await db.execute(
        select(OptimizationResult).where(OptimizationResult.run_id == run_uuid)
    )
    opt_results = opt_results_query.scalars().all()
    
    try:
        for item_id, option_id in zip(request.project_item_ids, request.procurement_option_ids):
            # The item_id from frontend is actually the OptimizationResult.id
            # We need to find the actual ProjectItem
            
            # Fetch the optimization result
            opt_result_query = await db.execute(
                select(OptimizationResult).where(OptimizationResult.id == item_id)
            )
            opt_result = opt_result_query.scalars().first()
            
            if not opt_result:
                continue
            
            # Now find the actual project item using item_code and project_id
            item_result = await db.execute(
                select(ProjectItem).where(
                    ProjectItem.item_code == opt_result.item_code,
                    ProjectItem.project_id == opt_result.project_id
                )
            )
            project_item = item_result.scalars().first()
            
            if not project_item:
                continue
            
            # Fetch the procurement option
            option_result = await db.execute(
                select(ProcurementOption).where(ProcurementOption.id == option_id)
            )
            procurement_option = option_result.scalars().first()
            
            if not procurement_option:
                continue
            
            # Calculate dates from optimization result
            # Convert time slots to actual dates (approximate)
            purchase_date = date.today() + timedelta(days=opt_result.purchase_time * 30)
            delivery_date = date.today() + timedelta(days=opt_result.delivery_time * 30)
            
            # Get invoice amount from delivery options (20% markup fallback)
            delivery_opt_result = await db.execute(
                select(DeliveryOption)
                .where(DeliveryOption.project_item_id == project_item.id)
                .limit(1)
            )
            delivery_opt = delivery_opt_result.scalars().first()
            
            if delivery_opt and delivery_opt.invoice_amount_per_unit:
                # Use actual invoice amount from delivery option
                forecast_invoice_amount = delivery_opt.invoice_amount_per_unit * opt_result.quantity
            else:
                # Fallback: Use 20% markup on cost
                forecast_invoice_amount = opt_result.final_cost * Decimal('1.20')
            
            # Check if decision already exists
            existing_check = await db.execute(
                select(FinalizedDecision).where(
                    FinalizedDecision.run_id == run_uuid,
                    FinalizedDecision.project_item_id == project_item.id,
                    FinalizedDecision.item_code == opt_result.item_code
                )
            )
            if existing_check.scalars().first():
                continue  # Skip duplicate
            
            # Create the finalized decision
            decision = FinalizedDecision(
                run_id=run_uuid,
                project_id=opt_result.project_id,
                project_item_id=project_item.id,
                item_code=opt_result.item_code,
                procurement_option_id=option_id,
                delivery_option_id=delivery_opt.id if delivery_opt else None,
                purchase_date=purchase_date,
                delivery_date=delivery_date,
                quantity=opt_result.quantity,
                final_cost=opt_result.final_cost,
                decision_maker_id=current_user.id,
                decision_date=datetime.utcnow(),
                status='PROPOSED',
                forecast_invoice_timing_type='RELATIVE',
                forecast_invoice_days_after_delivery=30,
                forecast_invoice_amount=forecast_invoice_amount
            )
            db.add(decision)
            await db.flush()
            
            # Create cashflow events
            outflow = CashflowEvent(
                related_decision_id=decision.id,
                event_type='OUTFLOW',
                forecast_type='FORECAST',
                event_date=purchase_date,
                amount=decision.final_cost,
                description=f"Payment for {opt_result.item_code}"
            )
            db.add(outflow)
            
            invoice_date = delivery_date + timedelta(days=30)
            inflow = CashflowEvent(
                related_decision_id=decision.id,
                event_type='INFLOW',
                forecast_type='FORECAST',
                event_date=invoice_date,
                amount=decision.forecast_invoice_amount,  # Use invoice amount, not cost!
                description=f"Revenue from {opt_result.item_code}"
            )
            db.add(inflow)
            
            saved_count += 1
        
        await db.commit()
        
        return {
            "message": "Decisions saved successfully",
            "saved_count": saved_count
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save batch decisions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save decisions: {str(e)}"
        )


@router.post("/finalize", response_model=dict)
async def finalize_decisions(
    request: FinalizeDecisionsRequest,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """
    Finalize (lock) decisions so they won't be re-optimized.
    Finance role required.
    """
    try:
        if request.finalize_all:
            # Finalize all PROPOSED decisions
            result = await db.execute(
                update(FinalizedDecision)
                .where(FinalizedDecision.status == 'PROPOSED')
                .values(
                    status='LOCKED',
                    finalized_at=datetime.utcnow(),
                    finalized_by_id=current_user.id
                )
            )
            count = result.rowcount
        else:
            # Finalize specific decisions
            # ✅ FIX: Allow finalizing both PROPOSED and REVERTED decisions
            # This allows "re-finalizing" previously reverted decisions
            result = await db.execute(
                update(FinalizedDecision)
                .where(FinalizedDecision.id.in_(request.decision_ids))
                .where(FinalizedDecision.status.in_(['PROPOSED', 'REVERTED']))
                .values(
                    status='LOCKED',
                    finalized_at=datetime.utcnow(),
                    finalized_by_id=current_user.id
                )
            )
            count = result.rowcount
            
            # ✅ Reactivate cashflow events if re-finalizing reverted decisions
            if count > 0:
                # Get the finalized decision IDs
                finalized_result = await db.execute(
                    select(FinalizedDecision.id)
                    .where(FinalizedDecision.id.in_(request.decision_ids))
                    .where(FinalizedDecision.status == 'LOCKED')
                )
                finalized_ids = [row[0] for row in finalized_result.all()]
                
                # Reactivate cancelled cashflow events for these decisions
                await db.execute(
                    update(CashflowEvent)
                    .where(CashflowEvent.related_decision_id.in_(finalized_ids))
                    .where(CashflowEvent.is_cancelled == True)
                    .values(
                        is_cancelled=False,
                        cancelled_at=None,
                        cancelled_by_id=None,
                        cancellation_reason=None
                    )
                )
                logger.info(f"✅ Reactivated cashflow events for {len(finalized_ids)} re-finalized decision(s)")
        
        await db.commit()
        
        return {
            "message": f"Successfully finalized {count} decision(s)",
            "finalized_count": count,
            "finalized_by": current_user.username
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to finalize decisions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finalize decisions: {str(e)}"
        )


@router.put("/{decision_id}/status", response_model=FinalizedDecisionSchema)
async def update_decision_status(
    decision_id: int,
    status_update: DecisionStatusUpdate,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Update the status of a finalized decision"""
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )
    
    # Prevent reverting if item is fully delivered and paid
    if status_update.status == 'REVERTED':
        is_delivered = decision.delivery_status == 'DELIVERY_COMPLETE'
        has_invoice = decision.actual_invoice_issue_date is not None
        has_payment = decision.actual_payment_date is not None
        
        if is_delivered and has_invoice and has_payment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot revert: Item is fully delivered, invoiced, and paid. This is a completed transaction."
            )
    
    # Update status
    update_data = {'status': status_update.status}
    
    if status_update.status == 'LOCKED':
        update_data['finalized_at'] = datetime.utcnow()
        update_data['finalized_by_id'] = current_user.id
    
    if status_update.notes:
        existing_notes = decision.notes or ''
        update_data['notes'] = f"{existing_notes}\n{status_update.notes}".strip()
    
    await db.execute(
        update(FinalizedDecision)
        .where(FinalizedDecision.id == decision_id)
        .values(**update_data)
    )
    
    # ✅ CRITICAL FIX: Cancel cashflow events when decision is reverted
    if status_update.status == 'REVERTED':
        from app.models import CashflowEvent
        
        # Cancel all cashflow events related to this decision
        await db.execute(
            update(CashflowEvent)
            .where(CashflowEvent.related_decision_id == decision_id)
            .where(CashflowEvent.is_cancelled == False)  # Only cancel active events
            .values(
                is_cancelled=True,
                cancelled_at=datetime.utcnow(),
                cancelled_by_id=current_user.id,
                cancellation_reason=f"Decision #{decision_id} reverted by {current_user.username}"
            )
        )
        logger.info(f"✅ Cancelled cashflow events for reverted decision #{decision_id}")
    
    await db.commit()
    
    # Fetch and return updated decision
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    return result.scalar_one()


@router.post("/{decision_id}/actual-invoice", response_model=FinalizedDecisionSchema)
async def enter_actual_invoice_data(
    decision_id: int,
    invoice_data: ActualInvoiceDataRequest,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Enter actual invoice data (for finance team)"""
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )
    
    # Update actual invoice fields
    await db.execute(
        update(FinalizedDecision)
        .where(FinalizedDecision.id == decision_id)
        .values(
            actual_invoice_issue_date=invoice_data.actual_invoice_issue_date,
            actual_invoice_amount=invoice_data.actual_invoice_amount,
            actual_invoice_received_date=invoice_data.actual_invoice_received_date,
            invoice_entered_by_id=current_user.id,
            invoice_entered_at=datetime.utcnow(),
            notes=sql_func.concat(
                sql_func.coalesce(FinalizedDecision.notes, ''),
                f"\n{invoice_data.notes}" if invoice_data.notes else ''
            )
        )
    )
    
    # Create ACTUAL cashflow event for the invoice received
    if invoice_data.actual_invoice_received_date:
        actual_inflow = CashflowEvent(
            related_decision_id=decision_id,
            event_type='INFLOW',
            forecast_type='ACTUAL',
            event_date=invoice_data.actual_invoice_received_date,
            amount=invoice_data.actual_invoice_amount,
            description=f"Actual revenue from {decision.item_code}"
        )
        db.add(actual_inflow)
    
    await db.commit()
    
    # Fetch and return updated decision
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    return result.scalar_one()


@router.post("/{decision_id}/actual-payment", response_model=FinalizedDecisionSchema)
async def enter_actual_payment_data(
    decision_id: int,
    payment_data: ActualPaymentDataRequest,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Enter actual payment data to supplier (for finance team)"""
    from sqlalchemy.orm import selectinload
    
    result = await db.execute(
        select(FinalizedDecision)
        .options(selectinload(FinalizedDecision.procurement_option))
        .where(FinalizedDecision.id == decision_id)
    )
    decision = result.scalar_one_or_none()
    
    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Decision not found"
        )
    
    # Get supplier name from procurement option
    supplier_name = decision.procurement_option.supplier_name if decision.procurement_option else "Supplier"
    
    # Update actual payment fields
    await db.execute(
        update(FinalizedDecision)
        .where(FinalizedDecision.id == decision_id)
        .values(
            actual_payment_amount=payment_data.actual_payment_amount,
            actual_payment_date=payment_data.actual_payment_date,
            actual_payment_installments=payment_data.actual_payment_installments,
            payment_entered_by_id=current_user.id,
            payment_entered_at=datetime.utcnow(),
            notes=sql_func.concat(
                sql_func.coalesce(FinalizedDecision.notes, ''),
                f"\n[Payment] {payment_data.notes}" if payment_data.notes else ''
            )
        )
    )
    
    # Create ACTUAL cashflow events for payments
    if payment_data.actual_payment_installments:
        # Multiple installments
        for installment in payment_data.actual_payment_installments:
            installment_date = datetime.strptime(installment['date'], '%Y-%m-%d').date()
            installment_amount = Decimal(str(installment['amount']))
            
            actual_outflow = CashflowEvent(
                related_decision_id=decision_id,
                event_type='OUTFLOW',
                forecast_type='ACTUAL',
                event_date=installment_date,
                amount=installment_amount,
                description=f"Actual payment installment to {supplier_name} for {decision.item_code}"
            )
            db.add(actual_outflow)
    else:
        # Single payment (cash)
        actual_outflow = CashflowEvent(
            related_decision_id=decision_id,
            event_type='OUTFLOW',
            forecast_type='ACTUAL',
            event_date=payment_data.actual_payment_date,
            amount=payment_data.actual_payment_amount,
            description=f"Actual payment to {supplier_name} for {decision.item_code}"
        )
        db.add(actual_outflow)
    
    await db.commit()
    
    # Fetch and return updated decision
    result = await db.execute(
        select(FinalizedDecision).where(FinalizedDecision.id == decision_id)
    )
    return result.scalar_one()
