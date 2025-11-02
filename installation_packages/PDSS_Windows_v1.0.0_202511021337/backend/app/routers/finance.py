"""
Finance and optimization endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from io import BytesIO
from app.database import get_db
from app.auth import get_current_user, require_finance
from app.crud import (
    create_budget_data, get_budget_data, get_all_budget_data,
    update_budget_data, delete_budget_data, get_optimization_results,
    get_latest_optimization_run, get_dashboard_stats
)
from app.optimization_engine import ProcurementOptimizer
from app.optimization_engine_enhanced import (
    EnhancedProcurementOptimizer, SolverType, OptimizationStrategy
)
from app.excel_handler import ExcelHandler
from app.models import User
from app.schemas import (
    BudgetData, BudgetDataCreate, BudgetDataUpdate,
    OptimizationResult, OptimizationRunRequest, OptimizationRunResponse,
    DashboardStats, ExcelImportResponse
)

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_finance_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get finance dashboard statistics"""
    return await get_dashboard_stats(db)


@router.get("/budget", response_model=List[BudgetData])
async def list_budget_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all budget data"""
    return await get_all_budget_data(db)


@router.post("/budget", response_model=BudgetData)
async def create_new_budget_data(
    budget: BudgetDataCreate,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Create new budget data (finance user only)"""
    # Check if budget for this date already exists
    existing = await get_budget_data(db, str(budget.budget_date))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget data for date {budget.budget_date} already exists"
        )
    
    return await create_budget_data(db, budget)


@router.get("/budget/{budget_date}", response_model=BudgetData)
async def get_budget_data_by_date(
    budget_date: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get budget data by date"""
    budget = await get_budget_data(db, budget_date)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget data not found"
        )
    return budget


@router.put("/budget/{budget_date}", response_model=BudgetData)
async def update_budget_data_by_date(
    budget_date: str,
    budget_update: BudgetDataUpdate,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Update budget data (finance user only)"""
    budget = await update_budget_data(db, budget_date, budget_update)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget data not found"
        )
    return budget


