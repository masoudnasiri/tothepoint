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
    item_code: Optional[str] = Field(None, min_length=1, max_length=100)  # Match model: String(100)
    item_name: Optional[str] = None  # No length limit - can be long
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


class ProcurementEligibilityIssue(BaseModel):
    code: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProcurementEligibilityDeliveryOptionInspection(BaseModel):
    delivery_option_id: Optional[int] = None
    source: str = "delivery_option"
    delivery_date: Optional[date] = None
    has_delivery_date: bool = False
    delivery_price_amount: Optional[Decimal] = None
    has_delivery_price: bool = False
    is_positive_delivery_price: bool = False
    delivery_price_currency: Optional[str] = None
    has_delivery_currency: bool = False
    is_valid: bool = False


class ProjectItemProcurementEligibility(BaseModel):
    project_item_id: int
    is_eligible: bool
    blockers: List[ProcurementEligibilityIssue] = Field(default_factory=list)
    warnings: List[ProcurementEligibilityIssue] = Field(default_factory=list)
    messages: List[str] = Field(default_factory=list)
    delivery_option_count: int = 0
    valid_delivery_option_count: int = 0
    has_delivery_schedule_dates: bool = False
    inspected_delivery_options: List[ProcurementEligibilityDeliveryOptionInspection] = Field(
        default_factory=list
    )


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


DeliveryDateSource = Literal["PROJECT_OPTION", "SUPPLIER_ACTUAL", "MANUAL"]
ForecastDateSource = Literal["SYSTEM_DEFAULT", "MANUAL_OVERRIDE"]


class ProcurementOptionBase(BaseModel):
    item_code: str = Field(..., min_length=1, max_length=100)  # Match model: String(100)
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
    payment_method_id: Optional[int] = Field(
        None,
        description="Selected payment method ID from master data",
    )
    planned_supplier_payment_date: Optional[date] = Field(
        None,
        description="Planned supplier payment date",
    )
    supplier_effective_receipt_date: Optional[date] = Field(
        None,
        description="Derived supplier effective receipt date (payment + settlement delay)",
    )
    is_finalized: Optional[bool] = Field(False, description="Mark option as finalized during creation")
    project_requested_delivery_date: Optional[date] = Field(
        None, description="Project requested/planned delivery date snapshot"
    )
    supplier_actual_delivery_date: Optional[date] = Field(
        None, description="Supplier-provided actual available delivery date"
    )
    selected_delivery_date: Optional[date] = Field(
        None, description="Delivery date selected for financial defaulting"
    )
    delivery_date_source: Optional[DeliveryDateSource] = Field(
        None, description="Source of selected delivery date"
    )
    delivery_date_variance_days: Optional[int] = Field(
        None, description="supplier_actual_delivery_date - project_requested_delivery_date"
    )
    forecast_customer_invoice_date: Optional[date] = Field(
        None, description="Defaulted/overridden customer invoice date"
    )
    forecast_customer_invoice_date_source: Optional[ForecastDateSource] = Field(
        None, description="Source of forecast_customer_invoice_date"
    )
    forecast_customer_receipt_date: Optional[date] = Field(
        None, description="Defaulted/overridden customer receipt date"
    )
    forecast_customer_receipt_date_source: Optional[ForecastDateSource] = Field(
        None, description="Source of forecast_customer_receipt_date"
    )
    forecast_customer_receipt_delay_days: Optional[int] = Field(
        None, description="Invoice-to-receipt delay in days when inferable"
    )
    date_calculation_trace: Optional[List[str]] = Field(
        None, description="Trace lines for delivery/invoice/receipt date defaults"
    )


class ProcurementOptionCreate(ProcurementOptionBase):
    # Phase 3: Support both package_id and project_item_id
    package_id: Optional[int] = Field(None, description="Package ID (preferred for new records)")
    project_item_id: Optional[int] = Field(None, description="ID of the project item this option belongs to")


