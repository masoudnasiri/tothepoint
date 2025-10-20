"""
Reseed Decision Factor Weights Only
This script recreates the default decision factor weights without affecting other data.
"""

import asyncio
from sqlalchemy import select, text
from app.database import AsyncSessionLocal
from app.models import DecisionFactorWeight
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def reseed_weights_only():
    """Reseed decision factor weights only"""
    async with AsyncSessionLocal() as db:
        try:
            # Check current weights
            result = await db.execute(select(DecisionFactorWeight))
            existing_weights = result.scalars().all()
            
            if existing_weights:
                logger.info(f"⚠️  Found {len(existing_weights)} existing decision factor weights")
                logger.info("Clearing existing weights...")
                await db.execute(text("DELETE FROM decision_factor_weights"))
                await db.commit()
                logger.info("✅ Cleared existing weights")
            else:
                logger.info("ℹ️  No existing weights found - creating new ones...")
            
            # Create decision factor weights
            weights_data = [
                {
                    'factor_name': 'cost_minimization',
                    'weight': 9,
                    'description': 'Prioritize minimizing total procurement cost'
                },
                {
                    'factor_name': 'lead_time_optimization',
                    'weight': 8,
                    'description': 'Optimize delivery times to meet project deadlines'
                },
                {
                    'factor_name': 'supplier_rating',
                    'weight': 7,
                    'description': 'Consider supplier reliability and quality ratings'
                },
                {
                    'factor_name': 'cash_flow_balance',
                    'weight': 8,
                    'description': 'Balance cash outflows across time periods'
                },
                {
                    'factor_name': 'bundle_discount_maximization',
                    'weight': 6,
                    'description': 'Maximize bulk purchase discounts when possible'
                },
                {
                    'factor_name': 'quality_assurance',
                    'weight': 7,
                    'description': 'Ensure high-quality materials and workmanship'
                },
                {
                    'factor_name': 'risk_mitigation',
                    'weight': 6,
                    'description': 'Minimize procurement and delivery risks'
                },
                {
                    'factor_name': 'sustainability',
                    'weight': 5,
                    'description': 'Prefer environmentally friendly options'
                }
            ]
            
            for weight_data in weights_data:
                weight = DecisionFactorWeight(
                    factor_name=weight_data['factor_name'],
                    weight=weight_data['weight'],
                    description=weight_data['description']
                )
                db.add(weight)
            
            await db.commit()
            logger.info("")
            logger.info("=" * 70)
            logger.info(f"✅ Successfully created {len(weights_data)} decision factor weights!")
            logger.info("=" * 70)
            logger.info("")
            
            # Verify and display
            result = await db.execute(select(DecisionFactorWeight))
            new_weights = result.scalars().all()
            
            logger.info("📊 Decision Factor Weights:")
            for w in new_weights:
                logger.info(f"   {w.id}. {w.factor_name}: {w.weight}/10")
                logger.info(f"      {w.description}")
            
            logger.info("")
            logger.info("✅ Done! Refresh your browser to see the weights in the UI.")
            logger.info("")
            
        except Exception as e:
            logger.error(f"❌ Error reseeding decision weights: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(reseed_weights_only())

