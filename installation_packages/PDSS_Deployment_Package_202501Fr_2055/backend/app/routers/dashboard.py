"""
Dashboard and cash flow analysis endpoints
"""

from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime
from decimal import Decimal
from collections import defaultdict
from sqlalchemy import and_
from io import BytesIO
import pandas as pd
from app.database import get_db
from app.auth import get_current_user
from app.models import User, CashflowEvent, BudgetData, FinalizedDecision

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/cashflow")
async def get_cashflow_analysis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forecast_type: Optional[str] = None,
    project_ids: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get cash flow analysis aggregated by month
    Returns time-series data showing monthly inflows, outflows, and net cash flow
    Supports filtering by forecast_type: 'FORECAST' or 'ACTUAL'
    Supports filtering by project_ids: comma-separated list of project IDs
    
    PM users: Only see revenue INFLOW data (restricted access)
    Procurement users: Only see payment OUTFLOW data (restricted access)
    Finance/Admin users: See all cash flow data
    """
    try:
        # Build query for cashflow events (exclude cancelled events)
        query = select(CashflowEvent).where(CashflowEvent.is_cancelled == False)
        
        # ✅ NEW: Filter by project(s) if specified
        if project_ids:
            project_id_list = [int(pid.strip()) for pid in project_ids.split(',') if pid.strip()]
            if project_id_list:
                # Join with finalized_decisions to filter by project
                query = query.join(
                    FinalizedDecision,
                    CashflowEvent.related_decision_id == FinalizedDecision.id
                ).where(FinalizedDecision.project_id.in_(project_id_list))
        
        # PM users can only see INFLOW (revenue) events from ASSIGNED projects
        if current_user.role == "pm":
            # Get PM's assigned projects
            from app.auth import get_user_projects
            assigned_projects = await get_user_projects(db, current_user)
            
            if assigned_projects:
                # Filter by INFLOW events from assigned projects only
                query = query.join(
                    FinalizedDecision,
                    CashflowEvent.related_decision_id == FinalizedDecision.id
                ).where(
                    CashflowEvent.event_type == "INFLOW",
                    FinalizedDecision.project_id.in_(assigned_projects)
                )
            else:
                # No assigned projects = no data
                query = query.where(CashflowEvent.id == None)  # Returns empty
        
        # Procurement users can only see OUTFLOW (payment) events
        elif current_user.role == "procurement":
            query = query.where(CashflowEvent.event_type == "OUTFLOW")
        
        # PMO users can see all data (like admin and finance)
        
        # Filter by forecast type if specified
        if forecast_type:
            query = query.where(CashflowEvent.forecast_type == forecast_type)
        
        if start_date:
            query = query.where(CashflowEvent.event_date >= date.fromisoformat(start_date))
        if end_date:
            query = query.where(CashflowEvent.event_date <= date.fromisoformat(end_date))
        
        # Execute query
        result = await db.execute(query.order_by(CashflowEvent.event_date))
        events = result.scalars().all()
        
        # Aggregate by month
        monthly_data = defaultdict(lambda: {"inflow": Decimal(0), "outflow": Decimal(0)})
        
        for event in events:
            month_key = event.event_date.strftime("%Y-%m")
            
            if event.event_type.upper() == "INFLOW":
                monthly_data[month_key]["inflow"] += event.amount
            else:
                monthly_data[month_key]["outflow"] += event.amount
        
        # PM and Procurement users should NOT see budget data (restricted)
        budgets = []
        if current_user.role in ["finance", "admin"]:
            # Get budget data for finance/admin only
            budget_query = select(BudgetData)
            if start_date:
                budget_query = budget_query.where(BudgetData.budget_date >= date.fromisoformat(start_date))
            if end_date:
                budget_query = budget_query.where(BudgetData.budget_date <= date.fromisoformat(end_date))
            
            budget_result = await db.execute(budget_query.order_by(BudgetData.budget_date))
            budgets = budget_result.scalars().all()
            
            # Add budgets as initial inflows
            for budget in budgets:
                month_key = budget.budget_date.strftime("%Y-%m")
                monthly_data[month_key]["budget"] = float(budget.available_budget)
        
        # Sort by month and calculate cumulative
        sorted_months = sorted(monthly_data.keys())
        cumulative_balance = Decimal(0)
        result_data = []
        
        total_inflow = Decimal(0)
        total_outflow = Decimal(0)
        
        for month in sorted_months:
            data = monthly_data[month]
            inflow = data["inflow"]
            outflow = data["outflow"]
            budget = Decimal(data.get("budget", 0))
            
            net_flow = inflow + budget - outflow
            cumulative_balance += net_flow
            
            total_inflow += inflow + budget
            total_outflow += outflow
            
            result_data.append({
                "month": month,
                "inflow": float(inflow),
                "outflow": float(outflow),
                "budget": float(budget),
                "net_flow": float(net_flow),
                "cumulative_balance": float(cumulative_balance)
            })
        
        # Calculate summary metrics
        summary = {
            "total_inflow": float(total_inflow),
            "total_outflow": float(total_outflow),
            "net_position": float(total_inflow - total_outflow),
            "peak_balance": max([d["cumulative_balance"] for d in result_data]) if result_data else 0,
            "min_balance": min([d["cumulative_balance"] for d in result_data]) if result_data else 0,
            "final_balance": float(cumulative_balance)
        }
        
        return {
            "time_series": result_data,
            "summary": summary,
            "period_count": len(result_data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error calculating cash flow: {str(e)}"
        )


@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall dashboard summary statistics
    
    PM users: Only see revenue inflow data (restricted)
    Finance/Admin users: See all data
    """
    try:
        # PMO users see all data (like admin/finance) - no restrictions
        # PM users only see INFLOW events from ASSIGNED projects
        if current_user.role == "pm":
            # Get PM's assigned projects
            from app.auth import get_user_projects
            assigned_projects = await get_user_projects(db, current_user)
            
            if assigned_projects:
                # Count only inflow events from assigned projects
                events_count_query = select(func.count(CashflowEvent.id)).select_from(CashflowEvent).join(
                    FinalizedDecision,
                    CashflowEvent.related_decision_id == FinalizedDecision.id
                ).where(
                    and_(
                        CashflowEvent.event_type == "INFLOW",
                        CashflowEvent.is_cancelled == False,
                        FinalizedDecision.project_id.in_(assigned_projects)
                    )
                )
                events_result = await db.execute(events_count_query)
                total_events = events_result.scalar()
                
                # Sum only inflows from assigned projects
                inflow_query = select(func.sum(CashflowEvent.amount)).select_from(CashflowEvent).join(
                    FinalizedDecision,
                    CashflowEvent.related_decision_id == FinalizedDecision.id
                ).where(
                    and_(
                        CashflowEvent.event_type == "INFLOW",
                        CashflowEvent.is_cancelled == False,
                        FinalizedDecision.project_id.in_(assigned_projects)
                    )
                )
                inflow_result = await db.execute(inflow_query)
                total_inflow = inflow_result.scalar() or Decimal(0)
            else:
                # No assigned projects = no data
                total_events = 0
                total_inflow = Decimal(0)
            
            # PM users don't see outflows or budgets
            return {
                "total_events": total_events,
                "total_budget": 0,  # Hidden from PM
                "total_inflow": float(total_inflow),
                "total_outflow": 0,  # Hidden from PM
                "net_position": float(total_inflow)
            }
        
        # Procurement users only see OUTFLOW events
        elif current_user.role == "procurement":
            # Count only outflow events
            events_count_query = select(func.count(CashflowEvent.id)).where(
                and_(CashflowEvent.event_type == "OUTFLOW", CashflowEvent.is_cancelled == False)
            )
            events_result = await db.execute(events_count_query)
            total_events = events_result.scalar()
            
            # Sum only outflows
            outflow_query = select(func.sum(CashflowEvent.amount)).where(
                and_(CashflowEvent.event_type == "OUTFLOW", CashflowEvent.is_cancelled == False)
            )
            outflow_result = await db.execute(outflow_query)
            total_outflow = outflow_result.scalar() or Decimal(0)
            
            # Procurement users don't see inflows or budgets
            return {
                "total_events": total_events,
                "total_budget": 0,  # Hidden from Procurement
                "total_inflow": 0,  # Hidden from Procurement
                "total_outflow": float(total_outflow),
                "net_position": -float(total_outflow)  # Negative (outflow only)
            }
        
        # Finance/Admin users see everything
        # Count total cashflow events (exclude cancelled)
        events_count_query = select(func.count(CashflowEvent.id)).where(CashflowEvent.is_cancelled == False)
        events_result = await db.execute(events_count_query)
        total_events = events_result.scalar()
        
        # Sum total inflows (exclude cancelled)
        inflow_query = select(func.sum(CashflowEvent.amount)).where(
            and_(CashflowEvent.event_type == "INFLOW", CashflowEvent.is_cancelled == False)
        )
        inflow_result = await db.execute(inflow_query)
        total_inflow = inflow_result.scalar() or Decimal(0)
        
        # Sum total outflows (exclude cancelled)
        outflow_query = select(func.sum(CashflowEvent.amount)).where(
            and_(CashflowEvent.event_type == "OUTFLOW", CashflowEvent.is_cancelled == False)
        )
        outflow_result = await db.execute(outflow_query)
        total_outflow = outflow_result.scalar() or Decimal(0)
        
        # Get total budget
        budget_query = select(func.sum(BudgetData.available_budget))
        budget_result = await db.execute(budget_query)
        total_budget = budget_result.scalar() or Decimal(0)
        
        return {
            "total_events": total_events,
            "total_budget": float(total_budget),
            "total_inflow": float(total_inflow),
            "total_outflow": float(total_outflow),
            "net_position": float(total_budget + total_inflow - total_outflow)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching dashboard summary: {str(e)}"
        )


