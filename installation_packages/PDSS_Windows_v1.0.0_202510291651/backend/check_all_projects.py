import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.routers.analytics import get_earned_value_analytics

async def check_all_projects_view():
    async for db in get_db():
        try:
            print('🔍 CHECKING ALL PROJECTS VIEW')
            print('=' * 60)
            
            # Get analytics for ALL projects (no project_id filter)
            analytics_result = await get_earned_value_analytics(
                project_id=None,  # This should show ALL projects
                currency_view='unified',
                current_user=None,  # Skip auth for test
                db=db
            )
            
            metrics = analytics_result['metrics']
            health = analytics_result['health_status']
            
            ev = metrics['ev']
            ac = metrics['ac']
            pv = metrics['pv']
            cpi = metrics['cpi']
            spi = metrics['spi']
            cv = metrics['cv']
            
            print(f'📊 ALL PROJECTS METRICS:')
            print(f'  EV: {ev:,.2f}')
            print(f'  AC: {ac:,.2f}')
            print(f'  PV: {pv:,.2f}')
            print(f'  CPI: {cpi:.3f}')
            print(f'  SPI: {spi:.3f}')
            print(f'  CV: {cv:,.2f}')
            
            print(f'\n🏥 ALL PROJECTS HEALTH:')
            health_overall = health['overall']
            health_cost = health['cost']
            health_schedule = health['schedule']
            print(f'  Overall: {health_overall}')
            print(f'  Cost Health: {health_cost}')
            print(f'  Schedule Health: {health_schedule}')
            
            # Check if this matches what user sees
            print(f'\n💡 COMPARISON WITH INDIVIDUAL PROJECTS:')
            print(f'  Individual projects show: CPI=1.000, Health=healthy')
            print(f'  All projects shows: CPI={cpi:.3f}, Health={health_overall}')
            
            if cpi < 0.9 or health_overall == 'critical':
                print(f'  🚨 INCONSISTENCY CONFIRMED!')
                print(f'     - All projects view shows problems')
                print(f'     - Individual projects show no problems')
                print(f'     - This is the bug you reported')
            else:
                print(f'  ✅ No inconsistency found')
            
        except Exception as e:
            print('❌ Error:', str(e))
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(check_all_projects_view())
