from pydantic import BaseModel
from typing import List, Optional

class ScenarioPoint(BaseModel):
    month: int
    month_name: str
    projected_revenue: float
    total_expenses: float
    subscription_expenses: float
    net_cashflow: float
    cash_balance: float
    is_depleted: bool

class SimulationRequest(BaseModel):
    revenue_shock_pct: float = 0.0 # e.g. -25.0 for 25% revenue dip
    paused_subscription_ids: List[int] = [] # Specific subscriptions toggled off
    pause_tier_3_discretionary: bool = False # Bulk toggle
    additional_monthly_burn: float = 0.0 # Any custom operating cost adjustment

class SimulationResult(BaseModel):
    scenario_name: str
    revenue_shock_pct: float
    initial_cash_reserves: float
    monthly_recurring_subscriptions: float
    optimized_recurring_subscriptions: float
    monthly_savings_from_paused: float
    baseline_runway_months: float
    simulated_runway_months: float
    runway_delta_months: float
    depletion_status: str # "Month 5", "Month 11", or "Sustainable (>24 mo)"
    is_cash_flow_positive: bool
    timeline: List[ScenarioPoint]

