import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.routers.analytics import get_portfolio_eva

async def test_portfolio_eva():
    async for db in get_db():
        try:
            print('🔍 TESTING PORTFOLIO EVA ENDPOINT')
            print('=' * 60)
            
            # Test portfolio EVA (all projects)
            result = await get_portfolio_eva(
                currency_view='unified',
                current_user=None,  # Skip auth for test
                db=db
            )
            
            print('📊 PORTFOLIO EVA RESULTS:')
            print(f'  BAC: {result["bac"]:,.2f}')
            print(f'  PV: {result["pv"]:,.2f}')
            print(f'  EV: {result["ev"]:,.2f}')
            print(f'  AC: {result["ac"]:,.2f}')
            print(f'  CPI: {result["cpi"]:.3f}')
            print(f'  SPI: {result["spi"]:.3f}')
            print(f'  CV: {result["cv"]:,.2f}')
            print(f'  SV: {result["sv"]:,.2f}')
            print(f'  EAC: {result["eac"]:,.2f}')
            print(f'  VAC: {result["vac"]:,.2f}')
            
            health = result['health_status']
            print(f'\n🏥 PORTFOLIO HEALTH:')
            print(f'  Overall: {health["overall"]}')
            print(f'  Cost Health: {health["cost"]}')
            print(f'  Schedule Health: {health["schedule"]}')
            
            # Check if this shows the inconsistency
            if result['cpi'] < 0.9 or health['overall'] == 'critical':
                print(f'\n🚨 INCONSISTENCY CONFIRMED!')
                print(f'     - Portfolio view shows CPI: {result["cpi"]:.3f}')
                print(f'     - Portfolio view shows Health: {health["overall"]}')
                print(f'     - Individual projects show CPI: 1.000, Health: healthy')
                print(f'     - This is the bug you reported!')
            
        except Exception as e:
            print('❌ Error:', str(e))
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(test_portfolio_eva())
