from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
import datetime

class HistoricalActuals(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reporting_period_start: Optional[str] = None
    reporting_period_end: Optional[str] = None
    operating_months_analyzed: int
    historical_monthly_operating_revenue: float
    historical_monthly_operating_expenses: float
    historical_monthly_subscription_expenses: float
    historical_monthly_non_sub_expenses: float
    historical_monthly_net_cash_flow: float
    verified_available_cash: Optional[float] = None
    cash_provenance: str
    is_cash_ledger_derived: bool
    paypal_balance_note: str


class ForwardCommitments(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    confirmed_monthly_subscription_commitments: float
    confirmed_annual_subscription_commitments: float
    potential_monthly_subscription_commitments: float
    potential_annual_subscription_commitments: float
    upcoming_renewals_count_next_60_days: int
    upcoming_renewals_amount_next_60_days: float


class ProjectedEstimates(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    forecast_months: int
    projected_monthly_revenue_baseline: float
    projected_monthly_net_cash_flow: float
    projected_lowest_cash_balance: Optional[float] = None
    projected_shortfall_month: Optional[str] = None
    estimated_runway_months: Optional[float] = None
    runway_status: str
    runway_explanation: str


class FinancialHealthIndex(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    score: Optional[int] = None
    status_label: str
    scoring_breakdown: Optional[Dict[str, Any]] = None
    scoring_methodology: str


class FinancialRiskItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    risk_type: str  # PRICE_CREEP, HIGH_SUBSCRIPTION_BURDEN, RENEWAL_CONCENTRATION, PROJECTED_CASH_DEFICIT, LARGE_ANNUAL_OBLIGATION, TRIAL_REVIEW
    severity: str  # high, medium, low
    title: str
    description: str
    supporting_evidence: str
    mitigation_action: str


class MonthlyBusinessBriefing(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reporting_period: str
    data_sufficiency_status: str  # sufficient_data, limited_data, insufficient_data
    is_ai_generated: bool
    generation_model: str
    overall_financial_position: str
    revenue_and_expense_summary: str
    subscription_spending_overview: str
    upcoming_payment_obligations: str
    critical_risks_summary: str
    recommended_cfo_actions: List[str]
    full_briefing_markdown: str


class FinancialIntelligenceOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: int
    company_name: str
    data_sufficiency_status: str
    missing_data_reasons: List[str] = []
    required_records_for_analysis: List[str] = []
    historical_actuals: HistoricalActuals
    forward_commitments: ForwardCommitments
    projected_estimates: ProjectedEstimates
    financial_health_index: FinancialHealthIndex
    risk_intelligence: List[FinancialRiskItem] = []
    monthly_briefing: MonthlyBusinessBriefing
    transparency_disclosure: str

