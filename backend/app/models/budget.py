import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String, default="Overall", nullable=False) # 'Overall' or standard category name
    monthly_limit = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    period_month = Column(Integer, nullable=True) # None for all months, or 1-12
    period_year = Column(Integer, nullable=True)  # None for ongoing, or e.g. 2026
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("business_id", "category", "period_month", "period_year", name="uq_budget_category_period"),
    )

    business = relationship("BusinessProfile", back_populates="budgets")

