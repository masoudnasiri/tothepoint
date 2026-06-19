"""
Check if reverted items appear in procurement
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.models import FinalizedDecision, ProjectItem
from app.config import settings

async def check():
    engine = create_async_engine(settings.database_url.replace('postgresql://', 'postgresql+asyncpg://'), echo=False)
    async_session = sessionmaker(engine, class_=__import__('sqlalchemy.ext.asyncio', fromlist=['AsyncSession']).AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("🔍 CHECKING REVERTED ITEMS IN PROCUREMENT")
        print("=" * 80)
        
        # Get all REVERTED decisions
        reverted_result = await db.execute(
            select(FinalizedDecision)
            .where(FinalizedDecision.status == 'REVERTED')
        )
        reverted = reverted_result.scalars().all()
        
        print(f"\n📋 Total REVERTED Decisions: {len(reverted)}")
        
        if reverted:
            print(f"\nReverted Items:")
            for d in reverted[:10]:
                print(f"  • {d.item_code} (Project {d.project_id})")
                
                # Check if this item has any LOCKED decisions
                locked_check = await db.execute(
                    select(FinalizedDecision)
                    .where(
                        FinalizedDecision.item_code == d.item_code,
                        FinalizedDecision.status == 'LOCKED'
                    )
                    .limit(1)
                )
                has_locked = locked_check.scalar_one_or_none() is not None
                
                if has_locked:
                    print(f"    ❌ Has LOCKED decision → Will NOT appear in procurement")
                else:
                    print(f"    ✅ No LOCKED decision → SHOULD appear in procurement")
        
        # Now check procurement logic
        print(f"\n{'='*80}")
        print("PROCUREMENT FILTER LOGIC TEST")
        print(f"{'='*80}\n")
        
        # Get all unique item codes
        all_codes_result = await db.execute(
            select(ProjectItem.item_code).distinct()
        )
        all_codes = [row[0] for row in all_codes_result.all()]
        
        print(f"Total unique item codes: {len(all_codes)}")
        
        # Filter out items with LOCKED decisions
        available_codes = []
        
        for code in all_codes:
            locked_check = await db.execute(
                select(FinalizedDecision)
                .where(
                    FinalizedDecision.item_code == code,
                    FinalizedDecision.status == 'LOCKED'
                )
                .limit(1)
            )
            has_locked = locked_check.scalar_one_or_none() is not None
            
            if not has_locked:
                available_codes.append(code)
        
        print(f"Available for procurement: {len(available_codes)}")
        
        # Check if reverted items are in available list
        print(f"\n{'='*80}")
        print("VERIFICATION")
        print(f"{'='*80}\n")
        
        reverted_codes = set(d.item_code for d in reverted)
        available_set = set(available_codes)
        
        reverted_and_available = reverted_codes & available_set
        reverted_but_locked = reverted_codes - available_set
        
        print(f"Reverted items that SHOULD appear: {len(reverted_and_available)}")
        if reverted_and_available:
            for code in list(reverted_and_available)[:10]:
                print(f"  ✅ {code}")
        
        print(f"\nReverted items that WON'T appear (have other LOCKED): {len(reverted_but_locked)}")
        if reverted_but_locked:
            for code in list(reverted_but_locked)[:10]:
                print(f"  ❌ {code} (has LOCKED decision from another project/run)")
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print(f"{'='*80}\n")
        print(f"✅ Reverted items WITHOUT other LOCKED decisions: {len(reverted_and_available)}")
        print(f"   These WILL appear in procurement page")
        print(f"\n❌ Reverted items WITH other LOCKED decisions: {len(reverted_but_locked)}")
        print(f"   These will NOT appear (correct behavior)")
        print(f"\n💡 If you reverted an item and it doesn't show:")
        print(f"   Check if the SAME item_code has a LOCKED decision from another project")
        print(f"{'='*80}\n")

asyncio.run(check())

