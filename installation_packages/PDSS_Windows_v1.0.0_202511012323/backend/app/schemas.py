from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime, date
from decimal import Decimal
import uuid
from enum import Enum


# Currency Schemas
class CurrencyBase(BaseModel):
    code: str = Field(..., min_length=3, max_length=3, description="Currency code (USD, EUR, IRR, etc.)")
    name: str = Field(..., min_length=1, max_length=100, description="Currency name")
    symbol: str = Field(..., min_length=1, max_length=10, description="Currency symbol")
    is_base_currency: bool = Field(default=False, description="Is this the base currency?")
    is_active: bool = Field(default=True, description="Is this currency active?")
    decimal_places: int = Field(default=2, ge=0, le=6, description="Number of decimal places for display")


class CurrencyCreate(CurrencyBase):
    pass


class CurrencyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)
    is_base_currency: Optional[bool] = None
    is_active: Optional[bool] = None
    decimal_places: Optional[int] = Field(None, ge=0, le=6)


class Currency(CurrencyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class ExchangeRateBase(BaseModel):
    date: date
    from_currency: str
    to_currency: str
    rate: Decimal
    is_active: bool = True


class ExchangeRateCreate(ExchangeRateBase):
    pass


class ExchangeRateUpdate(BaseModel):
    rate: Optional[Decimal] = Field(None, gt=0)
    is_active: Optional[bool] = None


class ExchangeRate(ExchangeRateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class ExchangeRateHistory(BaseModel):
    """Schema for historical exchange rate data"""
    date: date
    rate: Decimal


class CurrencyWithRates(BaseModel):
    """Currency with latest exchange rate - standalone to avoid circular inheritance"""
    id: int
    code: str
    name: str
    symbol: str
    is_base_currency: bool = False
    is_active: bool = True
    decimal_places: int = 2
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    latest_rate: Optional['ExchangeRate'] = None
    rate_to_base: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


# Enums
class ProjectItemStatusEnum(str, Enum):
    """Status enum for project items lifecycle"""
    PENDING = "PENDING"
    SUGGESTED = "SUGGESTED"
    DECIDED = "DECIDED"
    PROCURED = "PROCURED"
    FULFILLED = "FULFILLED"
    PAID = "PAID"
    CASH_RECEIVED = "CASH_RECEIVED"


# Items Master Schemas
class ItemMasterBase(BaseModel):
    company: str = Field(..., min_length=1, max_length=100)
    item_name: str = Field(..., min_length=1, max_length=200)
    model: Optional[str] = Field(None, max_length=100)
    part_number: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    category: Optional[str] = Field(None, max_length=100)
    unit: str = Field(default='piece', max_length=50)
    description: Optional[str] = None


class ItemMasterCreate(ItemMasterBase):
    pass  # item_code will be auto-generated


class ItemMasterUpdate(BaseModel):
    company: Optional[str] = Field(None, min_length=1, max_length=100)
    item_name: Optional[str] = Field(None, min_length=1, max_length=200)
    model: Optional[str] = Field(None, max_length=100)
    part_number: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    category: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ItemMaster(ItemMasterBase):
    id: int
    item_code: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    is_active: bool
    
    model_config = {"from_attributes": True}


# Sub-Item Schemas (under Items Master)
class ItemSubItemBase(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    part_number: Optional[str] = None


class ItemSubItemCreate(ItemSubItemBase):
    pass


class ItemSubItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    part_number: Optional[str] = None


class ItemSubItem(ItemSubItemBase):
    id: int
    item_master_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(..., pattern="^(admin|pmo|pm|procurement|finance)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, description="New password (leave empty to keep current)")
    role: Optional[str] = Field(None, pattern="^(admin|pmo|pm|procurement|finance)$")
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    created_at: datetime
    is_active: bool
    
    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Project Schemas
class ProjectBase(BaseModel):
    project_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1)
    priority_weight: int = Field(5, ge=1, le=10)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    project_code: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1)
    priority_weight: Optional[int] = Field(None, ge=1, le=10)
    is_active: Optional[bool] = None


class Project(ProjectBase):
    id: int
    created_at: datetime
    is_active: bool
    
    model_config = {"from_attributes": True}


class ProjectAssignmentCreate(BaseModel):
    user_id: int
    project_id: int


class ProjectAssignment(BaseModel):
    user_id: int
    project_id: int
    assigned_at: datetime
    
    model_config = {"from_attributes": True}


# Project Phase Schemas
class ProjectPhaseBase(BaseModel):
    phase_name: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: date
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('end_date must be after or equal to start_date')
        return v


class ProjectPhaseCreate(ProjectPhaseBase):
    project_id: int


class ProjectPhaseUpdate(BaseModel):
    phase_name: Optional[str] = Field(None, min_length=1, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectPhase(ProjectPhaseBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Project Item Schemas
class ProjectItemBase(BaseModel):
    master_item_id: Optional[int] = None  # Reference to Items Master
    item_code: str = Field(..., min_length=1, max_length=100)  # Denormalized from master
    item_name: Optional[str] = None  # Denormalized from master
    quantity: int = Field(..., gt=0)
    delivery_options: List[str] = Field(..., min_items=1)
    status: ProjectItemStatusEnum = ProjectItemStatusEnum.PENDING
    external_purchase: bool = False
    
    # Project-specific description (context for this project's usage)
    description: Optional[str] = None
    
    # File attachment (project-specific documents)
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    
    # Lifecycle date tracking
    decision_date: Optional[date] = None
    procurement_date: Optional[date] = None
    payment_date: Optional[date] = None
    invoice_submission_date: Optional[date] = None
    expected_cash_in_date: Optional[date] = None
    actual_cash_in_date: Optional[date] = None
    
    # Finalization tracking (PMO feature)
    is_finalized: bool = False
    finalized_by: Optional[int] = None
    finalized_at: Optional[datetime] = None
    # Sub-items quantities for this project item
    sub_items: Optional[List[Dict[str, int]]] = None  # [{"sub_item_id": int, "quantity": int}]
    
    @validator('delivery_options')
    def validate_delivery_options(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one delivery date must be provided')
        # Validate each date string format
        from datetime import datetime
        for date_str in v:
            try:
                datetime.fromisoformat(date_str)
            except (ValueError, TypeError):
                raise ValueError(f'Invalid date format: {date_str}. Use YYYY-MM-DD format')
        return v


class ProjectItemCreate(ProjectItemBase):
    project_id: int


class ProjectItemUpdate(BaseModel):
    item_code: Optional[str] = Field(None, min_length=1, max_length=50)
    item_name: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    delivery_options: Optional[List[str]] = Field(None, min_items=1)
    status: Optional[ProjectItemStatusEnum] = None
    external_purchase: Optional[bool] = None
    
    # NEW: Description and file attachment
    description: Optional[str] = None
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    
    # Lifecycle date tracking
    decision_date: Optional[date] = None
    procurement_date: Optional[date] = None
    payment_date: Optional[date] = None
    invoice_submission_date: Optional[date] = None
    expected_cash_in_date: Optional[date] = None
    actual_cash_in_date: Optional[date] = None
    
    # Finalization tracking (PMO feature)
    is_finalized: Optional[bool] = None
    finalized_by: Optional[int] = None
    finalized_at: Optional[datetime] = None
    sub_items: Optional[List[Dict[str, int]]] = None


class ProjectItem(ProjectItemBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class ProjectItemFinalize(BaseModel):
    """Schema for finalizing a project item (PMO only)"""
    is_finalized: bool = True
    finalized_at: Optional[datetime] = None  # Will be set by backend


# Procurement Option Schemas
class PaymentTermsCash(BaseModel):
    type: Literal["cash"] = "cash"
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="Discount percentage for cash payment")


class PaymentTermsInstallments(BaseModel):
    type: Literal["installments"] = "installments"
    schedule: List[Dict[str, Union[int, Decimal]]] = Field(..., min_items=1, description="Payment schedule")
    
    @validator('schedule')
    def validate_schedule(cls, v):
        total_percent = sum(installment.get('percent', 0) for installment in v)
        if abs(total_percent - 100) > 0.01:  # Allow small floating point differences
            raise ValueError('Schedule percentages must sum to 100')
        
        for i, installment in enumerate(v):
            if 'due_offset' not in installment or 'percent' not in installment:
                raise ValueError(f'Installment {i} must have due_offset and percent')
            if installment['due_offset'] < 0:
                raise ValueError(f'Installment {i} due_offset must be >= 0')
            if not (0 <= installment['percent'] <= 100):
                raise ValueError(f'Installment {i} percent must be between 0 and 100')
        
        return v


class ProcurementOptionBase(BaseModel):
    item_code: str = Field(..., min_length=1, max_length=50)
    supplier_name: str = Field(..., min_length=1)  # Legacy field - will be deprecated
    supplier_id: Optional[int] = Field(None, description="ID of supplier from centralized suppliers table")
    base_cost: Decimal = Field(..., gt=0)
    currency_id: int = Field(..., description="Currency ID for this procurement option")
    shipping_cost: Optional[Decimal] = Field(0, ge=0, description="Shipping cost in same currency as base_cost")
    delivery_option_id: Optional[int] = Field(None, description="Link to delivery option from project item")
    lomc_lead_time: int = Field(0, ge=0, description="Lead time in days (deprecated - use delivery_option)")
    purchase_date: Optional[date] = Field(None, description="When to place the order (purchase date)")
    expected_delivery_date: Optional[date] = Field(None, description="Expected delivery date (auto-filled from delivery_option)")
    discount_bundle_threshold: Optional[int] = Field(None, gt=0)
    discount_bundle_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    payment_terms: Union[PaymentTermsCash, PaymentTermsInstallments]
    is_finalized: Optional[bool] = Field(False, description="Mark option as finalized during creation")


class ProcurementOptionCreate(ProcurementOptionBase):
    project_item_id: Optional[int] = Field(None, description="ID of the project item this option belongs to")


class ProcurementOptionUpdate(BaseModel):
    item_code: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_name: Optional[str] = Field(None, min_length=1)  # Legacy field - will be deprecated
    supplier_id: Optional[int] = Field(None, description="ID of supplier from centralized suppliers table")
    base_cost: Optional[Decimal] = Field(None, gt=0)
    shipping_cost: Optional[Decimal] = Field(None, ge=0)
    delivery_option_id: Optional[int] = Field(None, description="Link to delivery option from project item")
    lomc_lead_time: Optional[int] = Field(None, ge=0, description="Lead time in days (deprecated)")
    purchase_date: Optional[date] = Field(None, description="When to place the order (purchase date)")
    expected_delivery_date: Optional[date] = Field(None, description="Expected delivery date (auto-filled from delivery_option)")
    discount_bundle_threshold: Optional[int] = Field(None, gt=0)
    discount_bundle_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    payment_terms: Optional[Union[PaymentTermsCash, PaymentTermsInstallments]] = None
    is_active: Optional[bool] = None
    is_finalized: Optional[bool] = None


class ProcurementOption(ProcurementOptionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    is_finalized: bool = False
    
    model_config = {"from_attributes": True}


class SupplierSummary(BaseModel):
    """Summary of supplier information for relationships"""
    id: int
    supplier_id: str
    company_name: str

    class Config:
        from_attributes = True


class ProcurementOptionWithSupplier(ProcurementOption):
    """Procurement option with supplier information included"""
    supplier: Optional[SupplierSummary] = None  # Include supplier details
    
    model_config = {"from_attributes": True}


# Budget Data Schemas
class BudgetDataBase(BaseModel):
    budget_date: date
    available_budget: Decimal = Field(..., ge=0)  # Base currency (IRR) for backward compatibility
    multi_currency_budget: Optional[Dict[str, Decimal]] = None  # e.g., {"USD": 1000000, "IRR": 1000000000000}


class BudgetDataCreate(BudgetDataBase):
    pass


class BudgetDataUpdate(BaseModel):
    budget_date: Optional[date] = None
    available_budget: Optional[Decimal] = Field(None, ge=0)
    multi_currency_budget: Optional[Dict[str, Decimal]] = None


class BudgetData(BudgetDataBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Optimization Result Schemas
class OptimizationResult(BaseModel):
    id: int
    run_id: uuid.UUID
    run_timestamp: datetime
    project_id: Optional[int]
    item_code: str
    procurement_option_id: int
    purchase_time: int
    delivery_time: int
    quantity: int
    final_cost: Decimal
    
    model_config = {"from_attributes": True}


class OptimizationRunRequest(BaseModel):
    max_time_slots: int = Field(12, ge=1, le=100)
    time_limit_seconds: int = Field(300, ge=10, le=3600)
    split_into_bunches: bool = Field(False, description="Split results into first bunch and rest")
    first_bunch_size: Optional[int] = Field(None, ge=1, description="Number of items in first bunch (by priority)")


# Individual decision in an optimization proposal
class OptimizationDecision(BaseModel):
    project_id: int
    project_code: str
    item_code: str
    item_name: str
    procurement_option_id: int
    supplier_name: str
    purchase_date: date
    delivery_date: date
    quantity: int
    unit_cost: Decimal
    final_cost: Decimal
    payment_terms: str
    priority_score: Optional[float] = None  # For bunch splitting
    project_item_id: Optional[int] = None  # Add project_item_id to identify specific project item


# A procurement bunch (subset of decisions)
class ProcurementBunch(BaseModel):
    bunch_id: str  # "BUNCH_1", "BUNCH_2"
    bunch_name: str  # "High Priority - Immediate", "Standard - Deferred"
    bunch_type: str  # "FIRST_BUNCH", "REST_BUNCH"
    total_cost: Decimal
    items_count: int
    decisions: List[OptimizationDecision]
    can_finalize_separately: bool = True
    priority_range: Optional[str] = None  # "1-5", "6-10", etc.


# A single optimization proposal (strategy) with bunches
class OptimizationProposal(BaseModel):
    proposal_name: str  # e.g., "Balanced Strategy", "Lowest Cost"
    strategy_type: str  # "BALANCED", "LOWEST_COST", etc.
    total_cost: Decimal
    weighted_cost: Decimal
    status: str  # "Optimal", "Feasible", "Infeasible"
    items_count: int
    decisions: List[OptimizationDecision]  # All decisions
    bunches: Optional[List[ProcurementBunch]] = None  # Split into bunches
    summary_notes: Optional[str] = None


# Response containing multiple proposals
class OptimizationRunResponse(BaseModel):
    run_id: uuid.UUID
    run_timestamp: datetime
    status: str  # Overall status
    execution_time_seconds: float
    total_cost: Decimal
    items_optimized: int
    proposals: List[OptimizationProposal]
    message: Optional[str] = None


# Optimization Run Schemas
class OptimizationRunBase(BaseModel):
    request_parameters: Dict[str, Any]
    status: str = Field(..., pattern="^(SUCCESS|FAILED|IN_PROGRESS)$")


class OptimizationRunCreate(OptimizationRunBase):
    pass


class OptimizationRun(OptimizationRunBase):
    run_id: uuid.UUID
    run_timestamp: datetime
    
    model_config = {"from_attributes": True}


# Finalized Decision Schemas
class FinalizedDecisionBase(BaseModel):
    run_id: Optional[uuid.UUID] = None
    project_id: int
    project_item_id: int
    item_code: str
    procurement_option_id: int
    purchase_date: date
    delivery_date: date
    quantity: int
    final_cost: Decimal
    decision_maker_id: int
    
    # Lifecycle
    status: str = Field(default='PROPOSED', pattern="^(PROPOSED|LOCKED|REVERTED)$")
    
    # NEW: Bunch tracking
    bunch_id: Optional[str] = None  # "BUNCH_1", "BUNCH_2", etc.
    bunch_name: Optional[str] = None  # "High Priority - Month 1", etc.
    
    # Forecasted Invoice Timing (from DeliveryOption)
    delivery_option_id: Optional[int] = None
    forecast_invoice_timing_type: str = Field(default='RELATIVE', pattern="^(ABSOLUTE|RELATIVE)$")
    forecast_invoice_issue_date: Optional[date] = None
    forecast_invoice_days_after_delivery: Optional[int] = Field(None, ge=0, le=365)
    forecast_invoice_amount: Optional[Decimal] = Field(None, ge=0)
    
    # Actual Invoice Data (entered by finance)
    actual_invoice_issue_date: Optional[date] = None
    actual_invoice_amount: Optional[Decimal] = Field(None, ge=0)
    actual_invoice_received_date: Optional[date] = None
    invoice_entered_by_id: Optional[int] = None
    invoice_entered_at: Optional[datetime] = None
    
    # Actual Payment Data (entered by finance for payments to suppliers)
    actual_payment_amount: Optional[Decimal] = Field(None, ge=0)
    actual_payment_date: Optional[date] = None
    actual_payment_installments: Optional[List[Dict[str, Any]]] = None
    payment_entered_by_id: Optional[int] = None
    payment_entered_at: Optional[datetime] = None
    
    # Delivery Tracking (Procurement Plan feature)
    delivery_status: str = Field(default='AWAITING_DELIVERY')
    actual_delivery_date: Optional[date] = None
    procurement_confirmed_at: Optional[datetime] = None
    procurement_confirmed_by_id: Optional[int] = None
    is_correct_item_confirmed: bool = False
    serial_number: Optional[str] = None
    procurement_delivery_notes: Optional[str] = None
    pm_accepted_at: Optional[datetime] = None
    pm_accepted_by_id: Optional[int] = None
    is_accepted_by_pm: bool = False
    pm_acceptance_notes: Optional[str] = None
    customer_delivery_date: Optional[date] = None
    
    is_manual_edit: bool = False
    notes: Optional[str] = None


class FinalizedDecisionCreate(FinalizedDecisionBase):
    decision_date: datetime = Field(default_factory=datetime.utcnow)


class FinalizedDecisionUpdate(BaseModel):
    procurement_option_id: Optional[int] = None
    purchase_date: Optional[date] = None
    delivery_date: Optional[date] = None
    quantity: Optional[int] = None
    final_cost: Optional[Decimal] = None
    status: Optional[str] = Field(None, pattern="^(PROPOSED|LOCKED|REVERTED)$")
    invoice_timing_type: Optional[str] = Field(None, pattern="^(ABSOLUTE|RELATIVE)$")
    invoice_issue_date: Optional[date] = None
    invoice_days_after_delivery: Optional[int] = Field(None, ge=0, le=365)
    is_manual_edit: Optional[bool] = None
    notes: Optional[str] = None


class FinalizedDecision(FinalizedDecisionBase):
    id: int
    decision_date: datetime
    finalized_at: Optional[datetime] = None
    finalized_by_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_final_invoice: bool = Field(default=False, description="Is this the final invoice for this item?")
    
    model_config = {"from_attributes": True}


# Request for finalizing decisions (locking them)
class FinalizeDecisionsRequest(BaseModel):
    decision_ids: List[int]
    finalize_all: bool = False  # If true, finalize all PROPOSED decisions
    bunch_id: Optional[str] = None  # NEW: Finalize specific bunch only


class FinalizeBunchRequest(BaseModel):
    """NEW: Finalize an entire bunch at once"""
    run_id: str
    bunch_id: str  # "BUNCH_1", "BUNCH_2"
    finalize: bool = True  # True to lock, False to just save as PROPOSED


class CancelBunchRequest(BaseModel):
    """NEW: Cancel/revert an entire bunch"""
    run_id: str
    bunch_id: str  # "BUNCH_1", "BUNCH_2"
    cancellation_reason: Optional[str] = None


class BatchSaveDecisionsRequest(BaseModel):
    run_id: str
    project_item_ids: List[int]
    procurement_option_ids: List[int]
    bunch_id: Optional[str] = None  # NEW: Tag with bunch ID


# Request for entering actual invoice data (finance team)
class ActualInvoiceDataRequest(BaseModel):
    actual_invoice_issue_date: date
    actual_invoice_amount: Decimal = Field(..., gt=0)
    actual_invoice_received_date: Optional[date] = None
    notes: Optional[str] = None


# Request for entering actual payment data
class ActualPaymentDataRequest(BaseModel):
    actual_payment_amount: Decimal = Field(..., gt=0)  # Total amount paid
    actual_payment_date: date  # First/single payment date
    actual_payment_installments: Optional[List[Dict[str, Any]]] = None  # [{"date": "2026-01-15", "amount": 10000}, ...]
    notes: Optional[str] = None


# Request for procurement team to confirm delivery
class ProcurementDeliveryConfirmationRequest(BaseModel):
    actual_delivery_date: date
    is_correct_item: bool = Field(..., description="Item matches order specification")
    serial_number: Optional[str] = Field(None, max_length=200)
    delivery_notes: Optional[str] = None


# Request for PM to accept delivery
class PMDeliveryAcceptanceRequest(BaseModel):
    is_accepted_for_project: bool = Field(..., description="Accept this item for the project")
    customer_delivery_date: Optional[date] = None
    acceptance_notes: Optional[str] = None


# Request for changing decision status
class DecisionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(PROPOSED|LOCKED|REVERTED)$")
    notes: Optional[str] = None


# Delivery Option Schemas
class DeliveryOptionBase(BaseModel):
    delivery_date: date
    delivery_slot: Optional[int] = None
    invoice_timing_type: str = Field(default='RELATIVE', pattern="^(ABSOLUTE|RELATIVE)$")
    invoice_issue_date: Optional[date] = None
    invoice_days_after_delivery: Optional[int] = Field(default=30, ge=0, le=365)
    invoice_amount_per_unit: Decimal = Field(..., gt=0)
    preference_rank: Optional[int] = Field(None, ge=1, le=100)
    notes: Optional[str] = None
    is_active: bool = True


class DeliveryOptionCreate(DeliveryOptionBase):
    project_item_id: int


class DeliveryOptionUpdate(BaseModel):
    delivery_date: Optional[date] = None
    invoice_timing_type: Optional[str] = Field(None, pattern="^(ABSOLUTE|RELATIVE)$")
    invoice_issue_date: Optional[date] = None
    invoice_days_after_delivery: Optional[int] = Field(None, ge=0, le=365)
    invoice_amount_per_unit: Optional[Decimal] = Field(None, gt=0)
    preference_rank: Optional[int] = Field(None, ge=1, le=100)
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class DeliveryOption(DeliveryOptionBase):
    id: int
    project_item_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Cashflow Event Schemas
class CashflowEventBase(BaseModel):
    related_decision_id: Optional[int] = None
    event_type: str = Field(..., pattern="^(INFLOW|OUTFLOW)$")
    forecast_type: str = Field(default='FORECAST', pattern="^(FORECAST|ACTUAL)$")
    event_date: date
    amount: Decimal = Field(..., ge=0)
    description: Optional[str] = None
    is_cancelled: bool = False


class CashflowEventCreate(CashflowEventBase):
    pass


class CashflowEventUpdate(BaseModel):
    event_date: Optional[date] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None
    is_cancelled: Optional[bool] = None
    cancellation_reason: Optional[str] = None


class CashflowEvent(CashflowEventBase):
    id: int
    cancelled_at: Optional[datetime] = None
    cancelled_by_id: Optional[int] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


# Decision Factor Weight Schemas
class DecisionFactorWeightBase(BaseModel):
    factor_name: str = Field(..., min_length=1, max_length=100)
    weight: int = Field(5, ge=1, le=10)
    description: Optional[str] = None


class DecisionFactorWeightCreate(DecisionFactorWeightBase):
    pass


class DecisionFactorWeightUpdate(BaseModel):
    factor_name: Optional[str] = Field(None, min_length=1, max_length=100)
    weight: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = None


class DecisionFactorWeight(DecisionFactorWeightBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Excel Import/Export Schemas
class ExcelImportResponse(BaseModel):
    success: bool
    imported_count: int
    errors: List[str] = []
    message: str


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_projects: int
    total_items: int
    total_procurement_options: int
    total_budget: Decimal
    last_optimization: Optional[datetime] = None
    pending_items: int = 0


class ProjectSummary(BaseModel):
    id: int
    project_code: str
    name: str
    item_count: int
    total_quantity: int
    estimated_cost: Optional[Decimal] = None
    estimated_revenue: Optional[Decimal] = None


# Invoice and Payment Schemas
class InvoiceBase(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=100)
    invoice_date: str = Field(..., description="Invoice date in ISO format")
    invoice_amount: Decimal = Field(..., ge=0, description="Invoice amount")
    currency: str = Field(default="IRR", max_length=3)
    due_date: str = Field(..., description="Due date in ISO format")
    payment_terms: Optional[str] = Field(None, max_length=100)
    is_final_invoice: bool = Field(default=False, description="Is this the final invoice for this item?")
    notes: Optional[str] = None

class InvoiceCreate(InvoiceBase):
    decision_id: int = Field(..., description="ID of the finalized decision")

class InvoiceUpdate(BaseModel):
    invoice_number: Optional[str] = Field(None, min_length=1, max_length=100)
    invoice_date: Optional[str] = Field(None, description="Invoice date in ISO format")
    invoice_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    due_date: Optional[str] = Field(None, description="Due date in ISO format")
    status: Optional[str] = Field(None, description="Invoice status")
    payment_terms: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: int
    decision_id: int
    item_code: str
    project_name: str
    supplier_name: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Payment Schemas
class PaymentBase(BaseModel):
    payment_date: str = Field(..., description="Payment date in ISO format")
    payment_amount: Decimal = Field(..., ge=0, description="Payment amount")
    currency: str = Field(default="IRR", max_length=3)
    payment_method: str = Field(..., description="Payment method")
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None

class PaymentCreate(PaymentBase):
    invoice_id: int = Field(..., description="ID of the invoice")

class PaymentUpdate(BaseModel):
    payment_date: Optional[str] = Field(None, description="Payment date in ISO format")
    payment_amount: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    payment_method: Optional[str] = Field(None, description="Payment method")
    reference_number: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, description="Payment status")
    notes: Optional[str] = None

class PaymentResponse(PaymentBase):
    id: int
    invoice_id: int
    decision_id: int
    item_code: str
    project_name: str
    supplier_name: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Summary Schema
class InvoicePaymentSummary(BaseModel):
    total_invoices: int
    total_payments: int
    paid_invoices: int
    pending_invoices: int
    overdue_invoices: int
    total_invoice_amount: float
    total_payment_amount: float
    pending_payment_amount: float

# Bulk Operations
class BulkStatusUpdate(BaseModel):
    ids: List[int] = Field(..., description="List of IDs to update")
    status: str = Field(..., description="New status")

class BulkDelete(BaseModel):
    ids: List[int] = Field(..., description="List of IDs to delete")

# Supplier Payment Schemas
class SupplierPaymentBase(BaseModel):
    decision_id: int = Field(..., description="ID of the finalized decision")
    supplier_name: str = Field(..., min_length=1, max_length=200, description="Supplier name")
    item_code: str = Field(..., min_length=1, max_length=100, description="Item code")
    project_id: int = Field(..., description="Project ID")
    payment_date: date = Field(..., description="Payment date")
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount")
    currency: str = Field(..., min_length=3, max_length=10, description="Currency code")
    payment_method: Literal["cash", "bank_transfer", "check", "credit_card"] = Field(..., description="Payment method")
    reference_number: Optional[str] = Field(None, max_length=100, description="Reference number")
    notes: Optional[str] = Field(None, description="Additional notes")
    status: Literal["pending", "completed", "failed", "cancelled"] = Field(default="completed", description="Payment status")


class SupplierPaymentCreate(SupplierPaymentBase):
    pass


class SupplierPaymentUpdate(BaseModel):
    supplier_name: Optional[str] = Field(None, min_length=1, max_length=200)
    payment_date: Optional[date] = None
    payment_amount: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = Field(None, min_length=3, max_length=10)
    payment_method: Optional[Literal["cash", "bank_transfer", "check", "credit_card"]] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    status: Optional[Literal["pending", "completed", "failed", "cancelled"]] = None


class SupplierPayment(SupplierPaymentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None

    class Config:
        from_attributes = True


class SupplierPaymentResponse(SupplierPayment):
    project_name: Optional[str] = None
    supplier_name: str
    item_code: str

# Resolve forward references for Pydantic v2
# This fixes circular dependencies between Currency and ExchangeRate schemas
Currency.model_rebuild()
ExchangeRate.model_rebuild()
CurrencyWithRates.model_rebuild()


# Supplier Management Schemas

class SupplierStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_APPROVAL = "PENDING_APPROVAL"


class ComplianceStatus(str, Enum):
    APPROVED = "APPROVED"
    PENDING = "PENDING"
    REJECTED = "REJECTED"
    UNDER_REVIEW = "UNDER_REVIEW"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Supplier Schemas
class SupplierBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name")
    legal_entity_type: Optional[str] = Field(None, max_length=50, description="Legal entity type (LLC, Ltd., JV, etc.)")
    registration_number: Optional[str] = Field(None, max_length=100, description="Registration number")
    tax_id: Optional[str] = Field(None, max_length=100, description="Tax ID")
    established_year: Optional[int] = Field(None, ge=1800, le=2030, description="Established year")
    
    # Location Information
    country: Optional[str] = Field(None, max_length=100, description="Country")
    city: Optional[str] = Field(None, max_length=100, description="City")
    address: Optional[str] = Field(None, description="Address")
    website: Optional[str] = Field(None, max_length=200, description="Website")
    domain: Optional[str] = Field(None, max_length=200, description="Domain")
    
    # Primary Contact Information
    primary_email: Optional[str] = Field(None, max_length=200, description="Primary email address")
    main_phone: Optional[str] = Field(None, max_length=50, description="Main phone number")
    
    # Social Media Links
    linkedin_url: Optional[str] = Field(None, max_length=200, description="LinkedIn URL")
    wechat_id: Optional[str] = Field(None, max_length=100, description="WeChat ID")
    telegram_id: Optional[str] = Field(None, max_length=100, description="Telegram ID")
    other_social_media: Optional[List[str]] = Field(None, description="Other social media links")
    
    # Business & Classification
    category: Optional[str] = Field(None, max_length=100, description="Category (Telecom, Oil & Gas, IT Equipment, etc.)")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")
    product_service_lines: Optional[List[str]] = Field(None, description="Product/service lines")
    main_brands_represented: Optional[List[str]] = Field(None, description="Main brands represented")
    main_markets_regions: Optional[List[str]] = Field(None, description="Main markets/regions")
    certifications: Optional[List[str]] = Field(None, description="Certifications (ISO, CE, UL, etc.)")
    ownership_type: Optional[str] = Field(None, max_length=50, description="Ownership type (Private, State-owned, Distributor, Agent, etc.)")
    annual_revenue_range: Optional[str] = Field(None, max_length=50, description="Annual revenue range")
    number_of_employees: Optional[str] = Field(None, max_length=50, description="Number of employees")
    
    # Operational Information
    warehouse_locations: Optional[List[str]] = Field(None, description="Warehouse/logistics locations")
    key_clients_references: Optional[List[str]] = Field(None, description="Key clients/references")
    payment_terms: Optional[str] = Field(None, max_length=100, description="Payment terms (T/T, LC, Net 30, etc.)")
    currency_preference: Optional[str] = Field("IRR", max_length=10, description="Currency preference")
    shipping_methods: Optional[List[str]] = Field(None, description="Shipping methods")
    incoterms: Optional[List[str]] = Field(None, description="Incoterms")
    average_lead_time_days: Optional[int] = Field(None, ge=0, le=365, description="Average lead time in days")
    
    # Quality and Service Information
    quality_assurance_process: Optional[str] = Field(None, description="Quality assurance process")
    warranty_policy: Optional[str] = Field(None, description="Warranty policy")
    after_sales_policy: Optional[str] = Field(None, description="After-sales policy")
    delivery_accuracy_percent: Optional[Decimal] = Field(None, ge=0, le=100, description="Delivery accuracy percentage")
    response_time_hours: Optional[int] = Field(None, ge=0, le=168, description="Response time in hours")
    
    # Document & Compliance Tracking
    business_license_path: Optional[str] = Field(None, max_length=500, description="Business license file path")
    tax_certificate_path: Optional[str] = Field(None, max_length=500, description="Tax certificate file path")
    iso_certificates_path: Optional[str] = Field(None, max_length=500, description="ISO certificates file path")
    financial_report_path: Optional[str] = Field(None, max_length=500, description="Financial report file path")
    supplier_evaluation_path: Optional[str] = Field(None, max_length=500, description="Supplier evaluation file path")
    compliance_status: ComplianceStatus = Field(ComplianceStatus.PENDING, description="Compliance status")
    last_review_date: Optional[date] = Field(None, description="Date of last review")
    last_audit_date: Optional[date] = Field(None, description="Date of last audit")
    
    # Internal Use & Meta
    status: SupplierStatus = Field(SupplierStatus.ACTIVE, description="Supplier status")
    risk_level: RiskLevel = Field(RiskLevel.MEDIUM, description="Risk level")
    internal_rating: Optional[Decimal] = Field(None, ge=1, le=5, description="Internal rating (1-5 stars)")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    notes: Optional[str] = Field(None, description="Notes or comments")


class SupplierCreate(SupplierBase):
    supplier_id: Optional[str] = Field(None, max_length=50, description="Supplier ID (auto-generated if empty)")


class SupplierUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=200)
    legal_entity_type: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=100)
    established_year: Optional[int] = Field(None, ge=1800, le=2030)
    
    # Location Information
    country: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    address: Optional[str] = None
    website: Optional[str] = Field(None, max_length=200)
    domain: Optional[str] = Field(None, max_length=200)
    
    # Primary Contact Information
    primary_email: Optional[str] = Field(None, max_length=200)
    main_phone: Optional[str] = Field(None, max_length=50)
    
    # Social Media Links
    linkedin_url: Optional[str] = Field(None, max_length=200)
    wechat_id: Optional[str] = Field(None, max_length=100)
    telegram_id: Optional[str] = Field(None, max_length=100)
    other_social_media: Optional[List[str]] = None
    
    # Business & Classification
    category: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    product_service_lines: Optional[List[str]] = None
    main_brands_represented: Optional[List[str]] = None
    main_markets_regions: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    ownership_type: Optional[str] = Field(None, max_length=50)
    annual_revenue_range: Optional[str] = Field(None, max_length=50)
    number_of_employees: Optional[str] = Field(None, max_length=50)
    
    # Operational Information
    warehouse_locations: Optional[List[str]] = None
    key_clients_references: Optional[List[str]] = None
    payment_terms: Optional[str] = Field(None, max_length=100)
    currency_preference: Optional[str] = Field(None, max_length=10)
    shipping_methods: Optional[List[str]] = None
    incoterms: Optional[List[str]] = None
    average_lead_time_days: Optional[int] = Field(None, ge=0, le=365)
    
    # Quality and Service Information
    quality_assurance_process: Optional[str] = None
    warranty_policy: Optional[str] = None
    after_sales_policy: Optional[str] = None
    delivery_accuracy_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    response_time_hours: Optional[int] = Field(None, ge=0, le=168)
    
    # Document & Compliance Tracking
    business_license_path: Optional[str] = Field(None, max_length=500)
    tax_certificate_path: Optional[str] = Field(None, max_length=500)
    iso_certificates_path: Optional[str] = Field(None, max_length=500)
    financial_report_path: Optional[str] = Field(None, max_length=500)
    supplier_evaluation_path: Optional[str] = Field(None, max_length=500)
    compliance_status: Optional[ComplianceStatus] = None
    last_review_date: Optional[date] = None
    last_audit_date: Optional[date] = None
    
    # Internal Use & Meta
    status: Optional[SupplierStatus] = None
    risk_level: Optional[RiskLevel] = None
    internal_rating: Optional[Decimal] = Field(None, ge=1, le=5)
    performance_metrics: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class Supplier(SupplierBase):
    id: int
    supplier_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    last_updated_by_id: Optional[int] = None

    class Config:
        from_attributes = True


# Supplier Contact Schemas
class SupplierContactBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200, description="Full name")
    job_title: Optional[str] = Field(None, max_length=100, description="Job title/role")
    role: Optional[str] = Field(None, max_length=100, description="Role (Sales Manager, Technical Support, etc.)")
    department: Optional[str] = Field(None, max_length=100, description="Department (Sales, Technical, Finance, etc.)")
    
    # Communication Details
    email: Optional[str] = Field(None, max_length=200, description="Email address")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    whatsapp_id: Optional[str] = Field(None, max_length=50, description="WhatsApp ID")
    telegram_id: Optional[str] = Field(None, max_length=50, description="Telegram ID")
    
    # Preferences
    language_preference: Optional[str] = Field("en", max_length=10, description="Language preference")
    timezone: Optional[str] = Field(None, max_length=50, description="Timezone")
    working_hours: Optional[str] = Field(None, max_length=100, description="Working hours")
    
    # Status
    is_primary_contact: bool = Field(False, description="Is primary contact")
    is_active: bool = Field(True, description="Is active")
    
    # Additional Information
    notes: Optional[str] = Field(None, description="Relationship information (e.g., 'Main negotiator for Cisco equipment')")


class SupplierContactCreate(SupplierContactBase):
    contact_id: Optional[str] = Field(None, max_length=50, description="Contact ID (auto-generated if empty)")


class SupplierContactUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    job_title: Optional[str] = Field(None, max_length=100)
    role: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    
    # Communication Details
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    whatsapp_id: Optional[str] = Field(None, max_length=50)
    telegram_id: Optional[str] = Field(None, max_length=50)
    
    # Preferences
    language_preference: Optional[str] = Field(None, max_length=10)
    timezone: Optional[str] = Field(None, max_length=50)
    working_hours: Optional[str] = Field(None, max_length=100)
    
    # Status
    is_primary_contact: Optional[bool] = None
    is_active: Optional[bool] = None
    
    # Additional Information
    notes: Optional[str] = None


class SupplierContact(SupplierContactBase):
    id: int
    contact_id: str
    supplier_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    supplier: Optional[SupplierSummary] = None

    class Config:
        from_attributes = True


# Supplier Document Schemas
class SupplierDocumentBase(BaseModel):
    document_name: str = Field(..., min_length=1, max_length=200, description="Document name")
    document_type: str = Field(..., min_length=1, max_length=100, description="Document type (Business License, Tax Certificate, ISO Certificate, etc.)")
    description: Optional[str] = Field(None, description="Description")
    document_number: Optional[str] = Field(None, max_length=100, description="Document number")
    issued_by: Optional[str] = Field(None, max_length=200, description="Issued by")
    issued_date: Optional[date] = Field(None, description="Issued date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    
    # Status
    is_active: bool = Field(True, description="Is active")
    is_verified: bool = Field(False, description="Is verified")
    
    # Additional Information
    notes: Optional[str] = Field(None, description="Notes")


class SupplierDocumentCreate(SupplierDocumentBase):
    document_id: Optional[str] = Field(None, max_length=50, description="Document ID (auto-generated if empty)")
    file_name: str = Field(..., min_length=1, max_length=200, description="File name")
    file_path: str = Field(..., min_length=1, max_length=500, description="File path")
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    mime_type: Optional[str] = Field(None, max_length=100, description="MIME type")


class SupplierDocumentUpdate(BaseModel):
    document_name: Optional[str] = Field(None, min_length=1, max_length=200)
    document_type: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    document_number: Optional[str] = Field(None, max_length=100)
    issued_by: Optional[str] = Field(None, max_length=200)
    issued_date: Optional[date] = None
    expiry_date: Optional[date] = None
    
    # Status
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    # Additional Information
    notes: Optional[str] = None


class SupplierDocument(SupplierDocumentBase):
    id: int
    document_id: str
    supplier_id: int
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None

    class Config:
        from_attributes = True


# Supplier with relationships
class SupplierWithContacts(Supplier):
    contacts: List[SupplierContact] = []


class SupplierWithDocuments(Supplier):
    documents: List[SupplierDocument] = []


class SupplierWithRelations(Supplier):
    contacts: List[SupplierContact] = []
    documents: List[SupplierDocument] = []


# Response schemas
class SupplierListResponse(BaseModel):
    suppliers: List[Supplier]
    total: int
    page: int
    size: int
    pages: int


class SupplierListWithRelationsResponse(BaseModel):
    suppliers: List[SupplierWithRelations]
    total: int
    page: int
    size: int
    pages: int


class SupplierContactListResponse(BaseModel):
    contacts: List[SupplierContact]
    total: int
    page: int
    size: int
    pages: int


class SupplierDocumentListResponse(BaseModel):
    documents: List[SupplierDocument]
    total: int
    page: int
    size: int
    pages: int
