"""
Reseed the database with fresh test data (preserving users)
"""
import asyncio
import sys
sys.path.append('/app')

from app.database import AsyncSessionLocal
from app.seed_data import (
    create_comprehensive_projects,
    create_project_assignments,
    create_project_phases,
    create_comprehensive_project_items,
    create_comprehensive_procurement_options,
    create_comprehensive_delivery_options,
    create_comprehensive_budget_data,
    create_decision_factor_weights
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def reseed():
    """Reseed all project data (preserving users)"""
    async with AsyncSessionLocal() as db:
        try:
            logger.info("Starting data seeding (users preserved)...")
            
            await create_comprehensive_projects(db)
            logger.info("✅ Projects created")
            
            await create_project_assignments(db)
            logger.info("✅ Project assignments created")
            
            await create_project_phases(db)
            logger.info("✅ Project phases created")
            
            await create_comprehensive_project_items(db)
            logger.info("✅ Project items created")
            
            await create_comprehensive_procurement_options(db)
            logger.info("✅ Procurement options created")
            
            await create_comprehensive_delivery_options(db)
            logger.info("✅ Delivery options created")
            
            await create_comprehensive_budget_data(db)
            logger.info("✅ Budget data created")
            
            await create_decision_factor_weights(db)
            logger.info("✅ Decision factor weights created")
            
            logger.info("✅✅✅ All data seeding completed successfully!")
            
        except Exception as e:
            logger.error(f"Error seeding data: {str(e)}")
            await db.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(reseed())

