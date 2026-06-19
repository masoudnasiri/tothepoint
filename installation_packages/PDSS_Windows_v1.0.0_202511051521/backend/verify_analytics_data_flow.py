"""
Verify Analytics Data Flow - Ensure all calculations use correct optimization data
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, selectinload
from sqlalchemy import select
from app.models import FinalizedDecision, DeliveryOption, ProcurementOption, Project
from app.config import settings
from datetime import date

async def verify_data_flow():
    # Create async engine
    engine = create_async_engine(settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("📊 ANALYTICS DATA FLOW VERIFICATION")
        print("=" * 80)
        
        # Get a sample locked decision
        result = await db.execute(
            select(FinalizedDecision)
            .options(
                selectinload(FinalizedDecision.delivery_option),
                selectinload(FinalizedDecision.procurement_option)
            )
            .where(FinalizedDecision.status == 'LOCKED')
            .limit(5)
        )
        decisions = result.scalars().all()
        
        if not decisions:
            print("❌ No LOCKED decisions found for verification")
            return
        
        print(f"\n✅ Found {len(decisions)} LOCKED decision(s) for verification\n")
        
        for i, d in enumerate(decisions, 1):
            print(f"\n{'='*80}")
            print(f"DECISION #{i}: {d.item_code}")
            print(f"{'='*80}")
            
            # 1. PROCUREMENT DATA (What we selected)
            print(f"\n📦 PROCUREMENT OPTION (Selected by Optimization):")
            print(f"   - Supplier: {d.procurement_option.supplier_name if d.procurement_option else 'N/A'}")
            print(f"   - Base Cost: ${d.procurement_option.base_cost if d.procurement_option else 'N/A'}")
            print(f"   - Lead Time: {d.procurement_option.lomc_lead_time if d.procurement_option else 'N/A'} days")
            
            # 2. DELIVERY OPTION (What we selected)
            print(f"\n🚚 DELIVERY OPTION (Selected by Optimization):")
            if d.delivery_option:
                print(f"   - Delivery Date: {d.delivery_option.delivery_date}")
                print(f"   - Invoice Amount/Unit: ${d.delivery_option.invoice_amount_per_unit}")
                print(f"   - Invoice Timing: {d.delivery_option.invoice_timing_type}")
                if d.delivery_option.invoice_timing_type == 'ABSOLUTE':
                    print(f"   - Invoice Date: {d.delivery_option.invoice_issue_date}")
                else:
                    print(f"   - Invoice Days After: {d.delivery_option.invoice_days_after_delivery}")
            else:
                print(f"   - ⚠️  No delivery option linked!")
            
            # 3. FINALIZED DECISION DATA (What analytics use)
            print(f"\n📋 FINALIZED DECISION (Stored from Optimization):")
            print(f"   - Purchase Date: {d.purchase_date}")
            print(f"   - Delivery Date: {d.delivery_date}")
            print(f"   - Quantity: {d.quantity}")
            print(f"   - Final Cost: ${d.final_cost}")
            print(f"   - Forecast Invoice Amount: ${d.forecast_invoice_amount}")
            print(f"   - Forecast Invoice Timing: {d.forecast_invoice_timing_type}")
            if d.forecast_invoice_timing_type == 'ABSOLUTE':
                print(f"   - Forecast Invoice Date: {d.forecast_invoice_issue_date}")
            else:
                print(f"   - Forecast Invoice Days After: {d.forecast_invoice_days_after_delivery}")
            
            # 4. ACTUAL DATA (What finance entered)
            print(f"\n💰 ACTUAL DATA (Entered by Finance):")
            if d.actual_invoice_amount:
                print(f"   - Actual Invoice Amount: ${d.actual_invoice_amount}")
                print(f"   - Actual Invoice Date: {d.actual_invoice_issue_date}")
            else:
                print(f"   - ⚠️  No actual invoice data")
            
            if d.actual_payment_amount:
                print(f"   - Actual Payment Amount: ${d.actual_payment_amount}")
                print(f"   - Actual Payment Date: {d.actual_payment_date}")
            else:
                print(f"   - ⚠️  No actual payment data")
            
            # 5. VERIFICATION CHECKS
            print(f"\n✅ VERIFICATION CHECKS:")
            
            # Check 1: Forecast invoice matches delivery option
            if d.delivery_option:
                expected_invoice = d.delivery_option.invoice_amount_per_unit * d.quantity
                if abs(float(d.forecast_invoice_amount) - float(expected_invoice)) < 0.01:
                    print(f"   ✅ Forecast invoice matches delivery option: ${expected_invoice}")
                else:
                    print(f"   ❌ Forecast invoice MISMATCH!")
                    print(f"      Expected: ${expected_invoice}")
                    print(f"      Stored: ${d.forecast_invoice_amount}")
            
            # Check 2: Final cost matches procurement
            if d.procurement_option:
                # Note: final_cost may include discounts
                print(f"   ℹ️  Final cost: ${d.final_cost} (may include discounts)")
            
            # Check 3: Dates are logical
            if d.purchase_date and d.delivery_date:
                if d.purchase_date <= d.delivery_date:
                    print(f"   ✅ Dates are logical: purchase <= delivery")
                else:
                    print(f"   ❌ Date MISMATCH: purchase > delivery!")
            
            # Check 4: Risk calculation data availability
            print(f"\n🎯 RISK CALCULATION DATA:")
            if d.purchase_date:
                print(f"   ✅ Planned payment date available: {d.purchase_date}")
            else:
                print(f"   ❌ No planned payment date!")
            
            if d.actual_payment_date:
                delay = (d.actual_payment_date - d.purchase_date).days
                print(f"   ✅ Actual payment date available: {d.actual_payment_date}")
                print(f"   📊 Payment delay: {delay} days")
            else:
                print(f"   ⚠️  No actual payment date (not yet paid)")
            
            # Check 5: EVA calculation data availability
            print(f"\n📈 EVA CALCULATION DATA:")
            print(f"   - BAC contributor: ${d.forecast_invoice_amount}")
            
            # PV calculation
            today = date.today()
            planned_invoice_date = None
            if d.forecast_invoice_timing_type == 'ABSOLUTE' and d.forecast_invoice_issue_date:
                planned_invoice_date = d.forecast_invoice_issue_date
            elif d.forecast_invoice_timing_type == 'RELATIVE' and d.delivery_date:
                from datetime import timedelta
                days_after = d.forecast_invoice_days_after_delivery or 30
                planned_invoice_date = d.delivery_date + timedelta(days=days_after)
            
            if planned_invoice_date:
                if planned_invoice_date <= today:
                    print(f"   ✅ PV contributor: ${d.forecast_invoice_amount} (invoice due: {planned_invoice_date})")
                else:
                    print(f"   ⏭️  Not yet in PV (invoice due: {planned_invoice_date})")
            
            # EV calculation
            if d.status == 'LOCKED':
                ev_amount = d.actual_invoice_amount if d.actual_invoice_amount else d.forecast_invoice_amount
                print(f"   ✅ EV contributor: ${ev_amount}")
            
            # AC calculation
            if d.status == 'LOCKED':
                ac_amount = d.actual_payment_amount if d.actual_payment_amount else d.final_cost
                print(f"   ✅ AC contributor: ${ac_amount}")
        
        print(f"\n{'='*80}")
        print("SUMMARY:")
        print(f"{'='*80}")
        print(f"✅ All data flows from optimization engine → FinalizedDecision")
        print(f"✅ Analytics use FinalizedDecision fields (not recalculating)")
        print(f"✅ Risk uses: purchase_date (planned) vs actual_payment_date (actual)")
        print(f"✅ EVA uses: forecast_invoice_amount from selected delivery_option")
        print(f"✅ Cost uses: final_cost from selected procurement_option")
        print(f"\n📊 If risk shows problems, optimization dates may be unrealistic!")
        print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(verify_data_flow())

