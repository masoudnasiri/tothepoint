import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import FinalizedDecision, CashflowEvent
from app.config import settings

async def check():
    engine = create_async_engine(settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'), echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Check decisions with actual invoice
        result = await db.execute(
            select(FinalizedDecision).where(FinalizedDecision.actual_invoice_amount != None)
        )
        decisions = result.scalars().all()
        print(f'Decisions with actual_invoice_amount: {len(decisions)}')
        for d in decisions[:10]:
            print(f'  {d.item_code}: Invoice=${d.actual_invoice_amount}, Date={d.actual_invoice_issue_date}, Project={d.project_id}')
        
        # Check ACTUAL INFLOW cashflow events
        result2 = await db.execute(
            select(CashflowEvent)
            .where(CashflowEvent.event_type == 'INFLOW')
            .where(CashflowEvent.forecast_type == 'ACTUAL')
        )
        events = result2.scalars().all()
        print(f'\nACTUAL INFLOW CashflowEvents: {len(events)}')
        for e in events[:10]:
            decision_result = await db.execute(
                select(FinalizedDecision).where(FinalizedDecision.id == e.related_decision_id)
            )
            decision = decision_result.scalars().first()
            print(f'  Date={e.event_date}, Amount=${e.amount}, Project={decision.project_id if decision else "N/A"}')

asyncio.run(check())

