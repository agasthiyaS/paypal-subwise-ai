from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ── Per-month projection row (Stage 1 & 2 baseline & scenarios) ──────────────
class ForecastMonthItem(BaseModel):
    month: int
    month_name: str
    projected_operating_revenue: float
    projected_non_sub_expenses: float
    projected_confirmed_subscription_expenses: float
    potential_subscription_expenses: float
    projected_net_cashflow: float
    projected_closing_cash_balance: float
    is_cash_depleted: bool


# ── Scenario assumptions (Stage 2) ───────────────────────────────────────────
class ScenarioAssumptions(BaseModel):
    scenario_name: str               # "optimistic" | "baseline" | "conservative"
    display_label: str               # Human-readable: "Optimistic Scenario"
    revenue_adjustment_pct: float    # e.g. +15.0, 0.0, -20.0
    expense_adjustment_pct: float    # Always 0.0 — subs fixed, non-sub unchanged
    confirmed_sub_expenses_unchanged: bool  # Always True — commitments are contractual
    description: str                 # Plain-English explanation of scenario logic


# ── Single scenario block (Stage 2) ───────────────────────────────────────────
class ScenarioForecast(BaseModel):
    scenario: str                    # "optimistic" | "baseline" | "conservative"
    display_label: str
    assumptions: ScenarioAssumptions
    monthly_revenue: float           # Scenario-adjusted projected monthly revenue
    monthly_non_sub_expenses: float
    monthly_confirmed_sub_expenses: float
    monthly_potential_sub_expenses: float
    monthly_net_cashflow: float
    months: List[ForecastMonthItem]
    runway_months: Optional[float] = None   # None when data insufficient
    runway_available: bool = False
    runway_note: str = ""


# ── Stage 3: Scheduled Payment Item in the 6-Month Calendar ───────────────────
class ScheduledSubscriptionPayment(BaseModel):
    vendor_name: str
    expected_payment_date: str          # "YYYY-MM-DD"
    expected_payment_amount: float
    currency: str = "USD"
    billing_frequency: str              # "monthly", "weekly", "quarterly", "annual"
    subscription_confidence: float
    detection_type: str                 # "confirmed" | "potential"
    is_date_confirmed: bool             # True if derived from confirmed next_billing_date
    is_contractual_commitment: bool     # True only for confirmed subscriptions
    month_index: int                    # 1 to 6
    month_name: str                     # e.g. "Dec 2026"


# ── Stage 3: Monthly Scheduled Subscription Total & Concentration Analysis ─────
class MonthlyScheduledSubscriptionTotal(BaseModel):
    month_index: int
    month_name: str
    total_confirmed_amount: float
    total_potential_amount: float
    confirmed_renewals_count: int
    largest_individual_payment: float
    largest_payment_vendor: Optional[str] = None
    revenue_commitment_pct: Optional[float] = None
    is_high_concentration: bool
    concentration_warning: Optional[str] = None


# ── Top-level response ────────────────────────────────────────────────────────
class ForecastResponse(BaseModel):
    # ── Stage 1 fields (preserved exactly) ───────────────────────────────────
    status: str                        # 'sufficient_data' | 'limited_data' | 'insufficient_data'
    currency: str = "USD"
    verified_starting_cash: Optional[float] = None
    has_verified_cash: bool
    historical_monthly_operating_revenue: float
    historical_monthly_non_sub_expenses: float
    historical_monthly_subscription_expenses: float
    confirmed_monthly_subscription_commitments: float
    potential_monthly_subscription_commitments: float
    forecast_months: int = 6
    forecast: List[ForecastMonthItem]  # Baseline timeline
    data_quality_warnings: List[str]
    assumptions_explanation: str
    missing_data_reasons: List[str]

    # ── Stage 2 fields (multi-scenario) ──────────────────────────────────────
    scenarios_available: bool = False          # False when status == insufficient_data
    optimistic: Optional[ScenarioForecast] = None
    baseline: Optional[ScenarioForecast] = None
    conservative: Optional[ScenarioForecast] = None
    scenario_methodology_note: str = (
        "Scenario revenue adjustments (+15% optimistic, -20% conservative) are deterministic "
        "configurable assumptions applied to the verified historical revenue average. "
        "They are not AI predictions. Confirmed subscription commitments are identical "
        "across all scenarios as they represent contractual obligations."
    )

    # ── Stage 3 fields (calendar-aware subscription forecasting) ───────────────
    payment_calendar: List[ScheduledSubscriptionPayment] = []
    upcoming_subscription_payments: List[ScheduledSubscriptionPayment] = []
    monthly_scheduled_subscription_totals: List[MonthlyScheduledSubscriptionTotal] = []
    renewal_concentration_warnings: List[str] = []
    unknown_renewal_date_count: int = 0
    payment_scheduling_methodology: str = (
        "Scheduled payments are projected from verified subscription billing dates and cadences. "
        "Weekly, monthly, quarterly, and annual renewals are mapped to their exact calendar payment dates "
        "rather than smoothed evenly across months. Potential subscriptions are tracked separately "
        "and excluded from baseline cash-flow deductions."
    )
