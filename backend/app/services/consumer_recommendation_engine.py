from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.expense import Expense
from app.schemas.consumer_intelligence import (
    ActionableSavingsRecommendation,
    SpendingAnalysisResult
)

class ConsumerRecommendationEngine:
    @classmethod
    def generate_recommendations(
        cls,
        business: BusinessProfile,
        analysis: SpendingAnalysisResult,
        subscriptions: List[Subscription],
        db: Session
    ) -> List[ActionableSavingsRecommendation]:
        recs: List[ActionableSavingsRecommendation] = []

        # 1. Overlapping Streaming / Media Services
        streaming_keywords = ["netflix", "hulu", "disney", "max", "hbo", "paramount", "peacock", "apple tv", "youtube premium", "spotify"]
        active_subs = [s for s in subscriptions if (s.status or "").lower() != "cancelled"]

        matched_streaming = [
            s for s in active_subs
            if any(k in (s.vendor_name or "").lower() for k in streaming_keywords)
        ]

        if len(matched_streaming) >= 2:
            names = [s.vendor_name for s in matched_streaming]
            total_monthly = sum(float(s.latest_amount or 0.0) for s in matched_streaming)
            # Consolidate / pause lowest active
            est_monthly = round(total_monthly * 0.40, 2)
            recs.append(ActionableSavingsRecommendation(
                id="rec_overlap_streaming",
                title=f"Consolidate {len(matched_streaming)} Overlapping Streaming Subscriptions",
                explanation=f"You are actively subscribed to {', '.join(names)}. Most households watch one primary service at a time.",
                supporting_evidence=f"${round(total_monthly, 2)}/mo total commitment across {len(matched_streaming)} streaming providers.",
                monthly_savings=est_monthly,
                annual_savings=round(est_monthly * 12, 2),
                confidence="High",
                priority="High",
                action_type="CANCEL_OVERLAP",
                recommended_action="Rotate services by month or consolidate under one family plan to eliminate overlapping monthly charges.",
                category="Subscriptions"
            ))

        # 2. Check for Category Spikes from Spending Analysis
        for spike in analysis.mom_changes:
            if spike.is_spike and spike.category in ("Food & Groceries", "Shopping", "Entertainment"):
                est_m = round(spike.dollar_change * 0.50, 2)
                recs.append(ActionableSavingsRecommendation(
                    id=f"rec_spike_{spike.category.lower().replace(' ', '_').replace('&', 'and')}",
                    title=f"Curb {spike.category} Surge (+{round(spike.percent_change)}% MoM)",
                    explanation=f"Spending in {spike.category} jumped from ${spike.prior_month_amount} to ${spike.current_month_amount}.",
                    supporting_evidence=f"+${spike.dollar_change} excess outlay this month compared to your previous billing period.",
                    monthly_savings=est_m,
                    annual_savings=round(est_m * 12, 2),
                    confidence="High",
                    priority="Medium",
                    action_type="CURB_SPIKE",
                    recommended_action=f"Set a weekly spending cap on {spike.category} to normalize outlays back to baseline.",
                    category=spike.category
                ))

        # 3. Annual Billing Switch Opportunity
        monthly_cadence_subs = [
            s for s in active_subs
            if (s.cadence or "").lower() in ("monthly", "month") and float(s.latest_amount or 0.0) >= 12.0
        ]
        if monthly_cadence_subs:
            top_sub = max(monthly_cadence_subs, key=lambda s: float(s.latest_amount or 0.0))
            amt = float(top_sub.latest_amount or 0.0)
            annual_discount_save = round(amt * 0.16, 2) # Typical 2 months free / 16% discount
            recs.append(ActionableSavingsRecommendation(
                id=f"rec_annual_{top_sub.id or 'sub'}",
                title=f"Switch {top_sub.vendor_name} to Annual Pre-Pay",
                explanation=f"Paying monthly for {top_sub.vendor_name} costs ${amt * 12:.2f}/year. Providers typically offer 15–20% off for annual prepayment.",
                supporting_evidence=f"Current billing: ${amt:.2f}/mo. Annualized: ${amt * 12:.2f}/yr.",
                monthly_savings=annual_discount_save,
                annual_savings=round(annual_discount_save * 12, 2),
                confidence="High",
                priority="Low",
                action_type="ANNUAL_DISCOUNT",
                recommended_action=f"Navigate to {top_sub.vendor_name} billing settings and select 'Pay Annually' to claim the discount.",
                category="Subscriptions"
            ))

        # 4. Supermarket / Grocery Price Optimization (Household & Individual)
        grocery_spend = next((c.current_month_amount for c in analysis.mom_changes if c.category == "Food & Groceries"), 0.0)
        if grocery_spend >= 300.0:
            est_save = round(grocery_spend * 0.14, 2) # Wholesale club staple savings
            recs.append(ActionableSavingsRecommendation(
                id="rec_grocery_wholesale",
                title="Wholesale Club Staple Arbitrage",
                explanation="Purchasing household paper products, non-perishables, and pantry staples in bulk averages 14% savings over standard supermarkets.",
                supporting_evidence=f"${round(grocery_spend, 2)} recorded on Food & Groceries this month.",
                monthly_savings=est_save,
                annual_savings=round(est_save * 12, 2),
                confidence="Medium",
                priority="Medium",
                action_type="SWITCH_TIER",
                recommended_action="Buy shelf-stable items and pantry goods in monthly bulk runs at Costco or Sam's Club instead of frequent local trips.",
                category="Food & Groceries"
            ))

        # 5. Fallback recommendation if data is brand new
        if not recs:
            recs.append(ActionableSavingsRecommendation(
                id="rec_general_budget",
                title="Establish 50/30/20 Budget Guidelines",
                explanation="Allocate 50% of income to living essentials, 30% to personal discretionary, and lock 20% into savings.",
                supporting_evidence=f"Current savings rate: {analysis.savings_rate_percent}%. Target standard benchmark: 20%.",
                monthly_savings=round(analysis.total_income * 0.05, 2),
                annual_savings=round(analysis.total_income * 0.05 * 12, 2),
                confidence="Medium",
                priority="Medium",
                action_type="SWITCH_TIER",
                recommended_action="Set up category limits in the Budget Manager to maintain clear guardrails for discretionary outlays.",
                category="Other"
            ))

        return recs

