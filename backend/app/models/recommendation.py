import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    
    action_type = Column(String, nullable=False) # 'REVIEW', 'DOWNGRADE', 'CONSOLIDATE', 'RENEGOTIATE', 'SWITCH_ANNUAL', 'CANCEL', 'REVENUE_AUDIT'
    title = Column(String, nullable=False)
    vendor_name = Column(String, nullable=True)
    identified_issue = Column(Text, nullable=True)
    supporting_evidence = Column(Text, nullable=True)
    confidence = Column(String, default="medium") # 'high', 'medium', 'low'
    explanation = Column(Text, nullable=True)
    rationale = Column(Text, nullable=False)
    action_plan = Column(Text, nullable=True) # Step-by-step guidance
    
    potential_monthly_saving = Column(Float, default=0.0)
    potential_annual_saving = Column(Float, default=0.0)
    runway_impact_days = Column(Integer, default=0)
    
    negotiation_script = Column(Text, nullable=True)
    status = Column(String, default="pending") # 'pending', 'applied', 'dismissed'
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="recommendations")
    subscription = relationship("Subscription", back_populates="recommendations")
