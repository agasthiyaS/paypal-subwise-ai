import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

class ScenarioSimulation(Base):
    __tablename__ = "scenario_simulations"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    
    scenario_name = Column(String, nullable=False) # e.g. "20% Revenue Dip + Freeze Discretionary"
    revenue_shock_pct = Column(Float, default=0.0) # -20.0 = 20% revenue drop
    paused_subscription_ids = Column(JSON, default=list) # List of subscription IDs paused
    
    initial_cash_reserves = Column(Float, nullable=False)
    projected_burn_rate = Column(Float, nullable=False)
    projected_runway_months = Column(Float, nullable=False)
    depletion_month = Column(String, nullable=True) # e.g. "Month 7" or "Sustainable"
    
    monthly_projection_data = Column(JSON, default=list) # [{month: 1, balance: 42000, revenue: 12000, expenses: 15000}]
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="scenarios")

