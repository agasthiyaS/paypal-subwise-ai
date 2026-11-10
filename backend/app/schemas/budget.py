from pydantic import BaseModel
from typing import Optional, List
import datetime

class BudgetBase(BaseModel):
    category: str = "Overall"
    monthly_limit: float
    currency: Optional[str] = "USD"
    period_month: Optional[int] = None
    period_year: Optional[int] = None

class BudgetCreate(BudgetBase):
    pass

class BudgetUpdate(BaseModel):
    monthly_limit: Optional[float] = None
    period_month: Optional[int] = None
    period_year: Optional[int] = None

class BudgetResponse(BudgetBase):
    id: int
    business_id: int
    current_spent: Optional[float] = 0.0
    utilization_percent: Optional[float] = 0.0
    remaining_amount: Optional[float] = 0.0
    is_over_budget: Optional[bool] = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

