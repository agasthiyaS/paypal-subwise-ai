import datetime
from typing import List, Dict, Any, Optional
from app.models.business import BusinessProfile
from app.schemas.consumer_intelligence import (
    MultiScenarioForecast,
    ScenarioForecastPoint,
    SpendingAnalysisResult
)

class MultiScenarioForecastService:
    @classmethod
    def generate_forecast(
        cls,
        business: BusinessProfile,
        analysis: SpendingAnalysisResult,
        days: int = 90
    ) -> MultiScenarioForecast:
        start_cash = float(business.current_cash_reserves or 0.0)
        daily_income = (analysis.total_income / 30.0) if analysis.total_income > 0 else 0.0
        daily_expense = (analysis.total_expenses / 30.0) if analysis.total_expenses > 0 else 0.0
        daily_recurring = (analysis.recurring_expenses_total / 30.0)

        # Baseline: daily net = daily_income - daily_expense
        daily_net_baseline = daily_income - daily_expense

        # Conservative: 15% lower income, 15% higher discretionary
        daily_income_cons = daily_income * 0.85
        daily_var_cons = (daily_expense - daily_recurring) * 1.15
        daily_net_conservative = daily_income_cons - (daily_recurring + daily_var_cons)

        # Optimistic: +5% income bonus, 12% discretionary trimming
        daily_income_opt = daily_income * 1.05
        daily_var_opt = (daily_expense - daily_recurring) * 0.88
        daily_net_optimistic = daily_income_opt - (daily_recurring + daily_var_opt)

        now = datetime.datetime.utcnow()
        timeline: List[ScenarioForecastPoint] = []
        b_cash = start_cash
        c_cash = start_cash
        o_cash = start_cash

        day_30_balance = {}
        day_60_balance = {}
        day_90_balance = {}
        shortfall_date = None

        # Sample every 5 days for smooth charting over 90 days
        for day in range(1, days + 1):
            b_cash += daily_net_baseline
            c_cash += daily_net_conservative
            o_cash += daily_net_optimistic

            if c_cash < 0 and shortfall_date is None:
                shortfall_date = (now + datetime.timedelta(days=day)).strftime("%B %d, %Y")

            if day == 30:
                day_30_balance = {
                    "baseline": round(b_cash, 2),
                    "conservative": round(c_cash, 2),
                    "optimistic": round(o_cash, 2)
                }
            elif day == 60:
                day_60_balance = {
                    "baseline": round(b_cash, 2),
                    "conservative": round(c_cash, 2),
                    "optimistic": round(o_cash, 2)
                }
            elif day == 90:
                day_90_balance = {
                    "baseline": round(b_cash, 2),
                    "conservative": round(c_cash, 2),
                    "optimistic": round(o_cash, 2)
                }

            if day % 5 == 0 or day == 1 or day == days:
                d_date = (now + datetime.timedelta(days=day)).strftime("%b %d")
                timeline.append(ScenarioForecastPoint(
                    day=day,
                    date=d_date,
                    baseline_cash=round(max(0.0, b_cash), 2),
                    conservative_cash=round(max(0.0, c_cash), 2),
                    optimistic_cash=round(max(0.0, o_cash), 2),
                    expected_inflows=round(daily_income * day, 2),
                    expected_commitments=round(daily_expense * day, 2)
                ))

        warning = None
        if not analysis.has_sufficient_data:
            warning = "Forecast based on baseline financial setup. Log additional expenses or link PayPal for higher predictive accuracy."

        return MultiScenarioForecast(
            current_cash=round(start_cash, 2),
            days_projected=days,
            timeline=timeline,
            day_30_balance=day_30_balance or {"baseline": round(b_cash, 2), "conservative": round(c_cash, 2), "optimistic": round(o_cash, 2)},
            day_60_balance=day_60_balance or {"baseline": round(b_cash, 2), "conservative": round(c_cash, 2), "optimistic": round(o_cash, 2)},
            day_90_balance=day_90_balance or {"baseline": round(b_cash, 2), "conservative": round(c_cash, 2), "optimistic": round(o_cash, 2)},
            projected_shortfall=shortfall_date,
            historical_data_warning=warning
        )

