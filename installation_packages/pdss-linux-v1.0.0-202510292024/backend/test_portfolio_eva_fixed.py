import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.routers.analytics import get_portfolio_eva

async def test_portfolio_eva():
    async for db in get_db():
        try:
            print('🔍 TESTING PORTFOLIO EVA ENDPOINT (AFTER FIX)')
            print('=' * 60)
            
            # Test portfolio EVA (all projects)
            result = await get_portfolio_eva(
                currency_view='unified',
                current_user=None,  # Skip auth for test
                db=db
            )
            
            print('📊 PORTFOLIO EVA RESULTS:')
            metrics = result['metrics']
            print(f'  BAC: {metrics["bac"]:,.2f}')
            print(f'  PV: {metrics["pv"]:,.2f}')
            print(f'  EV: {metrics["ev"]:,.2f}')
            print(f'  AC: {metrics["ac"]:,.2f}')
            print(f'  CPI: {metrics["cpi"]:.3f}')
            print(f'  SPI: {metrics["spi"]:.3f}')
            print(f'  CV: {metrics["cv"]:,.2f}')
            print(f'  SV: {metrics["sv"]:,.2f}')
            print(f'  EAC: {metrics["eac"]:,.2f}')
            print(f'  VAC: {metrics["vac"]:,.2f}')
            
            health = result['health_status']
            print(f'\n🏥 PORTFOLIO HEALTH:')
            print(f'  Overall: {health["overall"]}')
            print(f'  Cost Health: {health["cost_performance"]}')
            print(f'  Schedule Health: {health["schedule_performance"]}')
            
            # Check if this shows the inconsistency
            if metrics['cpi'] < 0.9 or health['overall'] == 'critical':
                print(f'\n🚨 INCONSISTENCY STILL EXISTS!')
                print(f'     - Portfolio view shows CPI: {metrics["cpi"]:.3f}')
                print(f'     - Portfolio view shows Health: {health["overall"]}')
                print(f'     - Individual projects show CPI: 1.000, Health: healthy')
                print(f'     - Fix did not work')
            else:
                print(f'\n✅ INCONSISTENCY FIXED!')
                print(f'     - Portfolio view now shows CPI: {metrics["cpi"]:.3f}')
                print(f'     - Portfolio view now shows Health: {health["overall"]}')
                print(f'     - This matches individual projects')
            
        except Exception as e:
            print('❌ Error:', str(e))
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(test_portfolio_eva())
