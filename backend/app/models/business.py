import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String, nullable=False)
    industry = Column(String, default="SaaS / Technology")
    monthly_baseline_revenue = Column(Float, default=0.0) # Baseline monthly sales
    current_cash_reserves = Column(Float, default=0.0)    # Liquid cash available
    target_runway_months = Column(Integer, default=6)        # Minimum comfortable runway
    risk_tolerance = Column(String, default="moderate")       # conservative, moderate, aggressive
    currency = Column(String, default="USD")
    
    # PayPal Connection Information
    paypal_connected = Column(Boolean, default=True)
    paypal_mode = Column(String, default="sandbox")             # 'live', 'sandbox', 'demo'
    paypal_client_id = Column(String, nullable=True)
    paypal_client_secret = Column(String, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    
    # Stage 8.5: Demo Environment Isolation
    is_demo = Column(Boolean, default=False, nullable=False)    # False for real Sandbox/Live, True for DemoTech Solutions
    profile_type = Column(String, default="STANDARD")           # 'STANDARD' vs 'DEMO'
    account_type = Column(String, default="business", server_default="business", nullable=False) # 'individual', 'household', 'business'
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "is_demo", name="uq_business_user_demo"),
    )

    owner = relationship("User", back_populates="businesses")
    transactions = relationship("Transaction", back_populates="business", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="business", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="business", cascade="all, delete-orphan")
    scenarios = relationship("ScenarioSimulation", back_populates="business", cascade="all, delete-orphan")
    household_members = relationship("HouseholdMember", back_populates="business", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="business", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="business", cascade="all, delete-orphan")
