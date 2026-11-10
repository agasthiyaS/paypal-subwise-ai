from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import datetime

class ExpenseBase(BaseModel):
    amount: float = Field(gt=0, description="Positive expense or income amount")
    currency: Optional[str] = "USD"
    expense_type: Optional[str] = "expense" # 'expense' or 'income'
    category: Optional[str] = "Other"
    description: str
    merchant: Optional[str] = None
    expense_date: Optional[datetime.datetime] = None
    is_recurring: Optional[bool] = False
    payment_method: Optional[str] = "Manual Entry"
    household_member_id: Optional[int] = None
    is_shared: Optional[bool] = True
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    expense_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    expense_date: Optional[datetime.datetime] = None
    is_recurring: Optional[bool] = None
    payment_method: Optional[str] = None
    household_member_id: Optional[int] = None
    is_shared: Optional[bool] = None
    notes: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: int
    business_id: int
    user_id: int
    data_source: str
    paypal_transaction_id: Optional[str] = None
    categorization_method: str
    member_name: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class CategorySpendingItem(BaseModel):
    category: str
    amount: float
    percentage: float
    count: int

class MonthlyExpenseSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    overall_budget: float
    budget_remaining: float
    budget_utilization_percent: float
    category_breakdown: List[CategorySpendingItem]
    grocery_total: float
    utility_total: float
    discretionary_total: float
    active_subscriptions_total: float
    recent_trend: List[Dict[str, Any]] = []

