from pydantic import BaseModel
from typing import Optional
import datetime

class UserRegister(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    company_name: str
    account_type: Optional[str] = "business"  # 'individual', 'household', 'business'
    industry: Optional[str] = "SaaS / Technology"
    monthly_baseline_revenue: Optional[float] = 0.0
    current_cash_reserves: Optional[float] = 0.0

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    business_id: int
    email: str
    company_name: str
    account_type: Optional[str] = "business"
    paypal_mode: Optional[str] = "sandbox"
    paypal_connected: Optional[bool] = True

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True