class ProcurementOptionUpdate(BaseModel):
    # Phase 3 dual-mode references
    package_id: Optional[int] = Field(None, description="Package ID (preferred)")
    project_item_id: Optional[int] = Field(None, description="Legacy project item reference")
    item_code: Optional[str] = Field(None, min_length=1, max_length=100)  # Match model: String(100)
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
    payment_method_id: Optional[int] = None
    planned_supplier_payment_date: Optional[date] = None
    supplier_effective_receipt_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_finalized: Optional[bool] = None
    project_requested_delivery_date: Optional[date] = None
    supplier_actual_delivery_date: Optional[date] = None
    selected_delivery_date: Optional[date] = None
    delivery_date_source: Optional[DeliveryDateSource] = None
    delivery_date_variance_days: Optional[int] = None
    forecast_customer_invoice_date: Optional[date] = None
    forecast_customer_invoice_date_source: Optional[ForecastDateSource] = None
    forecast_customer_receipt_date: Optional[date] = None
    forecast_customer_receipt_date_source: Optional[ForecastDateSource] = None
    forecast_customer_receipt_delay_days: Optional[int] = None
    date_calculation_trace: Optional[List[str]] = None


class ProcurementOption(ProcurementOptionBase):
    id: int
    package_id: Optional[int] = None
    project_item_id: Optional[int] = None
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


class PaymentMethodBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name_en: str = Field(..., min_length=1, max_length=200)
    name_fa: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    settlement_delay_days: int = Field(0, ge=0)
    is_active: bool = True


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    name_en: Optional[str] = Field(None, min_length=1, max_length=200)
    name_fa: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    settlement_delay_days: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PaymentMethod(PaymentMethodBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProcurementCostComponentType(str, Enum):
    BASE_PRICE = "BASE_PRICE"
    SHIPPING = "SHIPPING"
    VAT = "VAT"
    CUSTOMS = "CUSTOMS"
    CLEARANCE = "CLEARANCE"
    INSURANCE = "INSURANCE"
    BANK_FEE = "BANK_FEE"
    OTHER = "OTHER"


class ProcurementCostComponentPayeeType(str, Enum):
    SUPPLIER = "SUPPLIER"
    LOGISTICS_PROVIDER = "LOGISTICS_PROVIDER"
    INSURANCE_PROVIDER = "INSURANCE_PROVIDER"
    CUSTOMS_OR_CLEARANCE = "CUSTOMS_OR_CLEARANCE"
    BANK_OR_EXCHANGE = "BANK_OR_EXCHANGE"
    OTHER = "OTHER"


class ProcurementCostComponentPaymentType(str, Enum):
    CASH = "CASH"
    INSTALLMENTS = "INSTALLMENTS"


class ProcurementCostComponentPaymentScheduleRow(BaseModel):
    due_offset_days: Optional[int] = Field(None, ge=0)
    due_date: Optional[date] = None
    percent: Optional[Decimal] = Field(None, gt=0, le=100)
    amount_value: Optional[Decimal] = Field(None, gt=0)
    derived_effective_receipt_date: Optional[date] = None

    @validator("due_date", always=True)
    def validate_due_reference(cls, v, values):
        if v is None and values.get("due_offset_days") is None:
            raise ValueError(
                "Each payment schedule row must include due_offset_days or due_date"
            )
        return v


class ProcurementCostComponentPaymentMetadata(BaseModel):
    inherit_option_payment_schedule: bool = True
    payee_type: ProcurementCostComponentPayeeType = ProcurementCostComponentPayeeType.SUPPLIER
    payee_label: Optional[str] = None
    payment_method_id: Optional[int] = Field(None, gt=0)
    payment_type: ProcurementCostComponentPaymentType = ProcurementCostComponentPaymentType.CASH
    planned_payment_date: Optional[date] = None
    payment_schedule: List[ProcurementCostComponentPaymentScheduleRow] = Field(
        default_factory=list
    )
    notes: Optional[str] = None

    @validator("payment_method_id", always=True)
    def validate_payment_method_requirement(cls, v, values):
        if values.get("inherit_option_payment_schedule", True):
            return v
        if v is None:
            raise ValueError(
                "payment_method_id is required when inherit_option_payment_schedule is false"
            )
        return v

    @validator("planned_payment_date", always=True)
    def validate_planned_payment_date_for_cash(cls, v, values):
        if values.get("inherit_option_payment_schedule", True):
            return v
        payment_type = values.get("payment_type")
        if payment_type == ProcurementCostComponentPaymentType.CASH and v is None:
            raise ValueError(
                "planned_payment_date is required for CASH component payment metadata when inheritance is disabled"
            )
        return v

    @validator("payment_schedule", always=True)
    def validate_installment_schedule(cls, v, values):
        if values.get("inherit_option_payment_schedule", True):
            return v or []

        payment_type = values.get("payment_type")
        schedule = v or []
        if payment_type != ProcurementCostComponentPaymentType.INSTALLMENTS:
            return schedule

        if len(schedule) == 0:
            raise ValueError(
                "payment_schedule is required for INSTALLMENTS component payment metadata"
            )

        has_amount_values = any(row.amount_value is not None for row in schedule)
        if has_amount_values:
            total_amount = sum(
                Decimal(str(row.amount_value or 0)) for row in schedule
            )
            if total_amount <= 0:
                raise ValueError(
                    "INSTALLMENTS payment_schedule amount_value total must be greater than zero"
                )
        else:
            total_percent = sum(Decimal(str(row.percent or 0)) for row in schedule)
            if abs(total_percent - Decimal("100")) > Decimal("0.01"):
                raise ValueError(
                    "INSTALLMENTS payment_schedule percent total must equal 100"
                )
        return schedule


class ProcurementCostComponentBase(BaseModel):
    component_type: ProcurementCostComponentType
    description: Optional[str] = None
    amount_value: Decimal = Field(..., gt=0)
    amount_currency: str = Field(..., min_length=3, max_length=3)
    amount_irr: Optional[Decimal] = Field(None, ge=0)
    exchange_rate_date: Optional[date] = None
    payment_metadata: Optional[ProcurementCostComponentPaymentMetadata] = None
    is_active: bool = True

    @validator("description", always=True)
    def validate_other_description(cls, v, values):
        component_type = values.get("component_type")
        if component_type == ProcurementCostComponentType.OTHER and not (v or "").strip():
            raise ValueError("description is required when component_type is OTHER")
        return v


class ProcurementCostComponentCreate(ProcurementCostComponentBase):
    pass


class ProcurementCostComponentUpdate(BaseModel):
    component_type: Optional[ProcurementCostComponentType] = None
    description: Optional[str] = None
    amount_value: Optional[Decimal] = Field(None, gt=0)
    amount_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    amount_irr: Optional[Decimal] = Field(None, ge=0)
    exchange_rate_date: Optional[date] = None
    payment_metadata: Optional[ProcurementCostComponentPaymentMetadata] = None
    is_active: Optional[bool] = None

    @validator("description", always=True)
    def validate_other_description_on_update(cls, v, values):
        component_type = values.get("component_type")
        if component_type == ProcurementCostComponentType.OTHER and not (v or "").strip():
            raise ValueError("description is required when component_type is OTHER")
        return v


class ProcurementCostComponent(ProcurementCostComponentBase):
    id: int
    procurement_option_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LandedCostComponentLine(BaseModel):
    component_id: Optional[int] = None
    component_type: str
    amount_value: Decimal
    amount_currency: str
    amount_irr: Optional[Decimal] = None
    source: str
    description: Optional[str] = None


class ProcurementOptionLandedCostPreview(BaseModel):
    option_id: int
    base_amount: Dict[str, Any]
    component_lines: List[LandedCostComponentLine]
    totals_by_currency: Dict[str, Decimal]
    total_irr: Optional[Decimal] = None
    missing_exchange_rates: List[Dict[str, Any]] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class ProcurementOptionDeliveryFinancialPreviewRequest(BaseModel):
    delivery_date_source: Optional[DeliveryDateSource] = None
    supplier_actual_delivery_date: Optional[date] = None
    selected_delivery_date: Optional[date] = None
    manual_invoice_date: Optional[date] = None
    manual_receipt_date: Optional[date] = None


class ProcurementOptionDeliveryFinancialPreview(BaseModel):
    project_requested_delivery_date: Optional[date] = None
    supplier_actual_delivery_date: Optional[date] = None
    selected_delivery_date: Optional[date] = None
    delivery_date_source: Optional[DeliveryDateSource] = None
    delivery_date_variance_days: Optional[int] = None
    forecast_customer_invoice_date: Optional[date] = None
    forecast_customer_invoice_date_source: Optional[ForecastDateSource] = None
    forecast_customer_receipt_date: Optional[date] = None
    forecast_customer_receipt_date_source: Optional[ForecastDateSource] = None
    forecast_customer_receipt_delay_days: Optional[int] = None
    missing_inputs: List[str] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class ProcurementOptionReadinessSummary(BaseModel):
    option_id: int
    is_ready_for_candidate_builder: bool
    missing_required_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    cost_summary: Dict[str, Any] = Field(default_factory=dict)
    delivery_summary: Dict[str, Any] = Field(default_factory=dict)
    payment_summary: Dict[str, Any] = Field(default_factory=dict)
    derived_customer_schedule_summary: Dict[str, Any] = Field(default_factory=dict)
    trace_lines: List[str] = Field(default_factory=list)


class AtomicCandidateCoveredSubitem(BaseModel):
    subitem_id: Optional[int] = None
    subitem_name: Optional[str] = None
    requested_quantity: Optional[Decimal] = None
    covered_quantity: Optional[Decimal] = None
    unit: Optional[str] = None


class AtomicOptimizationCandidate(BaseModel):
    candidate_id: str
    project_id: Optional[int] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    project_item_id: Optional[int] = None
    project_item_name: Optional[str] = None
    package_id: Optional[int] = None
    package_name: Optional[str] = None
    package_type: Optional[str] = None
    procurement_option_id: int
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None

    covered_main_quantity: Optional[Decimal] = None
    requested_main_quantity: Optional[Decimal] = None
    coverage_ratio: Optional[Decimal] = None
    covered_subitems: List[AtomicCandidateCoveredSubitem] = Field(default_factory=list)
    coverage_trace_lines: List[str] = Field(default_factory=list)

    landed_cost_amount: Optional[Decimal] = None
    landed_cost_currency: Optional[str] = None
    base_price_amount: Optional[Decimal] = None
    base_price_currency: Optional[str] = None
    shipping_cost_amount: Optional[Decimal] = None
    cost_components_summary: List[Dict[str, Any]] = Field(default_factory=list)
    cost_trace_lines: List[str] = Field(default_factory=list)

    payment_method_id: Optional[int] = None
    payment_method_code: Optional[str] = None
    payment_method_name: Optional[str] = None
    planned_supplier_payment_date: Optional[date] = None
    supplier_effective_receipt_date: Optional[date] = None
    payment_trace_lines: List[str] = Field(default_factory=list)

    project_requested_delivery_date: Optional[date] = None
    supplier_actual_delivery_date: Optional[date] = None
    selected_delivery_date: Optional[date] = None
    delivery_date_variance_days: Optional[int] = None
    delivery_trace_lines: List[str] = Field(default_factory=list)

    forecast_customer_invoice_date: Optional[date] = None
    forecast_customer_receipt_date: Optional[date] = None
    customer_schedule_trace_lines: List[str] = Field(default_factory=list)

    gross_margin_amount: Optional[Decimal] = None
    gross_margin_ratio: Optional[Decimal] = None
    cash_gap_days: Optional[int] = None
    working_capital_exposure_amount: Optional[Decimal] = None
    metrics_trace_lines: List[str] = Field(default_factory=list)

    is_ready_for_candidate_builder: bool
    readiness_missing_required_fields: List[str] = Field(default_factory=list)
    readiness_warnings: List[str] = Field(default_factory=list)
    readiness_trace_lines: List[str] = Field(default_factory=list)

    blocking_issues: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class AtomicOptimizationCandidateCollectionResponse(BaseModel):
    project_id: Optional[int] = None
    package_id: Optional[int] = None
    procurement_option_id: Optional[int] = None
    total_candidates: int = 0
    ready_candidates: int = 0
    not_ready_candidates: int = 0
    candidates: List[AtomicOptimizationCandidate] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class CoverageValidationIssue(BaseModel):
    code: str
    severity: Literal["BLOCKING", "WARNING", "INFO"]
    message: str
    project_id: Optional[int] = None
    project_item_id: Optional[int] = None
    package_id: Optional[int] = None
    procurement_option_id: Optional[int] = None
    candidate_id: Optional[str] = None
    coverage_key: Optional[str] = None
    field: Optional[str] = None
    trace_lines: List[str] = Field(default_factory=list)


class CoverageLine(BaseModel):
    coverage_key: str
    coverage_type: Literal["MAIN_ITEM", "SUBITEM", "PACKAGE", "UNKNOWN"]
    project_id: Optional[int] = None
    project_item_id: Optional[int] = None
    subitem_id: Optional[int] = None
    package_id: Optional[int] = None
    requested_quantity: Optional[Decimal] = None
    covered_quantity: Optional[Decimal] = None
    remaining_quantity: Optional[Decimal] = None
    over_covered_quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    candidate_ids: List[str] = Field(default_factory=list)
    supplier_ids: List[int] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class CandidateCoverageConstraintRow(BaseModel):
    coverage_key: str
    required_quantity: Optional[Decimal] = None
    candidate_contributions: List[Dict[str, Any]] = Field(default_factory=list)
    relation: Literal["EQUAL_OR_GREATER", "LESS_OR_EQUAL", "EXACT"] = "EQUAL_OR_GREATER"


class CandidateCoverageValidationResult(BaseModel):
    scope_type: Literal["PROJECT", "PACKAGE", "OPTION"]
    scope_id: int
    is_valid_for_solver_input: bool
    total_candidates: int = 0
    ready_candidates: int = 0
    not_ready_candidates: int = 0
    validated_candidates: List[str] = Field(default_factory=list)
    excluded_candidates: List[str] = Field(default_factory=list)
    coverage_lines: List[CoverageLine] = Field(default_factory=list)
    constraint_rows: List[CandidateCoverageConstraintRow] = Field(default_factory=list)
    blocking_issues: List[CoverageValidationIssue] = Field(default_factory=list)
    warnings: List[CoverageValidationIssue] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class FinancialProjectionIssue(BaseModel):
    code: str
    severity: Literal["BLOCKING", "WARNING", "INFO"]
    message: str
    candidate_id: Optional[str] = None
    project_id: Optional[int] = None
    project_item_id: Optional[int] = None
    package_id: Optional[int] = None
    procurement_option_id: Optional[int] = None
    event_type: Optional[str] = None
    field: Optional[str] = None
    trace_lines: List[str] = Field(default_factory=list)


class FinancialProjectionEvent(BaseModel):
    projection_event_id: str
    candidate_id: str
    project_id: Optional[int] = None
    project_item_id: Optional[int] = None
    package_id: Optional[int] = None
    procurement_option_id: Optional[int] = None
    supplier_id: Optional[int] = None
    event_type: Literal[
        "SUPPLIER_PAYMENT_OUTFLOW",
        "PURCHASE_COST_OUTFLOW",
        "SHIPPING_OUTFLOW",
        "VAT_OUTFLOW",
        "CUSTOMS_OUTFLOW",
        "CLEARANCE_OUTFLOW",
        "INSURANCE_OUTFLOW",
        "BANK_FEE_OUTFLOW",
        "OTHER_COST_OUTFLOW",
        "CUSTOMER_INVOICE_INFLOW",
        "CUSTOMER_RECEIPT_INFLOW",
        "UNKNOWN_OUTFLOW",
        "UNKNOWN_INFLOW",
    ]
    direction: Literal["INFLOW", "OUTFLOW"]
    forecast_or_actual: Literal["FORECAST"] = "FORECAST"
    event_date: Optional[date] = None
    period_key: Optional[str] = None
    calendar_system: Literal["GREGORIAN", "JALALI"] = "GREGORIAN"
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    source_type: Literal[
        "ATOMIC_CANDIDATE",
        "COST_COMPONENT",
        "COST_COMPONENT_PAYMENT",
        "CUSTOMER_SCHEDULE",
        "DERIVED",
    ]
    source_id: Optional[str] = None
    is_cash_effective: bool = False
    trace_lines: List[str] = Field(default_factory=list)


class FinancialProjectionPeriodSummary(BaseModel):
    period_key: str
    currency: str
    total_inflow: Decimal = Decimal("0")
    total_outflow: Decimal = Decimal("0")
    net_cash_impact: Decimal = Decimal("0")
    candidate_ids: List[str] = Field(default_factory=list)
    event_count: int = 0
    trace_lines: List[str] = Field(default_factory=list)


class FinancialProjectionCandidateSummary(BaseModel):
    candidate_id: str
    project_id: Optional[int] = None
    project_item_id: Optional[int] = None
    package_id: Optional[int] = None
    procurement_option_id: Optional[int] = None
    supplier_id: Optional[int] = None
    currency: Optional[str] = None
    total_forecast_inflow: Decimal = Decimal("0")
    total_forecast_outflow: Decimal = Decimal("0")
    net_forecast_cash_impact: Decimal = Decimal("0")
    cash_gap_days: Optional[int] = None
    working_capital_exposure_amount: Optional[Decimal] = None
    gross_margin_amount: Optional[Decimal] = None
    gross_margin_ratio: Optional[Decimal] = None
    first_outflow_date: Optional[date] = None
    first_inflow_date: Optional[date] = None
    last_cash_event_date: Optional[date] = None
    trace_lines: List[str] = Field(default_factory=list)


class FinancialProjectionResult(BaseModel):
    scope_type: Literal["PROJECT", "PACKAGE", "OPTION"]
    scope_id: int
    is_projection_complete: bool
    total_candidates: int = 0
    projected_candidates: int = 0
    excluded_candidates: List[str] = Field(default_factory=list)
    projection_events: List[FinancialProjectionEvent] = Field(default_factory=list)
    period_summaries: List[FinancialProjectionPeriodSummary] = Field(default_factory=list)
    candidate_summaries: List[FinancialProjectionCandidateSummary] = Field(default_factory=list)
    blocking_issues: List[FinancialProjectionIssue] = Field(default_factory=list)
    warnings: List[FinancialProjectionIssue] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class OptimizationScenarioIssue(BaseModel):
    code: str
    severity: Literal["BLOCKING", "WARNING", "INFO"]
    message: str
    scenario_key: Optional[str] = None
    candidate_id: Optional[str] = None
    project_id: Optional[int] = None
    project_item_id: Optional[int] = None
    package_id: Optional[int] = None
    procurement_option_id: Optional[int] = None
    field: Optional[str] = None
    trace_lines: List[str] = Field(default_factory=list)


class OptimizationScenarioCandidateSelection(BaseModel):
    candidate_id: str
    project_id: Optional[int] = None
    project_item_id: Optional[int] = None
    package_id: Optional[int] = None
    procurement_option_id: Optional[int] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    selected: bool = False
    selection_reason: Optional[str] = None
    exclusion_reason: Optional[str] = None
    coverage_keys: List[str] = Field(default_factory=list)
    landed_cost_amount: Optional[Decimal] = None
    landed_cost_currency: Optional[str] = None
    selected_delivery_date: Optional[date] = None
    delivery_date_variance_days: Optional[int] = None
    planned_supplier_payment_date: Optional[date] = None
    forecast_customer_receipt_date: Optional[date] = None
    company_cash_gap_days: Optional[int] = None
    working_capital_exposure_amount: Optional[Decimal] = None
    gross_margin_amount: Optional[Decimal] = None
    gross_margin_ratio: Optional[Decimal] = None
    projection_summary: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class OptimizationScenarioSummary(BaseModel):
    scenario_key: str
    scenario_name: str
    scenario_type: Literal[
        "CHEAPEST",
        "FASTEST_DELIVERY",
        "BEST_CASHFLOW",
        "HIGHEST_MARGIN",
        "BALANCED",
        "FEASIBILITY_ONLY",
    ]
    is_feasible: bool
    selected_candidate_count: int = 0
    excluded_candidate_count: int = 0
    total_selected_cost_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    total_projected_inflow_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    total_projected_outflow_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    net_projected_cash_impact_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    worst_company_cash_gap_days: Optional[int] = None
    total_working_capital_exposure_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    total_gross_margin_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    max_delivery_delay_days: Optional[int] = None
    coverage_status: str
    candidate_selections: List[OptimizationScenarioCandidateSelection] = Field(default_factory=list)
    blocking_issues: List[OptimizationScenarioIssue] = Field(default_factory=list)
    warnings: List[OptimizationScenarioIssue] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


class OptimizationScenarioPreviewResult(BaseModel):
    scope_type: Literal["PROJECT", "PACKAGE"]
    scope_id: int
    scenario_count: int = 0
    feasible_scenario_count: int = 0
    scenarios: List[OptimizationScenarioSummary] = Field(default_factory=list)
    blocking_issues: List[OptimizationScenarioIssue] = Field(default_factory=list)
    warnings: List[OptimizationScenarioIssue] = Field(default_factory=list)
    trace_lines: List[str] = Field(default_factory=list)


# Procurement Package Schemas (Phase 3)
class ProcurementPackageBase(BaseModel):
    project_item_id: int = Field(..., description="Project item this package belongs to")
    package_name: Optional[str] = Field(None, description="Human-readable package name")
    package_type: str = Field(..., pattern="^(FULL|PARTIAL|CUSTOM)$", description="Package type")
    supplier_id: Optional[int] = Field(None, description="Preferred supplier for this package")
    description: Optional[str] = Field(None, description="Package description")
    is_active: bool = Field(True, description="Is this package active?")
    main_item_quantity: Optional[int] = Field(None, ge=0, description="Quantity of main item covered")
    is_finalized: Optional[bool] = Field(
        False,
        description="Finalized status for optimization eligibility (computed from linked options)",
    )


class ProcurementPackageCreate(ProcurementPackageBase):
    pass


class ProcurementPackageUpdate(BaseModel):
    package_name: Optional[str] = None
    package_type: Optional[str] = Field(None, pattern="^(FULL|PARTIAL|CUSTOM)$")
    supplier_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    main_item_quantity: Optional[int] = Field(None, ge=0)
    is_finalized: Optional[bool] = None


class ProcurementPackageResponse(ProcurementPackageBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by_id: Optional[int] = None
    supplier: Optional[SupplierSummary] = None
    subitems: Optional[List["PackageSubItemResponse"]] = Field(None, description="Sub-items included in this package")
    status: Optional[str] = Field("DRAFT", description="DRAFT, FINALIZED, SENT_TO_OPTIMIZATION, INACTIVE")
    is_locked_for_optimization: bool = Field(False, description="True when item has been sent to optimization")
    
    model_config = {"from_attributes": True}


# Package SubItem Schemas (Phase 3)
class PackageSubItemBase(BaseModel):
    package_id: int = Field(..., description="Package this sub-item belongs to")
    project_item_subitem_id: int = Field(..., description="Project item sub-item being covered")
    quantity_covered: int = Field(..., ge=0, description="Quantity of this sub-item covered")
    is_fully_covered: bool = Field(False, description="Whether this package fully satisfies the sub-item requirement")
    coverage_percentage: Optional[Decimal] = Field(None, ge=0, le=100, description="Percentage of required quantity covered (0-100)")


class PackageSubItemCreate(PackageSubItemBase):
    pass


class PackageSubItemUpdate(BaseModel):
    quantity_covered: Optional[int] = Field(None, ge=0)
    is_fully_covered: Optional[bool] = None
    coverage_percentage: Optional[Decimal] = Field(None, ge=0, le=100)


class PackageSubItemResponse(PackageSubItemBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class OptimizationSubmissionRequest(BaseModel):
    project_item_id: Optional[int] = Field(None, description="Single project item target")
    send_all_finalized: bool = Field(False, description="Submit all finalized items in procurement scope")
    project_item_ids: Optional[List[int]] = Field(None, description="Multiple project item targets")
    include_incomplete_with_confirmation: bool = Field(
        False,
        description="Allow incomplete coverage submissions after explicit confirmation",
    )
    confirmed_incomplete_item_ids: List[int] = Field(
        default_factory=list,
        description="Subset of incomplete items explicitly approved by user",
    )
    max_combinations: int = Field(128, ge=1, le=512, description="Safety cap for generated combinations")

    @validator("project_item_ids", always=True)
    def validate_target_scope(cls, v, values):
        if values.get("send_all_finalized"):
            return v
        if values.get("project_item_id") is not None:
            return v
        if v and len(v) > 0:
            return v
        raise ValueError(
            "Provide project_item_id, project_item_ids, or set send_all_finalized=true"
        )


class OptimizationSubmissionRollbackRequest(BaseModel):
    notes: Optional[str] = None


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
    require_all_items: bool = Field(
        False,
        description=(
            "When false, optimization can return partial feasible results and report skipped/infeasible items. "
            "When true, all eligible items must be satisfied."
        ),
    )
    budget_mode: Literal["constrained", "allow_shortage"] = Field(
        "allow_shortage",
        description=(
            "Budget handling mode for optimization execution: "
            "'constrained' enforces available budget, "
            "'allow_shortage' optimizes all eligible items and reports shortage."
        ),
    )
    budget_scenario: Literal[
        "minimum_feasible",
        "average_candidate",
        "conservative",
        "worst_case",
        "selected_result",
        "selected_optimization_result",
    ] = Field(
        "minimum_feasible",
        description="Scenario used when pre-checking optimization budget exposure.",
    )


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
    package_id: Optional[int] = None  # Package-aware decision boundary support


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


class OptimizationFinancialPeriod(BaseModel):
    period: str
    required_irr: Decimal
    available_irr: Decimal
    gap_irr: Decimal
    status: str


class OptimizationFinancialAnalysis(BaseModel):
    scenario: str
    base_currency: str = "IRR"
    analysis_scope: str = "pre_optimization"
    optimization_result_id: Optional[str] = None
    budget_mode: str = "analysis_only"
    items_analyzed: int = 0
    items_with_no_valid_candidate: int = 0
    candidate_count: int = 0
    combination_count: int = 0
    double_count_prevented: bool = True
    selected_scenario_candidates: List[Dict[str, Any]] = Field(default_factory=list)
    budget_required_irr: Decimal
    budget_available_irr: Decimal
    surplus_or_shortage_irr: Decimal
    budget_status: str
    is_blocking: bool = False
    can_continue_with_warning: bool = True
    allowed_actions: List[str] = Field(default_factory=list)
    budget_required_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    budget_available_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    surplus_shortage_by_currency: Dict[str, Decimal] = Field(default_factory=dict)
    critical_periods: List[str] = Field(default_factory=list)
    periods: List[OptimizationFinancialPeriod] = Field(default_factory=list)
    charts: Dict[str, Any] = Field(default_factory=dict)
    trace_lines: List[Dict[str, Any]] = Field(default_factory=list)
    reconciliation: Dict[str, Any] = Field(default_factory=dict)
    total_purchase_cost_irr: Decimal = Decimal("0")
    weighted_objective_cost_irr: Optional[Decimal] = None
    top_shortage_contributors: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    narrative_report: Optional[str] = None


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
    excluded_items_count: Optional[int] = None
    excluded_items: Optional[List[Dict[str, Any]]] = None
    budget_summary: Optional[Dict[str, Any]] = None
    financial_analysis: Optional[OptimizationFinancialAnalysis] = None
    total_purchase_cost_irr: Optional[Decimal] = None


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
    error_code: Optional[str] = None
    diagnostics: Optional[Dict[str, Any]] = None
    budget_mode: Optional[str] = None
    budget_precheck: Optional[OptimizationFinancialAnalysis] = None


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
    project_item_id: int  # Required for aggregation/backward compatibility
    item_code: str
    procurement_option_id: int
    purchase_date: date
    delivery_date: date
    quantity: int
    final_cost: Decimal
    decision_maker_id: int
    
    # Phase 3: Package-aware reference
    package_id: Optional[int] = Field(None, description="Package ID (for package-level execution tracking)")
    
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
    
    # Phase 3: Package context in response
    package_name: Optional[str] = Field(None, description="Package name (if package_id is set)")
    package_type: Optional[str] = Field(None, description="Package type: FULL, PARTIAL, CUSTOM")
    supplier_id: Optional[int] = Field(None, description="Supplier ID resolved from procurement option")
    supplier_name: Optional[str] = Field(None, description="Supplier name resolved from procurement option")
    
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
    # Phase 3: Support both package_id and project_item_id
    package_id: Optional[int] = Field(None, description="Package ID (preferred for new records)")
    project_item_id: Optional[int] = Field(None, description="Project item ID (legacy, required if package_id not provided)")


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
    package_id: Optional[int] = Field(None, description="Package ID (if package-level delivery)")
    project_item_id: Optional[int] = Field(None, description="Project item ID (legacy)")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Phase 3: Package context in response
    package_name: Optional[str] = Field(None, description="Package name (if package_id is set)")
    
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
    package_id: Optional[int] = None
    package_name: Optional[str] = None
    package_type: Optional[str] = None
    supplier_id: Optional[int] = None
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
    package_id: Optional[int] = None
    package_name: Optional[str] = None
    package_type: Optional[str] = None
    supplier_id: Optional[int] = None
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
    supplier_id: Optional[int] = Field(None, description="Supplier ID (normalized supplier reference)")
    item_code: str = Field(..., min_length=1, max_length=100, description="Item code")
    project_id: int = Field(..., description="Project ID")
    package_id: Optional[int] = Field(None, description="Package ID (for package-based decisions)")
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
    package_id: Optional[int] = None
    supplier_id: Optional[int] = None
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
ProcurementPackageResponse.model_rebuild()  # Resolve forward reference to PackageSubItemResponse


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
    established_year: Optional[int] = Field(
        None,
        ge=1200,
        le=2100,
        description="Established year (Gregorian or Jalali)"
    )
    
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
    established_year: Optional[int] = Field(None, ge=1200, le=2100)
    
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
