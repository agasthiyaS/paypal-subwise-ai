from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.business import BusinessProfile
from app.models.budget import Budget
from app.schemas.consumer_intelligence import (
    ExplainableHealthScore,
    HealthScoreFactor,
    SpendingAnalysisResult
)

class FinancialHealthService:
    @classmethod
    def calculate_health_score(
        cls,
        business: BusinessProfile,
        analysis: SpendingAnalysisResult,
        db: Session
    ) -> ExplainableHealthScore:
        factors: List[HealthScoreFactor] = []
        positive_highlights: List[str] = []
        risk_factors: List[str] = []
        actionable_improvements: List[str] = []
        missing_data_reasons: List[str] = []
        has_sufficient_data: bool = True

        # Check overall analysis data sufficiency
        if not getattr(analysis, "has_sufficient_data", True):
            has_sufficient_data = False
            missing_data_reasons.append("Insufficient historical ledger data to establish baseline spending patterns.")

        # 1. Savings Rate Factor (Max 30 pts)
        if analysis.total_income == 0 and analysis.total_expenses == 0:
            s_pts = 0
            impact = "neutral"
            desc = "No income or expense transactions recorded for the current period."
            has_sufficient_data = False
            missing_data_reasons.append("Zero income and zero expenses recorded for this period.")
        else:
            savings_rate = analysis.savings_rate_percent
            if savings_rate >= 25.0:
                s_pts = 30
                impact = "positive"
                desc = f"Exceptional {round(savings_rate)}% savings rate, surpassing the gold standard 20% benchmark."
                positive_highlights.append(f"Strong savings habit: Retaining {round(savings_rate)}% of monthly income.")
            elif savings_rate >= 15.0:
                s_pts = 22
                impact = "positive"
                desc = f"Healthy {round(savings_rate)}% savings rate. Approaching standard 20% wealth-building targets."
                positive_highlights.append(f"Consistent savings: {round(savings_rate)}% of monthly inflows preserved.")
            elif savings_rate >= 5.0:
                s_pts = 14
                impact = "neutral"
                desc = f"Modest {round(savings_rate)}% savings buffer. Trimming subscriptions can elevate this to 15%+."
                actionable_improvements.append("Increase monthly savings rate by auditing zombie subscriptions and takeout fees.")
            elif savings_rate > 0:
                s_pts = 8
                impact = "negative"
                desc = f"Thin {round(savings_rate)}% savings margin. Outflows are very close to total inflows."
                risk_factors.append("Low monthly savings margin puts you at risk of unexpected cash shocks.")
                actionable_improvements.append("Aim for a 10% emergency savings buffer by curbing non-essential spending.")
            else:
                s_pts = 0
                impact = "negative"
                desc = "Outflows exceed or equal total monthly inflows (0% savings rate)."
                risk_factors.append("Operating at net cash deficit this month.")
                actionable_improvements.append("Eliminate redundant recurring expenses immediately to prevent debt accumulation.")

        factors.append(HealthScoreFactor(
            factor_name="Monthly Savings Rate",
            score=s_pts,
            max_score=30,
            impact=impact,
            description=desc
        ))

        # 2. Budget Adherence Factor (Max 25 pts)
        # Check actual configured overall budget
        overall_budget = (
            db.query(Budget)
            .filter(Budget.business_id == business.id, Budget.category == "Overall")
            .first()
        )
        # Check aggregate category budgets if overall is not set
        cat_budgets = (
            db.query(Budget)
            .filter(Budget.business_id == business.id, Budget.category != "Overall")
            .all()
        )
        cat_budget_sum = sum(b.monthly_limit for b in cat_budgets if b.monthly_limit) if cat_budgets else 0.0

        budget_limit = None
        budget_source = None

        if overall_budget and overall_budget.monthly_limit and overall_budget.monthly_limit > 0:
            budget_limit = float(overall_budget.monthly_limit)
            budget_source = "configured monthly budget"
        elif cat_budget_sum > 0:
            budget_limit = float(cat_budget_sum)
            budget_source = "aggregate category budgets"
        elif business.monthly_baseline_revenue and float(business.monthly_baseline_revenue) > 0:
            budget_limit = float(business.monthly_baseline_revenue)
            budget_source = "monthly baseline revenue ceiling"

        spent = analysis.total_expenses

        if budget_limit is None:
            # Explicit insufficient data state - no arbitrary fallback numbers
            b_pts = 0
            b_impact = "neutral"
            b_desc = "No budget configured (Insufficient Data): Set a monthly budget to calculate adherence."
            risk_factors.append("No spending ceiling configured: Outflows are untracked against spending targets.")
            actionable_improvements.append("Configure a monthly spending budget in the Budget Manager to enable budget adherence scoring.")
            has_sufficient_data = False
            missing_data_reasons.append("No configured budget or monthly baseline revenue limit found.")
        elif spent == 0:
            b_pts = 25
            b_impact = "positive"
            b_desc = f"Zero expenses recorded against ${budget_limit:,.2f} {budget_source} (0% utilized)."
            positive_highlights.append(f"Under budget: Full ${budget_limit:,.2f} cushion remaining this month.")
        else:
            util_pct = (spent / budget_limit * 100) if budget_limit > 0 else 0.0
            if util_pct <= 75.0:
                b_pts = 25
                b_impact = "positive"
                b_desc = f"Outstanding budget control: Used only {round(util_pct)}% of {budget_source} (${spent:,.2f} of ${budget_limit:,.2f})."
                positive_highlights.append(f"Under budget: {round(100 - util_pct)}% remaining capacity this month.")
            elif util_pct <= 95.0:
                b_pts = 20
                b_impact = "positive"
                b_desc = f"Disciplined pacing: Consumed {round(util_pct)}% of {budget_source}."
            elif util_pct <= 100.0:
                b_pts = 12
                b_impact = "neutral"
                b_desc = f"At budget capacity: Consumed {round(util_pct)}% of {budget_source}."
                actionable_improvements.append("Pace remaining discretionary expenses to avoid breaking monthly budget.")
            else:
                b_pts = 4
                b_impact = "negative"
                b_desc = f"Over budget: Spending exceeded {budget_source} by {round(util_pct - 100)}% (${round(spent - budget_limit, 2)})."
                risk_factors.append(f"Spending has broken past your monthly budget target by ${round(spent - budget_limit, 2)}.")
                actionable_improvements.append("Adjust budget limit or pause non-critical discretionary commitments.")

        factors.append(HealthScoreFactor(
            factor_name="Budget Adherence",
            score=b_pts,
            max_score=25,
            impact=b_impact,
            description=b_desc
        ))

        # 3. Subscription & Recurring Burden (Max 25 pts)
        rec_spend = analysis.recurring_expenses_total
        income = analysis.total_income

        if income == 0 and rec_spend == 0:
            r_pts = 15
            r_impact = "neutral"
            r_desc = "No recurring subscription commitments recorded for this period."
        elif income == 0 and rec_spend > 0:
            r_pts = 4
            r_impact = "negative"
            r_desc = f"${rec_spend:,.2f}/mo in recurring commitments with zero recorded monthly income."
            risk_factors.append("Recurring subscription commitments active without recorded income inflows.")
            actionable_improvements.append("Audit active recurring subscriptions to reduce fixed commitments.")
        else:
            sub_ratio = (rec_spend / income * 100) if income > 0 else 0.0
            if sub_ratio <= 8.0:
                r_pts = 25
                r_impact = "positive"
                r_desc = f"Lean recurring commitments: Fixed bills consume only {round(sub_ratio, 1)}% of income."
                positive_highlights.append("Low fixed expense overhead gives you strong financial agility.")
            elif sub_ratio <= 18.0:
                r_pts = 18
                r_impact = "neutral"
                r_desc = f"Moderate recurring commitments: Fixed expenses account for {round(sub_ratio, 1)}% of income."
            elif sub_ratio <= 30.0:
                r_pts = 10
                r_impact = "negative"
                r_desc = f"Heavy recurring commitments: Fixed bills consume {round(sub_ratio, 1)}% of monthly income."
                risk_factors.append(f"High recurring bill burden ({round(sub_ratio, 1)}% of income) locks up cash flow.")
                actionable_improvements.append("Review apps and streaming subscriptions to consolidate overlapping services.")
            else:
                r_pts = 4
                r_impact = "negative"
                r_desc = f"Severe recurring burden: {round(sub_ratio, 1)}% of income is committed before discretionary spending."
                risk_factors.append("Critically high recurring obligations limit financial flexibility.")
                actionable_improvements.append("Cancel unused streaming, software, and club memberships to lower fixed monthly burn.")

        factors.append(HealthScoreFactor(
            factor_name="Recurring Expense Burden",
            score=r_pts,
            max_score=25,
            impact=r_impact,
            description=r_desc
        ))

        # 4. Liquidity & Reserve Buffer (Max 20 pts)
        cash_reserves = float(business.current_cash_reserves or 0.0)
        monthly_burn = float(analysis.total_expenses or 0.0)

        if monthly_burn == 0.0:
            if cash_reserves > 0:
                l_pts = 20
                l_impact = "positive"
                l_desc = f"Solid cash reserve: ${cash_reserves:,.2f} liquid cushion with zero recorded monthly burn."
                positive_highlights.append(f"Resilient safety net: ${cash_reserves:,.2f} liquid reserve buffer.")
            else:
                l_pts = 0
                l_impact = "neutral"
                l_desc = "No cash reserves or monthly expense burn rate recorded."
                has_sufficient_data = False
                missing_data_reasons.append("No liquid cash reserves or monthly expense burn rate recorded.")
        else:
            months_runway = cash_reserves / monthly_burn
            if months_runway >= 3.0:
                l_pts = 20
                l_impact = "positive"
                l_desc = f"Solid cash reserve: {round(months_runway, 1)} months of emergency spending cushion available."
                positive_highlights.append(f"Resilient safety net: {round(months_runway, 1)} months of operating liquidity.")
            elif months_runway >= 1.0:
                l_pts = 12
                l_impact = "neutral"
                l_desc = f"Adequate reserve buffer: {round(months_runway, 1)} months of expenses covered."
                actionable_improvements.append("Build emergency reserves to 3 full months of living costs.")
            else:
                l_pts = 5
                l_impact = "negative"
                l_desc = f"Vulnerable liquidity: Only {round(months_runway * 30)} days of living costs in reserve."
                risk_factors.append("Emergency fund buffer is below 1 month of expenses.")
                actionable_improvements.append("Channel monthly net savings directly into a high-yield emergency cash pool.")

        factors.append(HealthScoreFactor(
            factor_name="Liquidity & Safety Buffer",
            score=l_pts,
            max_score=20,
            impact=l_impact,
            description=l_desc
        ))

        # Total Score
        total_score = sum(f.score for f in factors)

        if total_score >= 80:
            rating = "Excellent"
        elif total_score >= 65:
            rating = "Good"
        elif total_score >= 50:
            rating = "Fair"
        else:
            rating = "Needs Attention"

        disclaimer = (
            "SubWise AI Financial Health Score is an informational wellness metric calculated from "
            "your recorded cash flows, budget compliance, and recurring bill commitments. "
            "It is not a credit score, regulatory rating, or professional investment appraisal."
        )

        return ExplainableHealthScore(
            score=total_score,
            rating=rating,
            factors=factors,
            positive_highlights=positive_highlights[:3],
            risk_factors=risk_factors[:3],
            actionable_improvements=actionable_improvements[:3],
            disclaimer=disclaimer,
            has_sufficient_data=has_sufficient_data,
            missing_data_reasons=missing_data_reasons
        )

