"""
Budget Analysis Service

IMPORTANT: This service is COMPLETELY SEPARATE from optimization logic.
- It is INDEPENDENT of the optimization engine
- It provides budget analysis for finance managers BEFORE optimization runs
- It does NOT perform currency conversion - all currencies remain in original form
- It supports dynamic multi-currency (ANY currency from currency management)

Purpose: Help finance managers understand budget needs per currency, identify shortages,
and allocate budget in the correct currencies before running optimization.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import date, datetime, timedelta
from collections import defaultdict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models import (
    Project, ProjectItem, ProcurementOption, BudgetData,
    FinalizedDecision, Currency
)

logger = logging.getLogger(__name__)


class BudgetAnalysisResult:
    """Result of budget analysis"""
    def __init__(self):
        self.periods: List[Dict] = []  # Monthly budget analysis
        self.total_needed_by_currency: Dict[str, Decimal] = {}
        self.total_available_by_currency: Dict[str, Decimal] = {}
        self.gap_by_currency: Dict[str, Decimal] = {}
        self.recommendations: List[Dict] = []  # Changed to List[Dict] with translation keys
        self.critical_months: List[str] = []
        self.status: str = "OK"  # OK, WARNING, CRITICAL


class BudgetAnalysisService:
    """
    Service for analyzing budget needs and gaps
    
    IMPORTANT: This service is INDEPENDENT of optimization logic.
    It provides budget analysis for finance managers BEFORE optimization runs.
    
    CURRENCY HANDLING:
    - NO currency conversion is performed
    - All currencies are preserved in their original form (USD stays USD, EUR stays EUR, etc.)
    - Each currency is tracked separately for accurate multi-currency budget analysis
    - Budget needs and gaps are calculated per currency independently
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # NO currency service - we preserve original currencies without conversion
    
    async def analyze_budget_needs(
        self,
        project_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> BudgetAnalysisResult:
        """
        Analyze budget needs for Finance Managers
        
        Purpose: Help finance managers predict and allocate budget BEFORE optimization runs.
        This analysis shows:
        - Total budget NEEDED (sum of all outflows from finalized decisions + pending items)
        - Current budget AVAILABLE (from budget management system)
        - BUDGET SHORTAGE (difference) - how much additional budget needs to be allocated
        
        IMPORTANT MULTI-CURRENCY PRINCIPLES:
        - NO currency conversion is performed - all currencies remain in original form
        - Each currency is analyzed independently (USD vs USD, EUR vs EUR, IRR vs IRR)
        - Budget gaps are calculated per currency separately
        - You cannot mix currencies - USD budget can only cover USD outflows, etc.
        
        The analysis considers:
        1. Finalized procurements (actual/predicted cash flows) - preserves original currency
        2. Pending project items (forecasted cash flows using maximum price from finalized options) - preserves original currency
        3. Current budget allocation (multi-currency support) - uses multi_currency_budget from BudgetData
        
        Finance managers use this to:
        - Understand how much budget should be assigned for each currency (USD, EUR, IRR, etc.)
        - Identify budget shortages per currency that need to be filled
        - Make informed decisions before running optimization
        - Allocate budget in the correct currencies (USD for USD items, EUR for EUR items, etc.)
        
        Args:
            project_ids: Optional list of project IDs to analyze (None = all projects)
            start_date: Optional start date for analysis period
            end_date: Optional end date for analysis period
        
        Returns:
            BudgetAnalysisResult with:
            - total_needed_by_currency: Total budget needed per currency (NO conversion - original currencies preserved)
            - total_available_by_currency: Current budget available per currency (NO conversion - from multi_currency_budget)
            - gap_by_currency: Budget shortage (negative) or surplus (positive) per currency
            - recommendations: Actionable guidance for finance managers per currency
        """
        result = BudgetAnalysisResult()
        
        # Load data
        projects = await self._load_projects(project_ids)
        items = await self._load_project_items(project_ids)
        procurement_options = await self._load_procurement_options()
        budgets = await self._load_budgets(start_date, end_date)
        finalized_decisions = await self._load_finalized_decisions(project_ids, start_date, end_date)
        
        # Calculate total project budgets by currency
        self._total_project_budgets = await self._calculate_total_project_budgets(projects)
        
        # Initialize cash flow dictionary
        cash_flow_by_period = defaultdict(lambda: defaultdict(lambda: {'outflow': Decimal(0), 'inflow': Decimal(0)}))
        
        # Calculate cash flows from finalized decisions (actual/predicted)
        # These represent committed procurements that have been finalized
        if finalized_decisions:
            logger.info(
                f"Calculating cash flows from {len(finalized_decisions)} finalized procurement decisions"
            )
            finalized_cash_flows = await self._calculate_finalized_decision_cash_flows(finalized_decisions, projects)
            # Merge finalized cash flows into main cash flow dict
            for period, currencies in finalized_cash_flows.items():
                for currency, flows in currencies.items():
                    cash_flow_by_period[period][currency]['outflow'] += flows.get('outflow', Decimal(0))
                    cash_flow_by_period[period][currency]['inflow'] += flows.get('inflow', Decimal(0))
                    # Debug logging for USD
                    if currency == 'USD' and flows.get('outflow', Decimal(0)) > 0:
                        logger.info(
                            f"USD Outflow from finalized decisions: {flows.get('outflow', Decimal(0)):,.2f} USD "
                            f"in period {period}"
                        )
        
        # Calculate cash flows from non-finalized items (forecast)
        # These represent project needs that haven't been finalized yet
        if items and procurement_options:
            # Filter items to only those with procurement options (normalize item codes for matching)
            item_codes_with_options = {opt.item_code.strip() if opt.item_code else '' for opt in procurement_options if opt.item_code}
            non_finalized_items = [item for item in items if item.item_code and item.item_code.strip() in item_codes_with_options]
            
            if non_finalized_items:
                logger.info(
                    f"Calculating budget needs for {len(non_finalized_items)} pending project items "
                    f"using maximum price from finalized procurement options"
                )
                non_finalized_cash_flows = await self._calculate_budget_needs(non_finalized_items, procurement_options)
                # Merge non-finalized cash flows into main cash flow dict
                for period, currencies in non_finalized_cash_flows.items():
                    for currency, flows in currencies.items():
                        cash_flow_by_period[period][currency]['outflow'] += flows.get('outflow', Decimal(0))
                        cash_flow_by_period[period][currency]['inflow'] += flows.get('inflow', Decimal(0))
                        # Debug logging for USD
                        if currency == 'USD' and flows.get('outflow', Decimal(0)) > 0:
                            logger.info(
                                f"USD Outflow from pending items: {flows.get('outflow', Decimal(0)):,.2f} USD "
                                f"in period {period}"
                            )
        
        # If no cash flows at all, return warning
        if not cash_flow_by_period:
            result.status = "WARNING"
            result.recommendations.append("⚠️  No cash flow data found for analysis (no finalized decisions or pending items)")
            return result
        
        # Convert defaultdict to regular dict for analysis
        cash_flow_by_period = dict(cash_flow_by_period)
        
        # Calculate cumulative available budget by period and currency
        available_by_period = self._calculate_available_budget(budgets)
        
        # Analyze gaps using cumulative budget and net cash flow
        result = await self._analyze_gaps(
            cash_flow_by_period,
            available_by_period,
            start_date,
            end_date
        )
        
        return result
    
    async def _load_projects(self, project_ids: Optional[List[int]]) -> List[Project]:
        """Load projects"""
        query = select(Project).where(Project.is_active == True)
        if project_ids:
            query = query.where(Project.id.in_(project_ids))
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _load_project_items(self, project_ids: Optional[List[int]]) -> List[ProjectItem]:
        """Load project items that are NOT finalized (for forecast analysis)"""
        # Exclude items that are already decided (LOCKED or PROPOSED)
        decided_query = await self.db.execute(
            select(FinalizedDecision.project_id, FinalizedDecision.item_code)
            .where(FinalizedDecision.status.in_(['LOCKED', 'PROPOSED']))
        )
        decided_items = {(row.project_id, row.item_code) for row in decided_query.all()}
        
        query = select(ProjectItem)
        if project_ids:
            query = query.where(ProjectItem.project_id.in_(project_ids))
        
        result = await self.db.execute(query)
        all_items = list(result.scalars().all())
        
        # Filter out decided items (these will be handled separately from finalized decisions)
        filtered_items = [
            item for item in all_items
            if (item.project_id, item.item_code) not in decided_items
        ]
        
        # Log for debugging
        logger.info(
            f"Loaded {len(all_items)} total project items, "
            f"{len(decided_items)} have finalized decisions, "
            f"{len(filtered_items)} pending items for budget analysis"
        )
        
        # Debug specific item if needed
        for item in all_items:
            if 'CUSCO-ROUTER' in item.item_code.upper():
                is_decided = (item.project_id, item.item_code) in decided_items
                logger.info(
                    f"Item {item.item_code} (Project {item.project_id}): "
                    f"decided={is_decided}, included={not is_decided}"
                )
        
        return filtered_items
    
    async def _load_finalized_decisions(
        self,
        project_ids: Optional[List[int]],
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[FinalizedDecision]:
        """Load finalized decisions for cash flow analysis"""
        query = select(FinalizedDecision).where(
            FinalizedDecision.status.in_(['LOCKED', 'PROPOSED'])
        )
        
        if project_ids:
            query = query.where(FinalizedDecision.project_id.in_(project_ids))
        
        # Filter by date range if provided (include decisions whose dates fall within range)
        if start_date or end_date:
            from sqlalchemy import or_, and_
            date_conditions = []
            
            # Include decisions where purchase_date OR delivery_date falls within the range
            if start_date and end_date:
                date_conditions.append(
                    or_(
                        and_(FinalizedDecision.purchase_date >= start_date, FinalizedDecision.purchase_date <= end_date),
                        and_(FinalizedDecision.delivery_date >= start_date, FinalizedDecision.delivery_date <= end_date)
                    )
                )
            elif start_date:
                date_conditions.append(
                    or_(
                        FinalizedDecision.purchase_date >= start_date,
                        FinalizedDecision.delivery_date >= start_date
                    )
                )
            elif end_date:
                date_conditions.append(
                    or_(
                        FinalizedDecision.purchase_date <= end_date,
                        FinalizedDecision.delivery_date <= end_date
                    )
                )
            
            if date_conditions:
                query = query.where(or_(*date_conditions))
        
        result = await self.db.execute(query)
        decisions = list(result.scalars().all())
        
        # Debug logging for specific item
        for decision in decisions:
            if 'CUSCO-ROUTER' in decision.item_code.upper():
                logger.info(
                    f"Found finalized decision for {decision.item_code}: "
                    f"status={decision.status}, cost={decision.final_cost_amount} {decision.final_cost_currency}"
                )
        
        logger.info(f"Loaded {len(decisions)} finalized decisions for budget analysis")
        return decisions
    
    async def _load_procurement_options(self) -> List[ProcurementOption]:
        """Load finalized procurement options for budget estimation"""
        # Use finalized options first (procurement team has approved these)
        # If no finalized options exist for an item, fall back to active options
        result = await self.db.execute(
            select(ProcurementOption).where(
                (ProcurementOption.is_finalized == True) | (ProcurementOption.is_active == True)
            )
        )
        return list(result.scalars().all())
    
    async def _load_budgets(
        self,
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> List[BudgetData]:
        """Load budget data"""
        query = select(BudgetData)
        if start_date:
            query = query.where(BudgetData.budget_date >= start_date)
        if end_date:
            query = query.where(BudgetData.budget_date <= end_date)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _calculate_budget_needs(
        self,
        items: List[ProjectItem],
        procurement_options: List[ProcurementOption]
    ) -> Dict[str, Dict[str, Dict[str, Decimal]]]:
        """
        Calculate budget needs (outflows) and expected revenue (inflows) by period and currency
        
        IMPORTANT: NO currency conversion - preserves original currency from procurement options.
        - Outflows use procurement_option.cost_currency (USD stays USD, EUR stays EUR, etc.)
        - Inflows use project.budget_currency or procurement currency
        - Supports ANY currency code from currency management (dynamic)
        - Each currency tracked separately with no mixing or conversion
        
        Returns:
            Dict[period, Dict[currency, Dict['outflow'|'inflow', amount]]]
            Example: {"2025-11": {"USD": {"outflow": 2000, "inflow": 3000}, "IRR": {"outflow": 5000000}}}
        """
        from app.models import DeliveryOption
        from sqlalchemy.orm import selectinload
        
        cash_flow_by_period = defaultdict(lambda: defaultdict(lambda: {'outflow': Decimal(0), 'inflow': Decimal(0)}))
        
        # Load projects to get their currencies
        project_ids = list({item.project_id for item in items})
        projects_query = await self.db.execute(
            select(Project).where(Project.id.in_(project_ids))
        )
        projects_by_id = {p.id: p for p in projects_query.scalars().all()}
        
        # Group procurement options by item_code (normalize for matching)
        options_by_item = defaultdict(list)
        for opt in procurement_options:
            if opt.item_code:
                normalized_code = opt.item_code.strip()
                options_by_item[normalized_code].append(opt)
        
        for item in items:
            project = projects_by_id.get(item.project_id)
            # Normalize item_code for matching
            normalized_item_code = item.item_code.strip() if item.item_code else ''
            all_options = options_by_item.get(normalized_item_code, [])
            if not all_options:
                logger.warning(f"No procurement options found for item_code: {item.item_code}")
                continue
            
            # Prioritize finalized options (procurement team has approved these)
            finalized_options = [opt for opt in all_options if opt.is_finalized == True]
            options_to_use = finalized_options if finalized_options else all_options
            
            # Debug logging for specific item
            if 'CUSCO-ROUTER' in item.item_code.upper():
                logger.info(
                    f"Item {item.item_code}: {len(finalized_options)} finalized options, "
                    f"{len(all_options)} total options"
                )
                for opt in all_options:
                    total_cost = (opt.cost_amount or opt.base_cost or Decimal(0)) + (opt.shipping_cost or Decimal(0))
                    logger.info(
                        f"  Option {opt.id}: finalized={opt.is_finalized}, "
                        f"currency={opt.cost_currency}, cost={total_cost}"
                    )
            
            # Use MAXIMUM price from finalized options for conservative budget estimation
            # This ensures we budget for the worst-case scenario
            if finalized_options:
                selected_option = max(
                    finalized_options,
                    key=lambda opt: (opt.cost_amount or opt.base_cost or Decimal(0)) + 
                                   (opt.shipping_cost or Decimal(0))
                )
                logger.info(
                    f"Item {item.item_code} - Using MAXIMUM price from {len(finalized_options)} finalized options: "
                    f"{selected_option.cost_amount} {selected_option.cost_currency}"
                )
            else:
                # If no finalized options, use maximum from all active options
                selected_option = max(
                    options_to_use,
                    key=lambda opt: (opt.cost_amount or opt.base_cost or Decimal(0)) + 
                                   (opt.shipping_cost or Decimal(0))
                )
                logger.debug(
                    f"Item {item.item_code} - No finalized options, using MAXIMUM from {len(options_to_use)} active options"
                )
            
            # Calculate total procurement cost (OUTFLOW) using maximum price
            unit_cost = (selected_option.cost_amount or selected_option.base_cost or Decimal(0))
            shipping_cost = selected_option.shipping_cost or Decimal(0)
            total_cost_per_unit = unit_cost + shipping_cost
            total_procurement_cost = total_cost_per_unit * item.quantity
            
            # Get currency for procurement (handle None, empty string, or whitespace)
            procurement_currency = (selected_option.cost_currency or 'IRR').strip() if selected_option.cost_currency else 'IRR'
            if not procurement_currency:
                procurement_currency = 'IRR'
            
            # Load delivery options for this item to get delivery and invoice data
            delivery_options_result = await self.db.execute(
                select(DeliveryOption).where(DeliveryOption.project_item_id == item.id)
            )
            delivery_options = delivery_options_result.scalars().all()
            
            # Determine procurement period (use first delivery date)
            if delivery_options:
                delivery_date = delivery_options[0].delivery_date
                procurement_period = delivery_date.strftime("%Y-%m")
            else:
                # Use current month if no delivery date
                delivery_date = date.today()
                procurement_period = datetime.now().strftime("%Y-%m")
            
            # Add procurement cost as OUTFLOW (preserve original currency)
            cash_flow_by_period[procurement_period][procurement_currency]['outflow'] += total_procurement_cost
            logger.debug(
                f"Item {item.item_code} (Qty: {item.quantity}) - Added outflow: "
                f"{total_procurement_cost} {procurement_currency} for period {procurement_period}"
            )
            
            if delivery_options:
                # Use the first delivery option's invoice data
                delivery_option = delivery_options[0]
                
                # Calculate total invoice amount (INFLOW)
                invoice_per_unit = delivery_option.invoice_amount_per_unit or Decimal(0)
                total_invoice = invoice_per_unit * item.quantity
                
                # Invoice currency: use project's budget currency, or procurement currency as fallback, or IRR as default
                if project and project.budget_currency:
                    invoice_currency = (project.budget_currency or '').strip() if project.budget_currency else 'IRR'
                    if not invoice_currency:
                        invoice_currency = 'IRR'
                else:
                    invoice_currency = procurement_currency
                
                # Determine invoice period (invoice date is typically after delivery)
                if delivery_option.invoice_timing_type == 'ABSOLUTE' and delivery_option.invoice_issue_date:
                    invoice_date = delivery_option.invoice_issue_date
                else:
                    # RELATIVE: add days after delivery
                    days_after = delivery_option.invoice_days_after_delivery or 30
                    invoice_date = delivery_date + timedelta(days=days_after)
                
                invoice_period = invoice_date.strftime("%Y-%m")
                
                # Add invoice as INFLOW (preserve original currency)
                cash_flow_by_period[invoice_period][invoice_currency]['inflow'] += total_invoice
        
        return dict(cash_flow_by_period)
    
    async def _calculate_finalized_decision_cash_flows(
        self,
        decisions: List[FinalizedDecision],
        projects: List[Project]
    ) -> Dict[str, Dict[str, Dict[str, Decimal]]]:
        """
        Calculate cash flows from finalized decisions based on payment and invoice schedules
        
        IMPORTANT: NO currency conversion - preserves original currencies from decisions.
        - Outflows use final_cost_currency from FinalizedDecision
        - Payment installments preserve their currency per installment
        - Inflows use actual_invoice_amount_currency or forecast_invoice_amount_currency
        - Supports ANY currency code from currency management (dynamic)
        
        Returns:
            Dict[period, Dict[currency, Dict['outflow'|'inflow', amount]]]
            Example: {"2025-11": {"USD": {"outflow": 2000, "inflow": 0}, "IRR": {"outflow": 0, "inflow": 5000000}}}
        """
        from app.models import ProcurementOption
        
        cash_flow_by_period = defaultdict(lambda: defaultdict(lambda: {'outflow': Decimal(0), 'inflow': Decimal(0)}))
        
        # Create project lookup
        projects_by_id = {p.id: p for p in projects}
        
        # Load procurement options to get payment terms
        decision_procurement_ids = [d.procurement_option_id for d in decisions]
        if decision_procurement_ids:
            procurement_query = await self.db.execute(
                select(ProcurementOption).where(ProcurementOption.id.in_(decision_procurement_ids))
            )
            procurement_by_id = {opt.id: opt for opt in procurement_query.scalars().all()}
        else:
            procurement_by_id = {}
        
        for decision in decisions:
            project = projects_by_id.get(decision.project_id)
            procurement_opt = procurement_by_id.get(decision.procurement_option_id)
            
            # Get currency for costs
            cost_currency = (decision.final_cost_currency or 'IRR').strip() if decision.final_cost_currency else 'IRR'
            if not cost_currency:
                cost_currency = 'IRR'
            
            total_cost = Decimal(str(decision.final_cost_amount or decision.final_cost or 0))
            
            # Calculate OUTFLOWS (payments to suppliers)
            if decision.actual_payment_installments:
                # Use actual payment installments if available
                import json
                if isinstance(decision.actual_payment_installments, str):
                    installments = json.loads(decision.actual_payment_installments)
                else:
                    installments = decision.actual_payment_installments
                
                for installment in installments:
                    if isinstance(installment, dict):
                        payment_date = installment.get('date')
                        payment_amount = Decimal(str(installment.get('amount', 0)))
                        payment_currency = (installment.get('currency', cost_currency) or cost_currency).strip()
                        if not payment_currency:
                            payment_currency = cost_currency
                        
                        if payment_date:
                            try:
                                if isinstance(payment_date, str):
                                    from datetime import datetime
                                    payment_date_obj = datetime.fromisoformat(payment_date).date()
                                else:
                                    payment_date_obj = payment_date
                                
                                payment_period = payment_date_obj.strftime("%Y-%m")
                                cash_flow_by_period[payment_period][payment_currency]['outflow'] += payment_amount
                                
                                logger.debug(
                                    f"Finalized Decision {decision.id} - Payment installment: "
                                    f"{payment_amount} {payment_currency} on {payment_period}"
                                )
                            except Exception as e:
                                logger.warning(f"Error parsing payment date {payment_date}: {e}")
            
            elif decision.actual_payment_date:
                # Use single payment date if installments not available
                payment_date = decision.actual_payment_date
                payment_amount = total_cost  # Assume full payment if single date
                payment_currency = (decision.actual_payment_amount_currency or cost_currency).strip() if decision.actual_payment_amount_currency else cost_currency
                if not payment_currency:
                    payment_currency = cost_currency
                
                payment_period = payment_date.strftime("%Y-%m")
                cash_flow_by_period[payment_period][payment_currency]['outflow'] += payment_amount
                
                logger.debug(
                    f"Finalized Decision {decision.id} - Single payment: "
                    f"{payment_amount} {payment_currency} on {payment_period}"
                )
            
            elif procurement_opt and procurement_opt.payment_terms:
                # Parse payment terms from procurement option
                import json
                if isinstance(procurement_opt.payment_terms, str):
                    payment_terms = json.loads(procurement_opt.payment_terms)
                else:
                    payment_terms = procurement_opt.payment_terms
                
                # Calculate payment schedule from payment terms
                if isinstance(payment_terms, dict) and 'installments' in payment_terms:
                    installments = payment_terms['installments']
                    purchase_date = decision.purchase_date
                    
                    for installment in installments:
                        days_after = installment.get('days_after_purchase', 0)
                        percentage = Decimal(str(installment.get('percentage', 100)))
                        
                        payment_date = purchase_date + timedelta(days=int(days_after))
                        payment_amount = total_cost * (percentage / 100)
                        payment_period = payment_date.strftime("%Y-%m")
                        
                        cash_flow_by_period[payment_period][cost_currency]['outflow'] += payment_amount
                        
                        logger.debug(
                            f"Finalized Decision {decision.id} - Payment from terms: "
                            f"{payment_amount} {cost_currency} on {payment_period}"
                        )
                else:
                    # Default: single payment on purchase date
                    purchase_period = decision.purchase_date.strftime("%Y-%m")
                    cash_flow_by_period[purchase_period][cost_currency]['outflow'] += total_cost
            else:
                # Default: single payment on purchase date
                purchase_period = decision.purchase_date.strftime("%Y-%m")
                cash_flow_by_period[purchase_period][cost_currency]['outflow'] += total_cost
                logger.debug(
                    f"Finalized Decision {decision.id} - Default payment: "
                    f"{total_cost} {cost_currency} on {purchase_period}"
                )
            
            # Calculate INFLOWS (customer invoices/revenue)
            # Prefer actual invoice data, fallback to forecast
            invoice_date = None
            invoice_amount = Decimal(0)
            invoice_currency = cost_currency
            
            # Try actual invoice first
            if decision.actual_invoice_issue_date:
                invoice_date = decision.actual_invoice_issue_date
                invoice_amount = Decimal(str(decision.actual_invoice_amount_value or decision.actual_invoice_amount or 0))
                invoice_currency = (decision.actual_invoice_amount_currency or cost_currency).strip() if decision.actual_invoice_amount_currency else cost_currency
            elif decision.forecast_invoice_issue_date:
                invoice_date = decision.forecast_invoice_issue_date
                invoice_amount = Decimal(str(decision.forecast_invoice_amount_value or decision.forecast_invoice_amount or 0))
                invoice_currency = (decision.forecast_invoice_amount_currency or cost_currency).strip() if decision.forecast_invoice_amount_currency else cost_currency
            elif decision.forecast_invoice_timing_type == 'RELATIVE' and decision.forecast_invoice_days_after_delivery:
                # Calculate relative invoice date
                days_after = decision.forecast_invoice_days_after_delivery or 30
                invoice_date = decision.delivery_date + timedelta(days=days_after)
                invoice_amount = Decimal(str(decision.forecast_invoice_amount_value or decision.forecast_invoice_amount or 0))
                invoice_currency = (decision.forecast_invoice_amount_currency or cost_currency).strip() if decision.forecast_invoice_amount_currency else cost_currency
            
            if not invoice_currency:
                invoice_currency = cost_currency
            
            # If still no invoice date, use delivery date + 30 days default
            if not invoice_date:
                invoice_date = decision.delivery_date + timedelta(days=30)
            
            # If no invoice amount specified, try to get from delivery option
            if invoice_amount == 0 and decision.delivery_option_id:
                from app.models import DeliveryOption
                delivery_opt_query = await self.db.execute(
                    select(DeliveryOption).where(DeliveryOption.id == decision.delivery_option_id)
                )
                delivery_opt = delivery_opt_query.scalar_one_or_none()
                
                if delivery_opt and delivery_opt.invoice_amount_per_unit:
                    invoice_amount = Decimal(str(delivery_opt.invoice_amount_per_unit)) * Decimal(str(decision.quantity))
                    logger.debug(
                        f"Finalized Decision {decision.id} - Invoice amount from delivery option: "
                        f"{invoice_amount} {invoice_currency}"
                    )
            
            if invoice_amount == 0:
                logger.warning(f"Finalized Decision {decision.id} - No invoice amount specified")
            
            if invoice_amount > 0 and invoice_date:
                invoice_period = invoice_date.strftime("%Y-%m")
                cash_flow_by_period[invoice_period][invoice_currency]['inflow'] += invoice_amount
                
                logger.debug(
                    f"Finalized Decision {decision.id} - Invoice: "
                    f"{invoice_amount} {invoice_currency} on {invoice_period}"
                )
        
        return dict(cash_flow_by_period)
    
    def _calculate_available_budget(
        self,
        budgets: List[BudgetData]
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate available budget by period and currency
        
        IMPORTANT: NO currency conversion - uses multi_currency_budget as-is.
        - Uses BudgetData.multi_currency_budget JSON field (e.g., {"USD": 1000000, "IRR": 1000000000000, "EUR": 500000})
        - Each currency in multi_currency_budget is preserved separately
        - Supports ANY currency code from currency management (dynamic)
        - Falls back to available_budget only if multi_currency_budget is null (assumed IRR)
        - NO exchange rate conversion is performed
        
        Returns:
            Dict[period, Dict[currency, amount]]
            Example: {"2025-11": {"USD": 1000000, "IRR": 5000000000, "EUR": 500000}, "2025-12": {"GBP": 300000}}
        """
        available_by_period = {}
        
        # Use monthly budget data from Budget Management
        for budget in budgets:
            period = budget.budget_date.strftime("%Y-%m")
            
            # Initialize period dict if not exists
            if period not in available_by_period:
                available_by_period[period] = {}
            
            # Use multi_currency_budget if available - NO conversion, preserve all currencies
            if budget.multi_currency_budget:
                # multi_currency_budget is a JSON dict supporting ANY currency code
                # Example: {"USD": 1000000, "IRR": 1000000000000, "EUR": 500000, "GBP": 300000}
                import json
                if isinstance(budget.multi_currency_budget, str):
                    currency_dict = json.loads(budget.multi_currency_budget)
                else:
                    currency_dict = budget.multi_currency_budget
                
                # NO conversion - preserve each currency separately
                for currency, amount in currency_dict.items():
                    if currency not in available_by_period[period]:
                        available_by_period[period][currency] = Decimal(0)
                    available_by_period[period][currency] += Decimal(str(amount))
            else:
                # Fallback to legacy available_budget (assumed to be in IRR)
                # NO conversion - just use IRR as-is
                if 'IRR' not in available_by_period[period]:
                    available_by_period[period]['IRR'] = Decimal(0)
                available_by_period[period]['IRR'] += Decimal(str(budget.available_budget or 0))
        
        # If no budget data, return empty
        if not available_by_period:
            from datetime import datetime
            current_period = datetime.now().strftime("%Y-%m")
            available_by_period[current_period] = {'IRR': Decimal(0)}
        
        return available_by_period
    
    def _get_total_project_budgets(self) -> Dict[str, Decimal]:
        """Get total project budgets by currency"""
        # This will be populated by the calling method
        return getattr(self, '_total_project_budgets', {})
    
    async def _calculate_total_project_budgets(self, projects: List[Project]) -> Dict[str, Decimal]:
        """
        Calculate total project budgets by currency
        
        IMPORTANT: NO currency conversion - preserves original currencies.
        Each project's budget_currency is kept separate.
        """
        total_by_currency = defaultdict(Decimal)
        
        for project in projects:
            budget_amount = Decimal(str(project.budget_amount or 0))
            budget_currency = project.budget_currency or 'IRR'
            
            # NO conversion - preserve original currency
            # USD projects stay USD, EUR projects stay EUR, IRR projects stay IRR
            total_by_currency[budget_currency] += budget_amount
        
        return dict(total_by_currency)
    
    async def _analyze_gaps(
        self,
        cash_flow_by_period: Dict[str, Dict[str, Dict[str, Decimal]]],
        available_by_period: Dict[str, Dict[str, Decimal]],
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> BudgetAnalysisResult:
        """
        Analyze budget gaps for finance managers
        
        Purpose: Help finance managers predict how much budget should be assigned
        for optimization to work properly.
        
        Calculates:
        - Total NEEDED budget (sum of all outflows from finalized + pending items)
        - Total AVAILABLE budget (current budget allocation)
        - BUDGET SHORTAGE (needed - available) - negative values indicate shortage
        
        Budget accumulates over time, and we track cumulative position:
        Cumulative Position = Cumulative Budget + Cumulative Inflows - Cumulative Outflows
        """
        result = BudgetAnalysisResult()
        
        # Get all periods
        all_periods = sorted(set(list(cash_flow_by_period.keys()) + list(available_by_period.keys())))
        
        # Track cumulative cash flow by currency
        cumulative_outflow = defaultdict(Decimal)
        cumulative_inflow = defaultdict(Decimal)
        cumulative_net_flow = defaultdict(Decimal)
        cumulative_budget_by_currency = defaultdict(Decimal)  # Track cumulative budget per currency
        
        # Analyze each period
        for period in all_periods:
            period_cash_flow = cash_flow_by_period.get(period, {})
            period_available = available_by_period.get(period, {})
            
            # Get all currencies in this period (from both cash flows and available budget)
            all_currencies = set(list(period_cash_flow.keys()) + list(period_available.keys()))
            
            period_data = {
                'period': period,
                'currencies': {}
            }
            
            for currency in all_currencies:
                # Get cash flows for this period
                cash_flow = period_cash_flow.get(currency, {'outflow': Decimal(0), 'inflow': Decimal(0)})
                outflow = cash_flow.get('outflow', Decimal(0))
                inflow = cash_flow.get('inflow', Decimal(0))
                
                # Update cumulative flows
                cumulative_outflow[currency] += outflow
                cumulative_inflow[currency] += inflow
                cumulative_net_flow[currency] = cumulative_inflow[currency] - cumulative_outflow[currency]
                
                # Get available budget for this period and add to cumulative
                period_budget = period_available.get(currency, Decimal(0))
                cumulative_budget_by_currency[currency] += period_budget
                cumulative_budget = cumulative_budget_by_currency[currency]
                
                # Calculate cumulative position (budget + net cash flow)
                cumulative_position = cumulative_budget + cumulative_net_flow[currency]
                
                # Gap calculation for finance managers:
                # gap = available_budget - needed_budget (negative = shortage)
                # This shows directly how much budget is available vs needed, regardless of inflows
                gap = cumulative_budget - cumulative_outflow[currency]
                
                # Also calculate position (for informational purposes, considering inflows)
                cumulative_position = cumulative_budget + cumulative_net_flow[currency]
                gap_percentage = (gap / cumulative_outflow[currency] * 100) if cumulative_outflow[currency] > 0 else Decimal(0)
                
                period_data['currencies'][currency] = {
                    'outflow': float(outflow),
                    'inflow': float(inflow),
                    'cumulative_outflow': float(cumulative_outflow[currency]),
                    'cumulative_inflow': float(cumulative_inflow[currency]),
                    'cumulative_budget': float(cumulative_budget),
                    'cumulative_position': float(cumulative_position),
                    'gap': float(gap),
                    'gap_percentage': float(gap_percentage),
                    'status': 'OK' if gap >= 0 else 'DEFICIT'
                }
                
                # Check for gaps in this period
                if gap < 0:
                    if period not in result.critical_months:
                        result.critical_months.append(period)
            
            result.periods.append(period_data)
        
        # Track final totals by currency (after processing all periods)
        # This ensures we capture all currencies, even if they only appear in cash flows or only in budget
        all_currencies_final = set(list(cumulative_outflow.keys()) + list(cumulative_budget_by_currency.keys()))
        
        logger.info(
            f"Final currency tracking: "
            f"Currencies with outflows: {list(cumulative_outflow.keys())}, "
            f"Currencies with budget: {list(cumulative_budget_by_currency.keys())}, "
            f"All currencies: {sorted(all_currencies_final)}"
        )
        
        for currency in all_currencies_final:
            total_needed = cumulative_outflow.get(currency, Decimal(0))
            total_available = cumulative_budget_by_currency.get(currency, Decimal(0))
            # Gap = available - needed (negative means shortage)
            gap = total_available - total_needed
            
            result.total_needed_by_currency[currency] = total_needed
            result.total_available_by_currency[currency] = total_available
            result.gap_by_currency[currency] = gap
            
            # Critical: Ensure currencies with outflows are always tracked, even with 0 budget
            if total_needed > 0:
                logger.info(
                    f"Currency {currency}: Needed={total_needed:,.2f}, "
                    f"Available={total_available:,.2f}, Gap={gap:,.2f}"
                )
            
            # Log for debugging all currencies (dynamic - supports any currency)
            if total_needed > 0 or total_available > 0:
                logger.info(
                    f"{currency} Currency Summary: "
                    f"Needed={total_needed:,.2f}, Available={total_available:,.2f}, Gap={gap:,.2f}"
                )
                if gap < 0:
                    logger.warning(
                        f"⚠️  {currency} Budget Shortage: {abs(gap):,.2f} {currency} required"
                    )
                elif total_needed > 0 and total_available == 0:
                    logger.warning(
                        f"⚠️  {currency} Budget Missing: {total_needed:,.2f} {currency} needed but no budget allocated"
                    )
        
        # Generate recommendations
        result = self._generate_recommendations(result)
        
        return result
    
    def _generate_recommendations(self, result: BudgetAnalysisResult) -> BudgetAnalysisResult:
        """
        Generate actionable recommendations for finance managers
        
        Purpose: Help finance managers understand:
        1. How much budget is NEEDED for optimization to work
        2. Current budget AVAILABILITY
        3. BUDGET SHORTAGES that need to be filled
        4. Action items to allocate budget before running optimization
        """
        
        # Check overall status
        has_critical_gaps = any(gap < 0 for gap in result.gap_by_currency.values())
        has_warnings = any(
            Decimal(-0.1) <= gap < 0 for gap in result.gap_by_currency.values()
        )
        
        if has_critical_gaps:
            result.status = "CRITICAL"
        elif has_warnings:
            result.status = "WARNING"
        else:
            result.status = "OK"
        
        # Summary for finance managers - using structured format for translation
        result.recommendations.append({
            "type": "header",
            "key": "optimization.budgetAnalysisSummary",
        })
        result.recommendations.append({
            "type": "divider",
        })
        
        # Show totals by currency
        # Include ALL currencies that have either outflows OR available budget
        # This ensures currencies with outflows but no budget (like USD) are shown
        all_report_currencies = set(list(result.total_needed_by_currency.keys()) + list(result.total_available_by_currency.keys()))
        
        logger.info(
            f"Generating recommendations for currencies: {sorted(all_report_currencies)}"
        )
        
        for currency in sorted(all_report_currencies):
            needed = result.total_needed_by_currency.get(currency, Decimal(0))
            available = result.total_available_by_currency.get(currency, Decimal(0))
            gap = result.gap_by_currency.get(currency, Decimal(0))
            
            result.recommendations.append({
                "type": "currency_header",
                "key": "optimization.currencyHeader",
                "params": {"currency": currency}
            })
            result.recommendations.append({
                "type": "info",
                "key": "optimization.budgetNeeded",
                "params": {"amount": float(needed), "currency": currency}
            })
            result.recommendations.append({
                "type": "info",
                "key": "optimization.budgetAvailable",
                "params": {"amount": float(available), "currency": currency}
            })
            
            if gap < 0:
                shortage = abs(gap)
                result.recommendations.append({
                    "type": "warning",
                    "key": "optimization.budgetShortage",
                    "params": {"amount": float(shortage), "currency": currency}
                })
                result.recommendations.append({
                    "type": "action",
                    "key": "optimization.addBudgetAction",
                    "params": {"amount": float(shortage), "currency": currency}
                })
            elif gap > 0:
                result.recommendations.append({
                    "type": "success",
                    "key": "optimization.budgetSurplus",
                    "params": {"amount": float(gap), "currency": currency}
                })
            else:
                result.recommendations.append({
                    "type": "success",
                    "key": "optimization.budgetMatches",
                })
        
        # Overall status message
        if result.status == "OK":
            result.recommendations.append({
                "type": "success",
                "key": "optimization.budgetStatusSufficient",
            })
            result.recommendations.append({
                "type": "info",
                "key": "optimization.allProcurementsFunded",
            })
            result.recommendations.append({
                "type": "info",
                "key": "optimization.optimizationCanProceed",
            })
        else:
            result.recommendations.append({
                "type": "warning",
                "key": "optimization.budgetStatus",
                "params": {"status": result.status}
            })
            result.recommendations.append({
                "type": "warning",
                "key": "optimization.actionRequired",
            })
        
        # Period-specific critical shortages
        if result.critical_months:
            result.recommendations.append({
                "type": "warning",
                "key": "optimization.criticalPeriods",
                "params": {"months": ", ".join(result.critical_months)}
            })
            result.recommendations.append({
                "type": "info",
                "key": "optimization.immediateBudgetAllocation",
            })
        
        # Action items for finance managers
        result.recommendations.append({
            "type": "header",
            "key": "optimization.recommendedActions",
        })
        
        action_num = 1
        # Show action items for all currencies with shortages or needs but no budget
        for currency in sorted(all_report_currencies):
            gap = result.gap_by_currency.get(currency, Decimal(0))
            total_needed = result.total_needed_by_currency.get(currency, Decimal(0))
            total_available = result.total_available_by_currency.get(currency, Decimal(0))
            
            if gap < 0:
                shortage = abs(gap)
                result.recommendations.append({
                    "type": "action",
                    "key": "optimization.allocateBudget",
                    "params": {"number": action_num, "amount": float(shortage), "currency": currency}
                })
                action_num += 1
            elif total_needed > 0 and total_available == 0:
                # Special case: need exists but no budget allocated at all
                result.recommendations.append({
                    "type": "action",
                    "key": "optimization.allocateBudget",
                    "params": {"number": action_num, "amount": float(total_needed), "currency": currency}
                })
                action_num += 1
        
        if result.status != "OK":
            result.recommendations.append({
                "type": "action",
                "key": "optimization.reviewBudgetAllocation",
                "params": {"number": action_num}
            })
            action_num += 1
            result.recommendations.append({
                "type": "action",
                "key": "optimization.rerunAnalysis",
                "params": {"number": action_num}
            })
            action_num += 1
            result.recommendations.append({
                "type": "action",
                "key": "optimization.runOptimizationAfter",
                "params": {"number": action_num}
            })
        else:
            result.recommendations.append({
                "type": "action",
                "key": "optimization.budgetSufficientAction",
                "params": {"number": 1}
            })
            result.recommendations.append({
                "type": "action",
                "key": "optimization.monitorCashFlows",
                "params": {"number": 2}
            })
        
        return result



