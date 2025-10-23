from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, DateTime, Date, ForeignKey, JSON, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.database import Base


class ProjectItemStatus(enum.Enum):
    """Status enum for project items lifecycle"""
    PENDING = "PENDING"
    SUGGESTED = "SUGGESTED"
    DECIDED = "DECIDED"
    PROCURED = "PROCURED"
    FULFILLED = "FULFILLED"
    PAID = "PAID"
    CASH_RECEIVED = "CASH_RECEIVED"


class ItemMaster(Base):
    """
    Master catalog of all items (products, materials, equipment)
    Items are defined once here, then referenced by project_items
    """
    __tablename__ = "items_master"
    
    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(100), unique=True, nullable=False, index=True)  # Auto-generated: COMPANY-NAME-MODEL
    company = Column(String(100), nullable=False, index=True)  # Manufacturer/Brand
    item_name = Column(String(200), nullable=False)  # Product name
    model = Column(String(100), nullable=True)  # Model number/variant
    specifications = Column(JSON, nullable=True)  # Standard specs (length, weight, material, etc.)
    category = Column(String(100), nullable=True, index=True)  # Construction, Electrical, etc.
    unit = Column(String(50), default='piece')  # piece, meter, kg, etc.
    description = Column(Text, nullable=True)  # General description of the item
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    project_items = relationship("ProjectItem", back_populates="master_item")


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'admin', 'pm', 'procurement', 'finance'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    project_assignments = relationship("ProjectAssignment", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    project_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(Text, nullable=False)
    priority_weight = Column(Integer, nullable=False, default=5)
    
    # Financial fields with proper currency support
    budget_amount = Column(Numeric(15, 2), nullable=True)  # Project budget amount
    budget_currency = Column(String(3), nullable=True, default='IRR')  # Currency of budget (e.g., 'IRR', 'USD')
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Add check constraints
    __table_args__ = (
        CheckConstraint('priority_weight >= 1 AND priority_weight <= 10', name='check_priority_weight_range'),
        CheckConstraint('budget_amount IS NULL OR budget_amount >= 0', name='check_positive_budget'),
    )
    
    # Relationships
    project_items = relationship("ProjectItem", back_populates="project", cascade="all, delete-orphan")
    project_assignments = relationship("ProjectAssignment", back_populates="project", cascade="all, delete-orphan")
    optimization_results = relationship("OptimizationResult", back_populates="project")
    phases = relationship("ProjectPhase", back_populates="project", cascade="all, delete-orphan")


class ProjectAssignment(Base):
    __tablename__ = "project_assignments"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="project_assignments")
    project = relationship("Project", back_populates="project_assignments")


class ProjectPhase(Base):
    __tablename__ = "project_phases"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    phase_name = Column(String(100), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="phases")


class ProjectItem(Base):
    __tablename__ = "project_items"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # NEW: Reference to Items Master
    master_item_id = Column(Integer, ForeignKey("items_master.id", ondelete="RESTRICT"), nullable=True, index=True)
    
    # Denormalized from master (for backward compatibility and performance)
    item_code = Column(String(100), nullable=False, index=True)
    item_name = Column(Text)
    
    # Project-specific fields
    quantity = Column(Integer, nullable=False)
    delivery_options = Column(JSON, nullable=False, default=list)  # Array of possible delivery dates
    status = Column(SQLEnum(ProjectItemStatus), nullable=False, default=ProjectItemStatus.PENDING)
    external_purchase = Column(Boolean, default=False)
    
    # Project-specific description (context for THIS project's usage)
    description = Column(Text, nullable=True)
    
    # File attachment (project-specific documents)
    file_path = Column(String(500), nullable=True)
    file_name = Column(String(255), nullable=True)
    
    # Lifecycle date tracking
    decision_date = Column(Date, nullable=True)
    procurement_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    invoice_submission_date = Column(Date, nullable=True)
    expected_cash_in_date = Column(Date, nullable=True)
    actual_cash_in_date = Column(Date, nullable=True)
    
    # Finalization tracking (PMO feature)
    is_finalized = Column(Boolean, default=False, nullable=False)
    finalized_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    finalized_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="project_items")
    master_item = relationship("ItemMaster", back_populates="project_items")
    delivery_options_rel = relationship("DeliveryOption", back_populates="project_item", cascade="all, delete-orphan")
    finalized_decisions = relationship("FinalizedDecision", back_populates="project_item", cascade="all, delete-orphan")


