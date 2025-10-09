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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Add check constraint for priority_weight
    __table_args__ = (
        CheckConstraint('priority_weight >= 1 AND priority_weight <= 10', name='check_priority_weight_range'),
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
    item_code = Column(String(50), nullable=False)
    item_name = Column(Text)
    quantity = Column(Integer, nullable=False)
    delivery_options = Column(JSON, nullable=False, default=list)  # Array of possible delivery dates
    status = Column(SQLEnum(ProjectItemStatus), nullable=False, default=ProjectItemStatus.PENDING)
    external_purchase = Column(Boolean, default=False)
    
    # Lifecycle date tracking
    decision_date = Column(Date, nullable=True)
    procurement_date = Column(Date, nullable=True)
    payment_date = Column(Date, nullable=True)
    invoice_submission_date = Column(Date, nullable=True)
    expected_cash_in_date = Column(Date, nullable=True)
    actual_cash_in_date = Column(Date, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="project_items")
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
    base_cost = Column(Numeric(12, 2), nullable=False)
    lomc_lead_time = Column(Integer, default=0)  # Lead time in time slots
    discount_bundle_threshold = Column(Integer)
    discount_bundle_percent = Column(Numeric(5, 2))
    payment_terms = Column(JSON, nullable=False)  # Structured JSON for payment terms
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    optimization_results = relationship("OptimizationResult", back_populates="procurement_option")


class BudgetData(Base):
    __tablename__ = "budget_data"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_date = Column(Date, unique=True, nullable=False, index=True)
    available_budget = Column(Numeric(15, 2), nullable=False)
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
    amount = Column(Numeric(15, 2), nullable=False)
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
    final_cost = Column(Numeric(12, 2), nullable=False)
    
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
    forecast_invoice_amount = Column(Numeric(12, 2), nullable=True)  # Expected invoice amount
    
    # Actual Invoice Data (entered by finance team)
    actual_invoice_issue_date = Column(Date, nullable=True)
    actual_invoice_amount = Column(Numeric(12, 2), nullable=True)
    actual_invoice_received_date = Column(Date, nullable=True)  # When payment actually received
    invoice_entered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invoice_entered_at = Column(DateTime(timezone=True), nullable=True)
    
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