@router.get("/cashflow/export")
async def export_cashflow_to_excel(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export cash flow events to Excel file"""
    try:
        # Query cashflow events
        # ✅ FIX: Exclude cancelled events from export
        query = select(CashflowEvent).where(CashflowEvent.is_cancelled == False)
        
        if start_date:
            query = query.where(CashflowEvent.event_date >= date.fromisoformat(start_date))
        if end_date:
            query = query.where(CashflowEvent.event_date <= date.fromisoformat(end_date))
        
        result = await db.execute(query.order_by(CashflowEvent.event_date))
        events = result.scalars().all()
        
        # Convert to DataFrame
        data = []
        for event in events:
            data.append({
                'Event Date': event.event_date.isoformat(),
                'Event Type': event.event_type.upper(),
                'Amount': float(event.amount),
                'Description': event.description or '',
                'Related Decision ID': event.related_decision_id or '',
                'Created At': event.created_at.isoformat()
            })
        
        df = pd.DataFrame(data)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, index=False, sheet_name='Cash Flow Events')
            
            # Summary sheet
            if len(df) > 0:
                inflows = df[df['Event Type'] == 'INFLOW']['Amount'].sum()
                outflows = df[df['Event Type'] == 'OUTFLOW']['Amount'].sum()
                
                summary_df = pd.DataFrame({
                    'Metric': ['Total Inflow', 'Total Outflow', 'Net Position', 'Event Count'],
                    'Value': [inflows, outflows, inflows - outflows, len(df)]
                })
                summary_df.to_excel(writer, index=False, sheet_name='Summary')
        
        output.seek(0)
        
        # Generate filename with timestamp
        filename = f"cashflow_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
        
        return StreamingResponse(
            output, 
            headers=headers, 
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error exporting cash flow: {str(e)}"
        )

