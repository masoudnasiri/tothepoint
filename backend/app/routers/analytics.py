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
from app.auth import require_finance, require_admin, get_current_user
from app.models import (
    User, Project, ProjectItem, FinalizedDecision, 
    CashflowEvent, OptimizationResult, ProcurementOption
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/eva/{project_id}")
async def get_earned_value_analytics(
    project_id: int,
    current_user: User = Depends(require_finance),
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
    # Sum of all planned costs for project items
    total_planned_cost = Decimal('0')
    for item in items:
        # Get average procurement cost for each item
        avg_cost_result = await db.scalar(
            select(func.avg(ProcurementOption.base_cost))
            .where(ProcurementOption.item_code == item.item_code)
            .where(ProcurementOption.is_active == True)
        )
        if avg_cost_result:
            total_planned_cost += Decimal(str(avg_cost_result)) * item.quantity
    
    BAC = float(total_planned_cost)
    
    # Calculate total planned work (number of items)
    total_items = len(items)
    
    # Calculate Actual Cost (AC) - sum of actual payments
    AC = sum(
        float(d.actual_payment_amount or d.final_cost)
        for d in decisions
        if d.status == 'LOCKED'
    )
    
    # Calculate Planned Value (PV) - based on what should be completed by now
    # Using delivery dates as milestones
    today = date.today()
    items_should_be_done = sum(
        1 for item in items
        if item.decision_date and item.decision_date <= today
    )
    PV = BAC * (items_should_be_done / total_items) if total_items > 0 else 0
    
    # Calculate Earned Value (EV) - value of actually completed work
    # Count locked decisions with actual delivery
    items_actually_done = sum(
        1 for d in decisions
        if d.status == 'LOCKED' and d.delivery_date and d.delivery_date <= today
    )
    EV = BAC * (items_actually_done / total_items) if total_items > 0 else 0
    
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
    start_date = current_date - timedelta(days=180)  # Last 6 months
    
    for month_offset in range(7):  # 6 months + current
        target_date = start_date + timedelta(days=30 * month_offset)
        
        # PV at this date
        items_planned = sum(
            1 for item in items
            if item.decision_date and item.decision_date <= target_date
        )
        pv_at_date = BAC * (items_planned / total_items) if total_items > 0 else 0
        
        # EV at this date
        items_earned = sum(
            1 for d in decisions
            if d.status == 'LOCKED' and d.delivery_date and d.delivery_date <= target_date
        )
        ev_at_date = BAC * (items_earned / total_items) if total_items > 0 else 0
        
        # AC at this date
        ac_at_date = sum(
            float(d.actual_payment_amount or d.final_cost)
            for d in decisions
            if d.status == 'LOCKED' and d.payment_date and d.payment_date <= target_date
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
            'total_items': total_items,
            'items_planned': items_should_be_done,
            'items_completed': items_actually_done,
            'percent_planned': round((items_should_be_done / total_items * 100), 1) if total_items > 0 else 0,
            'percent_complete': round((items_actually_done / total_items * 100), 1) if total_items > 0 else 0,
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
    
    # Group by date and type
    daily_cashflow: Dict[str, Dict[str, Decimal]] = {}
    
    for event in events:
        date_key = event.event_date.isoformat()
        if date_key not in daily_cashflow:
            daily_cashflow[date_key] = {
                'inflow_forecast': Decimal('0'),
                'outflow_forecast': Decimal('0'),
                'inflow_actual': Decimal('0'),
                'outflow_actual': Decimal('0'),
            }
        
        amount = event.amount
        if event.event_type == 'INFLOW':
            if event.forecast_type == 'ACTUAL':
                daily_cashflow[date_key]['inflow_actual'] += amount
            else:
                daily_cashflow[date_key]['inflow_forecast'] += amount
        else:  # OUTFLOW
            if event.forecast_type == 'ACTUAL':
                daily_cashflow[date_key]['outflow_actual'] += amount
            else:
                daily_cashflow[date_key]['outflow_forecast'] += amount
    
    # Generate forecast for future months
    today = date.today()
    forecast_data = []
    cumulative_balance = Decimal('0')
    
    for month_offset in range(-6, months_ahead + 1):  # 6 months history + forecast
        target_date = today + timedelta(days=30 * month_offset)
        date_key = target_date.isoformat()
        
        cashflow = daily_cashflow.get(date_key, {
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
            'date': date_key,
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
    current_user: User = Depends(require_finance),
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
    time_delays = []
    for decision in decisions:
        if decision.delivery_date and decision.actual_payment_date:
            # Assume procurement_date is the planned payment date
            planned_payment = decision.payment_date or decision.purchase_date
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


@router.get("/all-projects-summary")
async def get_all_projects_analytics_summary(
    current_user: User = Depends(require_finance),
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
        
        summaries.append({
            'project_id': project.id,
            'project_code': project.project_code,
            'project_name': project.name,
            'locked_decisions': len(decisions),
            'cpi': round(cpi, 3),
            'spi': round(spi, 3),
            'health': health,
        })
    
    return {
        'total_projects': len(projects),
        'projects': summaries,
    }

