"""
Stage 6: Financial Reporting & Export Intelligence Schemas
Pydantic schemas for Monthly Financial Reports, Subscription Expense Reports,
Upcoming Renewal Reports, 6-Month Forecast Reports, and Export Requests.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any


class ReportPeriodFilter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    period_preset: str = "all"  # 'all', 'last_30_days', 'last_90_days', 'last_180_days', 'ytd', 'custom'
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    available_history_start: Optional[str] = None
    available_history_end: Optional[str] = None
    total_operating_records_in_period: int = 0


class MonthlyReportMonthItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    month_key: str  # YYYY-MM
    month_label: str  # e.g. "Oct 2026"
    operating_revenue: float
    non_sub_expenses: float
    confirmed_subscription_expenses: float
    potential_subscription_expenses: float
    total_operating_expenses: float
    net_operating_cashflow: float
    operating_transaction_count: int
    period_type: str = "ACTUAL"


class MonthlyFinancialReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: int
    company_name: str
    generated_at: str
    reporting_period: str
    period_filter: ReportPeriodFilter
    data_sufficiency_status: str  # 'sufficient_data', 'limited_data', 'insufficient_data'
    total_operating_revenue: float
    total_non_sub_expenses: float
    total_confirmed_sub_expenses: float
    total_potential_sub_expenses: float
    total_operating_expenses: float
    net_operating_cashflow: float
    average_monthly_revenue: float
    average_monthly_expenses: float
    verified_available_cash: Optional[float] = None
    cash_provenance: str
    paypal_balance_note: str
    monthly_breakdown: List[MonthlyReportMonthItem] = []
    disclaimer: str


class SubscriptionExpenseReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    vendor_name: str
    category: str
    billing_frequency: str
    latest_amount: float
    average_amount: float
    monthly_equivalent: float
    annual_run_rate: float
    detection_type: str  # 'confirmed' or 'potential'
    priority_tier: int = 2
    status: str = "active"
    price_change_pct: float = 0.0
    has_price_creep: bool = False
    price_change_note: Optional[str] = None
    next_billing_date: Optional[str] = None
    historical_payment_count: int = 0
    total_historical_spend: float = 0.0


class SubscriptionExpenseReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: int
    company_name: str
    generated_at: str
    confirmed_subscriptions_count: int
    potential_subscriptions_count: int
    total_confirmed_monthly_commitments: float
    total_confirmed_annual_commitments: float
    total_potential_monthly_commitments: float
    total_potential_annual_commitments: float
    items: List[SubscriptionExpenseReportItem] = []
    category_breakdown: List[Dict[str, Any]] = []
    disclaimer: str


class UpcomingRenewalReportItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_name: str
    expected_payment_date: str
    expected_payment_amount: float
    currency: str = "USD"
    billing_frequency: str
    detection_type: str
    is_date_confirmed: bool = True
    month_index: int
    month_name: str
    is_high_concentration: bool = False


class UpcomingRenewalReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: int
    company_name: str
    generated_at: str
    total_upcoming_60_days_count: int
    total_upcoming_60_days_amount: float
    unknown_renewal_date_count: int
    monthly_concentration_warnings: List[str] = []
    monthly_totals: List[Dict[str, Any]] = []
    scheduled_renewals: List[UpcomingRenewalReportItem] = []
    disclaimer: str


class ForecastScenarioMonthItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    month_index: int
    month_name: str
    projected_revenue: float
    projected_non_sub_expenses: float
    projected_confirmed_sub_expenses: float
    potential_sub_expenses: float
    projected_net_cashflow: float
    projected_closing_balance: Optional[float] = None
    is_cash_depleted: bool = False


class ForecastScenarioSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scenario_name: str
    display_label: str
    revenue_adjustment_pct: float
    monthly_projected_revenue: float
    monthly_projected_expenses: float
    monthly_confirmed_sub_expenses: float
    monthly_projected_net_cashflow: float
    lowest_projected_closing_balance: Optional[float] = None
    runway_status: str
    runway_months: Optional[float] = None
    runway_note: str
    timeline: List[ForecastScenarioMonthItem] = []


class CashFlowForecastReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: int
    company_name: str
    generated_at: str
    data_sufficiency_status: str
    forecast_months: int = 6
    scenarios: Dict[str, ForecastScenarioSummary] = {}
    assumptions_disclosure: str
    methodology_note: str


class ComprehensiveFinancialReport(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_id: int
    company_name: str
    generated_at: str
    reporting_period: str
    monthly_report: MonthlyFinancialReport
    subscription_report: SubscriptionExpenseReport
    renewal_report: UpcomingRenewalReport
    forecast_report: CashFlowForecastReport
    health_score: Optional[int] = None
    health_status: str
    health_scoring_methodology: str
    risk_triggers: List[Dict[str, Any]] = []
    executive_briefing_markdown: str
    overall_transparency_disclosure: str