class DeliveryOption(Base):
    """
    Represents a specific delivery option for a project item with associated invoice timing.
    Each option defines when the item can be delivered and how/when the invoice will be issued.
    """
    __tablename__ = "delivery_options"
    
    id = Column(Integer, primary_key=True, index=True)
    project_item_id = Column(Integer, ForeignKey("project_items.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Delivery Timing
    delivery_slot = Column(Integer, nullable=True)  # For optimization engine compatibility (1, 2, 3...)
    delivery_date = Column(Date, nullable=False, index=True)
    
    # Invoice Timing Configuration
    invoice_timing_type = Column(String(20), nullable=False, default='RELATIVE')
    # Values: 'ABSOLUTE' (specific date), 'RELATIVE' (days after delivery)
    invoice_issue_date = Column(Date, nullable=True)  # Used when invoice_timing_type = 'ABSOLUTE'
    invoice_days_after_delivery = Column(Integer, nullable=True, default=30)  # Used when invoice_timing_type = 'RELATIVE'
    
    # Revenue Configuration
    invoice_amount_per_unit = Column(Numeric(12, 2), nullable=False)
    # Defines the revenue per unit for this specific delivery option
    # Allows different pricing for different delivery dates
    
    # Priority/Preference
    preference_rank = Column(Integer, nullable=True)  # 1 = most preferred, null = no preference
    
    # Metadata
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project_item = relationship("ProjectItem", back_populates="delivery_options_rel")


class ProcurementOption(Base):
    __tablename__ = "procurement_options"
    
    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(50), nullable=False, index=True)
    supplier_name = Column(Text, nullable=False)
    
    # Updated financial fields with proper currency support
    cost_amount = Column(Numeric(15, 2), nullable=False)  # Cost amount in original currency
    cost_currency = Column(String(3), nullable=False, default='IRR')  # Currency of cost (e.g., 'USD', 'IRR')
    shipping_cost = Column(Numeric(15, 2), nullable=True, default=0)  # Shipping cost in same currency as cost_amount
    
    # Legacy field for backward compatibility (will be deprecated)
    base_cost = Column(Numeric(12, 2), nullable=True)  # Keep for migration
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=True)  # Keep for migration
    
    lomc_lead_time = Column(Integer, default=0)  # Lead time in days (deprecated - use expected_delivery_date)
    expected_delivery_date = Column(Date, nullable=True)  # Expected delivery date from supplier
    delivery_option_id = Column(Integer, ForeignKey("delivery_options.id"), nullable=True)  # Link to project item's delivery option
    discount_bundle_threshold = Column(Integer)
    discount_bundle_percent = Column(Numeric(5, 2))
    payment_terms = Column(JSON, nullable=False)  # Structured JSON for payment terms
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    is_finalized = Column(Boolean, default=False)  # Whether procurement team has finalized this option for optimization
    
    # Relationships
    currency = relationship("Currency")  # Keep for backward compatibility
    optimization_results = relationship("OptimizationResult", back_populates="procurement_option")
    
    # Add check constraints
    __table_args__ = (
        CheckConstraint('cost_amount > 0', name='check_positive_cost'),
    )


class BudgetData(Base):
    __tablename__ = "budget_data"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_date = Column(Date, unique=True, nullable=False, index=True)
    available_budget = Column(Numeric(15, 2), nullable=False)  # Kept for backward compatibility (in base currency IRR)
    multi_currency_budget = Column(JSON, nullable=True)  # New: {"USD": 1000000, "IRR": 1000000000000, "AED": 12000000000}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CashflowEvent(Base):
    __tablename__ = "cashflow_events"
    
    id = Column(Integer, primary_key=True, index=True)
    related_decision_id = Column(Integer, ForeignKey("finalized_decisions.id", ondelete="CASCADE"), nullable=True)
    event_type = Column(String(10), nullable=False)  # 'INFLOW' or 'OUTFLOW'
    forecast_type = Column(String(10), nullable=False, default='FORECAST', index=True)
    # Values: 'FORECAST' (predicted), 'ACTUAL' (real data from finance)
    event_date = Column(Date, nullable=False, index=True)
    
    # Updated financial fields with proper currency support
    amount_value = Column(Numeric(15, 2), nullable=False)  # Amount in original currency
    amount_currency = Column(String(3), nullable=False, default='IRR')  # Currency of amount
    
    # Legacy field for backward compatibility (will be deprecated)
    amount = Column(Numeric(15, 2), nullable=True)  # Keep for migration
    
    description = Column(Text, nullable=True)
    
    # Auditability Enhancement
    is_cancelled = Column(Boolean, default=False, nullable=False, index=True)
    # When a decision is REVERTED, events are marked as cancelled instead of deleted
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    related_decision = relationship("FinalizedDecision", foreign_keys=[related_decision_id], back_populates="cashflow_events")
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])


