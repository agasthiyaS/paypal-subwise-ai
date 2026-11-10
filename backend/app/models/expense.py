import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    amount = Column(Float, nullable=False) # Positive value representing expenditure or income
    currency = Column(String, default="USD")
    expense_type = Column(String, default="expense", nullable=False) # 'expense' or 'income'
    category = Column(String, default="Other", nullable=False, index=True)
    description = Column(String, nullable=False)
    merchant = Column(String, nullable=True, index=True)
    expense_date = Column(DateTime, nullable=False, index=True)
    
    is_recurring = Column(Boolean, default=False)
    payment_method = Column(String, default="Manual Entry") # 'Manual Entry', 'PayPal', 'Credit Card', 'Cash', etc.
    
    # Household member attribution & sharing
    household_member_id = Column(Integer, ForeignKey("household_members.id", ondelete="SET NULL"), nullable=True, index=True)
    is_shared = Column(Boolean, default=True) # Shared household expense vs personal
    
    # Data provenance and sync
    data_source = Column(String, default="manual") # 'manual', 'paypal_sync', 'demo'
    paypal_transaction_id = Column(String, nullable=True, index=True)
    categorization_method = Column(String, default="manual") # 'manual', 'rules_engine', 'user_corrected'
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="expenses")
    user = relationship("User")
    member = relationship("HouseholdMember", back_populates="expenses")

Index("idx_expense_biz_date", Expense.business_id, Expense.expense_date)
Index("idx_expense_biz_cat", Expense.business_id, Expense.category)

