import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from app.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id"), nullable=False, index=True)
    paypal_transaction_id = Column(String, index=True, nullable=True)
    
    transaction_date = Column(DateTime, nullable=False, index=True)
    raw_description = Column(String, nullable=False)
    normalized_vendor = Column(String, nullable=False, index=True)
    category = Column(String, default="General Software")
    
    gross_amount = Column(Float, nullable=False) # e.g. -49.99 for expense, +500.0 for income
    fee_amount = Column(Float, default=0.0)
    net_amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    status = Column(String, default="COMPLETED") # COMPLETED, PENDING, REFUNDED
    data_source = Column(String, default="demo")  # 'live', 'sandbox', 'demo', 'demo_fixture'
    is_simulated = Column(Boolean, default=False, nullable=False) # True for demo_fixture transactions
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    business = relationship("BusinessProfile", back_populates="transactions")

Index("idx_biz_vendor_date", Transaction.business_id, Transaction.normalized_vendor, Transaction.transaction_date)
