#!/usr/bin/env python3
"""
Script to check and sync cash flow data
"""

import asyncio
import sys
import os
from sqlalchemy import select, func
from decimal import Decimal

# Add the app directory to the path
sys.path.append('/app')

from app.database import get_db
from app.models import CashflowEvent, FinalizedDecision, SupplierPayment
from app.cashflow_sync_service import CashflowSyncService

async def check_cashflow_data():
    """Check existing cash flow data and sync if needed"""
    
    async for db in get_db():
        try:
            print("🔍 Checking existing cash flow data...")
            
            # Check existing cash flow events
            cashflow_result = await db.execute(select(CashflowEvent))
            existing_events = cashflow_result.scalars().all()
            print(f"📊 Found {len(existing_events)} existing cash flow events")
            
            # Check finalized decisions with payment data
            payments_result = await db.execute(
                select(FinalizedDecision).where(
                    FinalizedDecision.actual_payment_date.isnot(None),
                    FinalizedDecision.actual_payment_amount_value.isnot(None)
                )
            )
            payments = payments_result.scalars().all()
            print(f"💰 Found {len(payments)} decisions with payment data")
            
            # Check supplier payments
            supplier_payments_result = await db.execute(select(SupplierPayment))
            supplier_payments = supplier_payments_result.scalars().all()
            print(f"🏪 Found {len(supplier_payments)} supplier payments")
            
            # Check finalized decisions with invoice data
            invoices_result = await db.execute(
                select(FinalizedDecision).where(
                    FinalizedDecision.actual_invoice_issue_date.isnot(None),
                    FinalizedDecision.actual_invoice_amount_value.isnot(None)
                )
            )
            invoices = invoices_result.scalars().all()
            print(f"📄 Found {len(invoices)} decisions with invoice data")
            
            if len(payments) > 0 or len(supplier_payments) > 0 or len(invoices) > 0:
                print("\n🔄 Syncing payments with cash flow system...")
                cashflow_service = CashflowSyncService(db)
                result = await cashflow_service.sync_all_payments()
                
                print(f"✅ Sync completed:")
                print(f"   - Synced: {result['synced_count']} items")
                print(f"   - Errors: {len(result['errors'])}")
                print(f"   - Success: {result['success']}")
                
                if result['errors']:
                    print("❌ Errors encountered:")
                    for error in result['errors'][:5]:  # Show first 5 errors
                        print(f"   - {error}")
            else:
                print("ℹ️  No payment data found to sync")
            
            # Check cash flow events after sync
            cashflow_result_after = await db.execute(select(CashflowEvent))
            events_after = cashflow_result_after.scalars().all()
            print(f"\n📈 Cash flow events after sync: {len(events_after)}")
            
            # Show breakdown by type
            inflow_count = sum(1 for e in events_after if e.event_type == 'INFLOW')
            outflow_count = sum(1 for e in events_after if e.event_type == 'OUTFLOW')
            print(f"   - INFLOW events: {inflow_count}")
            print(f"   - OUTFLOW events: {outflow_count}")
            
            # Show breakdown by forecast type
            forecast_count = sum(1 for e in events_after if e.forecast_type == 'FORECAST')
            actual_count = sum(1 for e in events_after if e.forecast_type == 'ACTUAL')
            print(f"   - FORECAST events: {forecast_count}")
            print(f"   - ACTUAL events: {actual_count}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            await db.close()
        break

if __name__ == "__main__":
    asyncio.run(check_cashflow_data())
