"""
Extract Risk Analysis Data for Professional Review
Shows all source data and calculations step-by-step
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import FinalizedDecision, Project
from app.config import settings
from datetime import date
import statistics
import json

async def extract_risk_data():
    engine = create_async_engine(settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'), echo=False)
    async_session = sessionmaker(engine, class_=__import__('sqlalchemy.ext.asyncio', fromlist=['AsyncSession']).AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("📊 RISK ANALYSIS DATA EXTRACTION")
        print("For Professional Review")
        print("=" * 80)
        
        # Get all locked decisions
        decisions_result = await db.execute(
            select(FinalizedDecision)
            .where(FinalizedDecision.status == 'LOCKED')
            .order_by(FinalizedDecision.project_id, FinalizedDecision.item_code)
        )
        decisions = decisions_result.scalars().all()
        
        print(f"\n📋 Total LOCKED Decisions: {len(decisions)}")
        
        if len(decisions) < 2:
            print("❌ Insufficient data for risk analysis (need at least 2 locked decisions)")
            return
        
        # Extract source data
        print(f"\n{'='*80}")
        print("SOURCE DATA - All LOCKED Decisions")
        print(f"{'='*80}\n")
        
        source_data = []
        for i, d in enumerate(decisions, 1):
            data = {
                'id': d.id,
                'project_id': d.project_id,
                'item_code': d.item_code,
                'quantity': d.quantity,
                'planned_cost': float(d.final_cost),
                'planned_purchase_date': str(d.purchase_date) if d.purchase_date else None,
                'planned_delivery_date': str(d.delivery_date) if d.delivery_date else None,
                'finalized_at': str(d.finalized_at.date()) if d.finalized_at else None,
                'actual_payment_amount': float(d.actual_payment_amount) if d.actual_payment_amount else None,
                'actual_payment_date': str(d.actual_payment_date) if d.actual_payment_date else None,
            }
            source_data.append(data)
            
            # Print first 10 in detail
            if i <= 10:
                print(f"Decision #{i}: {d.item_code}")
                print(f"  Project ID: {d.project_id}")
                print(f"  Planned Cost: ${data['planned_cost']:,.2f}")
                print(f"  Planned Purchase Date: {data['planned_purchase_date']}")
                print(f"  Planned Delivery Date: {data['planned_delivery_date']}")
                print(f"  Finalized At: {data['finalized_at']}")
                print(f"  Actual Payment: ${data['actual_payment_amount'] or 'Not paid yet'}")
                print(f"  Actual Payment Date: {data['actual_payment_date'] or 'Not paid yet'}")
                print()
        
        if len(decisions) > 10:
            print(f"... and {len(decisions) - 10} more decisions")
        
        # Save to JSON for professional review
        with open('/app/risk_analysis_source_data.json', 'w') as f:
            json.dump(source_data, f, indent=2)
        print(f"\n💾 Full source data saved to: risk_analysis_source_data.json")
        
        # CALCULATION 1: TIME DELAYS
        print(f"\n{'='*80}")
        print("CALCULATION 1: TIME DELAY ANALYSIS")
        print(f"{'='*80}\n")
        
        print("Formula: Time Delay = Actual Payment Date - Planned Purchase Date\n")
        
        time_delays = []
        for d in decisions:
            if d.purchase_date and d.actual_payment_date:
                planned = d.purchase_date
                actual = d.actual_payment_date
                delay = (actual - planned).days
                time_delays.append(delay)
                
                if len(time_delays) <= 10:
                    print(f"  {d.item_code}:")
                    print(f"    Planned Purchase: {planned}")
                    print(f"    Actual Payment:   {actual}")
                    print(f"    Delay: {delay} days {'(late)' if delay > 0 else '(early)' if delay < 0 else '(on time)'}")
                    print()
        
        if len(time_delays) > 10:
            print(f"... {len(time_delays) - 10} more delays calculated")
        
        print(f"\n📊 Time Delay Statistics:")
        print(f"   Sample Size: {len(time_delays)} items with actual payment dates")
        
        if time_delays:
            mean_delay = statistics.mean(time_delays)
            sigma_delay = statistics.stdev(time_delays) if len(time_delays) > 1 else 0
            min_delay = min(time_delays)
            max_delay = max(time_delays)
            median_delay = statistics.median(time_delays)
            
            print(f"   Mean (μ): {mean_delay:.2f} days")
            print(f"   Std Dev (σ): {sigma_delay:.2f} days")
            print(f"   Min: {min_delay} days")
            print(f"   Max: {max_delay} days")
            print(f"   Median: {median_delay:.0f} days")
            
            # P50 and P90
            delay_p50 = int(statistics.median(time_delays))
            if len(time_delays) >= 10:
                delay_p90 = int(statistics.quantiles(time_delays, n=10)[8])
            else:
                delay_p90 = int(mean_delay * 1.5)
            
            print(f"\n   P50 (50th percentile): {delay_p50} days")
            print(f"   P90 (90th percentile): {delay_p90} days")
            
            # Risk classification
            time_risk = 'high' if sigma_delay > 30 else 'medium' if sigma_delay > 15 else 'low'
            print(f"\n   Time Risk Level: {time_risk.upper()}")
            print(f"   Classification:")
            print(f"     σ > 30 days → HIGH risk")
            print(f"     σ > 15 days → MEDIUM risk")
            print(f"     σ ≤ 15 days → LOW risk")
        else:
            print(f"   ⚠️  No items have actual payment dates yet")
        
        # CALCULATION 2: COST OVERRUNS
        print(f"\n{'='*80}")
        print("CALCULATION 2: COST OVERRUN ANALYSIS")
        print(f"{'='*80}\n")
        
        print("Formula: Cost Overrun % = (Actual Payment / Planned Cost - 1) × 100\n")
        
        cost_overruns = []
        for d in decisions:
            if d.actual_payment_amount and d.actual_payment_amount > 0:
                planned = float(d.final_cost)
                actual = float(d.actual_payment_amount)
                overrun_pct = (actual / planned - 1.0) * 100
                cost_overruns.append(overrun_pct)
                
                if len(cost_overruns) <= 10:
                    print(f"  {d.item_code}:")
                    print(f"    Planned Cost:  ${planned:,.2f}")
                    print(f"    Actual Payment: ${actual:,.2f}")
                    print(f"    Overrun: {overrun_pct:+.2f}% {'(over budget)' if overrun_pct > 0 else '(under budget)' if overrun_pct < 0 else '(on budget)'}")
                    print()
        
        if len(cost_overruns) > 10:
            print(f"... {len(cost_overruns) - 10} more overruns calculated")
        
        print(f"\n📊 Cost Overrun Statistics:")
        print(f"   Sample Size: {len(cost_overruns)} items with actual payments")
        
        if cost_overruns:
            mean_overrun = statistics.mean(cost_overruns)
            sigma_overrun = statistics.stdev(cost_overruns) if len(cost_overruns) > 1 else 0
            min_overrun = min(cost_overruns)
            max_overrun = max(cost_overruns)
            median_overrun = statistics.median(cost_overruns)
            
            print(f"   Mean (μ): {mean_overrun:+.2f}%")
            print(f"   Std Dev (σ): {sigma_overrun:.2f}%")
            print(f"   Min: {min_overrun:+.2f}%")
            print(f"   Max: {max_overrun:+.2f}%")
            print(f"   Median: {median_overrun:+.2f}%")
            
            # Risk classification
            cost_risk = 'high' if sigma_overrun > 20 else 'medium' if sigma_overrun > 10 else 'low'
            print(f"\n   Cost Risk Level: {cost_risk.upper()}")
            print(f"   Classification:")
            print(f"     σ > 20% → HIGH risk")
            print(f"     σ > 10% → MEDIUM risk")
            print(f"     σ ≤ 10% → LOW risk")
        else:
            print(f"   ⚠️  No items have actual payment amounts yet")
        
        # OVERALL RISK
        print(f"\n{'='*80}")
        print("OVERALL RISK ASSESSMENT")
        print(f"{'='*80}\n")
        
        if time_delays and cost_overruns:
            time_risk = 'high' if sigma_delay > 30 else 'medium' if sigma_delay > 15 else 'low'
            cost_risk = 'high' if sigma_overrun > 20 else 'medium' if sigma_overrun > 10 else 'low'
            
            overall_risk = 'high' if (sigma_delay > 30 or sigma_overrun > 20) else \
                          'medium' if (sigma_delay > 15 or sigma_overrun > 10) else 'low'
            
            print(f"Time Risk: {time_risk.upper()}")
            print(f"Cost Risk: {cost_risk.upper()}")
            print(f"Overall Risk: {overall_risk.upper()}")
            
            print(f"\nInterpretation:")
            if overall_risk == 'low':
                print(f"  ✅ Project shows consistent performance")
                print(f"  ✅ Low variability in delays and costs")
                print(f"  ✅ Predictable execution")
            elif overall_risk == 'medium':
                print(f"  ⚠️  Moderate variability in performance")
                print(f"  ⚠️  Some unpredictability in timelines or costs")
                print(f"  💡 Consider risk mitigation strategies")
            else:
                print(f"  🔴 High variability in performance")
                print(f"  🔴 Significant unpredictability")
                print(f"  🚨 Requires immediate risk management")
        else:
            print(f"⚠️  Insufficient actual data for complete risk analysis")
        
        # Distribution data
        print(f"\n{'='*80}")
        print("DISTRIBUTION DATA (For Histograms)")
        print(f"{'='*80}\n")
        
        print(f"Time Delays (days): {time_delays[:20] if time_delays else 'No data'}")
        print(f"Cost Overruns (%): {[round(c, 2) for c in cost_overruns[:20]] if cost_overruns else 'No data'}")
        
        # Summary for professional review
        print(f"\n{'='*80}")
        print("SUMMARY FOR PROFESSIONAL REVIEW")
        print(f"{'='*80}\n")
        
        summary = {
            'data_collection': {
                'total_locked_decisions': len(decisions),
                'decisions_with_actual_payment_date': len(time_delays),
                'decisions_with_actual_payment_amount': len(cost_overruns),
            },
            'time_delay_analysis': {
                'metric': 'Actual Payment Date - Planned Purchase Date (in days)',
                'sample_size': len(time_delays),
                'mean': round(mean_delay, 2) if time_delays else None,
                'std_dev': round(sigma_delay, 2) if time_delays else None,
                'median': round(median_delay, 2) if time_delays else None,
                'p50': delay_p50 if time_delays else None,
                'p90': delay_p90 if time_delays else None,
                'risk_level': time_risk if time_delays else None,
            },
            'cost_overrun_analysis': {
                'metric': '(Actual Payment / Planned Cost - 1) × 100 (%)',
                'sample_size': len(cost_overruns),
                'mean': round(mean_overrun, 2) if cost_overruns else None,
                'std_dev': round(sigma_overrun, 2) if cost_overruns else None,
                'median': round(median_overrun, 2) if cost_overruns else None,
                'risk_level': cost_risk if cost_overruns else None,
            },
            'overall_risk': overall_risk if (time_delays and cost_overruns) else None,
        }
        
        print(json.dumps(summary, indent=2))
        
        # Save complete dataset
        with open('/app/risk_analysis_complete_data.json', 'w') as f:
            json.dump({
                'source_data': source_data,
                'time_delays': time_delays,
                'cost_overruns': [round(c, 2) for c in cost_overruns],
                'statistics': summary,
            }, f, indent=2)
        
        print(f"\n💾 Complete dataset saved to: risk_analysis_complete_data.json")
        
        # Questions for professional
        print(f"\n{'='*80}")
        print("QUESTIONS FOR PROFESSIONAL REVIEW")
        print(f"{'='*80}\n")
        
        print("1. Time Delay Calculation:")
        print("   Q: Is 'Actual Payment Date - Planned Purchase Date' the correct metric?")
        print("   Alternative: Should we use 'Actual Delivery Date - Planned Delivery Date'?")
        print()
        
        print("2. Cost Overrun Calculation:")
        print("   Q: Is '(Actual Payment / Planned Cost - 1)' correct?")
        print("   Note: Actual Payment may include discounts or installments")
        print()
        
        print("3. Risk Classification Thresholds:")
        print("   Q: Are these thresholds appropriate?")
        print("      Time: σ > 30 days = HIGH, σ > 15 days = MEDIUM")
        print("      Cost: σ > 20% = HIGH, σ > 10% = MEDIUM")
        print()
        
        print("4. Sample Size:")
        print(f"   Q: Is {len(time_delays)} samples sufficient for statistical analysis?")
        print(f"   Q: Is {len(cost_overruns)} samples sufficient for cost variance?")
        print()
        
        print("5. P90 Calculation:")
        print("   Q: Is P90 correctly calculated as 90th percentile of delays?")
        print("   Current method: statistics.quantiles(data, n=10)[8]")
        print()
        
        print(f"{'='*80}\n")

if __name__ == "__main__":
    asyncio.run(extract_risk_data())

