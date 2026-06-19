"""
Wipe calculated/results data while keeping base input data

DELETES:
- Optimization results
- Optimization runs
- Finalized decisions
- Cashflow events

KEEPS:
- Users
- Projects, Project Items, Delivery Options
- Procurement Options
- Budget Data
- Decision Factor Weights
"""

import asyncio
from sqlalchemy import text
from app.database import AsyncSessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def wipe_calculated_data():
    """Wipe only calculated/results data, keep base data"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting to wipe calculated data...")
            
            # Delete in correct order (respecting foreign keys)
            tables_to_clear = [
                ("cashflow_events", "Cashflow Events"),
                ("finalized_decisions", "Finalized Decisions"),
                ("optimization_results", "Optimization Results"),
                ("optimization_runs", "Optimization Runs"),
            ]
            
            total_deleted = 0
            
            for table_name, display_name in tables_to_clear:
                # Count before delete
                count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = count_result.scalar()
                
                if count > 0:
                    # Delete all rows
                    await db.execute(text(f"DELETE FROM {table_name}"))
                    logger.info(f"✅ Deleted {count} rows from {display_name}")
                    total_deleted += count
                else:
                    logger.info(f"⏭️  {display_name} already empty")
            
            await db.commit()
            
            logger.info("=" * 60)
            logger.info(f"✅ Successfully wiped {total_deleted} calculated records!")
            logger.info("=" * 60)
            logger.info("")
            logger.info("DELETED:")
            logger.info("  - All optimization runs and results")
            logger.info("  - All finalized decisions")
            logger.info("  - All cashflow events")
            logger.info("")
            logger.info("KEPT (Unchanged):")
            logger.info("  - Users")
            logger.info("  - Projects, Project Items, Delivery Options")
            logger.info("  - Procurement Options")
            logger.info("  - Budget Data")
            logger.info("  - Decision Factor Weights")
            logger.info("")
            logger.info("You can now run fresh optimizations!")
            
        except Exception as e:
            logger.error(f"❌ Error wiping data: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(wipe_calculated_data())

