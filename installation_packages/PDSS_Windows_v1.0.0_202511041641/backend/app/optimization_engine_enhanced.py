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
            
            # Get best proposal (lowest cost among proposals with items)
            proposals_with_items = [p for p in proposals if p.items_count > 0]
            best_proposal = min(proposals_with_items, key=lambda p: p.total_cost) if proposals_with_items else None
            
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
            
            response = OptimizationRunResponse(
                run_id=uuid.UUID(self.run_id),
                run_timestamp=self.start_time,
                status=status_val,
                execution_time_seconds=execution_time,
                total_cost=best_proposal.total_cost if best_proposal else Decimal('0'),
                items_optimized=best_proposal.items_count if best_proposal else 0,
                proposals=proposals,
                message=user_message
            )
            
            logger.info(f"DEBUG: Returning optimization response with run_id: {response.run_id} (type: {type(response.run_id)})")
            return response
            
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
        logger.info(f"=== BUILDING CP-SAT MODEL ===")
        logger.info(f"Processing {len(self.project_items)} items for optimization")
        
        items_processed = 0
        variables_created = 0
        
        for item in self.project_items:
            logger.info(f"DEBUG: Processing item {item.item_code} (project_id: {item.project_id}, id: {item.id})")
            
            # Check delivery options from relationship (DeliveryOption table) - NEW SYSTEM
            # Fallback to JSON field for legacy items - OLD SYSTEM
            has_delivery_options = False
            if item.delivery_options_rel and len(item.delivery_options_rel) > 0:
                has_delivery_options = True
                logger.info(f"DEBUG: Item {item.item_code} has {len(item.delivery_options_rel)} delivery options from table")
            elif item.delivery_options:
                try:
                    import json
                    delivery_options = json.loads(item.delivery_options) if isinstance(item.delivery_options, str) else item.delivery_options
                    if delivery_options and len(delivery_options) > 0:
                        has_delivery_options = True
                        logger.info(f"DEBUG: Item {item.item_code} has {len(delivery_options)} delivery options from JSON (legacy)")
                except Exception as e:
                    logger.error(f"DEBUG: Failed to parse delivery options for {item.item_code}: {e}")
            
            if not has_delivery_options:
                logger.warning(f"❌ Item {item.item_code} has NO delivery options - SKIPPING")
                continue
            
            item_options = [opt for opt in self.procurement_options.values() 
                          if opt.item_code == item.item_code and opt.project_item_id == item.id]
            
            # Use actual purchase and delivery dates from procurement options
            # No need to calculate time slots - use the real dates directly
            valid_times = []
            for option in item_options:
                if option.purchase_date and option.expected_delivery_date:
                    # Use a simple time slot based on the option ID
                    # Each procurement option gets its own time slot
                    time_slot = option.id  # Use option ID as time slot
                    valid_times.append(time_slot)
            
            logger.info(f"DEBUG: Item {item.item_code} using time slots from procurement options: {valid_times}")
            
            if not valid_times:
                logger.warning(f"❌ Item {item.item_code} has NO valid procurement options with dates - SKIPPING")
                continue
            
            logger.info(f"DEBUG: Item {item.item_code} has {len(item_options)} procurement options:")
            for opt in item_options:
                logger.info(f"  - Option {opt.id}: {opt.supplier_name} (cost: {opt.base_cost}, lead_time: {opt.lomc_lead_time})")
            
            if not item_options:
                logger.warning(f"❌ Item {item.item_code} has NO finalized procurement options - SKIPPING")
                continue
            
            logger.info(f"✅ Processing item {item.item_code}: {len(item_options)} options, {len(valid_times)} time slots")
            items_processed += 1
            
            for option in item_options:
                for delivery_time in valid_times:
                    # Use actual purchase and delivery dates from procurement option
                    # No need to calculate purchase_time - use the real dates
                    if option.purchase_date and option.expected_delivery_date:
                        var_name = f"buy_{item.project_id}_{item.item_code}_{option.id}_{delivery_time}"
                        variables[var_name] = model.NewBoolVar(var_name)
                        variables_created += 1
                        logger.debug(f"    Created variable: {var_name}")
        
        logger.info(f"=== MODEL BUILDING SUMMARY ===")
        logger.info(f"Items processed: {items_processed}/{len(self.project_items)}")
        logger.info(f"Variables created: {variables_created}")
        logger.info(f"Model ready for solving...")
        
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
        
        logger.info(f"=== SOLVER RESULTS ===")
        logger.info(f"Solver status: {status}")
        logger.info(f"Status meaning: {'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE' if status == cp_model.FEASIBLE else 'INFEASIBLE' if status == cp_model.INFEASIBLE else 'UNKNOWN'}")
        
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            decisions = self._extract_cpsat_decisions(solver, variables)
            total_cost = sum(d.final_cost for d in decisions)
            weighted_cost = self._calculate_weighted_cost(decisions)
            
            logger.info(f"✅ Optimization successful!")
            logger.info(f"Items optimized: {len(decisions)}")
            logger.info(f"Total cost: ${total_cost}")
            
            # Debug: Check which variables were actually selected
            selected_vars = []
            for var_name, var in variables.items():
                if solver.Value(var) == 1:
                    selected_vars.append(var_name)
            
            logger.info(f"Selected variables: {len(selected_vars)}")
            for var in selected_vars[:10]:  # Show first 10
                logger.info(f"  {var}")
            if len(selected_vars) > 10:
                logger.info(f"  ... and {len(selected_vars) - 10} more")
            
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
        else:
            logger.warning(f"❌ Optimization failed with status: {status}")
            logger.warning(f"Possible reasons: No feasible solution, budget constraints too tight, or no valid items")
        
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
            # Check delivery options from relationship (NEW) or JSON (legacy)
            has_delivery_options = False
            delivery_options_count = 0
            if item.delivery_options_rel and len(item.delivery_options_rel) > 0:
                has_delivery_options = True
                delivery_options_count = len(item.delivery_options_rel)
            elif item.delivery_options:
                try:
                    import json
                    delivery_options = json.loads(item.delivery_options) if isinstance(item.delivery_options, str) else item.delivery_options
                    if delivery_options and len(delivery_options) > 0:
                        has_delivery_options = True
                        delivery_options_count = len(delivery_options)
                except:
                    pass
            if not has_delivery_options:
                continue
            
            # Use a larger range to accommodate lead times (start from 5 instead of 1)
            # Use delivery_options_count or default to max_time_slots if none found
            valid_times = list(range(5, min(delivery_options_count + 5 if delivery_options_count > 0 else request.max_time_slots, request.max_time_slots + 1)))
            item_options = [opt for opt in self.procurement_options.values() 
                          if opt.item_code == item.item_code and opt.project_item_id == item.id]
            
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
            constraint = solver.Constraint(1, 1)  # Exactly once (demand fulfillment)
            for var in vars_list:
                constraint.SetCoefficient(var, 1)
        
        # Add budget constraints (MULTI-CURRENCY SUPPORT)
        # Group by time slot AND currency
        time_currency_groups = {}  # {(time_slot, currency): [(var, cost), ...]}
        
        time_groups = self._group_by_purchase_time(variables, request.max_time_slots)
        for time_slot, var_data in time_groups.items():
            for var, cost, currency in var_data:
                key = (time_slot, currency)
                if key not in time_currency_groups:
                    time_currency_groups[key] = []
                time_currency_groups[key].append((var, cost))
        
        # Apply budget constraints per currency
        for (time_slot, currency), var_cost_pairs in time_currency_groups.items():
            if time_slot in self.budget_data_by_currency:
                currency_budgets = self.budget_data_by_currency[time_slot]
                budget_amount = currency_budgets.get(currency, Decimal(0))
                budget_limit = float(budget_amount)
            else:
                # No budget data for this time slot - use large default
                budget_limit = 100000000000000.0  # $100T default
            
            constraint = solver.Constraint(0, budget_limit)
            
            for var, cost in var_cost_pairs:
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
            # Check delivery options from relationship (NEW) or JSON (legacy)
            has_delivery_options = False
            delivery_options_count = 0
            if item.delivery_options_rel and len(item.delivery_options_rel) > 0:
                has_delivery_options = True
                delivery_options_count = len(item.delivery_options_rel)
            elif item.delivery_options:
                try:
                    import json
                    delivery_options = json.loads(item.delivery_options) if isinstance(item.delivery_options, str) else item.delivery_options
                    if delivery_options and len(delivery_options) > 0:
                        has_delivery_options = True
                        delivery_options_count = len(delivery_options)
                except:
                    pass
            if not has_delivery_options:
                continue
            
            # Use a larger range to accommodate lead times (start from 5 instead of 1)
            # Use delivery_options_count or default to max_time_slots if none found
            valid_times = list(range(5, min(delivery_options_count + 5 if delivery_options_count > 0 else request.max_time_slots, request.max_time_slots + 1)))
            item_options = [opt for opt in self.procurement_options.values() 
                          if opt.item_code == item.item_code and opt.project_item_id == item.id]
            
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
            constraint = solver.Constraint(1, 1)  # Exactly once (demand fulfillment)
            for var in vars_list:
                constraint.SetCoefficient(var, 1)
        
        # Add budget constraints (MULTI-CURRENCY SUPPORT)
        # Group by time slot AND currency
        time_currency_groups = {}  # {(time_slot, currency): [(var, cost), ...]}
        
        time_groups = self._group_by_purchase_time(variables, request.max_time_slots)
        for time_slot, var_data in time_groups.items():
            for var, cost, currency in var_data:
                key = (time_slot, currency)
                if key not in time_currency_groups:
                    time_currency_groups[key] = []
                time_currency_groups[key].append((var, cost))
        
        # Apply budget constraints per currency
        for (time_slot, currency), var_cost_pairs in time_currency_groups.items():
            if time_slot in self.budget_data_by_currency:
                currency_budgets = self.budget_data_by_currency[time_slot]
                budget_amount = currency_budgets.get(currency, Decimal(0))
                budget_limit = float(budget_amount)
            else:
                # No budget data for this time slot - use large default
                budget_limit = 100000000000000.0  # $100T default
            
            constraint = solver.Constraint(0, budget_limit)
            
            for var, cost in var_cost_pairs:
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
            # Use delivery options from relationship or JSON (for backwards compatibility)
            delivery_options_data = None
            if item.delivery_options_rel and len(item.delivery_options_rel) > 0:
                # Convert delivery options from table to list of dates
                delivery_options_data = [opt.delivery_date.isoformat() for opt in item.delivery_options_rel if opt.delivery_date]
            elif item.delivery_options:
                delivery_options_data = item.delivery_options
            self.dependency_graph.add_node(
                node_id,
                project_id=item.project_id,
                item_code=item.item_code,
                quantity=item.quantity,
                delivery_options=delivery_options_data
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
        
        # Load items that are already decided (LOCKED or PROPOSED)
        # These items should not be re-optimized
        decided_query = await self.db.execute(
            select(FinalizedDecision.project_item_id)
            .where(FinalizedDecision.status.in_(['LOCKED', 'PROPOSED']))
        )
        decided_project_item_ids = {row.project_item_id for row in decided_query.all() if row.project_item_id is not None}
        
        # Load project items with delivery options relationship
        # ONLY load items that are finalized by PMO (is_finalized == True)
        from sqlalchemy.orm import selectinload
        items_result = await self.db.execute(
            select(ProjectItem)
            .options(selectinload(ProjectItem.delivery_options_rel))
            .where(
                ProjectItem.project_id.in_(self.projects.keys()),
                ProjectItem.is_finalized == True  # Only finalized items
            )
        )
        all_items = list(items_result.scalars().all())
        self.project_items = [
            item for item in all_items
            if item.id not in decided_project_item_ids
        ]
        
        if not self.project_items:
            if all_items:
                raise ValueError(
                    "❌ All items are already decided (LOCKED or PROPOSED).\n\n"
                    "📝 What you need to do:\n"
                    "   1. Go to 'Finalized Decisions' page\n"
                    "   2. Revert or unlock items you want to re-optimize\n"
                    "   3. Or add new items to your projects\n\n"
                    "💡 Tip: Items with PROPOSED or LOCKED status are excluded from optimization to avoid duplicates."
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
        
        # Load procurement options - ONLY FINALIZED OPTIONS for optimization
        options_result = await self.db.execute(
            select(ProcurementOption).where(
                ProcurementOption.is_active == True,
                ProcurementOption.is_finalized == True
            )
        )
        self.procurement_options = {opt.id: opt for opt in options_result.scalars().all()}
        
        logger.info(f"DEBUG: Loaded {len(self.procurement_options)} finalized procurement options:")
        for opt_id, opt in self.procurement_options.items():
            logger.info(f"  - Option {opt_id}: {opt.item_code} (project_item_id: {opt.project_item_id}, finalized: {opt.is_finalized})")
        
        if not self.procurement_options:
            raise ValueError(
                "❌ No finalized procurement options found.\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Procurement' page\n"
                "   2. For each item, click 'Add Option' button\n"
                "   3. Enter supplier details:\n"
                "      • Supplier name\n"
                "      • Base cost per unit\n"
                "      • Lead time (delivery days)\n"
                "      • Payment terms (cash/installments)\n"
                "   4. ✅ CHECK the 'Finalized' checkbox to mark options ready for optimization\n"
                "   5. Add at least 2-3 finalized options per item for better optimization\n\n"
                "💡 Tip: More finalized procurement options = better optimization results!"
            )
        
        # Filter project items to only include those with FINALIZED procurement options
        # FIXED: Filter by both item_code AND project_item_id to ensure project-specific options
        project_items_with_finalized_options = {
            (opt.item_code, opt.project_item_id) 
            for opt in self.procurement_options.values() 
            if opt.project_item_id is not None
        }
        
        logger.info(f"DEBUG: Found {len(project_items_with_finalized_options)} project items with finalized options:")
        for item_code, project_item_id in project_items_with_finalized_options:
            logger.info(f"  - {item_code} (project_item_id: {project_item_id})")
        
        items_before_filter = len(self.project_items)
        self.project_items = [
            item for item in self.project_items
            if (item.item_code, item.id) in project_items_with_finalized_options
        ]
        
        logger.info(f"DEBUG: Filtered {items_before_filter} items down to {len(self.project_items)} items")
        for item in self.project_items:
            logger.info(f"  - {item.item_code} (project_id: {item.project_id}, id: {item.id})")
        
        if not self.project_items:
            raise ValueError(
                f"❌ No items with finalized procurement options found.\n\n"
                f"📊 Status:\n"
                f"   • Total project items: {items_before_filter}\n"
                f"   • Items with finalized procurement options: 0\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Procurement' page\n"
                "   2. Add procurement options for your project items\n"
                "   3. ✅ CHECK the 'Finalized' checkbox for options you want to use\n"
                "   4. Use 'Finalize All' button to quickly finalize all options for an item\n\n"
                "💡 Tip: Only items with finalized procurement options can be optimized!"
            )
        
        items_without_finalized_options = items_before_filter - len(self.project_items)
        if items_without_finalized_options > 0:
            logger.info(f"Filtered out {items_without_finalized_options} items without finalized procurement options. "
                       f"Optimizing {len(self.project_items)} items.")
        
        # === DETAILED DEBUG INFO ===
        logger.info(f"=== OPTIMIZATION DEBUG INFO ===")
        logger.info(f"Total projects: {len(self.projects)}")
        logger.info(f"Total project items before filtering: {items_before_filter}")
        logger.info(f"Total project items after filtering: {len(self.project_items)}")
        logger.info(f"Total finalized procurement options: {len(self.procurement_options)}")
        
        # Check each item's status
        valid_items = 0
        for item in self.project_items[:10]:  # Check first 10 items
            item_options = [opt for opt in self.procurement_options.values() if opt.item_code == item.item_code and opt.project_item_id == item.id]
            # Check delivery options from relationship or JSON (legacy)
            delivery_options_count = 0
            if item.delivery_options_rel and len(item.delivery_options_rel) > 0:
                delivery_options_count = len(item.delivery_options_rel)
            elif item.delivery_options:
                try:
                    import json
                    delivery_options = json.loads(item.delivery_options) if isinstance(item.delivery_options, str) else item.delivery_options
                    delivery_options_count = len(delivery_options) if delivery_options else 0
                except:
                    delivery_options_count = 0
            logger.info(f"Item {item.item_code}: {len(item_options)} finalized options, {delivery_options_count} delivery options")
            
            if len(item_options) == 0:
                logger.warning(f"❌ Item {item.item_code} has NO finalized procurement options")
            if delivery_options_count == 0:
                logger.warning(f"❌ Item {item.item_code} has NO delivery options")
            
            if len(item_options) > 0 and delivery_options_count > 0:
                valid_items += 1
                logger.info(f"✅ Item {item.item_code} is VALID for optimization")
            else:
                logger.warning(f"❌ Item {item.item_code} is INVALID - finalized: {len(item_options) > 0}, delivery: {delivery_options_count > 0}")
        
        logger.info(f"=== SUMMARY: {valid_items} items are valid for optimization (checked first 10) ===")
        
        # Validate items have finalized procurement options (should not happen due to filtering above, but double-check)
        items_without_finalized_options_check = []
        for item in self.project_items[:5]:  # Check first 5 items
            matching_options = [opt for opt in self.procurement_options.values() 
                              if opt.item_code == item.item_code and opt.project_item_id == item.id]
            if not matching_options:
                items_without_finalized_options_check.append(item.item_code)
        
        if items_without_finalized_options_check:
            raise ValueError(
                f"❌ Some items don't have finalized procurement options.\n\n"
                f"Items without finalized options: {', '.join(items_without_finalized_options_check[:3])}"
                f"{' and more...' if len(items_without_finalized_options_check) > 3 else ''}\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Procurement' page\n"
                "   2. Find these items in the list\n"
                "   3. Add procurement options and ✅ CHECK 'Finalized' checkbox\n"
                "   4. Use 'Finalize All' button to quickly finalize all options\n\n"
                "💡 Tip: All items must have at least one finalized procurement option for optimization."
            )
        
        # Load budget data with multi-currency support
        budget_result = await self.db.execute(
            select(BudgetData).order_by(BudgetData.budget_date)
        )
        budget_list = budget_result.scalars().all()
        self.budget_data = {}
        self.budget_data_by_currency = {}  # NEW: Track budgets by currency {time_slot: {currency: amount}}
        
        for idx, bd in enumerate(budget_list, start=1):
            self.budget_data[idx] = bd
            
            # Load multi_currency_budget if available
            if bd.multi_currency_budget:
                import json
                if isinstance(bd.multi_currency_budget, str):
                    currency_dict = json.loads(bd.multi_currency_budget)
                else:
                    currency_dict = bd.multi_currency_budget
                
                if idx not in self.budget_data_by_currency:
                    self.budget_data_by_currency[idx] = {}
                
                # Store each currency separately
                for currency, amount in currency_dict.items():
                    currency_code = currency.strip().upper() if currency else 'IRR'
                    if currency_code not in self.budget_data_by_currency[idx]:
                        self.budget_data_by_currency[idx][currency_code] = Decimal(0)
                    self.budget_data_by_currency[idx][currency_code] += Decimal(str(amount))
            else:
                # Fallback to legacy available_budget (assumed IRR)
                if idx not in self.budget_data_by_currency:
                    self.budget_data_by_currency[idx] = {}
                if 'IRR' not in self.budget_data_by_currency[idx]:
                    self.budget_data_by_currency[idx]['IRR'] = Decimal(0)
                self.budget_data_by_currency[idx]['IRR'] += Decimal(str(bd.available_budget or 0))
        
        if not self.budget_data:
            raise ValueError(
                "❌ No budget data found.\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Finance' page\n"
                "   2. Click 'Budget Management' tab\n"
                "   3. Add monthly budgets:\n"
                "      • Select month\n"
                "      • Enter available budget amount (or multi-currency budget)\n"
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
            project_id = int(parts[1])
            item_code = parts[2]
            option_id = int(parts[3])
            
            # Get the project_item_id from the procurement option
            option = self.procurement_options[option_id]
            project_item_id = option.project_item_id
            
            key = (project_id, project_item_id)
            if key not in item_groups:
                item_groups[key] = []
            item_groups[key].append(var)
        
        logger.info(f"=== DEMAND CONSTRAINTS ===")
        logger.info(f"Item groups: {len(item_groups)}")
        for key, vars_list in item_groups.items():
            logger.info(f"  Item {key}: {len(vars_list)} options")
        
        # Check if we have any feasible options
        if len(variables) == 0:
            logger.error("No feasible variables found - optimization will fail")
            return
        
        # DEMAND FULFILLMENT: each project item must be purchased exactly once (== 1)
        # This ensures all project items are procured, not just the most cost-effective ones
        for key, vars_list in item_groups.items():
            if len(vars_list) > 0:  # Only add constraints for items with options
                project_id, project_item_id = key
                
                # Find the project item to get its quantity
                project_item = next((item for item in self.project_items 
                                   if item.project_id == project_id and item.id == project_item_id), None)
                
                if project_item:
                    # Each project item must be purchased exactly once
                    model.Add(sum(vars_list) == 1)
                    logger.info(f"  Added demand constraint for project_item_id {project_item_id}: {len(vars_list)} options must sum to 1 (quantity: {project_item.quantity})")
                else:
                    logger.warning(f"  Could not find project item for key {key}")
    
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
            
            # Skip options with impossible lead times (purchase time in the past or too far in the past)
            if purchase_time < 0:
                logger.debug(f"Skipping option {option_id} for {item_code}: purchase_time={purchase_time} (negative)")
                continue
            
            if purchase_time not in time_groups:
                time_groups[purchase_time] = []
            
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if item:
                time_groups[purchase_time].append((var, option, item))
        
        # Store slack variables for penalty in objective
        self.cpsat_budget_slack_vars = []
        
        # FIXED: Iterate over actual time slots that have variables, not a fixed range
        logger.info(f"=== BUDGET CONSTRAINTS ===")
        logger.info(f"Time groups keys: {sorted(time_groups.keys())}")
        logger.info(f"Budget data keys: {list(self.budget_data.keys())}")
        
        for time_slot in sorted(time_groups.keys()):
            if time_slot not in time_groups:
                continue
            
            cash_flow_vars = []
            cash_flow_coeffs = []
            
            # Group costs by currency (MULTI-CURRENCY SUPPORT)
            costs_by_currency = {}  # {currency: [(var, cost), ...]}
            
            for var, option, item in time_groups[time_slot]:
                cost, currency = self._calculate_effective_cost(option, item)
                total_cost = cost * item.quantity
                
                if currency not in costs_by_currency:
                    costs_by_currency[currency] = []
                costs_by_currency[currency].append((var, total_cost))
                
                logger.debug(
                    f"    Cost: {total_cost:,.2f} {currency} for {item.item_code} {option.supplier_name}"
                )
            
            # Apply budget constraints PER CURRENCY (not mixed)
            for currency, var_cost_pairs in costs_by_currency.items():
                cash_flow_vars = [v for v, _ in var_cost_pairs]
                # Scale to thousands for numerical stability
                cash_flow_coeffs = [int(c / 1000) for _, c in var_cost_pairs]
                
                # Get budget for this currency and time slot
                if time_slot in self.budget_data_by_currency:
                    currency_budgets = self.budget_data_by_currency[time_slot]
                    budget_amount = currency_budgets.get(currency, Decimal(0))
                    budget_limit = int(budget_amount / 1000)
                    logger.info(
                        f"Time slot {time_slot} ({currency}): budget={budget_limit}K, "
                        f"vars={len(cash_flow_vars)}"
                    )
                else:
                    # No budget data for this time slot - use large default
                    budget_limit = 100000000000  # $100T default (100,000,000,000K)
                    logger.info(
                        f"Time slot {time_slot} ({currency}): DEFAULT budget={budget_limit}K, "
                        f"vars={len(cash_flow_vars)}"
                    )
                
                # Calculate total cost for this currency in this time slot
                total_cost = sum(cash_flow_coeffs)
                logger.info(
                    f"  Total cost for time slot {time_slot} ({currency}): "
                    f"{total_cost}K (budget: {budget_limit}K)"
                )
                
                if cash_flow_vars:
                    # Create slack variable to allow exceeding budget
                    max_slack = max(budget_limit // 2, 500)  # At least $500K
                    slack_var = model.NewIntVar(
                        0, max_slack, 
                        f'cpsat_budget_slack_{time_slot}_{currency}'
                    )
                    
                    # Soft constraint: spending <= budget + slack (per currency)
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
            cost, _ = self._calculate_effective_cost(option, item)
            cost = float(cost * item.quantity)
            
            # Calculate business value (revenue from item)
            business_value = 0
            # Try to get invoice amount from delivery options relationship (NEW SYSTEM)
            if item.delivery_options_rel and len(item.delivery_options_rel) > 0:
                # Use the first delivery option's invoice amount
                first_delivery_option = item.delivery_options_rel[0]
                if first_delivery_option.invoice_amount_per_unit:
                    business_value = float(first_delivery_option.invoice_amount_per_unit) * item.quantity
            # Fallback to JSON field for legacy items (OLD SYSTEM)
            elif hasattr(item, 'delivery_options') and item.delivery_options:
                try:
                    import json
                    delivery_options = json.loads(item.delivery_options) if isinstance(item.delivery_options, str) else item.delivery_options
                    if isinstance(delivery_options, list) and delivery_options:
                        first_delivery = delivery_options[0]
                        if isinstance(first_delivery, dict) and 'invoice_amount_per_unit' in first_delivery:
                            business_value = float(first_delivery['invoice_amount_per_unit']) * item.quantity
                except:
                    pass
            
            # If no delivery option, use 200% markup as default to ensure profitability
            if business_value == 0:
                business_value = cost * 3.0  # 200% profit margin
            
            # Debug logging for objective function
            logger.debug(f"Objective for {item.item_code}: cost={cost:,.2f}, value={business_value:,.2f}, profit={business_value-cost:,.2f}")
            
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
                # Normalize delivery_time (days) to a reasonable scale
                # Shorter delivery time = higher value weight
                max_delivery_days = 90  # Assume max 90 days
                normalized_delivery = min(delivery_time, max_delivery_days) / max_delivery_days
                cost_weight = 1.0
                value_weight = 1.0 + (1.0 - normalized_delivery) * 2.0  # Range: 1.0 to 3.0
            elif strategy == OptimizationStrategy.SMOOTH_CASHFLOW:
                # Prefer middle time slots to balance cash flow
                # Normalize delivery_time to 0-1 range
                max_delivery_days = 90
                normalized_delivery = min(delivery_time, max_delivery_days) / max_delivery_days
                # Prefer middle range (around 0.5)
                distance_from_middle = abs(normalized_delivery - 0.5)
                cost_weight = 1.0 + distance_from_middle
                value_weight = 1.0 + (0.5 - distance_from_middle) * 0.5  # Bonus for middle range
            else:  # BALANCED
                # Balance between priority and delivery time
                priority = project.priority_weight if project else 5
                priority_factor = float(11 - priority) * 0.05  # Range: 0.3 to 0.55
                # Normalize delivery time
                max_delivery_days = 90
                normalized_delivery = min(delivery_time, max_delivery_days) / max_delivery_days
                delivery_factor = (1.0 - normalized_delivery) * 0.3  # Range: 0 to 0.3
                cost_weight = priority_factor + delivery_factor + 0.5
                value_weight = 1.0 + (priority * 0.1) + (1.0 - normalized_delivery) * 0.2
            
            # Scale to thousands for numerical stability
            cost_scaled = int(cost / 1000 * cost_weight)
            value_scaled = int(business_value / 1000 * value_weight)
            
            cost_terms.append(var * cost_scaled)
            value_terms.append(var * value_scaled)
        
        # Add budget penalty if slack variables exist
        budget_penalty = 0
        if hasattr(self, 'cpsat_budget_slack_vars') and self.cpsat_budget_slack_vars:
            BUDGET_PENALTY_MULTIPLIER = 1000000  # High penalty for budget violations in demand fulfillment
            budget_penalty = sum(slack * BUDGET_PENALTY_MULTIPLIER for slack in self.cpsat_budget_slack_vars)
        
        # Objective: Minimize(Cost - Value + Budget_Penalty)
        total_cost = sum(cost_terms)
        total_value = sum(value_terms)
        objective_value = total_cost - total_value + budget_penalty
        
        logger.info(f"=== OBJECTIVE FUNCTION ===")
        logger.info(f"Total cost terms: {len(cost_terms)}")
        logger.info(f"Total value terms: {len(value_terms)}")
        logger.info(f"Budget penalty: {budget_penalty}")
        logger.info(f"Final objective: [CP-SAT Expression]")
        
        model.Minimize(objective_value)
    
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
            
            cost, _ = self._calculate_effective_cost(option, item)
            cost = float(cost * item.quantity)
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
                cost, _ = self._calculate_effective_cost(option, item)
                cost = float(cost * item.quantity)
                if purchase_time not in time_groups:
                    time_groups[purchase_time] = []
                time_groups[purchase_time].append((var, cost))
        
        return time_groups
    
    def _calculate_effective_cost(self, option: ProcurementOption, item: ProjectItem) -> Tuple[Decimal, str]:
        """
        Calculate effective cost with discounts and shipping
        
        IMPORTANT: Returns cost AND currency to support multi-currency optimization.
        NO currency conversion is performed - cost stays in original currency.
        
        Returns:
            Tuple[cost_amount, currency_code]
            Example: (Decimal('2000'), 'USD') or (Decimal('5000000'), 'IRR')
        """
        # Get the original cost in its original currency
        if hasattr(option, 'cost_amount') and option.cost_amount:
            base_cost = option.cost_amount
            cost_currency = getattr(option, 'cost_currency', 'IRR') or 'IRR'
        else:
            # Fallback to legacy field for backward compatibility
            base_cost = option.base_cost
            cost_currency = 'IRR'
        
        # Normalize currency code
        cost_currency = cost_currency.strip().upper() if cost_currency else 'IRR'
        
        # Add shipping cost (same currency)
        shipping_cost = getattr(option, 'shipping_cost', 0) or Decimal(0)
        base_cost = base_cost + shipping_cost
        
        # Apply discounts (cost stays in same currency)
        if option.payment_terms.get('type') == 'cash':
            discount = option.payment_terms.get('discount_percent', 0)
            base_cost = base_cost * (1 - Decimal(discount) / 100)
        
        if (option.discount_bundle_threshold and 
            item.quantity >= option.discount_bundle_threshold and 
            option.discount_bundle_percent):
            base_cost = base_cost * (1 - option.discount_bundle_percent / 100)
        
        return base_cost, cost_currency
    
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
        
        # FIXED: Find the item by project_item_id from the procurement option
        item = next((i for i in self.project_items 
                    if i.project_id == project_id and i.id == option.project_item_id), None)
        project = self.projects.get(project_id)
        
        if not (option and item and project):
            return None
        
        unit_cost, _ = self._calculate_effective_cost(option, item)
        final_cost = unit_cost * item.quantity
        purchase_time = delivery_time - option.lomc_lead_time
        
        # CORRECTED: Use procurement option's purchase_date and expected_delivery_date
        # These are the actual dates when orders should be placed and when suppliers deliver
        
        if option.purchase_date and option.expected_delivery_date:
            # Use the actual purchase and delivery dates from procurement option
            purchase_date = option.purchase_date
            delivery_date = option.expected_delivery_date
        else:
            # Fallback: Calculate from project delivery options and lead time
            from datetime import datetime
            actual_delivery_date = None
            today = date.today()
            
            # Try delivery options from relationship (NEW SYSTEM)
            if item.delivery_options_rel and len(item.delivery_options_rel) > 0:
                for delivery_option in item.delivery_options_rel:
                    if delivery_option.delivery_date:
                        days_from_today = (delivery_option.delivery_date - today).days
                        if days_from_today == delivery_time:
                            actual_delivery_date = delivery_option.delivery_date
                            break
            # Fallback to JSON field (LEGACY SYSTEM)
            elif item.delivery_options:
                try:
                    import json
                    delivery_options = json.loads(item.delivery_options) if isinstance(item.delivery_options, str) else item.delivery_options
                    for delivery_date_str in delivery_options:
                        try:
                            if isinstance(delivery_date_str, dict):
                                delivery_date_str = delivery_date_str.get('delivery_date', '')
                            
                            if delivery_date_str:
                                delivery_date = datetime.fromisoformat(delivery_date_str.replace('Z', '+00:00')).date()
                                days_from_today = (delivery_date - today).days
                                
                                if days_from_today == delivery_time:
                                    actual_delivery_date = delivery_date
                                    break
                        except (ValueError, TypeError):
                            continue
                except:
                    pass
            
            if actual_delivery_date:
                # Calculate purchase date based on actual delivery date and lead time
                purchase_date = actual_delivery_date - timedelta(days=option.lomc_lead_time)
                delivery_date = actual_delivery_date
            else:
                # Final fallback to approximate calculation
                purchase_date = date.today() + timedelta(days=delivery_time - option.lomc_lead_time)
                delivery_date = date.today() + timedelta(days=delivery_time)
        
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
            payment_terms=str(option.payment_terms.get('type', 'unknown')),
            project_item_id=item.id  # Add project_item_id to identify specific project item
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

