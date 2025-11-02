"""
Debug cashflow date aggregation issue
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import CashflowEvent, FinalizedDecision, Project
from app.config import settings
from datetime import date

async def debug():
    engine = create_async_engine(settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'), echo=False)
    async_session = sessionmaker(engine, class_=__import__('sqlalchemy.ext.asyncio', fromlist=['AsyncSession']).AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("🔍 CASHFLOW DATE AGGREGATION DEBUG")
        print("=" * 80)
        
        # Get actual inflow events in Feb and Mar 2026
        result = await db.execute(
            select(CashflowEvent)
            .where(CashflowEvent.event_type == 'INFLOW')
            .where(CashflowEvent.forecast_type == 'ACTUAL')
            .where(CashflowEvent.event_date >= date(2026, 2, 1))
            .where(CashflowEvent.event_date < date(2026, 4, 1))
            .where(CashflowEvent.is_cancelled == False)
            .order_by(CashflowEvent.event_date)
        )
        events = result.scalars().all()
        
        print(f"\n📋 ACTUAL INFLOW events in Feb-Mar 2026: {len(events)}")
        
        if not events:
            print("❌ No events found!")
            return
        
        # Group by exact date
        from collections import defaultdict
        by_date = defaultdict(list)
        
        for event in events:
            by_date[event.event_date].append(event)
        
        print(f"\n📅 Events by EXACT DATE:")
        for event_date in sorted(by_date.keys()):
            events_on_date = by_date[event_date]
            total = sum(float(e.amount) for e in events_on_date)
            print(f"\n  {event_date} ({event_date.strftime('%Y-%m')} month):")
            print(f"    Count: {len(events_on_date)} events")
            print(f"    Total: ${total:,.2f}")
            
            for e in events_on_date:
                # Get decision
                dec_result = await db.execute(
                    select(FinalizedDecision).where(FinalizedDecision.id == e.related_decision_id)
                )
                decision = dec_result.scalars().first()
                
                print(f"      • ${e.amount:,.2f} - {e.description[:50]}")
                if decision:
                    print(f"        Item: {decision.item_code}, Project: {decision.project_id}")
        
        # Now test cashflow endpoint logic
        print(f"\n{'='*80}")
        print("CASHFLOW ENDPOINT AGGREGATION LOGIC")
        print(f"{'='*80}\n")
        
        # Get a project with events
        project_result = await db.execute(
            select(Project).where(Project.id == 233).limit(1)
        )
        project = project_result.scalars().first()
        
        if not project:
            print("❌ Project 233 not found")
            return
        
        print(f"Testing with Project: {project.project_code} - {project.name}")
        
        # Get all events for this project
        events_result = await db.execute(
            select(CashflowEvent)
            .join(FinalizedDecision, CashflowEvent.related_decision_id == FinalizedDecision.id)
            .where(FinalizedDecision.project_id == project.id)
            .where(CashflowEvent.is_cancelled == False)
            .order_by(CashflowEvent.event_date)
        )
        all_events = events_result.scalars().all()
        
        print(f"\nTotal events for this project: {len(all_events)}")
        
        # Group by date (as in cashflow endpoint)
        from decimal import Decimal
        daily_cashflow = {}
        
        for event in all_events:
            date_key = event.event_date.isoformat()  # ← THIS IS THE ISSUE!
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
        
        print(f"\n📊 Aggregated by ISO DATE (current method):")
        feb_mar_dates = [k for k in sorted(daily_cashflow.keys()) if k.startswith('2026-02') or k.startswith('2026-03')]
        
        for date_key in feb_mar_dates:
            data = daily_cashflow[date_key]
            if data['inflow_actual'] > 0:
                print(f"  {date_key}: ${data['inflow_actual']:,.2f}")
        
        # Now test monthly aggregation
        print(f"\n📊 Aggregated by MONTH (as chart should show):")
        from datetime import datetime, timedelta
        
        # Method 1: Using date_key.isoformat() and iterating by 30-day intervals
        print(f"\n  Method 1: Current implementation (30-day intervals from start):")
        today = date.today()
        for month_offset in range(-6, 13):
            target_date = today + timedelta(days=30 * month_offset)
            date_key = target_date.isoformat()
            
            if date_key in daily_cashflow:
                data = daily_cashflow[date_key]
                if data['inflow_actual'] > 0:
                    print(f"    {date_key}: ${data['inflow_actual']:,.2f}")
        
        # Method 2: Group by month string
        print(f"\n  Method 2: Better approach (group by YYYY-MM):")
        monthly_cashflow = defaultdict(lambda: {'inflow_actual': Decimal('0')})
        
        for event in all_events:
            if event.event_type == 'INFLOW' and event.forecast_type == 'ACTUAL':
                month_key = event.event_date.strftime('%Y-%m')
                monthly_cashflow[month_key]['inflow_actual'] += event.amount
        
        feb_mar_months = [k for k in sorted(monthly_cashflow.keys()) if k.startswith('2026-02') or k.startswith('2026-03')]
        for month_key in feb_mar_months:
            print(f"    {month_key}: ${monthly_cashflow[month_key]['inflow_actual']:,.2f}")
        
        print(f"\n{'='*80}")
        print("ISSUE IDENTIFIED:")
        print(f"{'='*80}\n")
        print("Current method uses date.isoformat() which gives exact dates:")
        print("  - 2026-02-08 is treated as different from 2026-02-15")
        print("  - When iterating by 30-day intervals, may miss specific dates")
        print("  - For monthly chart, should aggregate by YYYY-MM month")
        print()
        print("Solution: Aggregate by month string, not exact ISO date")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(debug())

