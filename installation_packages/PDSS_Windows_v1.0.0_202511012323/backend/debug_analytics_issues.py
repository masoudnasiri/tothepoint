"""
Debug Analytics Issues:
1. Check cashflow events (main dashboard vs analytics dashboard)
2. Check PV calculation (why it's 0)
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import CashflowEvent, FinalizedDecision, Project
from app.config import settings
from datetime import date, timedelta
from collections import defaultdict

async def debug_analytics():
    engine = create_async_engine(settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("🔍 ANALYTICS ISSUES DIAGNOSIS")
        print("=" * 80)
        
        # Get a project with locked decisions
        project_result = await db.execute(
            select(Project).where(Project.is_active == True).limit(1)
        )
        project = project_result.scalars().first()
        
        if not project:
            print("❌ No active projects found")
            return
        
        print(f"\n📊 Analyzing Project: {project.project_code} - {project.name}")
        print(f"   Project ID: {project.id}")
        
        # ISSUE 1: CASHFLOW EVENTS
        print(f"\n{'='*80}")
        print("ISSUE 1: CASHFLOW EVENTS (Main Dashboard vs Analytics)")
        print(f"{'='*80}")
        
        # Get all cashflow events for this project
        events_result = await db.execute(
            select(CashflowEvent)
            .join(FinalizedDecision, CashflowEvent.related_decision_id == FinalizedDecision.id)
            .where(FinalizedDecision.project_id == project.id)
            .where(CashflowEvent.is_cancelled == False)
            .order_by(CashflowEvent.event_date)
        )
        events = events_result.scalars().all()
        
        print(f"\n📋 Total Cashflow Events: {len(events)}")
        
        # Group by type and forecast_type
        grouped = defaultdict(list)
        for event in events:
            key = f"{event.event_type}_{event.forecast_type}"
            grouped[key].append(event)
        
        print(f"\n📊 Breakdown:")
        for key, events_list in grouped.items():
            event_type, forecast_type = key.split('_')
            total_amount = sum(float(e.amount) for e in events_list)
            print(f"   - {event_type} {forecast_type}: {len(events_list)} events, Total: ${total_amount:,.2f}")
            
            # Show first few events
            if events_list:
                print(f"     Sample events:")
                for e in events_list[:3]:
                    print(f"       • Date: {e.event_date}, Amount: ${e.amount}, Desc: {e.description[:40]}...")
        
        # ACTUAL INFLOW specifically
        actual_inflows = [e for e in events if e.event_type == 'INFLOW' and e.forecast_type == 'ACTUAL']
        print(f"\n💰 ACTUAL INFLOW Events: {len(actual_inflows)}")
        for e in actual_inflows:
            print(f"   • Date: {e.event_date}, Amount: ${e.amount}, Decision ID: {e.related_decision_id}")
        
        # Check main dashboard logic
        print(f"\n🔍 Main Dashboard Logic (should show {len(actual_inflows)} actual inflows)")
        
        # Check analytics dashboard logic
        daily_cashflow = {}
        for event in events:
            date_key = event.event_date.isoformat()
            if date_key not in daily_cashflow:
                daily_cashflow[date_key] = {
                    'inflow_forecast': 0,
                    'outflow_forecast': 0,
                    'inflow_actual': 0,
                    'outflow_actual': 0,
                }
            
            amount = float(event.amount)
            if event.event_type.upper() == 'INFLOW':
                if event.forecast_type == 'FORECAST':
                    daily_cashflow[date_key]['inflow_forecast'] += amount
                else:
                    daily_cashflow[date_key]['inflow_actual'] += amount
            else:
                if event.forecast_type == 'FORECAST':
                    daily_cashflow[date_key]['outflow_forecast'] += amount
                else:
                    daily_cashflow[date_key]['outflow_actual'] += amount
        
        print(f"\n📈 Analytics Dashboard Aggregation:")
        actual_inflow_dates = [k for k, v in daily_cashflow.items() if v['inflow_actual'] > 0]
        print(f"   Dates with ACTUAL INFLOW: {len(actual_inflow_dates)}")
        for date_key in sorted(actual_inflow_dates):
            print(f"   • {date_key}: ${daily_cashflow[date_key]['inflow_actual']:,.2f}")
        
        # ISSUE 2: PV CALCULATION
        print(f"\n{'='*80}")
        print("ISSUE 2: PLANNED VALUE (PV) - Why is it 0?")
        print(f"{'='*80}")
        
        # Get finalized decisions
        decisions_result = await db.execute(
            select(FinalizedDecision)
            .where(FinalizedDecision.project_id == project.id)
            .where(FinalizedDecision.status.in_(['LOCKED', 'PROPOSED']))
        )
        decisions = decisions_result.scalars().all()
        
        print(f"\n📋 Total Decisions (LOCKED + PROPOSED): {len(decisions)}")
        
        today = date.today()
        print(f"📅 Today's Date: {today}")
        
        # Calculate PV step by step
        PV = 0
        pv_contributors = []
        future_pv = []
        
        for d in decisions:
            # Calculate planned invoice date
            planned_invoice_date = None
            if d.forecast_invoice_timing_type == 'ABSOLUTE' and d.forecast_invoice_issue_date:
                planned_invoice_date = d.forecast_invoice_issue_date
            elif d.forecast_invoice_timing_type == 'RELATIVE' and d.delivery_date:
                days_after = d.forecast_invoice_days_after_delivery or 30
                planned_invoice_date = d.delivery_date + timedelta(days=days_after)
            
            if planned_invoice_date:
                invoice_amount = float(d.forecast_invoice_amount or 0)
                if planned_invoice_date <= today:
                    PV += invoice_amount
                    pv_contributors.append({
                        'item': d.item_code,
                        'planned_date': planned_invoice_date,
                        'amount': invoice_amount
                    })
                else:
                    future_pv.append({
                        'item': d.item_code,
                        'planned_date': planned_invoice_date,
                        'amount': invoice_amount
                    })
        
        print(f"\n💰 Calculated PV: ${PV:,.2f}")
        
        if pv_contributors:
            print(f"\n✅ Items contributing to PV (planned invoice ≤ today):")
            for item in pv_contributors[:10]:
                print(f"   • {item['item']}: ${item['amount']:,.2f} (planned: {item['planned_date']})")
            if len(pv_contributors) > 10:
                print(f"   ... and {len(pv_contributors) - 10} more")
        else:
            print(f"\n❌ NO items contributing to PV!")
            print(f"\n🔍 Analyzing why:")
            
            # Check delivery dates
            decisions_with_delivery = [d for d in decisions if d.delivery_date]
            print(f"\n   Decisions with delivery_date: {len(decisions_with_delivery)}/{len(decisions)}")
            
            if decisions_with_delivery:
                earliest_delivery = min(d.delivery_date for d in decisions_with_delivery)
                latest_delivery = max(d.delivery_date for d in decisions_with_delivery)
                print(f"   Delivery date range: {earliest_delivery} to {latest_delivery}")
                
                # Calculate invoice dates
                for d in decisions_with_delivery[:5]:
                    days_after = d.forecast_invoice_days_after_delivery or 30
                    invoice_date = d.delivery_date + timedelta(days=days_after)
                    print(f"   • {d.item_code}:")
                    print(f"      Delivery: {d.delivery_date}")
                    print(f"      Invoice (delivery + {days_after} days): {invoice_date}")
                    print(f"      Is invoice ≤ today? {invoice_date <= today}")
        
        if future_pv:
            print(f"\n⏭️  Future PV (planned invoice > today): ${sum(f['amount'] for f in future_pv):,.2f}")
            print(f"   Next planned invoices:")
            for item in sorted(future_pv, key=lambda x: x['planned_date'])[:5]:
                print(f"   • {item['item']}: ${item['amount']:,.2f} (planned: {item['planned_date']})")
        
        # Check BAC
        BAC = sum(float(d.forecast_invoice_amount or 0) for d in decisions)
        print(f"\n📊 BAC (Budget at Completion): ${BAC:,.2f}")
        
        # Summary
        print(f"\n{'='*80}")
        print("SUMMARY & DIAGNOSIS:")
        print(f"{'='*80}")
        
        print(f"\n1️⃣ CASHFLOW ISSUE:")
        print(f"   Main Dashboard: Shows {len(actual_inflows)} ACTUAL INFLOW events")
        print(f"   Analytics Dashboard: Shows {len(actual_inflow_dates)} dates with actual inflow")
        if len(actual_inflows) != len(actual_inflow_dates):
            print(f"   ⚠️  MISMATCH! Analytics may be aggregating by date")
            print(f"   💡 Solution: Analytics aggregates multiple events on same date into one")
        else:
            print(f"   ✅ Both dashboards should show same data")
        
        print(f"\n2️⃣ PV = 0 ISSUE:")
        if PV == 0:
            print(f"   ❌ PV is ZERO because:")
            if not decisions:
                print(f"      • No finalized decisions exist")
            elif not decisions_with_delivery:
                print(f"      • No delivery dates set on decisions")
            elif future_pv:
                print(f"      • All planned invoice dates are in the FUTURE")
                earliest_future = min(f['planned_date'] for f in future_pv)
                print(f"      • Earliest invoice date: {earliest_future}")
                print(f"      • Days until first invoice: {(earliest_future - today).days} days")
                print(f"   💡 Solution: PV will increase as invoice dates pass")
            else:
                print(f"      • Unknown reason - check data integrity")
        else:
            print(f"   ✅ PV = ${PV:,.2f} (correct)")
        
        print(f"\n{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(debug_analytics())

