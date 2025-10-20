from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Literal
from datetime import datetime, date
from decimal import Decimal
import uuid
from enum import Enum


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


# User Schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    role: str = Field(..., pattern="^(admin|pmo|pm|procurement|finance)$")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
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


class ProjectItem(ProjectItemBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


# Procurement Option Schemas
class PaymentTermsCash(BaseModel):
    type: Literal["cash"] = "cash"
    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)


class PaymentTermsInstallments(BaseModel):
    type: Literal["installments"] = "installments"
    schedule: List[Dict[str, Union[int, Decimal]]] = Field(..., min_items=1)
    
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
    supplier_name: str = Field(..., min_length=1)
    base_cost: Decimal = Field(..., gt=0)
    lomc_lead_time: int = Field(0, ge=0)
    discount_bundle_threshold: Optional[int] = Field(None, gt=0)
    discount_bundle_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    payment_terms: Union[PaymentTermsCash, PaymentTermsInstallments]


class ProcurementOptionCreate(ProcurementOptionBase):
    pass


class ProcurementOptionUpdate(BaseModel):
    item_code: Optional[str] = Field(None, min_length=1, max_length=50)
    supplier_name: Optional[str] = Field(None, min_length=1)
    base_cost: Optional[Decimal] = Field(None, gt=0)
    lomc_lead_time: Optional[int] = Field(None, ge=0)
    discount_bundle_threshold: Optional[int] = Field(None, gt=0)
    discount_bundle_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    payment_terms: Optional[Union[PaymentTermsCash, PaymentTermsInstallments]]
    is_active: Optional[bool] = None


class ProcurementOption(ProcurementOptionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    
    model_config = {"from_attributes": True}


# Budget Data Schemas
class BudgetDataBase(BaseModel):
    budget_date: date
    available_budget: Decimal = Field(..., ge=0)


class BudgetDataCreate(BudgetDataBase):
    pass


class BudgetDataUpdate(BaseModel):
    budget_date: Optional[date] = None
    available_budget: Optional[Decimal] = Field(None, ge=0)


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
