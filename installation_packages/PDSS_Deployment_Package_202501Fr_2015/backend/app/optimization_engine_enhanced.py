"""
Enhanced Optimization Engine with Multiple OR-Tools Solvers
Supports CP-SAT, Glop (LP), and MIP solvers with advanced features
"""

from typing import Dict, List, Tuple, Optional, Any
from decimal import Decimal
from ortools.sat.python import cp_model
from ortools.linear_solver import pywraplp
import uuid
from datetime import datetime, timedelta, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import (
    Project, ProjectItem, ProcurementOption, BudgetData, 
    OptimizationResult, FinalizedDecision, OptimizationRun
)
from app.schemas import OptimizationRunRequest, OptimizationRunResponse, OptimizationProposal, OptimizationDecision
import logging
from enum import Enum
import networkx as nx

logger = logging.getLogger(__name__)


class SolverType(str, Enum):
    """Available solver types"""
    CP_SAT = "CP_SAT"  # Constraint Programming (default)
    GLOP = "GLOP"      # Linear Programming
    SCIP = "SCIP"      # Mixed-Integer Programming
    CBC = "CBC"        # Coin-or Branch and Cut


class OptimizationStrategy(str, Enum):
    """Optimization strategies for multi-proposal generation"""
    LOWEST_COST = "LOWEST_COST"              # Minimize total cost
    BALANCED = "BALANCED"                     # Balance cost, lead time, and cash flow
    SMOOTH_CASHFLOW = "SMOOTH_CASHFLOW"      # Minimize cash flow variance
    PRIORITY_WEIGHTED = "PRIORITY_WEIGHTED"  # Weight by project priority
    FAST_DELIVERY = "FAST_DELIVERY"          # Minimize total delivery time


