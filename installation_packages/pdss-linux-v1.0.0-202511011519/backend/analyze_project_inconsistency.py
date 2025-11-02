import asyncio
import sys
sys.path.append('/app')
from app.database import get_db
from app.routers.analytics import get_earned_value_analytics
from sqlalchemy import select
from app.models import Project, FinalizedDecision

async def analyze_project_analytics_inconsistency():
    async for db in get_db():
        try:
            print('🔍 ANALYZING PROJECT ANALYTICS INCONSISTENCY')
            print('=' * 60)
            
            # Get all active projects
            projects_result = await db.execute(
                select(Project).where(Project.is_active == True)
            )
            projects = projects_result.scalars().all()
            
            print(f'📊 Total active projects: {len(projects)}')
            
            # Analyze each project individually
            print('\n📋 INDIVIDUAL PROJECT ANALYSIS:')
            
            total_ev = 0
            total_ac = 0
            total_pv = 0
            projects_with_issues = []
            
            for project in projects:
                try:
                    # Get analytics for this project
                    analytics_result = await get_earned_value_analytics(
                        project_id=project.id,
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
                    
                    total_ev += ev
                    total_ac += ac
                    total_pv += pv
                    
                    # Check for issues
                    has_issues = False
                    issues = []
                    
                    if cpi < 0.9:
                        has_issues = True
                        issues.append(f'CPI: {cpi:.3f} (over budget)')
                    
                    if spi < 0.9:
                        has_issues = True
                        issues.append(f'SPI: {spi:.3f} (behind schedule)')
                    
                    if cv < 0:
                        has_issues = True
                        issues.append(f'CV: {cv:,.2f} (cost overrun)')
                    
                    health_overall = health['overall']
                    if health_overall == 'critical':
                        has_issues = True
                        issues.append('Health: Critical')
                    
                    if has_issues:
                        projects_with_issues.append({
                            'project': project.name,
                            'project_id': project.id,
                            'issues': issues,
                            'ev': ev,
                            'ac': ac,
                            'pv': pv,
                            'cpi': cpi,
                            'spi': spi,
                            'cv': cv,
                            'health': health_overall
                        })
                    
                    print(f'  Project {project.id} ({project.name}):')
                    print(f'    EV: {ev:,.2f}, AC: {ac:,.2f}, PV: {pv:,.2f}')
                    print(f'    CPI: {cpi:.3f}, SPI: {spi:.3f}, CV: {cv:,.2f}')
                    print(f'    Health: {health_overall}')
                    if has_issues:
                        issues_str = ', '.join(issues)
                        print(f'    ⚠️  ISSUES: {issues_str}')
                    else:
                        print(f'    ✅ No issues')
                    
                except Exception as e:
                    print(f'  ❌ Error analyzing project {project.id}: {str(e)}')
            
            # Calculate aggregate metrics
            print('\n📊 AGGREGATE ANALYSIS:')
            print(f'  Total EV: {total_ev:,.2f}')
            print(f'  Total AC: {total_ac:,.2f}')
            print(f'  Total PV: {total_pv:,.2f}')
            
            if total_ac > 0:
                aggregate_cpi = total_ev / total_ac
                print(f'  Aggregate CPI: {aggregate_cpi:.3f}')
                
                if aggregate_cpi < 0.9:
                    print(f'  ⚠️  AGGREGATE CPI INDICATES OVER BUDGET')
                else:
                    print(f'  ✅ Aggregate CPI indicates on/under budget')
            
            aggregate_cv = total_ev - total_ac
            print(f'  Aggregate CV: {aggregate_cv:,.2f}')
            
            if aggregate_cv < 0:
                print(f'  ⚠️  AGGREGATE CV INDICATES COST OVERRUN')
            else:
                print(f'  ✅ Aggregate CV indicates under budget')
            
            # Show projects with issues
            print('\n🚨 PROJECTS WITH ISSUES:')
            if projects_with_issues:
                for project_data in projects_with_issues:
                    print(f'  Project: {project_data["project"]} (ID: {project_data["project_id"]})')
                    issues_str = ', '.join(project_data['issues'])
                    print(f'    Issues: {issues_str}')
                    print(f'    CPI: {project_data["cpi"]:.3f}, CV: {project_data["cv"]:,.2f}')
            else:
                print('  ❌ NO INDIVIDUAL PROJECTS SHOW ISSUES')
                print('  ⚠️  This is the inconsistency you reported!')
            
            print('\n💡 ANALYSIS:')
            if len(projects_with_issues) == 0 and (total_ev / total_ac < 0.9 or aggregate_cv < 0):
                print('  🚨 INCONSISTENCY CONFIRMED:')
                print('     - Aggregate view shows over budget/critical health')
                print('     - No individual projects show these issues')
                print('     - This suggests a calculation error in individual project analytics')
            elif len(projects_with_issues) > 0:
                print('  ✅ CONSISTENCY CONFIRMED:')
                print('     - Individual projects with issues found')
                print('     - Aggregate view correctly reflects these issues')
            
        except Exception as e:
            print('❌ Error:', str(e))
            import traceback
            traceback.print_exc()
        finally:
            await db.close()

if __name__ == "__main__":
    asyncio.run(analyze_project_analytics_inconsistency())
