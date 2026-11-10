import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, func
from app.database import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    paypal_event_id = Column(String(120), unique=True, index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), index=True, nullable=True)
    business_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="processed", nullable=False, index=True)  # processed, duplicate, failed, ignored
    verification_status = Column(String(30), default="unverified", nullable=False)  # verified, unverified, simulated
    payload = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, server_default=func.now(), nullable=False)
    processed_at = Column(DateTime, nullable=True)

