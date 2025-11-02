import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.models import ProcurementOption
from sqlalchemy import select, update
from datetime import date, timedelta

async def populate_purchase_dates():
    async for db in get_db():
        try:
            print('🔧 Populating purchase_date field for existing procurement options...')
            
            # Get all procurement options that have expected_delivery_date but no purchase_date
            result = await db.execute(
                select(ProcurementOption).where(
                    ProcurementOption.expected_delivery_date.isnot(None),
                    ProcurementOption.purchase_date.is_(None)
                )
            )
            options = result.scalars().all()
            
            print(f'Found {len(options)} procurement options to update')
            
            updated_count = 0
            for option in options:
                if option.expected_delivery_date and option.lomc_lead_time:
                    # Calculate purchase_date = expected_delivery_date - lead_time
                    purchase_date = option.expected_delivery_date - timedelta(days=option.lomc_lead_time)
                    
                    # Update the option
                    await db.execute(
                        update(ProcurementOption)
                        .where(ProcurementOption.id == option.id)
                        .values(purchase_date=purchase_date)
                    )
                    
                    updated_count += 1
                    print(f'  Updated option {option.id}: purchase_date = {purchase_date} (delivery: {option.expected_delivery_date}, lead: {option.lomc_lead_time} days)')
            
            await db.commit()
            print(f'✅ Successfully updated {updated_count} procurement options with purchase_date')
            
            # Verify the updates
            result = await db.execute(
                select(ProcurementOption).where(
                    ProcurementOption.purchase_date.isnot(None)
                )
            )
            updated_options = result.scalars().all()
            print(f'📊 Total procurement options with purchase_date: {len(updated_options)}')
            
            break
        except Exception as e:
            print(f'❌ ERROR: {e}')
            import traceback
            traceback.print_exc()
            break

asyncio.run(populate_purchase_dates())
