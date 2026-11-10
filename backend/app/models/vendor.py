import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False, index=True)  # e.g. "Cloud & Hosting", "Project Management", "Design"
    description = Column(Text, nullable=True)
    website_url = Column(String, nullable=True)
    rating = Column(Float, default=4.5)
    is_recommended = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    plans = relationship("VendorPlan", back_populates="vendor", cascade="all, delete-orphan")


class VendorPlan(Base):
    __tablename__ = "vendor_plans"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_name = Column(String, nullable=False)  # e.g. "Starter", "Team", "Enterprise"
    price = Column(Float, nullable=False, default=0.0)
    cadence = Column(String, default="monthly")  # monthly, annual
    currency = Column(String, default="USD")
    features = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    vendor = relationship("Vendor", back_populates="plans")

