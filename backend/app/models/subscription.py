import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    
    vendor_name = Column(String, nullable=False, index=True)
    category = Column(String, default="Productivity")
    cadence = Column(String, default="monthly") # 'monthly', 'quarterly', 'annual', 'weekly'
    
    average_amount = Column(Float, nullable=False) # e.g. 129.0
    latest_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    first_billed_date = Column(DateTime, nullable=False)
    last_billed_date = Column(DateTime, nullable=False)
    next_billing_date = Column(DateTime, nullable=False)
    
    price_change_pct = Column(Float, default=0.0) # +15.5% price creeping
    confidence_score = Column(Float, default=0.95) # Detection confidence 0.0-1.0
    
    # Priority & Lifecycle
    # 1: Mission Critical (Core Ops), 2: Important, 3: Discretionary / Convenience
    priority_tier = Column(Integer, default=2)
    redundancy_group = Column(String, nullable=True) # e.g. "team_collaboration", "cloud_storage", "project_mgmt"
    status = Column(String, default="active") # 'active', 'zombie', 'at_risk', 'cancelled', 'paused'
    
    # Hybrid Detection Classification
    detection_type = Column(String, default="confirmed") # 'confirmed', 'potential', 'uncertain'
    detection_reason = Column(String, nullable=True)     # Human-readable detection explanation
    billing_type = Column(String, default="fixed")       # 'fixed', 'variable'
    
    utilization_score = Column(Float, default=0.7) # 0.0 to 1.0 estimated / indicated utility
    is_essential = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="subscriptions")
    recommendations = relationship("Recommendation", back_populates="subscription", cascade="all, delete-orphan")

