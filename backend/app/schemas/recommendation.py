from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
import datetime

class RecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    subscription_id: Optional[int] = None
    action_type: str  # REVIEW, DOWNGRADE, CONSOLIDATE, RENEGOTIATE, SWITCH_ANNUAL, CANCEL, REVENUE_AUDIT, RENEWAL_RISK, CASHFLOW_PROTECTION
    title: str
    vendor_name: Optional[str] = None
    identified_issue: Optional[str] = None
    supporting_evidence: Optional[str] = None
    confidence: Optional[str] = "medium"  # high, medium, low
    explanation: Optional[str] = None
    rationale: str
    action_plan: Optional[str] = None
    potential_monthly_saving: float
    potential_annual_saving: float
    runway_impact_days: int
    negotiation_script: Optional[str] = None
    status: str
    created_at: datetime.datetime


class RecommendationUpdate(BaseModel):
    status: str  # 'pending', 'applied', 'dismissed'


class PurchaseSimulationRequest(BaseModel):
    proposed_vendor: str
    amount: float
    cadence: str = "monthly"  # monthly, annual, quarterly, weekly
    first_payment_date: Optional[str] = None  # YYYY-MM-DD
    business_purpose: Optional[str] = None
    verified_annual_discount_pct: Optional[float] = None  # only if verified by user


class AnnualVsMonthlyComparison(BaseModel):
    monthly_payment_amount: float
    annual_payment_amount: float
    annualized_monthly_cost: float
    discount_pct: Optional[float] = None
    has_verified_discount: bool = False
    discount_disclosure: str
    immediate_cash_outflow_difference: float
    impact_on_projected_closing_balance: str


class MonthProjectionPoint(BaseModel):
    month: int
    month_name: str
    baseline_closing_balance: Optional[float] = None
    simulated_closing_balance: Optional[float] = None
    proposed_outflow: float
    is_cash_depleted: bool = False


class PurchaseSimulationResponse(BaseModel):
    proposed_vendor: str
    amount: float
    cadence: str
    business_purpose: Optional[str] = None
    verdict: str  # "Affordable under current assumptions", "Affordable with caution", "Consider postponing", "Insufficient financial data"
    verdict_badge: str  # "success", "warning", "danger", "neutral"
    verdict_explanation: str
    immediate_cash_impact: float
    monthly_equivalent_cost: float
    annual_cost: float
    projected_shortfall_detected: bool
    shortfall_month: Optional[str] = None
    renewal_concentration_effect: str
    current_monthly_burn: float
    simulated_monthly_burn: float
    current_lowest_balance: Optional[float] = None
    simulated_lowest_balance: Optional[float] = None
    annual_vs_monthly: Optional[AnnualVsMonthlyComparison] = None
    timeline_comparison: List[MonthProjectionPoint] = []
    action_advice: List[str] = []
    confidence: str = "high"
    is_hypothetical_simulation: bool = True
    simulation_methodology_note: str
