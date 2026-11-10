import datetime
from typing import List, Dict, Any, Optional, Tuple
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.schemas.financial_intelligence import (
    FinancialIntelligenceOverview,
    HistoricalActuals,
    ForwardCommitments,
    ProjectedEstimates,
    FinancialHealthIndex,
    FinancialRiskItem,
)
from app.services.forecast_engine import ForecastEngine
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer
from app.services.ai_advisor import AIAdvisor


class FinancialIntelligenceEngine:
    """
    Stage 5: Financial Intelligence & Business Insights Engine.

    Principles:
    1. Assembles a provider-independent structured financial overview from verified
       ForecastEngine, SubscriptionExpenseAnalyzer, and RecommendationEngine outputs.
    2. Calculates a transparent Financial Health Index using a documented scoring
       methodology grounded in operating metrics.
    3. Identifies and explains financial risks with supporting ledger evidence.
    4. Generates an AI-enhanced monthly briefing via AIAdvisor (falls back to
       deterministic synthesis when no LLM provider is configured).
    5. Never fabricates amounts, invents vendors, or claims LLM capabilities
       not implemented.
    """

    # Health scoring weights (total: 100 points)
    SCORE_WEIGHTS = {
        "subscription_burden_ratio":  30,  # Points lost if sub/rev ratio is high
        "net_cashflow_positive":      25,  # Points if net monthly cash flow positive
        "runway_adequacy":            25,  # Points based on estimated runway months
        "renewal_concentration_risk": 10,  # Points lost for high concentration
        "data_sufficiency":           10,  # Points for verified data quality
    }

    SCORING_METHODOLOGY = (
        "Financial Health Index is composed of four deterministic components drawn from verified PayPal ledger data: "
        "(1) Subscription Burden Ratio — 30 pts: how much confirmed software overhead consumes operating sales; "
        "(2) Net Cash Flow — 25 pts: whether monthly outflows exceed verified inflows; "
        "(3) Cash Runway Adequacy — 25 pts: estimated months of liquidity based on verified starting cash and burn rate; "
        "(4) Renewal Concentration Risk — 10 pts: whether upcoming renewal clustering creates lump-sum liquidity spikes; "
        "(5) Data Sufficiency — 10 pts: quality and volume of underlying evidence. "
        "Scores are only assigned when sufficient ledger evidence exists; a score of None indicates insufficient baseline data."
    )

    @classmethod
    def _extract_reporting_period(cls, transactions: List[Transaction]) -> Tuple[Optional[str], Optional[str]]:
        """Returns (start_date_str, end_date_str) of valid operating transaction history."""
        dates = [
            tx.transaction_date for tx in transactions
            if tx.transaction_date and (tx.status or "").upper() == "COMPLETED"
        ]
        if not dates:
            return None, None
        return (min(dates).strftime("%Y-%m-%d"), max(dates).strftime("%Y-%m-%d"))

    @classmethod
    def _build_risk_items(
        cls,
        forecast: Dict[str, Any],
        subscriptions: List[Subscription],
        hist_rev: float,
        confirmed_commit: float,
    ) -> List[FinancialRiskItem]:
        """
        Identifies financial risk items from forecast intelligence and subscription metadata.
        Only generates a risk when supporting evidence exists in the data.
        """
        risks: List[FinancialRiskItem] = []
        status = forecast.get("status", "insufficient_data")
        monthly_scheduled = forecast.get("monthly_scheduled_subscription_totals", [])
        payment_calendar = forecast.get("payment_calendar", [])
        forecast_timeline = forecast.get("forecast") or []

        active_subs = [s for s in subscriptions if s.status != "cancelled"]

        # --- Risk 1: Price Creep on Confirmed Subscriptions ---
        for sub in active_subs:
            pct = float(sub.price_change_pct or 0.0)
            det_type = getattr(sub, "detection_type", "confirmed")
            is_var = getattr(sub, "billing_type", "fixed") == "variable"
            if pct >= 15.0 and det_type == "confirmed" and not is_var:
                creep_diff = sub.latest_amount - sub.average_amount
                risks.append(FinancialRiskItem(
                    risk_type="PRICE_CREEP",
                    severity="high" if pct >= 20.0 else "medium",
                    title=f"Price Escalation: {sub.vendor_name} (+{pct:.1f}%)",
                    description=f"{sub.vendor_name} has experienced an unannounced billing increase of {pct:.1f}% across recorded cycles.",
                    supporting_evidence=(
                        f"Historical average: ${sub.average_amount:.2f}; Current charge: ${sub.latest_amount:.2f}. "
                        f"Monthly escalation: +${creep_diff:.2f} vs baseline."
                    ),
                    mitigation_action="Request a rate review and lock with the supplier billing team before the next renewal cycle."
                ))

        # --- Risk 2: High Subscription Burden on Revenue ---
        if hist_rev > 0 and confirmed_commit > 0:
            ratio = confirmed_commit / hist_rev
            if ratio >= 0.25:
                risks.append(FinancialRiskItem(
                    risk_type="HIGH_SUBSCRIPTION_BURDEN",
                    severity="high" if ratio >= 0.35 else "medium",
                    title=f"High SaaS-to-Revenue Ratio ({ratio * 100:.1f}%)",
                    description=(
                        f"Monthly confirmed software obligations represent {ratio * 100:.1f}% of operating revenue, "
                        f"exceeding the recommended 15–20% ceiling."
                    ),
                    supporting_evidence=(
                        f"Confirmed monthly commitments: ${confirmed_commit:.2f}. "
                        f"Verified monthly operating revenue: ${hist_rev:.2f}."
                    ),
                    mitigation_action="Conduct a portfolio audit of Tier 3 discretionary subscriptions and implement a SaaS acquisition freeze."
                ))

        # --- Risk 3: Renewal Concentration Spikes ---
        for m_tot in monthly_scheduled:
            is_high = m_tot.get("is_high_concentration", False)
            c_amt = m_tot.get("total_confirmed_amount", 0.0)
            c_count = m_tot.get("confirmed_renewals_count", 0)
            m_name = m_tot.get("month_name", "")
            if is_high and c_count >= 2:
                risks.append(FinancialRiskItem(
                    risk_type="RENEWAL_CONCENTRATION",
                    severity="high",
                    title=f"Renewal Cluster Risk in {m_name} ({c_count} renewals, ${c_amt:.2f})",
                    description=(
                        f"Multiple subscriptions renewing simultaneously in {m_name} create a "
                        f"concentrated single-month outflow of ${c_amt:.2f}."
                    ),
                    supporting_evidence=(
                        f"{c_count} confirmed renewals scheduled in {m_name} totalling ${c_amt:.2f}. "
                        + (f"Consumes {m_tot.get('revenue_commitment_pct', 0):.1f}% of projected revenue." if hist_rev > 0 else "")
                    ),
                    mitigation_action="Contact vendor account managers to stagger billing anchor dates across adjacent months."
                ))
            # Only flag the first concentration month to avoid alert fatigue
            if is_high:
                break

        # --- Risk 4: Projected Cash Deficit ---
        if status != "insufficient_data":
            for pt in forecast_timeline:
                if pt.get("is_cash_depleted", False) or (
                    pt.get("projected_closing_cash_balance", 1.0) is not None
                    and pt.get("projected_closing_cash_balance", 1.0) <= 0
                ):
                    m_name = pt.get("month_name", "a projected month")
                    bal = pt.get("projected_closing_cash_balance", 0.0)
                    risks.append(FinancialRiskItem(
                        risk_type="PROJECTED_CASH_DEFICIT",
                        severity="high",
                        title=f"Projected Liquidity Deficit in {m_name}",
                        description=(
                            f"Baseline forecast projects closing cash balance falling to ${bal:.2f} in {m_name}, "
                            f"indicating operating disbursements exceed inflows."
                        ),
                        supporting_evidence=(
                            f"Forecast baseline uses ${hist_rev:.2f}/mo verified revenue against combined "
                            f"confirmed subscription and operating expense burn. Depletion occurs in {m_name}."
                        ),
                        mitigation_action="Freeze discretionary SaaS acquisition and audit Tier 3 subscriptions immediately."
                    ))
                    break  # Flag only the first deficit month

        # --- Risk 5: Approaching Large Annual Renewals ---
        for pmt in forecast.get("upcoming_subscription_payments", []):
            cadence = (pmt.get("billing_frequency") or "").lower()
            amt = float(pmt.get("expected_payment_amount") or 0.0)
            if cadence == "annual" and pmt.get("detection_type") == "confirmed" and amt >= 500.0:
                risks.append(FinancialRiskItem(
                    risk_type="LARGE_ANNUAL_OBLIGATION",
                    severity="medium",
                    title=f"Large Annual Renewal Due: {pmt.get('vendor_name')} (${amt:,.2f})",
                    description=(
                        f"A contractual annual subscription renewal of ${amt:,.2f} for {pmt.get('vendor_name')} "
                        f"is due on {pmt.get('expected_payment_date', 'an upcoming date')}."
                    ),
                    supporting_evidence=(
                        f"Scheduled renewal on {pmt.get('expected_payment_date')}: ${amt:,.2f} single-day disbursement. "
                        f"Annual renewals are verified from confirmed recurring billing history."
                    ),
                    mitigation_action=(
                        f"Audit seat utilization before {pmt.get('expected_payment_date')} and ensure liquid reserves cover ${amt:,.2f}."
                    )
                ))

        # --- Risk 6: Potential Trial Subscriptions ---
        potential_subs = [s for s in active_subs if getattr(s, "detection_type", "confirmed") == "potential"]
        if potential_subs:
            total_potential = sum(s.latest_amount for s in potential_subs)
            vendor_names = ", ".join(s.vendor_name for s in potential_subs[:3])
            risks.append(FinancialRiskItem(
                risk_type="TRIAL_REVIEW",
                severity="low",
                title=f"{len(potential_subs)} Potential Trial Subscription(s) Detected",
                description=(
                    f"First-time payments detected for {len(potential_subs)} recognized SaaS vendor(s) ({vendor_names}). "
                    f"These require team verification before auto-renewal commitments are made."
                ),
                supporting_evidence=(
                    f"Total first-cycle payment amount: ${total_potential:.2f}. "
                    f"Awaiting second billing cycle to confirm as recurring contracts."
                ),
                mitigation_action="Verify with team leads whether these are approved ongoing purchases or one-time trial evaluations."
            ))

        # Sort by severity: high first
        severity_order = {"high": 0, "medium": 1, "low": 2}
        risks.sort(key=lambda r: severity_order.get(r.severity, 3))
        return risks

    @classmethod
    def _calculate_health_index(
        cls,
        status: str,
        hist_rev: float,
        confirmed_commit: float,
        net_monthly_flow: float,
        runway_months: Optional[float],
        has_concentration_risk: bool,
        operating_months: int,
    ) -> FinancialHealthIndex:
        """
        Calculates a transparent Financial Health Index score with documented methodology.
        Returns score=None if insufficient data to score.
        """
        if status == "insufficient_data":
            return FinancialHealthIndex(
                score=None,
                status_label="Unscored – Insufficient Evidence",
                scoring_breakdown=None,
                scoring_methodology=cls.SCORING_METHODOLOGY,
            )

        score = 0
        breakdown: Dict[str, Any] = {}

        # Component 1: Subscription Burden Ratio (0–30 pts)
        if hist_rev > 0:
            ratio = confirmed_commit / hist_rev
            if ratio <= 0.10:
                sub_pts = 30
            elif ratio <= 0.20:
                sub_pts = 24
            elif ratio <= 0.30:
                sub_pts = 15
            elif ratio <= 0.40:
                sub_pts = 7
            else:
                sub_pts = 0
        else:
            sub_pts = 15  # Neutral if no revenue data
        score += sub_pts
        breakdown["subscription_burden_ratio_score"] = sub_pts
        breakdown["subscription_burden_ratio_max"] = 30

        # Component 2: Net Cash Flow Positive (0–25 pts)
        if net_monthly_flow > 0:
            cf_pts = 25
        elif net_monthly_flow == 0:
            cf_pts = 12
        else:
            cf_pts = 0
        score += cf_pts
        breakdown["net_cashflow_score"] = cf_pts
        breakdown["net_cashflow_max"] = 25

        # Component 3: Runway Adequacy (0–25 pts)
        if runway_months is None:
            rw_pts = 10  # Neutral unknown
        elif runway_months >= 12.0:
            rw_pts = 25
        elif runway_months >= 6.0:
            rw_pts = 18
        elif runway_months >= 3.0:
            rw_pts = 10
        else:
            rw_pts = 0
        score += rw_pts
        breakdown["runway_adequacy_score"] = rw_pts
        breakdown["runway_adequacy_max"] = 25

        # Component 4: Renewal Concentration Risk (0–10 pts)
        conc_pts = 0 if has_concentration_risk else 10
        score += conc_pts
        breakdown["renewal_concentration_score"] = conc_pts
        breakdown["renewal_concentration_max"] = 10

        # Component 5: Data Sufficiency (0–10 pts)
        if operating_months >= 3:
            data_pts = 10
        elif operating_months >= 1:
            data_pts = 5
        else:
            data_pts = 0
        score += data_pts
        breakdown["data_sufficiency_score"] = data_pts
        breakdown["data_sufficiency_max"] = 10

        # Determine Label
        if score >= 80:
            label = "Financially Resilient"
        elif score >= 65:
            label = "Moderate Risk – Monitor Closely"
        elif score >= 45:
            label = "Elevated Risk – Action Required"
        else:
            label = "Critical – Immediate Triage Required"

        return FinancialHealthIndex(
            score=score,
            status_label=label,
            scoring_breakdown=breakdown,
            scoring_methodology=cls.SCORING_METHODOLOGY,
        )

    @classmethod
    def generate_overview(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
    ) -> FinancialIntelligenceOverview:
        """
        Assembles a complete Financial Intelligence Overview for the business.
        """
        # 1. Generate base forecast (all calendar-aware intelligence)
        forecast = ForecastEngine.generate_forecast(
            business=business,
            subscriptions=subscriptions,
            transactions=transactions,
            forecast_months=6,
        )

        status = forecast.get("status", "insufficient_data")
        hist_rev = forecast.get("historical_monthly_operating_revenue", 0.0)
        hist_non_sub = forecast.get("historical_monthly_non_sub_expenses", 0.0)
        hist_sub = forecast.get("historical_monthly_subscription_expenses", 0.0)
        confirmed_commit = forecast.get("confirmed_monthly_subscription_commitments", 0.0)
        potential_commit = forecast.get("potential_monthly_subscription_commitments", 0.0)
        verified_cash = forecast.get("verified_starting_cash")
        has_verified_cash = forecast.get("has_verified_cash", False)
        missing_reasons = forecast.get("missing_data_reasons", [])
        forecast_timeline = forecast.get("forecast") or []
        monthly_scheduled = forecast.get("monthly_scheduled_subscription_totals", [])
        upcoming_payments = forecast.get("upcoming_subscription_payments", [])
        operating_months = sum(
            1 for _ in [tx for tx in transactions if (tx.status or "").upper() == "COMPLETED"]
        )
        # Better: count distinct calendar months from valid transactions
        valid_txs = [tx for tx in transactions if ForecastEngine.is_valid_operating(tx) and tx.transaction_date]
        month_keys = set(f"{tx.transaction_date.year}-{tx.transaction_date.month:02d}" for tx in valid_txs)
        operating_months = len(month_keys)

        # 2. Reporting period
        period_start, period_end = cls._extract_reporting_period(transactions)
        if period_start and period_end:
            reporting_period = f"{period_start} to {period_end}"
        else:
            reporting_period = "No verified transaction history"

        # 3. Cash provenance note
        total_net = sum(float(tx.net_amount if tx.net_amount is not None else tx.gross_amount) for tx in [t for t in transactions if (t.status or "").upper() == "COMPLETED"])
        if has_verified_cash and verified_cash is not None:
            cash_provenance = (
                f"Net sum of all settled PayPal ledger transactions (${verified_cash:,.2f}). "
                f"Note: This reflects net PayPal transaction flows, not an independently verified PayPal Account Balance. "
                f"Actual account balance may differ due to fees, holds, or transfers not reflected in this export."
            )
            is_ledger_derived = True
        elif business.current_cash_reserves and business.current_cash_reserves > 0:
            cash_provenance = "Business Profile declared reserves (not independently verified against PayPal Account Balance)."
            is_ledger_derived = False
        else:
            cash_provenance = "No verified cash basis available."
            is_ledger_derived = False

        paypal_balance_note = (
            "IMPORTANT: The displayed cash figure is derived from net PayPal transaction flows in this dataset. "
            "It is NOT equivalent to your verified PayPal Account Balance, which may include unreported holds, "
            "pending transactions, fees, or inter-account transfers. Always verify your actual balance in PayPal."
        )

        # 4. Historical Actuals
        net_flow = round(hist_rev - (hist_non_sub + confirmed_commit), 2)
        historical_actuals = HistoricalActuals(
            reporting_period_start=period_start,
            reporting_period_end=period_end,
            operating_months_analyzed=operating_months,
            historical_monthly_operating_revenue=hist_rev,
            historical_monthly_operating_expenses=round(hist_non_sub + hist_sub, 2),
            historical_monthly_subscription_expenses=hist_sub,
            historical_monthly_non_sub_expenses=hist_non_sub,
            historical_monthly_net_cash_flow=net_flow,
            verified_available_cash=verified_cash if has_verified_cash else None,
            cash_provenance=cash_provenance,
            is_cash_ledger_derived=is_ledger_derived,
            paypal_balance_note=paypal_balance_note,
        )

        # 5. Forward Commitments
        upcoming_60d_count = sum(1 for p in upcoming_payments if p.get("month_index", 99) <= 2)
        upcoming_60d_amt = sum(
            float(p.get("expected_payment_amount") or 0.0)
            for p in upcoming_payments
            if p.get("month_index", 99) <= 2 and p.get("detection_type") == "confirmed"
        )
        forward_commitments = ForwardCommitments(
            confirmed_monthly_subscription_commitments=confirmed_commit,
            confirmed_annual_subscription_commitments=round(confirmed_commit * 12.0, 2),
            potential_monthly_subscription_commitments=potential_commit,
            potential_annual_subscription_commitments=round(potential_commit * 12.0, 2),
            upcoming_renewals_count_next_60_days=upcoming_60d_count,
            upcoming_renewals_amount_next_60_days=round(upcoming_60d_amt, 2),
        )

        # 6. Projected Estimates
        lowest_proj: Optional[float] = None
        shortfall_month: Optional[str] = None
        for pt in forecast_timeline:
            bal = pt.get("projected_closing_cash_balance")
            if bal is not None:
                if lowest_proj is None or bal < lowest_proj:
                    lowest_proj = bal
            if pt.get("is_cash_depleted", False) and shortfall_month is None:
                shortfall_month = pt.get("month_name")

        # Runway calc
        monthly_burn = round((hist_non_sub + confirmed_commit) - hist_rev, 2)
        if has_verified_cash and verified_cash is not None and monthly_burn > 0:
            runway_months_val: Optional[float] = round(verified_cash / monthly_burn, 1)
        elif has_verified_cash and verified_cash is not None and monthly_burn <= 0:
            runway_months_val = None  # Cash-flow positive
        else:
            runway_months_val = None

        if status == "insufficient_data":
            runway_status = "Indeterminate"
            runway_explanation = "Runway cannot be estimated without verified operating revenue and confirmed subscription commitments."
        elif monthly_burn <= 0:
            runway_status = "Cash-Flow Positive"
            runway_explanation = f"Operating inflows (${hist_rev:.2f}/mo) exceed total confirmed burn (${(hist_non_sub + confirmed_commit):.2f}/mo). No net depletion in baseline."
        elif runway_months_val is not None and runway_months_val >= 12:
            runway_status = "Adequate (12+ Months)"
            runway_explanation = f"At current burn of ${monthly_burn:.2f}/mo, estimated runway is {runway_months_val:.1f} months."
        elif runway_months_val is not None and runway_months_val >= 6:
            runway_status = "Moderate (6–12 Months)"
            runway_explanation = f"Runway estimated at {runway_months_val:.1f} months. Consider cost reduction to extend buffer."
        else:
            runway_status = "Critical (<6 Months)"
            runway_explanation = f"Runway critically short at {runway_months_val:.1f} months. Immediate expense reduction required."

        projected_estimates = ProjectedEstimates(
            forecast_months=6,
            projected_monthly_revenue_baseline=hist_rev,
            projected_monthly_net_cash_flow=net_flow,
            projected_lowest_cash_balance=lowest_proj,
            projected_shortfall_month=shortfall_month,
            estimated_runway_months=runway_months_val,
            runway_status=runway_status,
            runway_explanation=runway_explanation,
        )

        # 7. Risk Intelligence
        has_concentration = any(m.get("is_high_concentration", False) for m in monthly_scheduled)
        risk_items = cls._build_risk_items(forecast, subscriptions, hist_rev, confirmed_commit)

        # 8. Financial Health Index
        health_index = cls._calculate_health_index(
            status=status,
            hist_rev=hist_rev,
            confirmed_commit=confirmed_commit,
            net_monthly_flow=net_flow,
            runway_months=runway_months_val,
            has_concentration_risk=has_concentration,
            operating_months=operating_months,
        )

        # 9. Required records message for insufficient data
        required_records: List[str] = []
        if status == "insufficient_data":
            required_records = [
                "At least 2 months of verified PayPal operating revenue transactions (status: COMPLETED).",
                "At least 1 confirmed recurring subscription with two or more billing cycles.",
                "A verified starting cash balance from settled PayPal ledger activity or declared business reserves.",
            ]

        # 10. Key CFO actions (from risk items)
        key_actions = [r.mitigation_action for r in risk_items[:4]]
        if not key_actions:
            key_actions = [
                "Maintain subscription calendar monitoring for upcoming renewal dates.",
                "Review subscription-to-revenue ratio quarterly.",
            ]

        # 11. Monthly Briefing via AIAdvisor
        monthly_briefing = AIAdvisor.generate_monthly_briefing(
            company_name=business.company_name,
            reporting_period=reporting_period,
            status=status,
            historical_rev=hist_rev,
            historical_non_sub=hist_non_sub,
            historical_sub=hist_sub,
            confirmed_commit=confirmed_commit,
            potential_commit=potential_commit,
            verified_cash=verified_cash,
            cash_provenance=cash_provenance if has_verified_cash else "Not Verified",
            runway_months=runway_months_val,
            risks=[{"title": r.title, "supporting_evidence": r.supporting_evidence} for r in risk_items],
            key_actions=key_actions,
        )

        return FinancialIntelligenceOverview(
            business_id=business.id,
            company_name=business.company_name,
            data_sufficiency_status=status,
            missing_data_reasons=missing_reasons,
            required_records_for_analysis=required_records,
            historical_actuals=historical_actuals,
            forward_commitments=forward_commitments,
            projected_estimates=projected_estimates,
            financial_health_index=health_index,
            risk_intelligence=risk_items,
            monthly_briefing=monthly_briefing,
            transparency_disclosure=(
                "All financial figures are derived strictly from completed PayPal Sandbox ledger transactions. "
                "No amounts, vendors, or savings are invented. Projections are forward estimates using verified "
                "historical averages and are not guaranteed outcomes. The displayed cash balance reflects net "
                "PayPal transaction flows in this dataset — not an independently verified PayPal Account Balance. "
                "AI-generated briefing sections are labelled accordingly and do not modify underlying calculations."
            ),
        )