class OptimizationRun(Base):
    __tablename__ = "optimization_runs"
    
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    request_parameters = Column(JSON, nullable=False)
    status = Column(String(20), nullable=False)  # 'SUCCESS', 'FAILED', 'IN_PROGRESS'
    
    # Relationships
    finalized_decisions = relationship("FinalizedDecision", back_populates="optimization_run")


class FinalizedDecision(Base):
    __tablename__ = "finalized_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(UUID(as_uuid=True), ForeignKey("optimization_runs.run_id"), nullable=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    project_item_id = Column(Integer, ForeignKey("project_items.id", ondelete="CASCADE"), nullable=False)
    item_code = Column(String(50), nullable=False, index=True)
    procurement_option_id = Column(Integer, ForeignKey("procurement_options.id"), nullable=False)
    purchase_date = Column(Date, nullable=False)
    delivery_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False)
    
    # Updated financial fields with proper currency support
    final_cost_amount = Column(Numeric(15, 2), nullable=False)  # Final cost amount in original currency
    final_cost_currency = Column(String(3), nullable=False, default='IRR')  # Currency of final cost
    
    # Legacy field for backward compatibility (will be deprecated)
    final_cost = Column(Numeric(12, 2), nullable=True)  # Keep for migration
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=True)  # Keep for migration
    
    # Lifecycle Management
    status = Column(String(20), nullable=False, default='PROPOSED', index=True)
    # Values: 'PROPOSED', 'LOCKED', 'REVERTED'
    
    # NEW: Bunch Management for Phased Finalization
    bunch_id = Column(String(50), nullable=True, index=True)  # "BUNCH_1", "BUNCH_2", etc.
    bunch_name = Column(String(200), nullable=True)  # "High Priority - Month 1", etc.
    
    # Forecasted Invoice Timing (from DeliveryOption during planning)
    delivery_option_id = Column(Integer, ForeignKey("delivery_options.id"), nullable=True)
    forecast_invoice_timing_type = Column(String(20), nullable=False, default='RELATIVE')
    # Values: 'ABSOLUTE', 'RELATIVE'
    forecast_invoice_issue_date = Column(Date, nullable=True)  # For ABSOLUTE timing
    forecast_invoice_days_after_delivery = Column(Integer, nullable=True)  # For RELATIVE timing
    # Forecast Invoice with currency support
    forecast_invoice_amount_value = Column(Numeric(15, 2), nullable=True)  # Expected invoice amount
    forecast_invoice_amount_currency = Column(String(3), nullable=True, default='IRR')  # Currency of forecast invoice
    
    # Actual Invoice Data (entered by finance team) with currency support
    actual_invoice_issue_date = Column(Date, nullable=True)
    actual_invoice_amount_value = Column(Numeric(15, 2), nullable=True)  # Actual invoice amount
    actual_invoice_amount_currency = Column(String(3), nullable=True, default='IRR')  # Currency of actual invoice
    actual_invoice_received_date = Column(Date, nullable=True)  # When payment actually received
    invoice_entered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invoice_entered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Actual Payment Data (entered by finance team for payments to suppliers) with currency support
    actual_payment_amount_value = Column(Numeric(15, 2), nullable=True)  # Total amount paid
    actual_payment_amount_currency = Column(String(3), nullable=True, default='IRR')  # Currency of payment
    actual_payment_date = Column(Date, nullable=True)  # First/single payment date
    actual_payment_installments = Column(JSON, nullable=True)  # For installment payments: [{"date": "2026-01-15", "amount": 10000, "currency": "USD"}, ...]
    payment_entered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payment_entered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Legacy fields for backward compatibility (will be deprecated)
    forecast_invoice_amount = Column(Numeric(12, 2), nullable=True)  # Keep for migration
    actual_invoice_amount = Column(Numeric(12, 2), nullable=True)  # Keep for migration
    actual_payment_amount = Column(Numeric(12, 2), nullable=True)  # Keep for migration
    
    # Delivery Tracking (Procurement Plan feature)
    delivery_status = Column(String(50), nullable=False, default='AWAITING_DELIVERY', index=True)
    # Values: 'AWAITING_DELIVERY', 'CONFIRMED_BY_PROCUREMENT', 'DELIVERY_COMPLETE'
    
    # Procurement Team Confirmation
    actual_delivery_date = Column(Date, nullable=True)
    procurement_confirmed_at = Column(DateTime(timezone=True), nullable=True)
    procurement_confirmed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_correct_item_confirmed = Column(Boolean, default=False)
    serial_number = Column(String(200), nullable=True)
    procurement_delivery_notes = Column(Text, nullable=True)
    
    # Project Manager Acceptance
    pm_accepted_at = Column(DateTime(timezone=True), nullable=True)
    pm_accepted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_accepted_by_pm = Column(Boolean, default=False)
    pm_acceptance_notes = Column(Text, nullable=True)
    customer_delivery_date = Column(Date, nullable=True)
    
    decision_maker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision_date = Column(DateTime(timezone=True), nullable=False)
    finalized_at = Column(DateTime(timezone=True), nullable=True)  # When status changed to LOCKED
    finalized_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who locked it
    is_manual_edit = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    project_item = relationship("ProjectItem", back_populates="finalized_decisions")
    procurement_option = relationship("ProcurementOption", foreign_keys=[procurement_option_id])
    delivery_option = relationship("DeliveryOption", foreign_keys=[delivery_option_id])
    optimization_run = relationship("OptimizationRun", back_populates="finalized_decisions")
    decision_maker = relationship("User", foreign_keys=[decision_maker_id])
    finalized_by = relationship("User", foreign_keys=[finalized_by_id])
    invoice_entered_by = relationship("User", foreign_keys=[invoice_entered_by_id])
    payment_entered_by = relationship("User", foreign_keys=[payment_entered_by_id])
    procurement_confirmed_by = relationship("User", foreign_keys=[procurement_confirmed_by_id])
    pm_accepted_by = relationship("User", foreign_keys=[pm_accepted_by_id])
    currency = relationship("Currency")
    cashflow_events = relationship("CashflowEvent", back_populates="related_decision", cascade="all, delete-orphan")


