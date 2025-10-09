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
            
            return OptimizationRunResponse(
                run_id=uuid.UUID(self.run_id),
                run_timestamp=self.start_time,
                status=status_val,
                execution_time_seconds=execution_time,
                total_cost=best_proposal.total_cost if best_proposal else Decimal('0'),
                items_optimized=best_proposal.items_count if best_proposal else 0,
                proposals=proposals,
                message=f"Generated {len(proposals)} proposal(s) using {self.solver_type} solver"
            )
            
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}", exc_info=True)
            execution_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            return OptimizationRunResponse(
                run_id=uuid.UUID(self.run_id),
                run_timestamp=self.start_time if self.start_time else datetime.now(),
                status="ERROR",
                execution_time_seconds=execution_time,
                total_cost=Decimal('0'),
                items_optimized=0,
                proposals=[],
                message=f"Optimization error: {str(e)}"
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
            
            valid_times = list(range(1, min(len(delivery_options) + 1, request.max_time_slots + 1)))
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
            
            valid_times = list(range(1, min(len(delivery_options) + 1, request.max_time_slots + 1)))
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
        
        # Add demand fulfillment constraints (each item must be procured exactly once)
        item_groups = {}
        for var_name, var in variables.items():
            parts = var_name.split('_')
            key = (int(parts[1]), parts[2])  # (project_id, item_code)
            if key not in item_groups:
                item_groups[key] = []
            item_groups[key].append(var)
        
        for vars_list in item_groups.values():
            constraint = solver.Constraint(1, 1)
            for var in vars_list:
                constraint.SetCoefficient(var, 1)
        
        # Add budget constraints
        time_groups = self._group_by_purchase_time(variables, request.max_time_slots)
        for time_slot, var_data in time_groups.items():
            if time_slot not in self.budget_data:
                continue
            
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
            
            valid_times = list(range(1, min(len(delivery_options) + 1, request.max_time_slots + 1)))
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
        
        # Add demand fulfillment constraints
        item_groups = {}
        for var_name, var in variables.items():
            parts = var_name.split('_')
            key = (int(parts[1]), parts[2])
            if key not in item_groups:
                item_groups[key] = []
            item_groups[key].append(var)
        
        for vars_list in item_groups.values():
            constraint = solver.Constraint(1, 1)
            for var in vars_list:
                constraint.SetCoefficient(var, 1)
        
        # Add budget constraints
        time_groups = self._group_by_purchase_time(variables, request.max_time_slots)
        for time_slot, var_data in time_groups.items():
            if time_slot not in self.budget_data:
                continue
            
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
        """Load all necessary data from database"""
        # [Same as original implementation]
        projects_result = await self.db.execute(
            select(Project).where(Project.is_active == True)
        )
        self.projects = {p.id: p for p in projects_result.scalars().all()}
        
        locked_query = await self.db.execute(
            select(FinalizedDecision.project_id, FinalizedDecision.item_code)
            .where(FinalizedDecision.status == 'LOCKED')
        )
        locked_items = {(row.project_id, row.item_code) for row in locked_query.all()}
        
        items_result = await self.db.execute(
            select(ProjectItem).where(ProjectItem.project_id.in_(self.projects.keys()))
        )
        all_items = list(items_result.scalars().all())
        self.project_items = [
            item for item in all_items
            if (item.project_id, item.item_code) not in locked_items
        ]
        
        options_result = await self.db.execute(
            select(ProcurementOption).where(ProcurementOption.is_active == True)
        )
        self.procurement_options = {opt.id: opt for opt in options_result.scalars().all()}
        
        budget_result = await self.db.execute(
            select(BudgetData).order_by(BudgetData.budget_date)
        )
        budget_list = budget_result.scalars().all()
        self.budget_data = {}
        for idx, bd in enumerate(budget_list, start=1):
            self.budget_data[idx] = bd
        
        logger.info(f"Loaded {len(self.projects)} projects, {len(self.project_items)} items, "
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
        
        for vars_list in item_groups.values():
            model.Add(sum(vars_list) == 1)
    
    def _add_cpsat_budget_constraints(self, model: cp_model.CpModel, variables: Dict, max_time_slots: int):
        """Add budget constraints for CP-SAT"""
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
        
        for time_slot in range(1, max_time_slots + 1):
            if time_slot not in time_groups:
                continue
            
            cash_flow_vars = []
            cash_flow_coeffs = []
            
            for var, option, item in time_groups[time_slot]:
                cost = self._calculate_effective_cost(option, item) * item.quantity
                cash_flow_vars.append(var)
                cash_flow_coeffs.append(int(cost * 100))
            
            if time_slot in self.budget_data:
                budget_limit = int(self.budget_data[time_slot].available_budget * 100)
            else:
                budget_limit = 0
            
            if cash_flow_vars:
                model.Add(sum(v * c for v, c in zip(cash_flow_vars, cash_flow_coeffs)) <= budget_limit)
    
    def _set_cpsat_objective(self, model: cp_model.CpModel, variables: Dict, strategy: OptimizationStrategy):
        """Set objective function for CP-SAT based on strategy"""
        objective_terms = []
        
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
            
            cost = self._calculate_effective_cost(option, item) * item.quantity
            project = self.projects.get(project_id)
            
            # Apply strategy-specific weighting
            if strategy == OptimizationStrategy.LOWEST_COST:
                weight = 1
            elif strategy == OptimizationStrategy.PRIORITY_WEIGHTED:
                priority_weight = project.priority_weight if project else 5
                weight = 11 - priority_weight
            elif strategy == OptimizationStrategy.FAST_DELIVERY:
                weight = delivery_time  # Prefer earlier deliveries
            elif strategy == OptimizationStrategy.SMOOTH_CASHFLOW:
                # Penalize extreme time slots
                mid_point = 6
                weight = 1 + abs(delivery_time - mid_point) * 0.1
            else:  # BALANCED
                priority_weight = project.priority_weight if project else 5
                weight = (11 - priority_weight) * 0.7 + delivery_time * 0.3
            
            weighted_cost = int(cost * 100 * weight)
            objective_terms.append(var * weighted_cost)
        
        model.Minimize(sum(objective_terms))
    
    def _set_glop_objective(self, objective, variables: Dict, strategy: OptimizationStrategy):
        """Set objective for Glop LP solver"""
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
                weight = 1.0
            elif strategy == OptimizationStrategy.PRIORITY_WEIGHTED:
                priority_weight = project.priority_weight if project else 5
                weight = float(11 - priority_weight)
            elif strategy == OptimizationStrategy.FAST_DELIVERY:
                weight = float(delivery_time)
            else:
                weight = 1.0
            
            objective.SetCoefficient(var, cost * weight)
    
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

