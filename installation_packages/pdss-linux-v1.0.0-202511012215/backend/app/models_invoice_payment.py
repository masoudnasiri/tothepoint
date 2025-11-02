from sqlalchemy import Column, Integer, String, DateTime, Numeric, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()

class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CREDIT_CARD = "credit_card"

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(Integer, ForeignKey("finalized_decisions.id"), nullable=False)
    invoice_number = Column(String(100), unique=True, nullable=False)
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    invoice_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="IRR")
    due_date = Column(DateTime(timezone=True), nullable=False)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT)
    payment_terms = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    decision = relationship("FinalizedDecision", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    decision_id = Column(Integer, ForeignKey("finalized_decisions.id"), nullable=False)
    payment_date = Column(DateTime(timezone=True), nullable=False)
    payment_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="IRR")
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    reference_number = Column(String(100), nullable=True)
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
    decision = relationship("FinalizedDecision", back_populates="payments")