class EnhancedProcurementOptimizer:
    """
    Advanced optimization engine with multiple solvers and strategies.
    
    Features:
    - Multiple solver support (CP-SAT, Glop, SCIP, CBC)
    - Graph-based dependency analysis
    - Custom search heuristics
    - Multi-proposal generation
    - Performance benchmarking
    """
    
    def __init__(self, db: AsyncSession, solver_type: SolverType = SolverType.CP_SAT):
        self.db = db
        self.solver_type = solver_type
        self.model = None
        self.variables = {}
        self.run_id = str(uuid.uuid4())
        self.start_time = None
        self.dependency_graph = None
        
    async def run_optimization(
        self, 
        request: OptimizationRunRequest,
        generate_multiple_proposals: bool = False,
        strategies: Optional[List[OptimizationStrategy]] = None
    ) -> OptimizationRunResponse:
        """
        Run optimization with selected solver and strategies.
        
        Args:
            request: Optimization configuration
            generate_multiple_proposals: If True, generate multiple proposals with different strategies
            strategies: List of strategies to use (default: all strategies)
        """
        self.start_time = datetime.now()
        
        try:
            # Load and validate data
            await self._load_data()
            
            # Build dependency graph for analysis
            self._build_dependency_graph()
            
            # Generate proposals based on strategies
            if generate_multiple_proposals:
                proposals = await self._generate_multiple_proposals(request, strategies)
            else:
                # Single optimization run with current strategy
                proposal = await self._run_single_optimization(request, OptimizationStrategy.PRIORITY_WEIGHTED)
                proposals = [proposal] if proposal else []
            
            # Calculate execution time
            execution_time = (datetime.now() - self.start_time).total_seconds()
            
            # Determine overall status
            status_val = "OPTIMAL" if any(p.status == "OPTIMAL" for p in proposals) else \
                     "FEASIBLE" if any(p.status == "FEASIBLE" for p in proposals) else \
                     "INFEASIBLE"
            
            # Get best proposal (lowest cost)
            best_proposal = min(proposals, key=lambda p: p.total_cost) if proposals else None
            
            # Save optimization run to database for later retrieval
            await self._save_optimization_run(request, status_val, proposals)
            
            # Save optimization results to database (from best proposal or all proposals)
            if best_proposal and proposals:
                await self._save_optimization_results(proposals)
            
            # Create user-friendly message
            if len(proposals) == 0:
                user_message = (
                    "❌ Could not generate any feasible solutions.\n\n"
                    "📝 Possible reasons and solutions:\n\n"
                    "1️⃣ Budget constraints too tight:\n"
                    "   • Go to Finance → Budget Management\n"
                    "   • Increase monthly budgets\n"
                    "   • Add more budget periods\n\n"
                    "2️⃣ Procurement options too expensive:\n"
                    "   • Go to Procurement page\n"
                    "   • Add more cost-effective supplier options\n"
                    "   • Review base costs and payment terms\n\n"
                    "3️⃣ Lead times too long:\n"
                    "   • Check supplier lead times\n"
                    "   • Add suppliers with shorter lead times\n"
                    "   • Adjust item delivery dates if possible\n\n"
                    "💡 Tip: Try increasing the time limit or using a different solver (Glop, CBC)."
                )
            else:
                user_message = f"✅ Successfully generated {len(proposals)} proposal(s) using {self.solver_type} solver"
            
            return OptimizationRunResponse(
                run_id=uuid.UUID(self.run_id),
                run_timestamp=self.start_time,
                status=status_val,
                execution_time_seconds=execution_time,
                total_cost=best_proposal.total_cost if best_proposal else Decimal('0'),
                items_optimized=best_proposal.items_count if best_proposal else 0,
                proposals=proposals,
                message=user_message
            )
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}", exc_info=True)
            execution_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            # Format error message for user
            error_msg = str(e)
            if "No active projects" in error_msg or "No project items" in error_msg or \
               "No procurement options" in error_msg or "No budget data" in error_msg:
                # User-friendly validation errors - pass through as-is
                user_message = error_msg
            else:
                # Technical errors - format for user
                user_message = (
                    f"❌ Optimization failed with technical error.\n\n"
                    f"Error details: {error_msg}\n\n"
                    "📝 What you can try:\n"
                    "   1. Check that all your data is valid:\n"
                    "      • Projects are active\n"
                    "      • Items have delivery dates\n"
                    "      • Procurement options exist\n"
                    "      • Budget data is entered\n"
                    "   2. Try reducing the time limit\n"
                    "   3. Try a different solver (Glop or CBC)\n\n"
                    "💡 If problem persists, contact system administrator."
                )
            
            return OptimizationRunResponse(
                run_id=uuid.UUID(self.run_id),
                run_timestamp=self.start_time if self.start_time else datetime.now(),
                status="ERROR",
                execution_time_seconds=execution_time,
                total_cost=Decimal('0'),
                items_optimized=0,
                proposals=[],
                message=user_message
            )
    
    async def _generate_multiple_proposals(
        self, 
        request: OptimizationRunRequest,
        strategies: Optional[List[OptimizationStrategy]] = None
    ) -> List[OptimizationProposal]:
        """Generate multiple optimization proposals with different strategies"""
        
        if strategies is None:
            strategies = list(OptimizationStrategy)
        
        proposals = []
        
        for strategy in strategies:
            logger.info(f"Generating proposal with strategy: {strategy}")
            proposal = await self._run_single_optimization(request, strategy)
            if proposal:
                proposals.append(proposal)
        
        return proposals
    
    async def _run_single_optimization(
        self, 
        request: OptimizationRunRequest,
        strategy: OptimizationStrategy
    ) -> Optional[OptimizationProposal]:
        """Run a single optimization with a specific strategy"""
        
        try:
            # Select solver based on configuration
            if self.solver_type == SolverType.CP_SAT:
                return await self._solve_with_cpsat(request, strategy)
            elif self.solver_type == SolverType.GLOP:
                return await self._solve_with_glop(request, strategy)
            elif self.solver_type in [SolverType.SCIP, SolverType.CBC]:
                return await self._solve_with_mip(request, strategy)
            else:
                raise ValueError(f"Unsupported solver type: {self.solver_type}")
                
        except Exception as e:
            logger.error(f"Strategy {strategy} failed: {str(e)}")
            return None
    
    async def _solve_with_cpsat(
        self, 
        request: OptimizationRunRequest,
        strategy: OptimizationStrategy
    ) -> Optional[OptimizationProposal]:
        """
        Solve using CP-SAT (Constraint Programming) solver.
        Best for: Complex constraints, non-linear relationships, logical conditions
        """
        
        model = cp_model.CpModel()
        variables = {}
        
        # Build decision variables
        for item in self.project_items:
            delivery_options = item.delivery_options if item.delivery_options else []
            if not delivery_options:
                continue
            
            # Use a larger range to accommodate lead times (start from 5 instead of 1)
            valid_times = list(range(5, min(len(delivery_options) + 5, request.max_time_slots + 1)))
            item_options = [opt for opt in self.procurement_options.values() 
                          if opt.item_code == item.item_code]
            
            for option in item_options:
                for delivery_time in valid_times:
                    purchase_time = delivery_time - option.lomc_lead_time
                    if purchase_time < 1:
                        continue
                    
                    var_name = f"buy_{item.project_id}_{item.item_code}_{option.id}_{delivery_time}"
                    variables[var_name] = model.NewBoolVar(var_name)
        
        # Add demand fulfillment constraints
        self._add_cpsat_demand_constraints(model, variables)
        
        # Add budget constraints
        self._add_cpsat_budget_constraints(model, variables, request.max_time_slots)
        
        # Set objective based on strategy
        self._set_cpsat_objective(model, variables, strategy)
        
        # Solve
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = request.time_limit_seconds
        
        # Apply strategy-specific search heuristics
        if strategy == OptimizationStrategy.FAST_DELIVERY:
            solver.parameters.linearization_level = 2
            solver.parameters.cp_model_presolve = True
        
        status = solver.Solve(model)
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            decisions = self._extract_cpsat_decisions(solver, variables)
            total_cost = sum(d.final_cost for d in decisions)
            weighted_cost = self._calculate_weighted_cost(decisions)
            
            return OptimizationProposal(
                proposal_name=self._get_strategy_name(strategy),
                strategy_type=strategy.value,
                total_cost=total_cost,
                weighted_cost=weighted_cost,
                status="OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                items_count=len(decisions),
                decisions=decisions,
                summary_notes=f"CP-SAT solver: {len(decisions)} items optimized"
            )
        
        return None
    
    async def _solve_with_glop(
        self, 
        request: OptimizationRunRequest,
        strategy: OptimizationStrategy
    ) -> Optional[OptimizationProposal]:
        """
        Solve using Glop (Linear Programming) solver.
        Best for: Pure linear objectives and constraints, fast for large problems
        
        Note: Glop requires all constraints to be linear. We'll relax some constraints
        or use continuous variables with rounding.
        """
        
        # Create Glop solver
        solver = pywraplp.Solver.CreateSolver('GLOP')
        if not solver:
            logger.error("Glop solver not available")
            return None
        
        variables = {}
        
        # Build decision variables (continuous [0,1] for LP relaxation)
        for item in self.project_items:
            delivery_options = item.delivery_options if item.delivery_options else []
            if not delivery_options:
                continue
            
            # Use a larger range to accommodate lead times (start from 5 instead of 1)
            valid_times = list(range(5, min(len(delivery_options) + 5, request.max_time_slots + 1)))
            item_options = [opt for opt in self.procurement_options.values() 
                          if opt.item_code == item.item_code]
            
            for option in item_options:
                for delivery_time in valid_times:
                    purchase_time = delivery_time - option.lomc_lead_time
                    if purchase_time < 1:
                        continue
                    
                    var_name = f"buy_{item.project_id}_{item.item_code}_{option.id}_{delivery_time}"
                    # Use continuous variable [0, 1] for LP relaxation
                    variables[var_name] = solver.NumVar(0, 1, var_name)
        
        # Add demand fulfillment constraints (each item can be procured at most once)
        # Allow partial optimization when budget is insufficient
        item_groups = {}
        for var_name, var in variables.items():
            parts = var_name.split('_')
            key = (int(parts[1]), parts[2])  # (project_id, item_code)
            if key not in item_groups:
                item_groups[key] = []
            item_groups[key].append(var)
        
        for vars_list in item_groups.values():
            constraint = solver.Constraint(0, 1)  # At most once (allows skipping items)
            for var in vars_list:
                constraint.SetCoefficient(var, 1)
        
        # Add budget constraints
        time_groups = self._group_by_purchase_time(variables, request.max_time_slots)
        for time_slot, var_data in time_groups.items():
            if time_slot not in self.budget_data:
                # Use a large budget for time slots without explicit budget data
                budget_limit = 1000000.0  # $1M default
            else:
                budget_limit = float(self.budget_data[time_slot].available_budget)
            
            constraint = solver.Constraint(0, budget_limit)
            
            for var, cost in var_data:
                constraint.SetCoefficient(var, cost)
        
        # Set objective based on strategy
        objective = solver.Objective()
        self._set_glop_objective(objective, variables, strategy)
        objective.SetMinimization()
        
        # Solve
        solver.SetTimeLimit(request.time_limit_seconds * 1000)  # milliseconds
        status = solver.Solve()
        
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            # Round LP solution to integer solution
            decisions = self._extract_glop_decisions(solver, variables)
            total_cost = sum(d.final_cost for d in decisions)
            weighted_cost = self._calculate_weighted_cost(decisions)
            
            return OptimizationProposal(
                proposal_name=self._get_strategy_name(strategy) + " (LP)",
                strategy_type=strategy.value,
                total_cost=total_cost,
                weighted_cost=weighted_cost,
                status="OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
                items_count=len(decisions),
                decisions=decisions,
                summary_notes=f"Glop LP solver: {len(decisions)} items, solution time: {solver.WallTime():.2f}ms"
            )
        
        return None
    
    async def _solve_with_mip(
        self, 
        request: OptimizationRunRequest,
        strategy: OptimizationStrategy
    ) -> Optional[OptimizationProposal]:
        """
        Solve using MIP solver (SCIP or CBC).
        Best for: Mixed-integer problems with linear constraints
        """
        
        # Create MIP solver
        solver_name = self.solver_type.value
        solver = pywraplp.Solver.CreateSolver(solver_name)
        if not solver:
            logger.error(f"{solver_name} solver not available")
            return None
        
        variables = {}
        
        # Build binary decision variables
        for item in self.project_items:
            delivery_options = item.delivery_options if item.delivery_options else []
            if not delivery_options:
                continue
            
            # Use a larger range to accommodate lead times (start from 5 instead of 1)
            valid_times = list(range(5, min(len(delivery_options) + 5, request.max_time_slots + 1)))
            item_options = [opt for opt in self.procurement_options.values() 
                          if opt.item_code == item.item_code]
            
            for option in item_options:
                for delivery_time in valid_times:
                    purchase_time = delivery_time - option.lomc_lead_time
                    if purchase_time < 1:
                        continue
                    
                    var_name = f"buy_{item.project_id}_{item.item_code}_{option.id}_{delivery_time}"
                    # Binary variable
                    variables[var_name] = solver.IntVar(0, 1, var_name)
        
        # Add demand fulfillment constraints (allow partial optimization)
        item_groups = {}
        for var_name, var in variables.items():
            parts = var_name.split('_')
            key = (int(parts[1]), parts[2])
            if key not in item_groups:
                item_groups[key] = []
            item_groups[key].append(var)
        
        for vars_list in item_groups.values():
            constraint = solver.Constraint(0, 1)  # At most once (allows skipping items)
            for var in vars_list:
                constraint.SetCoefficient(var, 1)
        
        # Add budget constraints
        time_groups = self._group_by_purchase_time(variables, request.max_time_slots)
        for time_slot, var_data in time_groups.items():
            if time_slot not in self.budget_data:
                # Use a large budget for time slots without explicit budget data
                budget_limit = 1000000.0  # $1M default
            else:
                budget_limit = float(self.budget_data[time_slot].available_budget)
            
            constraint = solver.Constraint(0, budget_limit)
            
            for var, cost in var_data:
                constraint.SetCoefficient(var, cost)
        
        # Set objective
        objective = solver.Objective()
        self._set_mip_objective(objective, variables, strategy)
        objective.SetMinimization()
        
        # Solve
        solver.SetTimeLimit(request.time_limit_seconds * 1000)
        status = solver.Solve()
        
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            decisions = self._extract_mip_decisions(solver, variables)
            total_cost = sum(d.final_cost for d in decisions)
            weighted_cost = self._calculate_weighted_cost(decisions)
            
            return OptimizationProposal(
                proposal_name=self._get_strategy_name(strategy) + f" ({solver_name})",
                strategy_type=strategy.value,
                total_cost=total_cost,
                weighted_cost=weighted_cost,
                status="OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
                items_count=len(decisions),
                decisions=decisions,
                summary_notes=f"{solver_name} MIP solver: {len(decisions)} items, wall time: {solver.WallTime():.2f}ms"
            )
        
        return None
    
    def _build_dependency_graph(self):
        """
        Build a directed graph representing project dependencies and delivery sequences.
        Useful for critical path analysis and dependency-aware scheduling.
        """
        
        self.dependency_graph = nx.DiGraph()
        
        # Add nodes for each project item
        for item in self.project_items:
            node_id = f"P{item.project_id}_I{item.item_code}"
            self.dependency_graph.add_node(
                node_id,
                project_id=item.project_id,
                item_code=item.item_code,
                quantity=item.quantity,
                delivery_options=item.delivery_options
            )
        
        # Add edges based on delivery sequence within same project
        # Items in the same project may have dependencies
        project_items_map = {}
        for item in self.project_items:
            if item.project_id not in project_items_map:
                project_items_map[item.project_id] = []
            project_items_map[item.project_id].append(item)
        
        # Simple sequential dependency (can be enhanced with actual dependency data)
        for project_id, items in project_items_map.items():
            sorted_items = sorted(items, key=lambda x: x.item_code)
            for i in range(len(sorted_items) - 1):
                from_node = f"P{sorted_items[i].project_id}_I{sorted_items[i].item_code}"
                to_node = f"P{sorted_items[i+1].project_id}_I{sorted_items[i+1].item_code}"
                self.dependency_graph.add_edge(from_node, to_node, weight=1)
        
        logger.info(f"Built dependency graph: {len(self.dependency_graph.nodes)} nodes, "
                   f"{len(self.dependency_graph.edges)} edges")
    
    def get_critical_path(self) -> List[str]:
        """
        Calculate critical path through the dependency graph.
        Returns the longest path (in terms of delivery time) through the network.
        """
        
        if not self.dependency_graph:
            return []
        
        try:
            # Find longest path using DAG longest path algorithm
            longest_path = nx.dag_longest_path(self.dependency_graph, weight='weight')
            return longest_path
        except:
            return []
    
    def analyze_network_flow(self) -> Dict[str, Any]:
        """
        Analyze the procurement network as a flow problem.
        Returns flow statistics and bottleneck analysis.
        """
        
        if not self.dependency_graph:
            return {}
        
        analysis = {
            'total_nodes': len(self.dependency_graph.nodes),
            'total_edges': len(self.dependency_graph.edges),
            'connected_components': nx.number_weakly_connected_components(self.dependency_graph),
            'critical_path_length': len(self.get_critical_path()),
        }
        
        # Calculate centrality measures
        if len(self.dependency_graph.nodes) > 0:
            try:
                analysis['betweenness_centrality'] = nx.betweenness_centrality(self.dependency_graph)
                analysis['in_degree_centrality'] = nx.in_degree_centrality(self.dependency_graph)
            except:
                pass
        
        return analysis
    
    # ============== Helper Methods ==============
    
    async def _load_data(self):
        """Load all necessary data from database with validation"""
        # Load projects
        projects_result = await self.db.execute(
            select(Project).where(Project.is_active == True)
        )
        self.projects = {p.id: p for p in projects_result.scalars().all()}
        
        if not self.projects:
            raise ValueError(
                "❌ No active projects found.\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Projects' page\n"
                "   2. Create at least one project\n"
                "   3. Make sure the project is marked as 'Active'\n\n"
                "💡 Tip: A project must have items before optimization can run."
            )
        
        # Load locked items
        locked_query = await self.db.execute(
            select(FinalizedDecision.project_id, FinalizedDecision.item_code)
            .where(FinalizedDecision.status == 'LOCKED')
        )
        locked_items = {(row.project_id, row.item_code) for row in locked_query.all()}
        
        # Load project items with delivery options relationship
        from sqlalchemy.orm import selectinload
        items_result = await self.db.execute(
            select(ProjectItem)
            .options(selectinload(ProjectItem.delivery_options_rel))
            .where(ProjectItem.project_id.in_(self.projects.keys()))
        )
        all_items = list(items_result.scalars().all())
        self.project_items = [
            item for item in all_items
            if (item.project_id, item.item_code) not in locked_items
        ]
        
        if not self.project_items:
            if all_items:
                raise ValueError(
                    "❌ All items are locked (already finalized).\n\n"
                    "📝 What you need to do:\n"
                    "   1. Go to 'Finalized Decisions' page\n"
                    "   2. Unlock some items you want to re-optimize\n"
                    "   3. Or add new items to your projects\n\n"
                    "💡 Tip: You can revert locked decisions to make them available for optimization."
                )
            else:
                raise ValueError(
                    "❌ No project items found.\n\n"
                    "📝 What you need to do:\n"
                    "   1. Go to 'Project Items' page\n"
                    "   2. Select a project\n"
                    "   3. Click 'Add Item' button\n"
                    "   4. Select items from the Items Master catalog\n"
                    "   5. Set quantities and delivery dates\n\n"
                    "💡 Tip: You need at least one item to run optimization."
                )
        
        # Load procurement options
        options_result = await self.db.execute(
            select(ProcurementOption).where(ProcurementOption.is_active == True)
        )
        self.procurement_options = {opt.id: opt for opt in options_result.scalars().all()}
        
        if not self.procurement_options:
            raise ValueError(
                "❌ No procurement options found.\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Procurement' page\n"
                "   2. For each item, click 'Add Option' button\n"
                "   3. Enter supplier details:\n"
                "      • Supplier name\n"
                "      • Base cost per unit\n"
                "      • Lead time (delivery days)\n"
                "      • Payment terms (cash/installments)\n"
                "   4. Add at least 2-3 options per item for better optimization\n\n"
                "💡 Tip: More procurement options = better optimization results!"
            )
        
        # Validate items have procurement options
        items_without_options = []
        for item in self.project_items[:5]:  # Check first 5 items
            matching_options = [opt for opt in self.procurement_options.values() 
                              if opt.item_code == item.item_code]
            if not matching_options:
                items_without_options.append(item.item_code)
        
        if items_without_options:
            raise ValueError(
                f"❌ Some items don't have procurement options.\n\n"
                f"Items without options: {', '.join(items_without_options[:3])}"
                f"{' and more...' if len(items_without_options) > 3 else ''}\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Procurement' page\n"
                "   2. Find these items in the list\n"
                "   3. Click 'Add Option' for each item\n"
                "   4. Add at least one supplier option per item\n\n"
                "💡 Tip: All items must have at least one procurement option."
            )
        
        # Load budget data
        budget_result = await self.db.execute(
            select(BudgetData).order_by(BudgetData.budget_date)
        )
        budget_list = budget_result.scalars().all()
        self.budget_data = {}
        for idx, bd in enumerate(budget_list, start=1):
            self.budget_data[idx] = bd
        
        if not self.budget_data:
            raise ValueError(
                "❌ No budget data found.\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Finance' page\n"
                "   2. Click 'Budget Management' tab\n"
                "   3. Add monthly budgets:\n"
                "      • Select month\n"
                "      • Enter available budget amount\n"
                "   4. Add at least 3-6 months of budget data\n\n"
                "💡 Tip: Budget data determines when purchases can be made."
            )
        
        logger.info(f"✅ Data loaded: {len(self.projects)} projects, {len(self.project_items)} items, "
                   f"{len(self.procurement_options)} options, {len(self.budget_data)} budget periods")
    
    def _add_cpsat_demand_constraints(self, model: cp_model.CpModel, variables: Dict):
        """Add demand fulfillment constraints for CP-SAT"""
        item_groups = {}
        for var_name, var in variables.items():
            parts = var_name.split('_')
            key = (int(parts[1]), parts[2])
            if key not in item_groups:
                item_groups[key] = []
            item_groups[key].append(var)
        
        # Allow partial optimization: each item can be purchased at most once (<= 1)
        # This allows the optimizer to skip items when budget is insufficient
        for vars_list in item_groups.values():
            model.Add(sum(vars_list) <= 1)
    
    def _add_cpsat_budget_constraints(self, model: cp_model.CpModel, variables: Dict, max_time_slots: int):
        """Add soft budget constraints for CP-SAT with slack variables"""
        time_groups = {}
        
        for var_name, var in variables.items():
            parts = var_name.split('_')
            delivery_time = int(parts[4])
            option_id = int(parts[3])
            project_id = int(parts[1])
            item_code = parts[2]
            
            option = self.procurement_options[option_id]
            purchase_time = delivery_time - option.lomc_lead_time
            
            if purchase_time not in time_groups:
                time_groups[purchase_time] = []
            
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if item:
                time_groups[purchase_time].append((var, option, item))
        
        # Store slack variables for penalty in objective
        self.cpsat_budget_slack_vars = []
        
        for time_slot in range(1, max_time_slots + 1):
            if time_slot not in time_groups:
                continue
            
            cash_flow_vars = []
            cash_flow_coeffs = []
            
            for var, option, item in time_groups[time_slot]:
                cost = self._calculate_effective_cost(option, item) * item.quantity
                cash_flow_vars.append(var)
                # Scale to thousands for numerical stability
                cash_flow_coeffs.append(int(cost / 1000))
            
            if time_slot in self.budget_data:
                budget_limit = int(self.budget_data[time_slot].available_budget / 1000)
            else:
                # Use a large budget for time slots without explicit budget data
                budget_limit = 1000  # $1M default
            
            if cash_flow_vars:
                # Create slack variable to allow exceeding budget
                max_slack = max(budget_limit // 2, 500)  # At least $500K
                slack_var = model.NewIntVar(0, max_slack, f'cpsat_budget_slack_{time_slot}')
                
                # Soft constraint: spending <= budget + slack
                total_spending = sum(v * c for v, c in zip(cash_flow_vars, cash_flow_coeffs))
                model.Add(total_spending <= budget_limit + slack_var)
                
                # Store slack for penalty
                self.cpsat_budget_slack_vars.append(slack_var)
    
    def _set_cpsat_objective(self, model: cp_model.CpModel, variables: Dict, strategy: OptimizationStrategy):
        """Set objective function for CP-SAT based on strategy
        
        Goal: Maximize business value minus cost
        Formula: Minimize(Total_Cost - Total_Business_Value + Budget_Penalty)
        
        This creates a proper trade-off between value and cost, making purchasing
        items profitable while still respecting strategy-based preferences.
        """
        cost_terms = []
        value_terms = []
        
        for var_name, var in variables.items():
            parts = var_name.split('_')
            option_id = int(parts[3])
            project_id = int(parts[1])
            item_code = parts[2]
            delivery_time = int(parts[4])
            
            option = self.procurement_options[option_id]
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if not item:
                continue
            
            # Calculate procurement cost
            cost = float(self._calculate_effective_cost(option, item) * item.quantity)
            
            # Calculate business value (revenue from item)
            business_value = 0
            if hasattr(item, 'delivery_options_rel') and item.delivery_options_rel:
                # Use the first delivery option's invoice amount
                first_delivery = item.delivery_options_rel[0]
                business_value = float(first_delivery.invoice_amount_per_unit) * item.quantity
            
            # If no delivery option, use 20% markup as default
            if business_value == 0:
                business_value = cost * 1.20
            
            project = self.projects.get(project_id)
            
            # Apply strategy-specific weighting to BOTH cost and value
            # This ensures strategies still differentiate while maintaining profitability
            if strategy == OptimizationStrategy.LOWEST_COST:
                cost_weight = 1.0
                value_weight = 1.0
            elif strategy == OptimizationStrategy.PRIORITY_WEIGHTED:
                priority = project.priority_weight if project else 5
                # Higher priority = lower cost weight, higher value weight
                cost_weight = float(11 - priority) * 0.1
                value_weight = float(priority) * 0.1
            elif strategy == OptimizationStrategy.FAST_DELIVERY:
                # Earlier delivery = higher value
                cost_weight = 1.0
                value_weight = float(12 - delivery_time) * 0.1
            elif strategy == OptimizationStrategy.SMOOTH_CASHFLOW:
                # Prefer middle time slots
                mid_point = 8.5
                distance = abs(delivery_time - mid_point)
                cost_weight = 1.0 + distance * 0.1
                value_weight = 1.0 - distance * 0.05
            else:  # BALANCED
                priority = project.priority_weight if project else 5
                priority_factor = float(11 - priority) * 0.05
                delivery_factor = float(12 - delivery_time) * 0.05
                cost_weight = priority_factor + delivery_factor + 0.5
                value_weight = 1.0
            
            # Scale to thousands for numerical stability
            cost_scaled = int(cost / 1000 * cost_weight)
            value_scaled = int(business_value / 1000 * value_weight)
            
            cost_terms.append(var * cost_scaled)
            value_terms.append(var * value_scaled)
        
        # Add budget penalty if slack variables exist
        budget_penalty = 0
        if hasattr(self, 'cpsat_budget_slack_vars') and self.cpsat_budget_slack_vars:
            BUDGET_PENALTY_MULTIPLIER = 10
            budget_penalty = sum(slack * BUDGET_PENALTY_MULTIPLIER for slack in self.cpsat_budget_slack_vars)
        
        # Objective: Minimize(Cost - Value + Budget_Penalty)
        model.Minimize(sum(cost_terms) - sum(value_terms) + budget_penalty)
    
    def _set_glop_objective(self, objective, variables: Dict, strategy: OptimizationStrategy):
        """Set objective for Glop LP solver
        
        Goal: Maximize items purchased while minimizing cost
        """
        PURCHASE_BONUS = 50000.0  # $50K bonus per item purchased (80% of avg cost)
        
        for var_name, var in variables.items():
            parts = var_name.split('_')
            option_id = int(parts[3])
            project_id = int(parts[1])
            item_code = parts[2]
            delivery_time = int(parts[4])
            
            option = self.procurement_options[option_id]
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if not item:
                continue
            
            cost = float(self._calculate_effective_cost(option, item) * item.quantity)
            project = self.projects.get(project_id)
            
            # Strategy-based weighting (same logic as CP-SAT)
            if strategy == OptimizationStrategy.LOWEST_COST:
                weight = 1.0  # Pure cost minimization
            elif strategy == OptimizationStrategy.PRIORITY_WEIGHTED:
                priority_weight = project.priority_weight if project else 5
                weight = float(11 - priority_weight)  # Higher priority = lower weight = better
            elif strategy == OptimizationStrategy.FAST_DELIVERY:
                weight = float(12 - delivery_time)  # Earlier delivery = lower weight = better
            elif strategy == OptimizationStrategy.SMOOTH_CASHFLOW:
                mid_point = 8.5  # Middle of range 5-12
                weight = 1.0 + float(abs(delivery_time - mid_point)) * 0.2
            else:  # BALANCED
                priority_weight = project.priority_weight if project else 5
                priority_factor = float(11 - priority_weight) * 0.7  # Higher priority = better
                delivery_factor = float(12 - delivery_time) * 0.3    # Earlier delivery = better
                weight = priority_factor + delivery_factor
            
            # Objective: Cost - Purchase Bonus (encourages purchasing)
            objective.SetCoefficient(var, (cost * weight) - PURCHASE_BONUS)
    
    def _set_mip_objective(self, objective, variables: Dict, strategy: OptimizationStrategy):
        """Set objective for MIP solver (same as Glop)"""
        self._set_glop_objective(objective, variables, strategy)
    
    def _group_by_purchase_time(self, variables: Dict, max_time_slots: int) -> Dict[int, List[Tuple[Any, float]]]:
        """Group variables by purchase time with their costs"""
        time_groups = {}
        
        for var_name, var in variables.items():
            parts = var_name.split('_')
            delivery_time = int(parts[4])
            option_id = int(parts[3])
            project_id = int(parts[1])
            item_code = parts[2]
            
            option = self.procurement_options[option_id]
            purchase_time = delivery_time - option.lomc_lead_time
            
            if purchase_time < 1:
                continue
            
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if item:
                cost = float(self._calculate_effective_cost(option, item) * item.quantity)
                if purchase_time not in time_groups:
                    time_groups[purchase_time] = []
                time_groups[purchase_time].append((var, cost))
        
        return time_groups
    
    def _calculate_effective_cost(self, option: ProcurementOption, item: ProjectItem) -> Decimal:
        """Calculate effective cost with discounts"""
        base_cost = option.base_cost
        
        if option.payment_terms.get('type') == 'cash':
            discount = option.payment_terms.get('discount_percent', 0)
            base_cost = base_cost * (1 - Decimal(discount) / 100)
        
        if (option.discount_bundle_threshold and 
            item.quantity >= option.discount_bundle_threshold and 
            option.discount_bundle_percent):
            base_cost = base_cost * (1 - option.discount_bundle_percent / 100)
        
        return base_cost
    
    def _extract_cpsat_decisions(self, solver: cp_model.CpSolver, variables: Dict) -> List[OptimizationDecision]:
        """Extract decisions from CP-SAT solution"""
        decisions = []
        
        for var_name, var in variables.items():
            if solver.Value(var) == 1:
                parts = var_name.split('_')
                project_id = int(parts[1])
                item_code = parts[2]
                option_id = int(parts[3])
                delivery_time = int(parts[4])
                
                decision = self._create_decision(project_id, item_code, option_id, delivery_time)
                if decision:
                    decisions.append(decision)
        
        return decisions
    
    def _extract_glop_decisions(self, solver, variables: Dict) -> List[OptimizationDecision]:
        """Extract and round LP solution to integer decisions"""
        decisions = []
        
        # Collect all variables with value > 0.5 (rounding threshold)
        for var_name, var in variables.items():
            if var.solution_value() > 0.5:
                parts = var_name.split('_')
                project_id = int(parts[1])
                item_code = parts[2]
                option_id = int(parts[3])
                delivery_time = int(parts[4])
                
                decision = self._create_decision(project_id, item_code, option_id, delivery_time)
                if decision:
                    decisions.append(decision)
        
        return decisions
    
    def _extract_mip_decisions(self, solver, variables: Dict) -> List[OptimizationDecision]:
        """Extract decisions from MIP solution"""
        decisions = []
        
        for var_name, var in variables.items():
            if var.solution_value() > 0.5:  # Should be exactly 1 for binary vars
                parts = var_name.split('_')
                project_id = int(parts[1])
                item_code = parts[2]
                option_id = int(parts[3])
                delivery_time = int(parts[4])
                
                decision = self._create_decision(project_id, item_code, option_id, delivery_time)
                if decision:
                    decisions.append(decision)
        
        return decisions
    
    def _create_decision(self, project_id: int, item_code: str, option_id: int, delivery_time: int) -> Optional[OptimizationDecision]:
        """Create an OptimizationDecision from solution data"""
        option = self.procurement_options.get(option_id)
        item = next((i for i in self.project_items 
                    if i.project_id == project_id and i.item_code == item_code), None)
        project = self.projects.get(project_id)
        
        if not (option and item and project):
            return None
        
        unit_cost = self._calculate_effective_cost(option, item)
        final_cost = unit_cost * item.quantity
        purchase_time = delivery_time - option.lomc_lead_time
        
        # Convert time slots to dates (approximate)
        base_date = date.today()
        purchase_date = base_date + timedelta(days=purchase_time * 30)
        delivery_date = base_date + timedelta(days=delivery_time * 30)
        
        return OptimizationDecision(
            project_id=project_id,
            project_code=project.project_code,
            item_code=item_code,
            item_name=item.item_name or item_code,
            procurement_option_id=option_id,
            supplier_name=option.supplier_name,
            purchase_date=purchase_date,
            delivery_date=delivery_date,
            quantity=item.quantity,
            unit_cost=unit_cost,
            final_cost=final_cost,
            payment_terms=str(option.payment_terms.get('type', 'unknown'))
        )
    
    def _calculate_weighted_cost(self, decisions: List[OptimizationDecision]) -> Decimal:
        """Calculate weighted cost considering project priorities"""
        weighted = Decimal('0')
        
        for decision in decisions:
            project = self.projects.get(decision.project_id)
            if project:
                weight = Decimal(11 - project.priority_weight)
                weighted += decision.final_cost * weight
        
        return weighted
    
    def _get_strategy_name(self, strategy: OptimizationStrategy) -> str:
        """Get human-readable strategy name"""
        names = {
            OptimizationStrategy.LOWEST_COST: "Lowest Cost Strategy",
            OptimizationStrategy.BALANCED: "Balanced Strategy",
            OptimizationStrategy.SMOOTH_CASHFLOW: "Smooth Cash Flow Strategy",
            OptimizationStrategy.PRIORITY_WEIGHTED: "Priority-Weighted Strategy",
            OptimizationStrategy.FAST_DELIVERY: "Fast Delivery Strategy"
        }
        return names.get(strategy, strategy.value)
    
    async def _save_optimization_run(
        self, 
        request: OptimizationRunRequest, 
        status: str, 
        proposals: List[OptimizationProposal]
    ):
        """Save optimization run to database for historical tracking"""
        try:
            run_uuid = uuid.UUID(self.run_id)
            
            # Check if run already exists
            existing = await self.db.execute(
                select(OptimizationRun).where(OptimizationRun.run_id == run_uuid)
            )
            if existing.scalars().first():
                logger.info(f"Optimization run {self.run_id} already exists")
                return
            
            # Create optimization run record
            optimization_run = OptimizationRun(
                run_id=run_uuid,
                request_parameters={
                    'max_time_slots': request.max_time_slots,
                    'time_limit_seconds': request.time_limit_seconds,
                    'solver_type': self.solver_type.value,
                    'proposals_count': len(proposals),
                    'strategies': [p.strategy_type for p in proposals]
                },
                status='SUCCESS' if status in ['OPTIMAL', 'FEASIBLE'] else 'FAILED'
            )
            self.db.add(optimization_run)
            await self.db.commit()
            
            logger.info(f"Saved optimization run {self.run_id} to database")
            
        except Exception as e:
            logger.error(f"Failed to save optimization run: {str(e)}")
            # Don't fail the whole optimization if saving fails
    
    async def _save_optimization_results(self, proposals: List[OptimizationProposal]):
        """Save optimization results from all proposals to database"""
        try:
            run_uuid = uuid.UUID(self.run_id)
            
            # Get the best proposal (lowest cost) for saving to OptimizationResult table
            best_proposal = min(proposals, key=lambda p: p.total_cost) if proposals else None
            
            if not best_proposal:
                return
            
            # Save each decision from the best proposal as an OptimizationResult
            results = []
            
            for decision in best_proposal.decisions:
                # Convert dates back to time slots (approximate)
                purchase_date = datetime.fromisoformat(str(decision.purchase_date))
                delivery_date = datetime.fromisoformat(str(decision.delivery_date))
                
                base_date = date.today()
                purchase_time = max(1, (purchase_date.date() - base_date).days // 30)
                delivery_time = max(1, (delivery_date.date() - base_date).days // 30)
                
                result = OptimizationResult(
                    run_id=run_uuid,
                    run_timestamp=self.start_time,
                    project_id=decision.project_id,
                    item_code=decision.item_code,
                    procurement_option_id=decision.procurement_option_id,
                    purchase_time=purchase_time,
                    delivery_time=delivery_time,
                    quantity=decision.quantity,
                    final_cost=decision.final_cost
                )
                results.append(result)
            
            # Save all results
            self.db.add_all(results)
            await self.db.commit()
            
            logger.info(f"Saved {len(results)} optimization results to database")
            
        except Exception as e:
            logger.error(f"Failed to save optimization results: {str(e)}")
            # Don't fail the whole optimization if saving fails

