import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Stage 8.5: Tracks selected active profile (Sandbox ID vs Demo ID)
    active_business_id = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    businesses = relationship("BusinessProfile", back_populates="owner", cascade="all, delete-orphan")

    @property
    def business(self):
        """
        Backward-compatible active business profile resolver.
        Prefers active_business_id, then standard profile, then first available.
        """
        if not self.businesses:
            return None
        if self.active_business_id:
            for b in self.businesses:
                if b.id == self.active_business_id:
                    return b
        # Fallback to standard (non-demo) profile
        for b in self.businesses:
            if not getattr(b, "is_demo", False):
                return b
        return self.businesses[0]
