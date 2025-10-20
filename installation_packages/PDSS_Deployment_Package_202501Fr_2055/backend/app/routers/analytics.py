"""
Analytics Router - Project Analytics & Forecasting
Provides Earned Value Management (EVM), Cash Flow Forecasting, and Risk Analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
import statistics
import numpy as np

from app.database import get_db
from app.auth import require_finance, require_admin, get_current_user, require_analytics_access
from app.models import (
    User, Project, ProjectItem, FinalizedDecision, 
    CashflowEvent, OptimizationResult, ProcurementOption
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/eva/{project_id}")
async def get_earned_value_analytics(
    project_id: int,
    current_user: User = Depends(require_analytics_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate Earned Value Analytics (EVA) for a project
    Returns: EV, PV, AC, CPI, SPI, CV, SV, EAC metrics
    """
    
    # Get project
    project_result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Get all project items
    items_result = await db.execute(
        select(ProjectItem).where(ProjectItem.project_id == project_id)
    )
    items = items_result.scalars().all()
    
    # Get finalized decisions for this project
    decisions_result = await db.execute(
        select(FinalizedDecision)
        .where(FinalizedDecision.project_id == project_id)
        .where(FinalizedDecision.status.in_(['LOCKED', 'PROPOSED']))
    )
    decisions = decisions_result.scalars().all()
    
    # Calculate Budget at Completion (BAC)
    # BAC = Total PLANNED COST (not revenue) for all work
    BAC = sum(float(d.final_cost) for d in decisions) if decisions else 0
    
    # Calculate total planned work (number of items)
    total_items = len(items)
    
    # Calculate Actual Cost (AC) - sum of actual payments or final cost for locked decisions
    AC = sum(
        float(d.actual_payment_amount if d.actual_payment_amount else d.final_cost)
        for d in decisions
        if d.status == 'LOCKED'
    ) if decisions else 0
    
    # Calculate Planned Value (PV) - budgeted cost of work scheduled to be complete by now
    # PV = Sum of planned costs for work that SHOULD be done by today (based on delivery dates)
    today = date.today()
    
    PV = 0
    items_should_be_done = 0
    for d in decisions:
        # Work is "scheduled" if delivery date has passed
        if d.delivery_date and d.delivery_date <= today:
            items_should_be_done += 1
            # Add the PLANNED COST (not invoice amount) to PV
            PV += float(d.final_cost)
    
    # Calculate Earned Value (EV) - budgeted cost of work actually completed
    # EV = Sum of planned costs for work that HAS BEEN done (LOCKED decisions)
    EV = 0
    items_actually_done = 0
    for d in decisions:
        if d.status == 'LOCKED':
            items_actually_done += 1
            # Add the PLANNED COST (not actual cost or invoice) to EV
            EV += float(d.final_cost)
    
    # Calculate performance indices
    CPI = EV / AC if AC > 0 else 1.0
    SPI = EV / PV if PV > 0 else 1.0
    
    # Calculate variances
    CV = EV - AC  # Cost Variance (positive = under budget)
    SV = EV - PV  # Schedule Variance (positive = ahead of schedule)
    
    # Estimate at Completion (EAC)
    # EAC = AC + (BAC - EV) / CPI
    remaining_work = BAC - EV
    EAC = AC + (remaining_work / CPI) if CPI > 0 else BAC
    
    # Estimate to Complete (ETC)
    ETC = EAC - AC
    
    # Variance at Completion (VAC)
    VAC = BAC - EAC
    
    # Time-series data for charts (monthly breakdown)
    monthly_data = []
    current_date = date.today()
    
    # Determine date range: 6 months history + enough future to cover all planned invoices
    start_date = current_date - timedelta(days=180)  # Last 6 months
    
    # Find latest invoice date to determine end date
    latest_invoice_date = current_date
    for d in decisions:
        if d.forecast_invoice_timing_type == 'ABSOLUTE' and d.forecast_invoice_issue_date:
            if d.forecast_invoice_issue_date > latest_invoice_date:
                latest_invoice_date = d.forecast_invoice_issue_date
        elif d.forecast_invoice_timing_type == 'RELATIVE' and d.delivery_date:
            days_after = d.forecast_invoice_days_after_delivery or 30
            invoice_date = d.delivery_date + timedelta(days=days_after)
            if invoice_date > latest_invoice_date:
                latest_invoice_date = invoice_date
    
    # Calculate number of months to cover
    days_span = (latest_invoice_date - start_date).days
    months_to_show = max(12, (days_span // 30) + 2)  # At least 12 months, or enough to cover all invoices
    
    for month_offset in range(months_to_show):
        target_date = start_date + timedelta(days=30 * month_offset)
        
        # PV at this date - budgeted cost of work scheduled by target_date
        pv_at_date = 0
        for d in decisions:
            # Work is "scheduled" if delivery date <= target_date
            if d.delivery_date and d.delivery_date <= target_date:
                pv_at_date += float(d.final_cost)
        
        # EV at this date - budgeted cost of work actually completed by target_date
        ev_at_date = 0
        for d in decisions:
            if d.status == 'LOCKED' and d.finalized_at and d.finalized_at.date() <= target_date:
                # Add PLANNED COST (not actual or invoice)
                ev_at_date += float(d.final_cost)
        
        # AC at this date - sum of costs for decisions finalized by this date
        ac_at_date = sum(
            float(d.actual_payment_amount if d.actual_payment_amount else d.final_cost)
            for d in decisions
            if d.status == 'LOCKED' and d.finalized_at and d.finalized_at.date() <= target_date
        )
        
        monthly_data.append({
            'date': target_date.isoformat(),
            'pv': round(pv_at_date, 2),
            'ev': round(ev_at_date, 2),
            'ac': round(ac_at_date, 2),
            'cpi': round(ev_at_date / ac_at_date, 3) if ac_at_date > 0 else 1.0,
            'spi': round(ev_at_date / pv_at_date, 3) if pv_at_date > 0 else 1.0,
        })
    
    return {
        'project_id': project_id,
        'project_code': project.project_code,
        'project_name': project.name,
        'metrics': {
            'bac': round(BAC, 2),
            'ev': round(EV, 2),
            'pv': round(PV, 2),
            'ac': round(AC, 2),
            'cpi': round(CPI, 3),
            'spi': round(SPI, 3),
            'cv': round(CV, 2),
            'sv': round(SV, 2),
            'eac': round(EAC, 2),
            'etc': round(ETC, 2),
            'vac': round(VAC, 2),
        },
        'progress': {
            'total_items': len(decisions) if decisions else total_items,
            'items_planned': items_should_be_done,
            'items_completed': items_actually_done,
            'percent_planned': round((items_should_be_done / len(decisions) * 100), 1) if decisions else 0,
            'percent_complete': round((items_actually_done / len(decisions) * 100), 1) if decisions else 0,
        },
        'time_series': monthly_data,
        'health_status': {
            'overall': 'healthy' if CPI >= 0.9 and SPI >= 0.9 else 'at_risk' if CPI >= 0.8 and SPI >= 0.8 else 'critical',
            'cost_performance': 'under_budget' if CPI > 1.0 else 'over_budget' if CPI < 0.9 else 'on_budget',
            'schedule_performance': 'ahead' if SPI > 1.0 else 'behind' if SPI < 0.9 else 'on_schedule',
        }
    }


@router.get("/cashflow-forecast/{project_id}")
async def get_cashflow_forecast(
    project_id: int,
    months_ahead: int = Query(default=12, ge=1, le=24),
    current_user: User = Depends(require_finance),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate cash flow forecast for a project
    Returns inflow/outflow projections and net balance
    """
    
    # Get all cashflow events for this project
    events_result = await db.execute(
        select(CashflowEvent)
        .join(FinalizedDecision, CashflowEvent.related_decision_id == FinalizedDecision.id)
        .where(FinalizedDecision.project_id == project_id)
        .where(CashflowEvent.is_cancelled == False)
    )
    events = events_result.scalars().all()
    
    # Group by MONTH (not exact date) for proper aggregation
    monthly_cashflow: Dict[str, Dict[str, Decimal]] = {}
    
    for event in events:
        month_key = event.event_date.strftime('%Y-%m')  # Group by month
        if month_key not in monthly_cashflow:
            monthly_cashflow[month_key] = {
                'inflow_forecast': Decimal('0'),
                'outflow_forecast': Decimal('0'),
                'inflow_actual': Decimal('0'),
                'outflow_actual': Decimal('0'),
            }
        
        amount = event.amount
        if event.event_type == 'INFLOW':
            if event.forecast_type == 'ACTUAL':
                monthly_cashflow[month_key]['inflow_actual'] += amount
            else:
                monthly_cashflow[month_key]['inflow_forecast'] += amount
        else:  # OUTFLOW
            if event.forecast_type == 'ACTUAL':
                monthly_cashflow[month_key]['outflow_actual'] += amount
            else:
                monthly_cashflow[month_key]['outflow_forecast'] += amount
    
    # Generate forecast for future months
    today = date.today()
    forecast_data = []
    cumulative_balance = Decimal('0')
    
    for month_offset in range(-6, months_ahead + 1):  # 6 months history + forecast
        target_date = today + timedelta(days=30 * month_offset)
        month_key = target_date.strftime('%Y-%m')  # Use month key
        
        cashflow = monthly_cashflow.get(month_key, {
            'inflow_forecast': Decimal('0'),
            'outflow_forecast': Decimal('0'),
            'inflow_actual': Decimal('0'),
            'outflow_actual': Decimal('0'),
        })
        
        inflow = float(cashflow.get('inflow_actual', 0) or cashflow.get('inflow_forecast', 0))
        outflow = float(cashflow.get('outflow_actual', 0) or cashflow.get('outflow_forecast', 0))
        net = inflow - outflow
        cumulative_balance += Decimal(str(net))
        
        forecast_data.append({
            'date': month_key,  # Use month key for consistent monthly display
            'inflow_forecast': float(cashflow.get('inflow_forecast', 0)),
            'outflow_forecast': float(cashflow.get('outflow_forecast', 0)),
            'inflow_actual': float(cashflow.get('inflow_actual', 0)),
            'outflow_actual': float(cashflow.get('outflow_actual', 0)),
            'net_cashflow': round(net, 2),
            'cumulative_balance': round(float(cumulative_balance), 2),
            'is_forecast': target_date > today,
        })
    
    # Identify periods with negative balance
    gap_intervals = [
        {
            'date': item['date'],
            'deficit': abs(item['cumulative_balance']),
        }
        for item in forecast_data
        if item['cumulative_balance'] < 0
    ]
    
    return {
        'project_id': project_id,
        'forecast_data': forecast_data,
        'gap_intervals': gap_intervals,
        'summary': {
            'total_inflow_forecast': sum(f['inflow_forecast'] for f in forecast_data),
            'total_outflow_forecast': sum(f['outflow_forecast'] for f in forecast_data),
            'total_inflow_actual': sum(f['inflow_actual'] for f in forecast_data),
            'total_outflow_actual': sum(f['outflow_actual'] for f in forecast_data),
            'final_balance': forecast_data[-1]['cumulative_balance'] if forecast_data else 0,
            'max_deficit': min((f['cumulative_balance'] for f in forecast_data), default=0),
            'financing_needed': abs(min((f['cumulative_balance'] for f in forecast_data), default=0)) if min((f['cumulative_balance'] for f in forecast_data), default=0) < 0 else 0,
        }
    }


@router.get("/risk/{project_id}")
async def get_risk_analytics(
    project_id: int,
    current_user: User = Depends(require_analytics_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate risk metrics and predictions
    Returns: delay variance, cost overrun variance, forecasts
    """
    
    # Get finalized decisions
    decisions_result = await db.execute(
        select(FinalizedDecision)
        .where(FinalizedDecision.project_id == project_id)
        .where(FinalizedDecision.status == 'LOCKED')
    )
    decisions = decisions_result.scalars().all()
    
    if len(decisions) < 2:
        return {
            'project_id': project_id,
            'message': 'Insufficient data for risk analysis (need at least 2 locked decisions)',
            'metrics': {},
        }
    
    # Calculate time delays (planned vs actual)
    # Compare: planned purchase_date vs actual_payment_date
    time_delays = []
    for decision in decisions:
        if decision.purchase_date and decision.actual_payment_date:
            # Planned payment date from optimization/decision
            planned_payment = decision.purchase_date
            # Actual payment date (when finance actually paid)
            actual_payment = decision.actual_payment_date
            delay_days = (actual_payment - planned_payment).days
            time_delays.append(delay_days)
    
    # Calculate cost overruns (planned vs actual)
    cost_ratios = []
    for decision in decisions:
        if decision.actual_payment_amount and decision.actual_payment_amount > 0:
            planned_cost = float(decision.final_cost)
            actual_cost = float(decision.actual_payment_amount)
            ratio = (actual_cost / planned_cost) - 1.0  # Percent over/under
            cost_ratios.append(ratio * 100)  # Convert to percentage
    
    # Statistical metrics
    sigma_time_delay = statistics.stdev(time_delays) if len(time_delays) > 1 else 0
    mean_time_delay = statistics.mean(time_delays) if time_delays else 0
    
    sigma_cost_overrun = statistics.stdev(cost_ratios) if len(cost_ratios) > 1 else 0
    mean_cost_overrun = statistics.mean(cost_ratios) if cost_ratios else 0
    
    # Simple forecast (linear trend)
    # If delays are increasing, project completion date shifts
    avg_delay = mean_time_delay
    remaining_items = len([d for d in decisions if d.status == 'PROPOSED'])
    forecasted_delay_days = int(avg_delay * remaining_items / max(len(decisions), 1))
    
    # Monte Carlo simulation (simplified)
    # P50 (median), P90 (90th percentile) completion dates
    if time_delays:
        delay_p50 = int(statistics.median(time_delays))
        delay_p90 = int(statistics.quantiles(time_delays, n=10)[8]) if len(time_delays) >= 10 else int(mean_time_delay * 1.5)
    else:
        delay_p50 = 0
        delay_p90 = 0
    
    return {
        'project_id': project_id,
        'metrics': {
            'sigma_time_delay': round(sigma_time_delay, 2),
            'mean_time_delay': round(mean_time_delay, 2),
            'sigma_cost_overrun': round(sigma_cost_overrun, 2),
            'mean_cost_overrun': round(mean_cost_overrun, 2),
            'sample_size_time': len(time_delays),
            'sample_size_cost': len(cost_ratios),
        },
        'forecast': {
            'forecasted_delay_days': forecasted_delay_days,
            'delay_probability_p50': delay_p50,
            'delay_probability_p90': delay_p90,
            'expected_completion_shift': f"{forecasted_delay_days} days",
        },
        'risk_level': {
            'time_risk': 'high' if sigma_time_delay > 30 else 'medium' if sigma_time_delay > 15 else 'low',
            'cost_risk': 'high' if sigma_cost_overrun > 20 else 'medium' if sigma_cost_overrun > 10 else 'low',
            'overall_risk': 'high' if (sigma_time_delay > 30 or sigma_cost_overrun > 20) else 'medium' if (sigma_time_delay > 15 or sigma_cost_overrun > 10) else 'low',
        },
        'distributions': {
            'time_delays': time_delays[:50],  # Sample for visualization
            'cost_overruns': [round(r, 2) for r in cost_ratios[:50]],
        }
    }


@router.get("/portfolio/eva")
async def get_portfolio_eva(
    current_user: User = Depends(require_analytics_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated EVA metrics for all projects (Portfolio View)
    """
    # Get all active projects
    projects_result = await db.execute(
        select(Project).where(Project.is_active == True)
    )
    projects = projects_result.scalars().all()
    
    # Aggregate all decisions across all projects
    all_decisions_result = await db.execute(
        select(FinalizedDecision)
        .join(Project, FinalizedDecision.project_id == Project.id)
        .where(Project.is_active == True)
        .where(FinalizedDecision.status.in_(['LOCKED', 'PROPOSED']))
    )
    all_decisions = all_decisions_result.scalars().all()
    
    # Calculate portfolio-level BAC, PV, EV, AC
    # BAC = Total PLANNED COST across all projects
    BAC = sum(float(d.final_cost) for d in all_decisions) if all_decisions else 0
    
    today = date.today()
    
    # PV - budgeted cost of work scheduled across all projects
    PV = 0
    for d in all_decisions:
        # Work is "scheduled" if delivery date has passed
        if d.delivery_date and d.delivery_date <= today:
            PV += float(d.final_cost)
    
    # EV - budgeted cost of work actually completed across all projects
    EV = 0
    items_actually_done = 0
    for d in all_decisions:
        if d.status == 'LOCKED':
            items_actually_done += 1
            # Add PLANNED COST (not actual or invoice)
            EV += float(d.final_cost)
    
    # AC - actual cost across all projects
    AC = sum(
        float(d.actual_payment_amount if d.actual_payment_amount else d.final_cost)
        for d in all_decisions
        if d.status == 'LOCKED'
    ) if all_decisions else 0
    
    # Performance indices
    CPI = EV / AC if AC > 0 else 1.0
    SPI = EV / PV if PV > 0 else 1.0
    CV = EV - AC
    SV = EV - PV
    
    # Forecasts
    remaining_work = BAC - EV
    EAC = AC + (remaining_work / CPI) if CPI > 0 else BAC
    ETC = EAC - AC
    VAC = BAC - EAC
    
    # Time-series data
    monthly_data = []
    start_date = today - timedelta(days=180)
    
    # Find latest invoice date to determine end date
    latest_invoice_date = today
    for d in all_decisions:
        if d.forecast_invoice_timing_type == 'ABSOLUTE' and d.forecast_invoice_issue_date:
            if d.forecast_invoice_issue_date > latest_invoice_date:
                latest_invoice_date = d.forecast_invoice_issue_date
        elif d.forecast_invoice_timing_type == 'RELATIVE' and d.delivery_date:
            days_after = d.forecast_invoice_days_after_delivery or 30
            invoice_date = d.delivery_date + timedelta(days=days_after)
            if invoice_date > latest_invoice_date:
                latest_invoice_date = invoice_date
    
    # Calculate number of months to cover
    days_span = (latest_invoice_date - start_date).days
    months_to_show = max(12, (days_span // 30) + 2)
    
    for month_offset in range(months_to_show):
        target_date = start_date + timedelta(days=30 * month_offset)
        
        pv_at_date = 0
        for d in all_decisions:
            # Work is "scheduled" if delivery date <= target_date
            if d.delivery_date and d.delivery_date <= target_date:
                pv_at_date += float(d.final_cost)
        
        ev_at_date = 0
        for d in all_decisions:
            if d.status == 'LOCKED' and d.finalized_at and d.finalized_at.date() <= target_date:
                # Add PLANNED COST (not actual or invoice)
                ev_at_date += float(d.final_cost)
        
        ac_at_date = sum(
            float(d.actual_payment_amount if d.actual_payment_amount else d.final_cost)
            for d in all_decisions
            if d.status == 'LOCKED' and d.finalized_at and d.finalized_at.date() <= target_date
        )
        
        monthly_data.append({
            'date': target_date.isoformat(),
            'pv': round(pv_at_date, 2),
            'ev': round(ev_at_date, 2),
            'ac': round(ac_at_date, 2),
            'cpi': round(ev_at_date / ac_at_date, 3) if ac_at_date > 0 else 1.0,
            'spi': round(ev_at_date / pv_at_date, 3) if pv_at_date > 0 else 1.0,
        })
    
    return {
        'project_id': 'all',
        'project_code': 'PORTFOLIO',
        'project_name': 'All Projects',
        'metrics': {
            'bac': round(BAC, 2),
            'ev': round(EV, 2),
            'pv': round(PV, 2),
            'ac': round(AC, 2),
            'cpi': round(CPI, 3),
            'spi': round(SPI, 3),
            'cv': round(CV, 2),
            'sv': round(SV, 2),
            'eac': round(EAC, 2),
            'etc': round(ETC, 2),
            'vac': round(VAC, 2),
        },
        'progress': {
            'total_items': len(all_decisions),
            'items_planned': sum(1 for d in all_decisions if d.delivery_date and d.delivery_date <= today),
            'items_completed': items_actually_done,
            'percent_planned': round((sum(1 for d in all_decisions if d.delivery_date and d.delivery_date <= today) / len(all_decisions) * 100), 1) if all_decisions else 0,
            'percent_complete': round((items_actually_done / len(all_decisions) * 100), 1) if all_decisions else 0,
        },
        'time_series': monthly_data,
        'health_status': {
            'overall': 'healthy' if CPI >= 0.9 and SPI >= 0.9 else 'at_risk' if CPI >= 0.8 and SPI >= 0.8 else 'critical',
            'cost_performance': 'under_budget' if CPI > 1.0 else 'over_budget' if CPI < 0.9 else 'on_budget',
            'schedule_performance': 'ahead' if SPI > 1.0 else 'behind' if SPI < 0.9 else 'on_schedule',
        }
    }


@router.get("/portfolio/cashflow-forecast")
async def get_portfolio_cashflow_forecast(
    months_ahead: int = Query(default=12, ge=1, le=24),
    current_user: User = Depends(require_finance),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate cash flow forecast for entire portfolio
    """
    # Get all cashflow events across all projects
    events_result = await db.execute(
        select(CashflowEvent)
        .join(FinalizedDecision, CashflowEvent.related_decision_id == FinalizedDecision.id)
        .join(Project, FinalizedDecision.project_id == Project.id)
        .where(Project.is_active == True)
        .where(CashflowEvent.is_cancelled == False)
    )
    events = events_result.scalars().all()
    
    # Group by MONTH (not exact date) for proper aggregation
    monthly_cashflow: Dict[str, Dict[str, Decimal]] = {}
    
    for event in events:
        month_key = event.event_date.strftime('%Y-%m')  # Group by month
        if month_key not in monthly_cashflow:
            monthly_cashflow[month_key] = {
                'inflow_forecast': Decimal('0'),
                'outflow_forecast': Decimal('0'),
                'inflow_actual': Decimal('0'),
                'outflow_actual': Decimal('0'),
            }
        
        amount = event.amount
        if event.event_type.upper() == 'INFLOW':
            if event.forecast_type == 'FORECAST':
                monthly_cashflow[month_key]['inflow_forecast'] += amount
            else:
                monthly_cashflow[month_key]['inflow_actual'] += amount
        else:
            if event.forecast_type == 'FORECAST':
                monthly_cashflow[month_key]['outflow_forecast'] += amount
            else:
                monthly_cashflow[month_key]['outflow_actual'] += amount
    
    # Generate forecast
    forecast_data = []
    cumulative_balance = Decimal('0')
    today = date.today()
    
    for i in range(months_ahead):
        target_date = today + timedelta(days=30 * i)
        month_key = target_date.strftime('%Y-%m')  # Use month key
        cashflow = monthly_cashflow.get(month_key, {})
        
        inflow = float(cashflow.get('inflow_actual', 0) or cashflow.get('inflow_forecast', 0))
        outflow = float(cashflow.get('outflow_actual', 0) or cashflow.get('outflow_forecast', 0))
        net = inflow - outflow
        cumulative_balance += Decimal(str(net))
        
        forecast_data.append({
            'date': month_key,  # Use month key for consistent monthly display
            'inflow_forecast': float(cashflow.get('inflow_forecast', 0)),
            'outflow_forecast': float(cashflow.get('outflow_forecast', 0)),
            'inflow_actual': float(cashflow.get('inflow_actual', 0)),
            'outflow_actual': float(cashflow.get('outflow_actual', 0)),
            'net_cashflow': round(net, 2),
            'cumulative_balance': round(float(cumulative_balance), 2),
            'is_forecast': target_date > today,
        })
    
    gap_intervals = [
        {'date': item['date'], 'deficit': abs(item['cumulative_balance'])}
        for item in forecast_data
        if item['cumulative_balance'] < 0
    ]
    
    return {
        'project_id': 'all',
        'forecast_data': forecast_data,
        'gap_intervals': gap_intervals,
        'summary': {
            'total_inflow_forecast': sum(f['inflow_forecast'] for f in forecast_data),
            'total_outflow_forecast': sum(f['outflow_forecast'] for f in forecast_data),
            'total_inflow_actual': sum(f['inflow_actual'] for f in forecast_data),
            'total_outflow_actual': sum(f['outflow_actual'] for f in forecast_data),
            'final_balance': forecast_data[-1]['cumulative_balance'] if forecast_data else 0,
            'max_deficit': min((f['cumulative_balance'] for f in forecast_data), default=0),
            'financing_needed': abs(min((f['cumulative_balance'] for f in forecast_data), default=0)) if min((f['cumulative_balance'] for f in forecast_data), default=0) < 0 else 0,
        }
    }


@router.get("/portfolio/risk")
async def get_portfolio_risk(
    current_user: User = Depends(require_analytics_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate portfolio-level risk metrics
    """
    # Get all locked decisions across all projects
    decisions_result = await db.execute(
        select(FinalizedDecision)
        .join(Project, FinalizedDecision.project_id == Project.id)
        .where(Project.is_active == True)
        .where(FinalizedDecision.status == 'LOCKED')
    )
    decisions = decisions_result.scalars().all()
    
    if len(decisions) < 2:
        return {
            'project_id': 'all',
            'message': 'Insufficient data for portfolio risk analysis',
            'metrics': {},
        }
    
    # Calculate time delays and cost overruns across all projects
    # Compare: planned purchase_date vs actual_payment_date
    time_delays = []
    cost_ratios = []
    
    for decision in decisions:
        if decision.purchase_date and decision.actual_payment_date:
            # Planned payment date from optimization/decision
            planned_payment = decision.purchase_date
            # Actual payment date (when finance actually paid)
            actual_payment = decision.actual_payment_date
            delay_days = (actual_payment - planned_payment).days
            time_delays.append(delay_days)
        
        if decision.actual_payment_amount and decision.actual_payment_amount > 0:
            planned_cost = float(decision.final_cost)
            actual_cost = float(decision.actual_payment_amount)
            ratio = (actual_cost / planned_cost) - 1.0
            cost_ratios.append(ratio * 100)
    
    sigma_time_delay = statistics.stdev(time_delays) if len(time_delays) > 1 else 0
    mean_time_delay = statistics.mean(time_delays) if time_delays else 0
    sigma_cost_overrun = statistics.stdev(cost_ratios) if len(cost_ratios) > 1 else 0
    mean_cost_overrun = statistics.mean(cost_ratios) if cost_ratios else 0
    
    if time_delays:
        delay_p50 = int(statistics.median(time_delays))
        delay_p90 = int(statistics.quantiles(time_delays, n=10)[8]) if len(time_delays) >= 10 else int(mean_time_delay * 1.5)
    else:
        delay_p50 = 0
        delay_p90 = 0
    
    return {
        'project_id': 'all',
        'metrics': {
            'sigma_time_delay': round(sigma_time_delay, 2),
            'mean_time_delay': round(mean_time_delay, 2),
            'sigma_cost_overrun': round(sigma_cost_overrun, 2),
            'mean_cost_overrun': round(mean_cost_overrun, 2),
            'sample_size_time': len(time_delays),
            'sample_size_cost': len(cost_ratios),
        },
        'forecast': {
            'forecasted_delay_days': 0,
            'delay_probability_p50': delay_p50,
            'delay_probability_p90': delay_p90,
            'expected_completion_shift': f"Portfolio-wide analysis",
        },
        'risk_level': {
            'time_risk': 'high' if sigma_time_delay > 30 else 'medium' if sigma_time_delay > 15 else 'low',
            'cost_risk': 'high' if sigma_cost_overrun > 20 else 'medium' if sigma_cost_overrun > 10 else 'low',
            'overall_risk': 'high' if (sigma_time_delay > 30 or sigma_cost_overrun > 20) else 'medium' if (sigma_time_delay > 15 or sigma_cost_overrun > 10) else 'low',
        },
        'distributions': {
            'time_delays': time_delays[:50],
            'cost_overruns': [round(r, 2) for r in cost_ratios[:50]],
        }
    }


@router.get("/all-projects-summary")
async def get_all_projects_analytics_summary(
    current_user: User = Depends(require_analytics_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get summary analytics for all projects
    Returns: CPI, SPI, health status for each project
    """
    
    # Get all active projects
    projects_result = await db.execute(
        select(Project).where(Project.is_active == True)
    )
    projects = projects_result.scalars().all()
    
    summaries = []
    
    for project in projects:
        # Quick health check based on finalized decisions
        decisions_result = await db.execute(
            select(FinalizedDecision)
            .where(FinalizedDecision.project_id == project.id)
            .where(FinalizedDecision.status == 'LOCKED')
        )
        decisions = decisions_result.scalars().all()
        
        if len(decisions) == 0:
            summaries.append({
                'project_id': project.id,
                'project_code': project.project_code,
                'project_name': project.name,
                'status': 'not_started',
                'cpi': None,
                'spi': None,
                'health': 'unknown',
            })
            continue
        
        # Calculate quick CPI
        total_planned = sum(float(d.final_cost) for d in decisions)
        total_actual = sum(float(d.actual_payment_amount or d.final_cost) for d in decisions)
        cpi = total_planned / total_actual if total_actual > 0 else 1.0
        
        # Calculate quick SPI (based on delivery dates)
        today = date.today()
        should_be_done = sum(1 for d in decisions if d.delivery_date <= today)
        actually_done = sum(1 for d in decisions if d.delivery_date <= today and d.actual_payment_date)
        spi = actually_done / should_be_done if should_be_done > 0 else 1.0
        
        health = 'healthy' if cpi >= 0.9 and spi >= 0.9 else 'at_risk' if cpi >= 0.8 and spi >= 0.8 else 'critical'
        
        # Calculate risk level (time and cost variance)
        time_delays = []
        cost_ratios = []
        
        for d in decisions:
            if d.purchase_date and d.actual_payment_date:
                delay_days = (d.actual_payment_date - d.purchase_date).days
                time_delays.append(delay_days)
            
            if d.actual_payment_amount and d.actual_payment_amount > 0:
                planned = float(d.final_cost)
                actual = float(d.actual_payment_amount)
                ratio = (actual / planned - 1.0) * 100
                cost_ratios.append(ratio)
        
        sigma_time = statistics.stdev(time_delays) if len(time_delays) > 1 else 0
        sigma_cost = statistics.stdev(cost_ratios) if len(cost_ratios) > 1 else 0
        
        time_risk = 'high' if sigma_time > 30 else 'medium' if sigma_time > 15 else 'low'
        cost_risk = 'high' if sigma_cost > 20 else 'medium' if sigma_cost > 10 else 'low'
        overall_risk = 'high' if (sigma_time > 30 or sigma_cost > 20) else 'medium' if (sigma_time > 15 or sigma_cost > 10) else 'low' if (time_delays or cost_ratios) else None
        
        summaries.append({
            'project_id': project.id,
            'project_code': project.project_code,
            'project_name': project.name,
            'locked_decisions': len(decisions),
            'cpi': round(cpi, 3),
            'spi': round(spi, 3),
            'health': health,
            'risk_level': overall_risk,
            'time_risk': time_risk if time_delays else None,
            'cost_risk': cost_risk if cost_ratios else None,
        })
    
    return {
        'total_projects': len(projects),
        'projects': summaries,
    }

