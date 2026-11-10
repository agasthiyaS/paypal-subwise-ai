from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
import datetime

class CategoryMoMChange(BaseModel):
    category: str
    current_month_amount: float
    prior_month_amount: float
    dollar_change: float
    percent_change: float
    is_spike: bool = False

class TopMerchantItem(BaseModel):
    merchant: str
    amount: float
    count: int
    category: str

class SpendingAnalysisResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    month: int
    year: int
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate_percent: float
    recurring_expenses_total: float
    discretionary_expenses_total: float
    top_categories: List[Dict[str, Any]] = []
    mom_changes: List[CategoryMoMChange] = []
    frequent_merchants: List[TopMerchantItem] = []
    unusual_spikes: List[str] = []
    has_sufficient_data: bool = True
    notes: Optional[str] = None

class HealthScoreFactor(BaseModel):
    factor_name: str
    score: int
    max_score: int
    impact: str # 'positive', 'neutral', 'negative'
    description: str

class ExplainableHealthScore(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: int = Field(ge=0, le=100)
    rating: str # 'Excellent', 'Good', 'Fair', 'Needs Attention'
    factors: List[HealthScoreFactor] = []
    positive_highlights: List[str] = []
    risk_factors: List[str] = []
    actionable_improvements: List[str] = []
    disclaimer: str

class ScenarioForecastPoint(BaseModel):
    day: int
    date: str
    baseline_cash: float
    conservative_cash: float
    optimistic_cash: float
    expected_inflows: float
    expected_commitments: float

class MultiScenarioForecast(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_cash: float
    days_projected: int
    timeline: List[ScenarioForecastPoint] = []
    day_30_balance: Dict[str, float]
    day_60_balance: Dict[str, float]
    day_90_balance: Dict[str, float]
    projected_shortfall: Optional[str] = None
    historical_data_warning: Optional[str] = None

class ActionableSavingsRecommendation(BaseModel):
    id: str
    title: str
    explanation: str
    supporting_evidence: str
    monthly_savings: float
    annual_savings: float
    confidence: str # 'High', 'Medium', 'Low'
    priority: str # 'High', 'Medium', 'Low'
    action_type: str # 'SWITCH_TIER', 'CANCEL_OVERLAP', 'CURB_SPIKE', 'ANNUAL_DISCOUNT', 'UTILITY_CHECK'
    recommended_action: str
    category: str

class UnifiedFinancialIntelligence(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_type: str
    company_or_family_name: str
    spending_analysis: SpendingAnalysisResult
    health_score: ExplainableHealthScore
    forecast: MultiScenarioForecast
    recommendations: List[ActionableSavingsRecommendation] = []
    total_potential_monthly_savings: float
    total_potential_annual_savings: float

