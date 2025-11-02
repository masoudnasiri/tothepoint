"""
Budget Analysis Service
Analyzes budget needs, identifies gaps, and provides recommendations
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
from app.currency_service import CurrencyService

logger = logging.getLogger(__name__)


class BudgetAnalysisResult:
    """Result of budget analysis"""
    def __init__(self):
        self.periods: List[Dict] = []  # Monthly budget analysis
        self.total_needed_by_currency: Dict[str, Decimal] = {}
        self.total_available_by_currency: Dict[str, Decimal] = {}
        self.gap_by_currency: Dict[str, Decimal] = {}
        self.recommendations: List[str] = []
        self.critical_months: List[str] = []
        self.status: str = "OK"  # OK, WARNING, CRITICAL


class BudgetAnalysisService:
    """Service for analyzing budget needs and gaps"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.currency_service = CurrencyService(db)
    
    async def analyze_budget_needs(
        self,
        project_ids: Optional[List[int]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> BudgetAnalysisResult:
        """
        Analyze budget needs based on project items and procurement options
        
        Args:
            project_ids: Optional list of project IDs to analyze (None = all projects)
            start_date: Optional start date for analysis
            end_date: Optional end date for analysis
        
        Returns:
            BudgetAnalysisResult with detailed analysis
        """
        result = BudgetAnalysisResult()
        
        # Load data
        projects = await self._load_projects(project_ids)
        items = await self._load_project_items(project_ids)
        procurement_options = await self._load_procurement_options()
        budgets = await self._load_budgets(start_date, end_date)
        
        # Calculate total project budgets by currency
        self._total_project_budgets = await self._calculate_total_project_budgets(projects)
        
        if not items:
            result.status = "WARNING"
            result.recommendations.append("⚠️  No project items found for analysis")
            return result
        
        if not procurement_options:
            result.status = "WARNING"
            result.recommendations.append("⚠️  No procurement options found for analysis")
            return result
        
        # Filter items to only those with procurement options
        item_codes_with_options = {opt.item_code for opt in procurement_options}
        items = [item for item in items if item.item_code in item_codes_with_options]
        
        if not items:
            result.status = "WARNING"
            result.recommendations.append("⚠️  No items with procurement options found")
            return result
        
        # Calculate cash flow (outflows and inflows) by period and currency
        cash_flow_by_period = await self._calculate_budget_needs(items, procurement_options)
        
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
        """Load project items"""
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
        
        # Filter out decided items
        return [
            item for item in all_items
            if (item.project_id, item.item_code) not in decided_items
        ]
    
    async def _load_procurement_options(self) -> List[ProcurementOption]:
        """Load active procurement options"""
        result = await self.db.execute(
            select(ProcurementOption).where(ProcurementOption.is_active == True)
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
        
        Returns:
            Dict[period, Dict[currency, Dict['outflow'|'inflow', amount]]]
        """
        from app.models import DeliveryOption
        from sqlalchemy.orm import selectinload
        
        cash_flow_by_period = defaultdict(lambda: defaultdict(lambda: {'outflow': Decimal(0), 'inflow': Decimal(0)}))
        
        # Group procurement options by item_code
        options_by_item = defaultdict(list)
        for opt in procurement_options:
            options_by_item[opt.item_code].append(opt)
        
        for item in items:
            # Get the cheapest option for this item (for budget estimation)
            options = options_by_item.get(item.item_code, [])
            if not options:
                continue
            
            # Find cheapest option considering shipping cost
            cheapest_option = min(
                options,
                key=lambda opt: (opt.cost_amount or opt.base_cost or Decimal(0)) + 
                               (opt.shipping_cost or Decimal(0))
            )
            
            # Calculate total procurement cost (OUTFLOW)
            unit_cost = (cheapest_option.cost_amount or cheapest_option.base_cost or Decimal(0))
            shipping_cost = cheapest_option.shipping_cost or Decimal(0)
            total_cost_per_unit = unit_cost + shipping_cost
            total_procurement_cost = total_cost_per_unit * item.quantity
            
            # Get currency for procurement
            procurement_currency = cheapest_option.cost_currency or 'IRR'
            
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
            
            # Add procurement cost as OUTFLOW (convert to IRR for unified comparison)
            if procurement_currency == 'IRR':
                cash_flow_by_period[procurement_period]['IRR']['outflow'] += total_procurement_cost
            else:
                # For now, assume 1:1 conversion for other currencies to IRR
                # In production, this should use real exchange rates
                cash_flow_by_period[procurement_period]['IRR']['outflow'] += total_procurement_cost
            
            if delivery_options:
                # Use the first delivery option's invoice data
                delivery_option = delivery_options[0]
                
                # Calculate total invoice amount (INFLOW)
                invoice_per_unit = delivery_option.invoice_amount_per_unit or Decimal(0)
                total_invoice = invoice_per_unit * item.quantity
                
                # Invoice currency (default to IRR if not specified)
                invoice_currency = 'IRR'  # Delivery options currently don't have currency field
                
                # Determine invoice period (invoice date is typically after delivery)
                if delivery_option.invoice_timing_type == 'ABSOLUTE' and delivery_option.invoice_issue_date:
                    invoice_date = delivery_option.invoice_issue_date
                else:
                    # RELATIVE: add days after delivery
                    days_after = delivery_option.invoice_days_after_delivery or 30
                    invoice_date = delivery_date + timedelta(days=days_after)
                
                invoice_period = invoice_date.strftime("%Y-%m")
                
                # Add invoice as INFLOW (convert to IRR for unified comparison)
                if invoice_currency == 'IRR':
                    cash_flow_by_period[invoice_period]['IRR']['inflow'] += total_invoice
                else:
                    # For now, assume 1:1 conversion for other currencies to IRR
                    # In production, this should use real exchange rates
                    cash_flow_by_period[invoice_period]['IRR']['inflow'] += total_invoice
        
        return dict(cash_flow_by_period)
    
    def _calculate_available_budget(
        self,
        budgets: List[BudgetData]
    ) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate available budget by period and currency
        Use monthly budget data from Budget Management instead of project budgets
        
        Returns:
            Dict[period, Dict[currency, amount]]
        """
        available_by_period = {}
        
        # Use monthly budget data from Budget Management
        for budget in budgets:
            period = budget.budget_date.strftime("%Y-%m")
            
            # Use the available_budget from monthly budget data
            available_by_period[period] = {
                'IRR': Decimal(str(budget.available_budget or 0))
            }
        
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
        """Calculate total project budgets by currency, converting all to IRR for comparison"""
        total_by_currency = defaultdict(Decimal)
        
        for project in projects:
            budget_amount = Decimal(str(project.budget_amount or 0))
            budget_currency = project.budget_currency or 'IRR'
            
            # Convert all currencies to IRR for unified comparison
            if budget_currency == 'IRR':
                total_by_currency['IRR'] += budget_amount
            else:
                # For now, assume 1:1 conversion for other currencies to IRR
                # In production, this should use real exchange rates
                total_by_currency['IRR'] += budget_amount
        
        return dict(total_by_currency)
    
    async def _analyze_gaps(
        self,
        cash_flow_by_period: Dict[str, Dict[str, Dict[str, Decimal]]],
        available_by_period: Dict[str, Dict[str, Decimal]],
        start_date: Optional[date],
        end_date: Optional[date]
    ) -> BudgetAnalysisResult:
        """
        Analyze gaps using cumulative budget and net cash flow
        
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
        
        # Analyze each period
        for period in all_periods:
            period_cash_flow = cash_flow_by_period.get(period, {})
            period_available = available_by_period.get(period, {})
            
            # Get all currencies in this period
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
                
                # Get cumulative available budget
                cumulative_budget = period_available.get(currency, Decimal(0))
                
                # Calculate cumulative position (budget + net cash flow)
                cumulative_position = cumulative_budget + cumulative_net_flow[currency]
                
                # Gap is the cumulative position (positive = surplus, negative = deficit)
                gap = cumulative_position
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
                
                # Track totals (use final period values)
                result.total_needed_by_currency[currency] = cumulative_outflow[currency]
                result.total_available_by_currency[currency] = cumulative_budget
                result.gap_by_currency[currency] = gap
                
                # Check for gaps
                if gap < 0:
                    if period not in result.critical_months:
                        result.critical_months.append(period)
            
            result.periods.append(period_data)
        
        # Generate recommendations
        result = self._generate_recommendations(result)
        
        return result
    
    def _generate_recommendations(self, result: BudgetAnalysisResult) -> BudgetAnalysisResult:
        """Generate recommendations based on analysis"""
        
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
        
        # Generate specific recommendations
        if result.status == "OK":
            result.recommendations.append(
                "✅ Budget is sufficient for all planned procurements"
            )
        
        # Currency-specific recommendations
        for currency, gap in result.gap_by_currency.items():
            if gap < 0:
                deficit = abs(gap)
                result.recommendations.append(
                    f"🔴 {currency} Deficit: {deficit:,.2f} {currency} needed"
                )
                result.recommendations.append(
                    f"   💡 Consider: Increase {currency} budget or negotiate better prices"
                )
        
        # Period-specific recommendations
        if result.critical_months:
            result.recommendations.append(
                f"⚠️  Critical months: {', '.join(result.critical_months)}"
            )
            result.recommendations.append(
                "   💡 Consider: Spread procurement across more months or increase budget for these periods"
            )
        
        # Optimization suggestions
        if result.status != "OK":
            result.recommendations.append(
                "💡 Run optimization to find cost-effective procurement options"
            )
            result.recommendations.append(
                "💡 Consider negotiating volume discounts with suppliers"
            )
            result.recommendations.append(
                "💡 Review delivery schedules to better align with budget availability"
            )
        
        return result

