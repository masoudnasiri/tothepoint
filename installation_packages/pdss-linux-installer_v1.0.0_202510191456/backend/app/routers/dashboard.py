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
from app.currency_conversion_service import CurrencyConversionService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/cashflow")
async def get_cashflow_analysis(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forecast_type: Optional[str] = None,
    project_ids: Optional[str] = None,
    currency_view: Optional[str] = 'unified',  # 'unified' (BASE/IRR) or 'original' (multi-currency)
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
    print(f"DEBUG: Cashflow endpoint called with currency_view='{currency_view}'")
    try:
        # Build query for cashflow events (exclude cancelled events)
        query = select(CashflowEvent).where(CashflowEvent.is_cancelled == False)
        
        # ✅ NEW: Filter by project(s) if specified
        project_id_list = []
        if project_ids:
            project_id_list = [int(pid.strip()) for pid in project_ids.split(',') if pid.strip()]
        
        # PM users can only see INFLOW (revenue) events from ASSIGNED projects
        if current_user.role == "pm":
            # Get PM's assigned projects
            from app.auth import get_user_projects
            assigned_projects = await get_user_projects(db, current_user)
            
            if assigned_projects:
                # Combine project filtering: use project_ids if specified, otherwise use assigned projects
                final_project_ids = project_id_list if project_id_list else assigned_projects
                
                # Single JOIN with finalized_decisions
                query = query.join(
                    FinalizedDecision,
                    CashflowEvent.related_decision_id == FinalizedDecision.id
                ).where(
                    CashflowEvent.event_type == "INFLOW",
                    FinalizedDecision.project_id.in_(final_project_ids)
                )
            else:
                # No assigned projects = no data
                query = query.where(CashflowEvent.id == None)  # Returns empty
        else:
            # Non-PM users: apply project filter if specified
            if project_id_list:
                query = query.join(
                    FinalizedDecision,
                    CashflowEvent.related_decision_id == FinalizedDecision.id
                ).where(FinalizedDecision.project_id.in_(project_id_list))
        
        # Procurement users can only see OUTFLOW (payment) events
        if current_user.role == "procurement":
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
        # Initialize currency conversion service
        currency_service = CurrencyConversionService(db)
        
        if currency_view == 'unified':
            # Unified view: Convert all amounts to base currency (IRR)
            monthly_data = defaultdict(lambda: {"inflow": Decimal(0), "outflow": Decimal(0)})
            
            for event in events:
                month_key = event.event_date.strftime("%Y-%m")
                
                # Get amount in original currency
                amount = event.amount_value if event.amount_value is not None else event.amount
                currency = event.amount_currency if event.amount_currency else 'IRR'
                
                # Convert to base currency (IRR)
                try:
                    if currency != 'IRR':
                        amount_in_irr = await currency_service.convert_to_base(amount, currency, event.event_date)
                    else:
                        amount_in_irr = amount
                except Exception as e:
                    # If conversion fails, use original amount (assume it's in IRR)
                    amount_in_irr = amount
                
                if event.event_type.upper() == "INFLOW":
                    monthly_data[month_key]["inflow"] += amount_in_irr
                else:
                    monthly_data[month_key]["outflow"] += amount_in_irr
        else:
            # Original currency view: Return data grouped by currency
            monthly_data_by_currency = defaultdict(lambda: defaultdict(lambda: {"inflow": Decimal(0), "outflow": Decimal(0)}))

            for event in events:
                month_key = event.event_date.strftime("%Y-%m")

                # Get amount in original currency
                amount = event.amount_value if event.amount_value is not None else event.amount
                currency = event.amount_currency if event.amount_currency else 'IRR'

                if event.event_type.upper() == "INFLOW":
                    monthly_data_by_currency[currency][month_key]["inflow"] += amount
                else:
                    monthly_data_by_currency[currency][month_key]["outflow"] += amount

            # Always set flag for original currency mode (even if no events yet)
            is_multi_currency = True
            print(f"DEBUG: Original currency mode - found {len(monthly_data_by_currency)} currencies: {list(monthly_data_by_currency.keys())}")
        
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
                
                if currency_view == 'unified':
                    # Convert all budget currencies to IRR
                    total_budget_irr = Decimal(budget.available_budget or 0)  # Base budget in IRR
                    print(f"DEBUG: Budget for {month_key} ({budget.budget_date}) - Base IRR: {total_budget_irr}")
                    
                    # Add multi-currency budgets converted to IRR
                    if budget.multi_currency_budget:
                        print(f"DEBUG: Multi-currency budget: {budget.multi_currency_budget}")
                        for curr_code, curr_amount in budget.multi_currency_budget.items():
                            try:
                                if curr_code != 'IRR':
                                    print(f"DEBUG: Converting {curr_amount} {curr_code} on {budget.budget_date}")
                                    converted_amount = await currency_service.convert_to_base(
                                        Decimal(str(curr_amount)), 
                                        curr_code, 
                                        budget.budget_date
                                    )
                                    print(f"DEBUG: Converted to {converted_amount} IRR")
                                    total_budget_irr += converted_amount
                                else:
                                    total_budget_irr += Decimal(str(curr_amount))
                            except Exception as e:
                                # If conversion fails, skip this currency
                                print(f"DEBUG: Conversion failed for {curr_code}: {str(e)}")
                                pass
                    
                    print(f"DEBUG: Total budget for {month_key}: {total_budget_irr}")
                    # Sum budgets for the same month instead of overwriting
                    current_budget = Decimal(monthly_data[month_key].get("budget", 0))
                    monthly_data[month_key]["budget"] = float(current_budget + total_budget_irr)
                else:
                    # Original currency view: distribute budget to appropriate currencies
                    # Base budget goes to IRR (sum if multiple budgets in same month)
                    current_irr_budget = Decimal(monthly_data_by_currency['IRR'][month_key].get("budget", 0))
                    monthly_data_by_currency['IRR'][month_key]["budget"] = float(current_irr_budget + budget.available_budget)
                    
                    # Multi-currency budgets go to their respective currencies (sum if multiple)
                    if budget.multi_currency_budget:
                        for curr_code, curr_amount in budget.multi_currency_budget.items():
                            current_curr_budget = Decimal(monthly_data_by_currency[curr_code][month_key].get("budget", 0))
                            monthly_data_by_currency[curr_code][month_key]["budget"] = float(current_curr_budget + Decimal(str(curr_amount)))
        
        # Build response based on currency view
        if currency_view == 'original' and 'is_multi_currency' in locals() and is_multi_currency:
            # Multi-currency response: Return data grouped by currency
            response_by_currency = {}
            
            for currency_code, currency_monthly_data in monthly_data_by_currency.items():
                sorted_months = sorted(currency_monthly_data.keys())
                cumulative_balance = Decimal(0)
                result_data = []
                
                total_inflow = Decimal(0)
                total_outflow = Decimal(0)
                
                for month in sorted_months:
                    data = currency_monthly_data[month]
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
                
                summary = {
                    "total_inflow": float(total_inflow),
                    "total_outflow": float(total_outflow),
                    "net_position": float(total_inflow - total_outflow),
                    "peak_balance": max([d["cumulative_balance"] for d in result_data]) if result_data else 0,
                    "min_balance": min([d["cumulative_balance"] for d in result_data]) if result_data else 0,
                    "final_balance": float(cumulative_balance)
                }
                
                response_by_currency[currency_code] = {
                    "time_series": result_data,
                    "summary": summary,
                    "period_count": len(result_data)
                }
            
            print(f"DEBUG: Returning multi-currency response with {len(response_by_currency)} currencies")
            return {
                "view_mode": "original",
                "currencies": response_by_currency
            }
        else:
            # Unified response: Single currency (IRR)
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
                "view_mode": "unified",
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

