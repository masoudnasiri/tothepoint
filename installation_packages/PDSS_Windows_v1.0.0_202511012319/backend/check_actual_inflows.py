"""Check actual inflow events across all projects"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import CashflowEvent, FinalizedDecision
from app.config import settings

async def check():
    engine = create_async_engine(settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get ALL actual inflow events
        result = await db.execute(
            select(CashflowEvent)
            .where(CashflowEvent.event_type == 'INFLOW')
            .where(CashflowEvent.forecast_type == 'ACTUAL')
            .where(CashflowEvent.is_cancelled == False)
        )
        actual_inflows = result.scalars().all()
        
        print(f"Total ACTUAL INFLOW events: {len(actual_inflows)}")
        
        if actual_inflows:
            print(f"\nDetails:")
            for event in actual_inflows:
                # Get related decision
                dec_result = await db.execute(
                    select(FinalizedDecision).where(FinalizedDecision.id == event.related_decision_id)
                )
                decision = dec_result.scalars().first()
                
                print(f"  • Event ID: {event.id}")
                print(f"    Date: {event.event_date}")
                print(f"    Amount: ${event.amount}")
                print(f"    Description: {event.description}")
                if decision:
                    print(f"    Project ID: {decision.project_id}")
                    print(f"    Item: {decision.item_code}")
                print()

asyncio.run(check())

