from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import datetime

class SubscriptionBase(BaseModel):
    vendor_name: str
    category: str
    cadence: str
    average_amount: float
    latest_amount: float
    currency: str = "USD"
    first_billed_date: datetime.datetime
    last_billed_date: datetime.datetime
    next_billing_date: datetime.datetime
    price_change_pct: float = 0.0
    confidence_score: float = 0.95
    priority_tier: int = 2
    redundancy_group: Optional[str] = None
    status: str = "active"
    utilization_score: float = 0.7
    is_essential: bool = True
    detection_type: Optional[str] = "confirmed"
    detection_reason: Optional[str] = None
    billing_type: Optional[str] = "fixed"

class SubscriptionUpdate(BaseModel):
    priority_tier: Optional[int] = None # 1, 2, or 3
    is_essential: Optional[bool] = None
    status: Optional[str] = None # active, paused, cancelled

class SubscriptionResponse(SubscriptionBase):
    id: int
    business_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

class SubscriptionSummaryResponse(BaseModel):
    total_active_count: int
    total_monthly_spend: float
    total_annual_spend: float
    zombie_count: int
    at_risk_count: int
    redundant_tool_count: int
    potential_monthly_savings: float
    category_distribution: dict
    potential_count: Optional[int] = 0
    confirmed_count: Optional[int] = 0
    subscriptions: List[SubscriptionResponse]

class VendorAnalysisItem(BaseModel):
    vendor_name: str
    category: str
    standard_category: str
    cadence: str
    billing_type: str
    latest_amount: float
    average_amount: float
    monthly_equivalent: float
    annual_equivalent: float
    status: str
    detection_type: str
    detection_reason: Optional[str] = None
    confidence_score: float
    historical_spend_total: float
    transaction_count: int
    price_change_pct: float
    first_billed_date: Optional[str] = None
    last_billed_date: Optional[str] = None
    next_billing_date: Optional[str] = None

class CategoryAnalysisItem(BaseModel):
    category: str
    monthly_spend: float
    annual_spend: float
    percentage_of_total: float
    subscription_count: int
    vendors: List[str]

class MonthlySpendHistoryItem(BaseModel):
    month: str
    month_label: str
    total_subscription_spend: float
    operating_revenue: float
    operating_expenses: float
    subscription_to_revenue_pct: Optional[float] = None
    vendor_breakdown: Dict[str, float] = {}
    spending_change_from_prev: Optional[float] = None
    spending_change_pct_from_prev: Optional[float] = None

class SpendingTrendAnalysis(BaseModel):
    current_month_spend: float
    previous_month_spend: float
    spending_change_amount: float
    spending_change_pct: Optional[float] = None
    trend_direction: str
    is_significant_increase: bool
    price_creep_alerts: List[Dict[str, Any]] = []
    trend_summary: str

class RevenueVsSubscriptionAnalysis(BaseModel):
    monthly_operating_revenue: float
    monthly_subscription_spend: float
    revenue_percentage: Optional[float] = None
    burden_level: str
    has_sufficient_revenue_data: bool
    explanation: str

class SubscriptionAnalysisResponse(BaseModel):
    has_data: bool
    has_subscriptions: bool
    status: str
    message: str
    currency: str = "USD"
    total_monthly_commitment: float
    total_annual_commitment: float
    confirmed_monthly_commitment: float
    confirmed_annual_commitment: float
    potential_monthly_commitment: float
    potential_annual_commitment: float
    actual_historical_spend_total: float
    vendor_analysis: List[VendorAnalysisItem]
    category_analysis: List[CategoryAnalysisItem]
    monthly_history: List[MonthlySpendHistoryItem]
    spending_trends: SpendingTrendAnalysis
    revenue_comparison: RevenueVsSubscriptionAnalysis


