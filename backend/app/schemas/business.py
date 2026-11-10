from pydantic import BaseModel
from typing import Optional
import datetime

class BusinessProfileBase(BaseModel):
    company_name: str
    account_type: Optional[str] = "business"
    industry: Optional[str] = "SaaS / Technology"
    monthly_baseline_revenue: float = 0.0
    current_cash_reserves: float = 0.0
    target_runway_months: int = 6
    risk_tolerance: str = "moderate"
    currency: str = "USD"

class BusinessProfileUpdate(BaseModel):
    company_name: Optional[str] = None
    account_type: Optional[str] = None
    industry: Optional[str] = None
    monthly_baseline_revenue: Optional[float] = None
    current_cash_reserves: Optional[float] = None
    target_runway_months: Optional[int] = None
    risk_tolerance: Optional[str] = None

class PayPalConnectRequest(BaseModel):
    paypal_mode: str = "sandbox" # 'live', 'sandbox', 'demo'
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None

class BusinessProfileResponse(BusinessProfileBase):
    id: int
    user_id: int
    paypal_connected: bool
    paypal_mode: str
    last_synced_at: Optional[datetime.datetime] = None
    total_transactions: Optional[int] = 0
    is_demo: bool = False
    profile_type: Optional[str] = "STANDARD"
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True
