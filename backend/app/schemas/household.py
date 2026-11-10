from pydantic import BaseModel, Field
from typing import Optional, List
import datetime

class HouseholdMemberBase(BaseModel):
    name: str
    role: Optional[str] = "Member"
    avatar_color: Optional[str] = "#0070ba"
    is_active: Optional[bool] = True
    monthly_income_share: Optional[float] = 0.0

class HouseholdMemberCreate(HouseholdMemberBase):
    pass

class HouseholdMemberUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    avatar_color: Optional[str] = None
    is_active: Optional[bool] = None
    monthly_income_share: Optional[float] = None

class HouseholdMemberResponse(HouseholdMemberBase):
    id: int
    business_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class MemberExpenseSummary(BaseModel):
    member_id: Optional[int] = None
    member_name: str
    role: str
    avatar_color: str
    total_spent: float
    percentage_of_household: float
    transaction_count: int

class HouseholdFinancialSummary(BaseModel):
    total_household_budget: float
    total_household_spent: float
    remaining_budget: float
    budget_utilization_percent: float
    grocery_spent: float
    utility_spent: float
    shared_spent: float
    personal_spent: float
    active_member_count: int
    members: List[MemberExpenseSummary]

