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
                user_message = (
                    "❌ Could not find a feasible solution.\n\n"
                    "📝 Possible reasons and solutions:\n\n"
                    "1️⃣ Budget constraints too tight:\n"
                    "   • Go to Finance → Budget Management\n"
                    "   • Increase monthly budgets or add more periods\n\n"
                    "2️⃣ Procurement options too expensive:\n"
                    "   • Go to Procurement page\n"
                    "   • Add more cost-effective suppliers\n\n"
                    "3️⃣ Lead times conflict with delivery dates:\n"
                    "   • Add suppliers with shorter lead times\n"
                    "   • Adjust item delivery dates\n\n"
                    "💡 Tip: Try Advanced Optimization with different solvers (Glop, CBC) for better results."
                )
                return OptimizationRunResponse(
                    run_id=uuid.UUID(self.run_id),
                    run_timestamp=self.start_time,
                    status="INFEASIBLE" if status == cp_model.INFEASIBLE else "UNKNOWN",
                    execution_time_seconds=execution_time,
                    total_cost=Decimal('0'),
                    items_optimized=0,
                    proposals=[],
                    message=user_message
                )
                
        except Exception as e:
            logger.error(f"Optimization failed: {str(e)}")
            execution_time = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            # Format error message for user
            error_msg = str(e)
            if "No active projects" in error_msg or "No project items" in error_msg or \
               "No procurement options" in error_msg or "No budget data" in error_msg:
                user_message = error_msg
            else:
                user_message = (
                    f"❌ Optimization failed with technical error.\n\n"
                    f"Error details: {error_msg}\n\n"
                    "📝 What you can try:\n"
                    "   1. Verify all data is complete (projects, items, options, budgets)\n"
                    "   2. Try reducing the time limit\n"
                    "   3. Use Advanced Optimization with different solvers\n\n"
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
    
    async def _load_data(self):
        """Load all necessary data from database, excluding locked items"""
        # Load projects and their items
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
                "   3. Make sure the project is marked as 'Active'"
            )
        
        # Get all locked decisions (items that should not be re-optimized)
        locked_query = await self.db.execute(
            select(FinalizedDecision.project_id, FinalizedDecision.item_code)
            .where(FinalizedDecision.status == 'LOCKED')
        )
        locked_items = {(row.project_id, row.item_code) for row in locked_query.all()}
        
        logger.info(f"Found {len(locked_items)} locked items that will be excluded from optimization")
        
        # Load project items with delivery options relationship
        from sqlalchemy.orm import selectinload
        items_result = await self.db.execute(
            select(ProjectItem)
            .options(selectinload(ProjectItem.delivery_options_rel))
            .where(ProjectItem.project_id.in_(self.projects.keys()))
        )
        all_items = list(items_result.scalars().all())
        
        # Filter out locked items
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
                    "   3. Or add new items to your projects"
                )
            else:
                raise ValueError(
                    "❌ No project items found.\n\n"
                    "📝 What you need to do:\n"
                    "   1. Go to 'Project Items' page\n"
                    "   2. Select a project and click 'Add Item'\n"
                    "   3. Choose items from the catalog\n"
                    "   4. Set quantities and delivery dates"
                )
        
        logger.info(f"Excluded {len(all_items) - len(self.project_items)} locked items from optimization")
        
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
                "   2. Click 'Add Option' for each item\n"
                "   3. Enter supplier details (name, cost, lead time)\n"
                "   4. Add 2-3 options per item for better optimization"
            )
        
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
        
        if not self.budget_data:
            raise ValueError(
                "❌ No budget data found.\n\n"
                "📝 What you need to do:\n"
                "   1. Go to 'Finance' page\n"
                "   2. Click 'Budget Management' tab\n"
                "   3. Add monthly budgets (month + amount)\n"
                "   4. Add at least 3-6 months of budget data"
            )
        
        logger.info(f"✅ Loaded {len(self.projects)} projects, {len(self.project_items)} items, "
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
            
            # Convert delivery dates to time slots
            # Use a larger range to accommodate lead times
            # Map each delivery option to a time slot starting from a higher number
            # to ensure purchase_time (delivery_time - lead_time) remains positive
            valid_times = list(range(5, min(len(delivery_options) + 5, max_time_slots + 1)))
            
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
        """Add constraints to allow partial procurement (when budget is insufficient)"""
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
        
        # Add constraint: each item can be procured at most once (allows skipping items)
        # This enables the optimizer to work within tight budget constraints
        for (project_id, item_code), vars_list in item_groups.items():
            self.model.Add(sum(vars_list) <= 1)
            
            # Find the required quantity for this item
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            if item:
                logger.debug(f"Item {item_code} in project {project_id} requires quantity {item.quantity}")
    
    def _add_budget_constraints(self):
        """Add soft budget constraints with slack variables
        
        Instead of hard constraints that make the problem infeasible,
        we use slack variables that allow going over budget but add
        a penalty to the objective function.
        """
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
        
        # Store slack variables for penalty in objective
        self.budget_slack_vars = []
        
        # Add soft budget constraint for each time period
        for time_slot in range(1, self.max_time_slots + 1):
            if time_slot not in time_groups:
                continue
                
            # Calculate total cash outflow for this time period
            # Scale by 1000 for numerical stability (thousands of dollars)
            cash_flow_vars = []
            cash_flow_coeffs = []
            
            for var, option, item in time_groups[time_slot]:
                cost_per_unit = self._calculate_effective_cost(option, item)
                total_cost = cost_per_unit * item.quantity
                
                # Scale to thousands (divide by 1000 for stability)
                cash_flow_vars.append(var)
                cash_flow_coeffs.append(int(total_cost / 1000))
            
            # Get available budget for this time period
            if time_slot in self.budget_data:
                available_budget = self.budget_data[time_slot]
            else:
                # Assign a large default budget for time slots without explicit data
                available_budget = type('obj', (object,), {'available_budget': Decimal('1000000')})()
            
            budget_limit = int(available_budget.available_budget / 1000)  # Scale to thousands
            
            if cash_flow_vars:
                # Create slack variable to allow exceeding budget
                # Maximum slack is 50% of budget (adjust as needed)
                max_slack = max(budget_limit // 2, 1000)  # At least 1000 (= $1M)
                slack_var = self.model.NewIntVar(0, max_slack, f'budget_slack_{time_slot}')
                
                # Soft constraint: spending = budget + slack
                total_spending = sum(var * coeff for var, coeff in zip(cash_flow_vars, cash_flow_coeffs))
                self.model.Add(total_spending <= budget_limit + slack_var)
                
                # Store slack variable for penalty
                self.budget_slack_vars.append(slack_var)
                
                logger.debug(f"Time slot {time_slot}: {len(cash_flow_vars)} variables, "
                           f"budget limit: ${budget_limit}K, max slack: ${max_slack}K")
    
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
        """Set the objective function to maximize business value minus cost
        
        Goal: Maximize the value delivered by purchasing items while minimizing cost.
        This creates a true trade-off between value and cost.
        
        Formula: Minimize(Total_Cost - Total_Business_Value)
        Where Business_Value represents the revenue/benefit from each item.
        
        The solver will now prefer purchasing items because each purchase
        adds more value than it costs (with 15% markup).
        """
        cost_terms = []
        value_terms = []
        
        for var_name, var in self.variables.items():
            parts = var_name.split('_')
            option_id = int(parts[3])
            project_id = int(parts[1])
            item_code = parts[2]
            
            option = self.procurement_options[option_id]
            item = next((i for i in self.project_items 
                        if i.project_id == project_id and i.item_code == item_code), None)
            
            if item:
                # Calculate procurement cost
                cost_per_unit = self._calculate_effective_cost(option, item)
                total_cost = cost_per_unit * item.quantity
                
                # Calculate business value (revenue from selling the item)
                # Use the invoice_amount_per_unit from delivery options relationship
                business_value = 0
                if hasattr(item, 'delivery_options_rel') and item.delivery_options_rel:
                    # Use the first delivery option's invoice amount
                    first_delivery = item.delivery_options_rel[0]
                    business_value = float(first_delivery.invoice_amount_per_unit) * item.quantity
                
                # If no delivery option found, use 20% markup as default
                if business_value == 0:
                    business_value = float(total_cost) * 1.20
                
                # Get project priority weight (higher = more important)
                project = self.projects.get(project_id)
                priority_weight = project.priority_weight if project else 5
                
                # Apply priority weighting to value (higher priority = higher effective value)
                # High priority (10) gets multiplier 1.5, low priority (1) gets multiplier 0.6
                priority_multiplier = 0.5 + (priority_weight / 10.0)
                weighted_value = business_value * priority_multiplier
                
                # Scale to dollars (divide by 1000 for numerical stability)
                # This converts $62,000 to 62, making the solver more efficient
                cost_scaled = int(total_cost / 1000)
                value_scaled = int(weighted_value / 1000)
                
                # Add to objective terms
                # When item is purchased (var=1): adds cost, subtracts value
                cost_terms.append(var * cost_scaled)
                value_terms.append(var * value_scaled)
        
        # Add penalty for exceeding budget (if slack variables exist)
        budget_penalty = 0
        if hasattr(self, 'budget_slack_vars') and self.budget_slack_vars:
            # Penalty multiplier: Each $1K over budget costs 10x in the objective
            # This makes exceeding budget very expensive but not impossible
            BUDGET_PENALTY_MULTIPLIER = 10
            budget_penalty = sum(slack * BUDGET_PENALTY_MULTIPLIER for slack in self.budget_slack_vars)
        
        # Objective: Minimize(Cost - Value + Budget_Penalty)
        # This means: prefer high value, low cost solutions, but heavily penalize going over budget
        # Each purchase that brings more value than cost will be favored
        # But the solver will try to stay within budget due to the penalty
        self.model.Minimize(sum(cost_terms) - sum(value_terms) + budget_penalty)
        logger.info(f"Set objective: Minimize(Cost - Value + Budget_Penalty) with {len(cost_terms)} decision variables")
    
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