@router.delete("/budget/{budget_date}")
async def delete_budget_data_by_date(
    budget_date: str,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Delete budget data (finance user only)"""
    success = await delete_budget_data(db, budget_date)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget data not found"
        )
    return {"message": "Budget data deleted successfully"}


@router.post("/optimize", response_model=OptimizationRunResponse)
async def run_optimization(
    request: OptimizationRunRequest,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Run procurement optimization (finance user only) - Legacy CP-SAT solver"""
    optimizer = ProcurementOptimizer(db)
    return await optimizer.run_optimization(request)


@router.post("/optimize-enhanced", response_model=OptimizationRunResponse)
async def run_enhanced_optimization(
    request: OptimizationRunRequest,
    solver_type: SolverType = Query(SolverType.CP_SAT, description="Solver type to use"),
    generate_multiple_proposals: bool = Query(False, description="Generate multiple proposals with different strategies"),
    strategies: Optional[List[OptimizationStrategy]] = Query(None, description="Strategies to use (default: all)"),
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """
    Run advanced optimization with solver and strategy selection.
    
    **Solver Types:**
    - **CP_SAT**: Constraint Programming (default) - Best for complex constraints and non-linear problems
    - **GLOP**: Linear Programming - Fast for large-scale linear problems
    - **SCIP**: Mixed-Integer Programming - Balance between CP and LP
    - **CBC**: Coin-or Branch and Cut - Alternative MIP solver
    
    **Strategies:**
    - **LOWEST_COST**: Minimize total procurement cost
    - **PRIORITY_WEIGHTED**: Weight decisions by project priority
    - **FAST_DELIVERY**: Minimize delivery time
    - **SMOOTH_CASHFLOW**: Balance cash flow across periods
    - **BALANCED**: Balance all factors
    """
    optimizer = EnhancedProcurementOptimizer(db, solver_type=solver_type)
    return await optimizer.run_optimization(
        request, 
        generate_multiple_proposals=generate_multiple_proposals,
        strategies=strategies
    )


@router.get("/solver-info")
async def get_solver_information(current_user: User = Depends(get_current_user)):
    """
    Get information about available solvers and their characteristics.
    """
    return {
        "available_solvers": [
            {
                "type": "CP_SAT",
                "name": "Constraint Programming SAT",
                "description": "Google's constraint programming solver with SAT engine",
                "best_for": "Complex constraints, logical conditions, non-linear relationships",
                "performance": "Excellent for medium-sized problems with complex constraints",
                "supports_strategies": True
            },
            {
                "type": "GLOP",
                "name": "Google Linear Optimizer",
                "description": "Linear programming solver optimized for large-scale problems",
                "best_for": "Pure linear objectives and constraints, very large problems",
                "performance": "Very fast for linear problems",
                "supports_strategies": True,
                "note": "Uses LP relaxation with rounding for integer solutions"
            },
            {
                "type": "SCIP",
                "name": "Solving Constraint Integer Programs",
                "description": "Mixed-integer programming solver",
                "best_for": "Mixed-integer linear problems, academic/research use",
                "performance": "Excellent for MIP problems",
                "supports_strategies": True
            },
            {
                "type": "CBC",
                "name": "Coin-or Branch and Cut",
                "description": "Open-source MIP solver from COIN-OR",
                "best_for": "Mixed-integer problems, production environments",
                "performance": "Good balance of speed and solution quality",
                "supports_strategies": True
            }
        ],
        "available_strategies": [
            {
                "type": "LOWEST_COST",
                "name": "Lowest Cost",
                "description": "Minimize total procurement cost without weighting",
                "objective": "Pure cost minimization"
            },
            {
                "type": "PRIORITY_WEIGHTED",
                "name": "Priority-Weighted",
                "description": "Weight costs by project priority (high priority = lower weight)",
                "objective": "Prioritize important projects"
            },
            {
                "type": "FAST_DELIVERY",
                "name": "Fast Delivery",
                "description": "Minimize total delivery time",
                "objective": "Get items delivered as soon as possible"
            },
            {
                "type": "SMOOTH_CASHFLOW",
                "name": "Smooth Cash Flow",
                "description": "Distribute spending evenly across time periods",
                "objective": "Avoid cash flow spikes"
            },
            {
                "type": "BALANCED",
                "name": "Balanced",
                "description": "Balance cost, priority, and delivery time",
                "objective": "Multi-criteria optimization"
            }
        ]
    }


@router.get("/optimization-run/{run_id}")
async def get_optimization_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific optimization run with all its data.
    Note: Enhanced runs store proposals in request_parameters.
    Legacy runs need to be reconstructed from optimization_results.
    """
    from app.models import OptimizationRun, OptimizationResult
    import uuid as uuid_lib
    
    try:
        run_uuid = uuid_lib.UUID(run_id)
        
        # Get the optimization run
        run_query = await db.execute(
            select(OptimizationRun).where(OptimizationRun.run_id == run_uuid)
        )
        run = run_query.scalars().first()
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Optimization run not found"
            )
        
        # Get optimization results
        results_query = await db.execute(
            select(OptimizationResult).where(OptimizationResult.run_id == run_uuid)
        )
        results = results_query.scalars().all()
        
        return {
            "run_id": str(run.run_id),
            "run_timestamp": run.run_timestamp,
            "status": run.status,
            "request_parameters": run.request_parameters,
            "results_count": len(results),
            "results": [
                {
                    "id": r.id,
                    "project_id": r.project_id,
                    "item_code": r.item_code,
                    "procurement_option_id": r.procurement_option_id,
                    "purchase_time": r.purchase_time,
                    "delivery_time": r.delivery_time,
                    "quantity": r.quantity,
                    "final_cost": float(r.final_cost)
                }
                for r in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve optimization run: {str(e)}"
        )


@router.get("/optimization-analysis/{run_id}")
async def get_optimization_analysis(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed analysis of an optimization run including graph-based insights.
    """
    # Create a temporary optimizer to analyze the results
    optimizer = EnhancedProcurementOptimizer(db)
    await optimizer._load_data()
    optimizer._build_dependency_graph()
    
    # Get network analysis
    network_analysis = optimizer.analyze_network_flow()
    critical_path = optimizer.get_critical_path()
    
    return {
        "run_id": run_id,
        "network_analysis": network_analysis,
        "critical_path": critical_path,
        "critical_path_length": len(critical_path),
        "analysis_notes": {
            "total_items": network_analysis.get('total_nodes', 0),
            "dependencies": network_analysis.get('total_edges', 0),
            "components": network_analysis.get('connected_components', 0),
            "critical_items": len(critical_path)
        }
    }


@router.get("/optimization-results", response_model=List[OptimizationResult])
async def list_optimization_results(
    run_id: str = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get optimization results"""
    return await get_optimization_results(db, run_id=run_id, skip=skip, limit=limit)


@router.get("/optimization-results/{run_id}", response_model=List[OptimizationResult])
async def get_optimization_results_by_run_id(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get optimization results for a specific run"""
    return await get_optimization_results(db, run_id=run_id)


@router.get("/latest-optimization")
async def get_latest_optimization_run_id(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the latest optimization run ID"""
    run_id = await get_latest_optimization_run(db)
    if not run_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No optimization runs found"
        )
    return {"run_id": run_id}


@router.get("/optimization-runs")
async def list_optimization_runs(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all optimization runs with summary information.
    Returns runs in reverse chronological order.
    """
    from app.models import OptimizationRun, OptimizationResult
    
    try:
        # Get all optimization runs
        runs_query = await db.execute(
            select(OptimizationRun)
            .order_by(OptimizationRun.run_timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        runs = runs_query.scalars().all()
        
        # For each run, get summary stats
        runs_with_stats = []
        for run in runs:
            # Count results
            results_query = await db.execute(
                select(func.count(OptimizationResult.id))
                .where(OptimizationResult.run_id == run.run_id)
            )
            results_count = results_query.scalar() or 0
            
            # Sum total cost
            cost_query = await db.execute(
                select(func.sum(OptimizationResult.final_cost))
                .where(OptimizationResult.run_id == run.run_id)
            )
            total_cost = cost_query.scalar() or 0
            
            runs_with_stats.append({
                "run_id": str(run.run_id),
                "run_timestamp": run.run_timestamp,
                "status": run.status,
                "request_parameters": run.request_parameters,
                "results_count": results_count,
                "total_cost": float(total_cost)
            })
        
        return runs_with_stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve optimization runs: {str(e)}"
        )


@router.delete("/optimization-results/{run_id}")
async def delete_optimization_results(
    run_id: str,
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Delete optimization results and update related finalized decisions"""
    from sqlalchemy import delete, update
    from app.models import OptimizationResult, OptimizationRun, FinalizedDecision, CashflowEvent
    
    try:
        # 1. Cancel all cashflow events from finalized decisions related to this optimization run
        await db.execute(
            update(CashflowEvent)
            .where(
                CashflowEvent.related_decision_id.in_(
                    select(FinalizedDecision.id).where(FinalizedDecision.run_id == run_id)
                )
            )
            .values(
                is_cancelled=True,
                cancelled_at=func.now(),
                cancelled_by_id=current_user.id,
                cancellation_reason=f"Optimization run {run_id} deleted"
            )
        )
        
        # 2. Update finalized decisions to revert them back to PROPOSED status
        await db.execute(
            update(FinalizedDecision)
            .where(FinalizedDecision.run_id == run_id)
            .values(
                status='PROPOSED',
                finalized_at=None,
                finalized_by_id=None,
                notes=func.concat(
                    func.coalesce(FinalizedDecision.notes, ''),
                    f"\n[REVERTED] Optimization run {run_id} was deleted"
                )
            )
        )
        
        # 3. Delete optimization results
        result_count = await db.execute(
            delete(OptimizationResult).where(OptimizationResult.run_id == run_id)
        )
        
        # 4. Clear run_id from finalized decisions (set to NULL)
        await db.execute(
            update(FinalizedDecision)
            .where(FinalizedDecision.run_id == run_id)
            .values(run_id=None)
        )
        
        # 5. Delete optimization run (now safe since no foreign key references)
        run_count = await db.execute(
            delete(OptimizationRun).where(OptimizationRun.run_id == run_id)
        )
        
        await db.commit()
        
        return {
            "message": f"Optimization run {run_id} deleted successfully",
            "results_deleted": result_count.rowcount,
            "run_deleted": run_count.rowcount,
            "finalized_decisions_reverted": True,
            "cashflow_events_cancelled": True
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete optimization results: {str(e)}"
        )


# Excel import/export endpoints
@router.post("/import/budget", response_model=ExcelImportResponse)
async def import_budget_data_from_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(require_finance()),
    db: AsyncSession = Depends(get_db)
):
    """Import budget data from Excel file (finance user only)"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    content = await file.read()
    return await ExcelHandler.import_budget_data(db, content)


@router.get("/export/budget")
async def export_budget_data_to_excel(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Export budget data to Excel file"""
    excel_data = await ExcelHandler.export_budget_data(db)
    
    return StreamingResponse(
        BytesIO(excel_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=budget_data.xlsx"}
    )


@router.get("/templates/budget")
async def download_budget_template():
    """Download budget data Excel template"""
    template_data = ExcelHandler.create_budget_template()
    
    return StreamingResponse(
        BytesIO(template_data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=budget_template.xlsx"}
    )
