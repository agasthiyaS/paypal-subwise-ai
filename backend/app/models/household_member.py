import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class HouseholdMember(Base):
    __tablename__ = "household_members"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    role = Column(String, default="Member") # Primary, Partner, Child, Roommate, Parent, Other
    avatar_color = Column(String, default="#0070ba")
    is_active = Column(Boolean, default=True, nullable=False)
    monthly_income_share = Column(Float, default=0.0) # Voluntary income allocation to household pool
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="household_members")
    expenses = relationship("Expense", back_populates="member")