class DecisionFactorWeight(Base):
    __tablename__ = "decision_factor_weights"
    
    id = Column(Integer, primary_key=True, index=True)
    factor_name = Column(String(100), unique=True, nullable=False)
    weight = Column(Integer, nullable=False, default=5)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Add check constraint for weight
    __table_args__ = (
        CheckConstraint('weight >= 1 AND weight <= 10', name='check_weight_range'),
    )


class Currency(Base):
    """Currency master table"""
    __tablename__ = "currencies"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False, index=True)  # USD, EUR, IRR, etc.
    name = Column(String(100), nullable=False)  # US Dollar, Euro, Iranian Rial, etc.
    symbol = Column(String(10), nullable=False)  # $, €, ﷼, etc.
    is_base_currency = Column(Boolean, default=False, index=True)  # Only one should be True
    is_active = Column(Boolean, default=True, index=True)
    decimal_places = Column(Integer, default=2)  # Number of decimal places for display
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])


class ExchangeRate(Base):
    """Historical daily exchange rates for currency conversion"""
    __tablename__ = "exchange_rates"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)  # Date for which this rate is valid
    from_currency = Column(String(3), nullable=False, index=True)  # Source currency (e.g., 'USD')
    to_currency = Column(String(3), nullable=False, index=True)    # Target currency (e.g., 'IRR')
    rate = Column(Numeric(15, 6), nullable=False)  # Exchange rate (from_currency to to_currency)
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Composite index for efficient lookups
    __table_args__ = (
        CheckConstraint('from_currency != to_currency', name='check_different_currencies'),
        CheckConstraint('rate > 0', name='check_positive_rate'),
    )


class OptimizationResult(Base):
    __tablename__ = "optimization_results"
    
    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    run_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    item_code = Column(String(50), nullable=False)
    procurement_option_id = Column(Integer, ForeignKey("procurement_options.id"), nullable=False)
    purchase_time = Column(Integer, nullable=False)  # The time slot the purchase decision is made
    delivery_time = Column(Integer, nullable=False)  # The time slot the item is delivered
    quantity = Column(Integer, nullable=False)
    final_cost = Column(Numeric(12, 2), nullable=False)
    
    # Relationships
    project = relationship("Project", back_populates="optimization_results")
    procurement_option = relationship("ProcurementOption", back_populates="optimization_results")
