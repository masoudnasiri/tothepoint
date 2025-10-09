"""
Optimization Engine using Google OR-Tools CP-SAT Solver
This module contains the core optimization logic for procurement planning.
"""

from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from ortools.sat.python import cp_model
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import (
    Project, ProjectItem, ProcurementOption, BudgetData, 
    OptimizationResult, FinalizedDecision
)
from app.schemas import OptimizationRunRequest, OptimizationRunResponse
import logging

logger = logging.getLogger(__name__)


class ProcurementOptimizer:
    """Main optimization engine for procurement planning"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model = None
        self.variables = {}
        self.run_id = str(uuid.uuid4())
        self.start_time = None
        
    async def run_optimization(self, request: OptimizationRunRequest) -> OptimizationRunResponse:
        """Run the complete optimization process"""
        self.start_time = datetime.now()
        
        try:
            # Step 1: Load and validate data
            await self._load_data()
            
            # Step 2: Build the optimization model
            self._build_model(request.max_time_slots)
            
            # Step 3: Solve the model
            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = request.time_limit_seconds
            
            status = solver.Solve(self.model)
            
            # Step 4: Process results
            if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                await self._save_results(solver)
                total_cost = self._calculate_total_cost(solver)
                execution_time = (datetime.now() - self.start_time).total_seconds()
                
                return OptimizationRunResponse(
                    run_id=uuid.UUID(self.run_id),
                    run_timestamp=self.start_time,
                    status="OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                    execution_time_seconds=execution_time,
                    total_cost=total_cost,
                    items_optimized=len([v for v in self.variables.values() if solver.Value(v) == 1]),
                    proposals=[],  # TODO: Generate multiple proposals
                    message="Optimization completed successfully"
                )
            else:
                execution_time = (datetime.now() - self.start_time).total_seconds()
                return OptimizationRunResponse(
                    run_id=uuid.UUID(self.run_id),
                    run_timestamp=self.start_time,
                    status="INFEASIBLE" if status == cp_model.INFEASIBLE else "UNKNOWN",
                    execution_time_seconds=execution_time,
                    total_cost=Decimal('0'),
                    items_optimized=0,
                    proposals=[],
                    message="Optimization failed - no feasible solution found"
                )
                
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
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
    
    async def _load_data(self):
        """Load all necessary data from database, excluding locked items"""
        # Load projects and their items
        projects_result = await self.db.execute(
            select(Project).where(Project.is_active == True)
        )
        self.projects = {p.id: p for p in projects_result.scalars().all()}
        
        # Get all locked decisions (items that should not be re-optimized)
        locked_query = await self.db.execute(
            select(FinalizedDecision.project_id, FinalizedDecision.item_code)
            .where(FinalizedDecision.status == 'LOCKED')
        )
        locked_items = {(row.project_id, row.item_code) for row in locked_query.all()}
        
        logger.info(f"Found {len(locked_items)} locked items that will be excluded from optimization")
        
        # Load project items
        items_result = await self.db.execute(
            select(ProjectItem).where(
                ProjectItem.project_id.in_(self.projects.keys())
            )
        )
        all_items = list(items_result.scalars().all())
        
        # Filter out locked items
        self.project_items = [
            item for item in all_items
            if (item.project_id, item.item_code) not in locked_items
        ]
        
        logger.info(f"Excluded {len(all_items) - len(self.project_items)} locked items from optimization")
        
        # Load procurement options
        options_result = await self.db.execute(
            select(ProcurementOption).where(ProcurementOption.is_active == True)
        )
        self.procurement_options = {opt.id: opt for opt in options_result.scalars().all()}
        
        # Load budget data
        budget_result = await self.db.execute(
            select(BudgetData).order_by(BudgetData.budget_date)
        )
        # Create a mapping: time_slot -> budget_data (for optimization engine compatibility)
        budget_list = budget_result.scalars().all()
        self.budget_data = {}
        for idx, bd in enumerate(budget_list, start=1):
            # Map budget to time slot (1, 2, 3, etc.)
            self.budget_data[idx] = bd
        
        logger.info(f"Loaded {len(self.projects)} projects, {len(self.project_items)} items, "
                   f"{len(self.procurement_options)} procurement options, "
                   f"{len(self.budget_data)} budget periods")
    
    def _build_model(self, max_time_slots: int):
        """Build the CP-SAT optimization model"""
        self.model = cp_model.CpModel()
        self.max_time_slots = max_time_slots
        
        # Create decision variables: buy[p, i, o, t] = 1 if item i for project p 
        # is procured using option o for delivery at time t
        self.variables = {}
        
        for item in self.project_items:
            project_id = item.project_id
            item_code = item.item_code
            
            # Get delivery options (list of ISO date strings)
            delivery_options = item.delivery_options if item.delivery_options else []
            
            if not delivery_options:
                logger.warning(f"Item {item_code} has no delivery options, skipping")
                continue
            
            # Convert delivery dates to time slots (for now, use a simple mapping)
            # TODO: In future, use actual calendar-based optimization
            # For now, we'll use slots 1-12 based on which delivery option
            valid_times = list(range(1, min(len(delivery_options) + 1, max_time_slots + 1)))
            
            if not valid_times:
                continue
                
            # Find procurement options for this item
            item_options = [opt for opt in self.procurement_options.values() 
                          if opt.item_code == item_code]
            
            if not item_options:
                continue
            
            # Create variables for each valid (project, item, option, time) combination
            for option in item_options:
                for delivery_time in valid_times:
                    purchase_time = delivery_time - option.lomc_lead_time
                    
                    # Purchase time must be >= 1 (time slot 0 doesn't exist)
                    if purchase_time < 1:
                        continue
                    
                    var_name = f"buy_{project_id}_{item_code}_{option.id}_{delivery_time}"
                    self.variables[var_name] = self.model.NewBoolVar(var_name)
        
        # Add constraints
        self._add_demand_fulfillment_constraints()
        self._add_budget_constraints()
        
        # Set objective: minimize total cost
        self._set_objective()
        
        logger.info(f"Built model with {len(self.variables)} variables")
    
    def _add_demand_fulfillment_constraints(self):
        """Add constraints to ensure each item is procured exactly once"""
        # Group variables by (project_id, item_code)
        item_groups = {}
        
        for var_name, var in self.variables.items():
            parts = var_name.split('_')
            project_id = int(parts[1])
            item_code = parts[2]
            key = (project_id, item_code)
            
            if key not in item_groups:
                item_groups[key] = []
            item_groups[key].append(var)
        
        # Add constraint: each item must be procured exactly once
        for (project_id, item_code), vars_list in item_groups.items():
            self.model.Add(sum(vars_list) == 1)
            
            # Find the required quantity for this item
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            if item:
                logger.debug(f"Item {item_code} in project {project_id} requires quantity {item.quantity}")
    
    def _add_budget_constraints(self):
        """Add budget constraints for each time period"""
        # Group variables by purchase time
        time_groups = {}
        
        for var_name, var in self.variables.items():
            parts = var_name.split('_')
            delivery_time = int(parts[4])
            option_id = int(parts[3])
            project_id = int(parts[1])
            item_code = parts[2]
            
            # Calculate purchase time
            option = self.procurement_options[option_id]
            purchase_time = delivery_time - option.lomc_lead_time
            
            if purchase_time not in time_groups:
                time_groups[purchase_time] = []
            
            # Find the item to get quantity
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if item:
                time_groups[purchase_time].append((var, option, item))
        
        # Add budget constraint for each time period
        for time_slot in range(1, self.max_time_slots + 1):
            if time_slot not in time_groups:
                continue
                
            # Calculate total cash outflow for this time period
            # CP-SAT requires integer coefficients, so we scale by 100 (cents)
            cash_flow_vars = []
            cash_flow_coeffs = []
            
            for var, option, item in time_groups[time_slot]:
                cost_per_unit = self._calculate_effective_cost(option, item)
                total_cost = cost_per_unit * item.quantity
                
                # Scale to cents (integer)
                cash_flow_vars.append(var)
                cash_flow_coeffs.append(int(total_cost * 100))
            
            # Get available budget for this time period
            # Get budget for this time slot, or create a dummy with zero budget
            if time_slot in self.budget_data:
                available_budget = self.budget_data[time_slot]
            else:
                # Create a dummy budget object for slots without budget
                available_budget = type('obj', (object,), {'available_budget': Decimal('0')})()
            budget_limit = int(available_budget.available_budget * 100)  # Scale to cents
            
            if cash_flow_vars:
                self.model.Add(
                    sum(var * coeff for var, coeff in zip(cash_flow_vars, cash_flow_coeffs)) <= budget_limit
                )
                
                logger.debug(f"Time slot {time_slot}: {len(cash_flow_vars)} variables, "
                           f"budget limit: {budget_limit / 100}")
    
    def _calculate_effective_cost(self, option: ProcurementOption, item: ProjectItem) -> Decimal:
        """Calculate the effective cost per unit considering discounts"""
        base_cost = option.base_cost
        
        # Apply cash discount if applicable
        if option.payment_terms.get('type') == 'cash':
            discount = option.payment_terms.get('discount_percent', 0)
            base_cost = base_cost * (1 - Decimal(discount) / 100)
        
        # Apply bundling discount if applicable
        if (option.discount_bundle_threshold and 
            item.quantity >= option.discount_bundle_threshold and 
            option.discount_bundle_percent):
            base_cost = base_cost * (1 - option.discount_bundle_percent / 100)
        
        return base_cost
    
    def _set_objective(self):
        """Set the objective function to minimize weighted total cost based on project priorities"""
        objective_terms = []
        
        for var_name, var in self.variables.items():
            parts = var_name.split('_')
            option_id = int(parts[3])
            project_id = int(parts[1])
            item_code = parts[2]
            
            option = self.procurement_options[option_id]
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if item:
                cost_per_unit = self._calculate_effective_cost(option, item)
                total_cost = cost_per_unit * item.quantity
                
                # Get project priority weight (higher = more important)
                project = self.projects.get(project_id)
                priority_weight = project.priority_weight if project else 5
                
                # Use inverse weighting: (11 - priority) to give preference to high-priority projects
                # High priority (10) gets weight (11-10=1), low priority (1) gets weight (11-1=10)
                # This makes high-priority items "cheaper" in the objective function
                weight_factor = 11 - priority_weight
                
                # Scale to cents (integer) for CP-SAT and apply weight
                weighted_cost = int(total_cost * 100 * weight_factor)
                objective_terms.append(var * weighted_cost)
        
        self.model.Minimize(sum(objective_terms))
        logger.info(f"Set objective with {len(objective_terms)} weighted terms (portfolio-level optimization)")
    
    async def _save_results(self, solver):
        """Save optimization results to database"""
        results = []
        
        for var_name, var in self.variables.items():
            if solver.Value(var) == 1:  # Variable is selected
                parts = var_name.split('_')
                project_id = int(parts[1])
                item_code = parts[2]
                option_id = int(parts[3])
                delivery_time = int(parts[4])
                
                option = self.procurement_options[option_id]
                item = next((i for i in self.project_items 
                            if i.project_id == project_id and i.item_code == item_code), None)
                
                if item:
                    purchase_time = delivery_time - option.lomc_lead_time
                    final_cost = self._calculate_effective_cost(option, item) * item.quantity
                    
                    result = OptimizationResult(
                        run_id=uuid.UUID(self.run_id),
                        project_id=project_id,
                        item_code=item_code,
                        procurement_option_id=option_id,
                        purchase_time=purchase_time,
                        delivery_time=delivery_time,
                        quantity=item.quantity,
                        final_cost=final_cost
                    )
                    results.append(result)
        
        # Save all results
        self.db.add_all(results)
        await self.db.commit()
        
        logger.info(f"Saved {len(results)} optimization results")
    
    def _calculate_total_cost(self, solver) -> Decimal:
        """Calculate total cost of the optimized solution"""
        total_cost = Decimal('0')
        
        for var_name, var in self.variables.items():
            if solver.Value(var) == 1:
                parts = var_name.split('_')
                option_id = int(parts[3])
                project_id = int(parts[1])
                item_code = parts[2]
                
                option = self.procurement_options[option_id]
                item = next((i for i in self.project_items 
                            if i.project_id == project_id and i.item_code == item_code), None)
                
                if item:
                    cost_per_unit = self._calculate_effective_cost(option, item)
                    total_cost += cost_per_unit * item.quantity
        
        return total_cost
