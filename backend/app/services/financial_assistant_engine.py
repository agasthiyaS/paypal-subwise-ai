"""
Stage 7: Intelligent Financial Assistant Engine
Provides authenticated, evidence-grounded financial Q&A for SMBs.

Core Principles:
1. Zero Hallucination: Every financial figure is calculated deterministically from
   verified ledger records, payment schedules, or simulation formulas.
2. AI-Enhanced with Transparent Fallback: If external LLM (Gemini 1.5 Flash) is available,
   it interprets questions and explains structured facts under strict guardrails.
   If unavailable or rate-limited, the deterministic engine answers every supported intent.
3. Affordability & Simulation Integration: Questions like "Can I afford X?" route to
   RecommendationEngine.simulate_purchase rather than using LLM math.
4. Report Integration: Queries requesting report summaries route to ReportEngine.
5. Structured Evidence Cards: Responses include verifiable metrics, data types,
   provenance disclosures, and deep navigation links for the frontend.
"""
import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
import httpx

from app.config import settings
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    EvidenceCard,
    SuggestionItem,
    AssistantSuggestionsResponse,
)
from app.schemas.recommendation import PurchaseSimulationRequest
from app.services.forecast_engine import ForecastEngine
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer
from app.services.recommendation_engine import RecommendationEngine
from app.services.financial_intelligence_engine import FinancialIntelligenceEngine
from app.services.report_engine import ReportEngine
from app.services.vendor_comparison_service import VendorComparisonService
from app.services.smart_spending_service import SmartSpendingService


class FinancialAssistantEngine:

    @classmethod
    def is_llm_configured(cls) -> bool:
        """
        Safely detects whether a valid Gemini API key is configured.
        Never reveals the secret key in returns, logs, or error messages.
        Requires non-empty string, length >= 16, and not placeholder values.
        """
        raw_key = (settings.GEMINI_API_KEY or settings.LLM_API_KEY or "").strip()
        if not raw_key:
            return False
        if len(raw_key) < 16 or raw_key.lower().startswith(("your_", "my_", "test_", "placeholder", "subwise_")):
            return False
        return True

    @classmethod
    def get_starter_suggestions(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
    ) -> AssistantSuggestionsResponse:
        """
        Returns dynamic conversation starters tailored to the business's data sufficiency status.
        """
        confirmed_subs = [s for s in subscriptions if (s.status or "").lower() == "active"]
        valid_txs = [t for t in transactions if ForecastEngine.is_valid_operating(t)]
        is_llm = cls.is_llm_configured()

        if not valid_txs and not confirmed_subs:
            status = "insufficient_data"
            suggestions = [
                SuggestionItem(
                    prompt="What is my current financial status and what data is missing?",
                    category="health",
                    label="Data Status & Gaps"
                ),
                SuggestionItem(
                    prompt="Can I afford a new project management tool for $40/month?",
                    category="affordability",
                    label="Simulate $40/mo Tool"
                ),
                SuggestionItem(
                    prompt="How does PayPal SubWise track subscriptions and cash flow?",
                    category="reports",
                    label="Methodology Overview"
                ),
                SuggestionItem(
                    prompt="What starting cash balance is configured for my business?",
                    category="forecast",
                    label="Check Starting Cash"
                ),
            ]
        else:
            status = "sufficient_data" if len(valid_txs) >= 10 else "limited_data"
            suggestions = [
                SuggestionItem(
                    prompt="What are my upcoming subscription renewals over the next 30 days?",
                    category="subscriptions",
                    label="Upcoming Renewals"
                ),
                SuggestionItem(
                    prompt="What is our projected cash runway and monthly burn rate?",
                    category="forecast",
                    label="Cash Runway & Burn"
                ),
                SuggestionItem(
                    prompt="Can we afford to upgrade to an enterprise software plan for $150/month?",
                    category="affordability",
                    label="Simulate $150/mo Purchase"
                ),
                SuggestionItem(
                    prompt="Summarize our latest monthly financial report and operating cash flow.",
                    category="reports",
                    label="Monthly Financial Summary"
                ),
                SuggestionItem(
                    prompt="What is our financial health score and what risks should we watch?",
                    category="health",
                    label="Health Score & Risks"
                ),
            ]

        return AssistantSuggestionsResponse(
            suggestions=suggestions,
            data_sufficiency_status=status,
            llm_provider_configured=is_llm,
            active_engine="Google Gemini 1.5 Flash (Hybrid Augmentation)" if is_llm else "SubWise Deterministic Engine"
        )

    # -------------------------------------------------------------------------
    # Intent Detection & Query Parsing
    # -------------------------------------------------------------------------
    @classmethod
    def detect_intent(cls, message: str) -> str:
        """
        Classifies incoming user question into fintech intent categories.
        """
        m = message.lower().strip()

        # 1. Vendor Alternatives & Cheaper Plans (Phase 4)
        if any(p in m for p in [
            "cheaper alternative", "alternative to", "switch provider", "cheaper plan",
            "cheaper tier", "compare vendor", "find alternatives", "cheaper options",
            "alternatives for", "cheaper software", "cheaper streaming", "substitute",
            "cheaper alternatives", "lower tier"
        ]):
            return "VENDOR_ALTERNATIVES"

        # 2. Spending Breakdown & Top Outflows (Phase 3 & 4)
        if any(p in m for p in [
            "where did my money go", "where did most of my money go", "biggest expense",
            "top spending", "highest spending", "which category", "spending breakdown",
            "spending by category", "what did i spend the most on", "spending on groceries",
            "which expenses increased", "unusual spending"
        ]):
            return "SPENDING_BREAKDOWN"

        # 3. Budget Pacing & Health Status (Phase 3 & 4)
        if any(p in m for p in [
            "exceeding my budget", "over budget", "budget limit", "how much budget",
            "am i over budget", "budget status", "budget remaining", "budget cushion"
        ]):
            return "BUDGET_STATUS"

        # 4. Affordability / Purchase Simulation
        if any(p in m for p in [
            "can i afford", "can we afford", "should we buy", "should i buy",
            "can we buy", "can i buy", "what if we buy", "what if we subscribe",
            "simulate purchase", "afford a", "afford to buy", "afford new"
        ]):
            return "AFFORDABILITY_CHECK"

        # 2. Upcoming Renewals / Payment Calendar
        if any(p in m for p in [
            "renewal", "renewing", "upcoming payment", "next payment",
            "payment calendar", "due date", "when is my next", "next renewal",
            "payments due", "renewals next"
        ]):
            return "RENEWAL_CALENDAR"

        # 3. Forecast / Runway / Cash Burn
        if any(p in m for p in [
            "forecast", "runway", "cash flow", "burn rate", "closing balance",
            "run out of money", "projected balance", "how long will", "cash projection",
            "how many months of cash"
        ]):
            return "FORECAST_INQUIRY"

        # 4. Reports / Summary
        if any(p in m for p in [
            "monthly report", "report summary", "summarize report", "financial report",
            "expense report", "briefing", "executive summary", "generate report"
        ]):
            return "REPORT_SUMMARY"

        # 5. Financial Health & Risks
        if any(p in m for p in [
            "health score", "health index", "financial health", "risks", "critical risk",
            "risk intelligence", "how healthy", "financial score"
        ]):
            return "HEALTH_AND_RISKS"

        # 6. Recommendations & Actions
        if any(p in m for p in [
            "recommendation", "what should i do", "cfo action", "cut cost",
            "save money", "optimize spend", "action plan", "negotiate"
        ]):
            return "RECOMMENDATIONS"

        # 7. Operating Revenue
        if any(p in m for p in [
            "operating revenue", "how much revenue", "how much money do we make",
            "monthly revenue", "sales revenue", "top line", "gross income"
        ]):
            return "REVENUE_INQUIRY"

        # 8. Subscription Spend / Vendor Inquiry
        if any(p in m for p in [
            "subscription", "subscriptions", "spend on", "how much do i spend",
            "total software", "software cost", "vendor", "saas spend", "monthly sub"
        ]):
            return "SPEND_OVERVIEW"

        return "GENERAL_FINTECH"

    @classmethod
    def _parse_affordability_params(cls, message: str) -> Dict[str, Any]:
        """
        Extracts proposed vendor, amount, cadence, and purpose from natural language.
        Examples:
          - "Can I afford Notion for $20/month?" -> vendor='Notion', amount=20.0, cadence='monthly'
          - "Can we buy Salesforce for $300 a month?" -> vendor='Salesforce', amount=300.0, cadence='monthly'
          - "Can we afford an annual AWS tool for $1200/year?" -> vendor='AWS tool', amount=1200.0, cadence='annual'
        """
        clean_msg = message.replace(",", "")

        # Cadence detection
        cadence = "monthly"
        if re.search(r"\b(annually|annual|per year|a year|/yr|/year)\b", clean_msg, re.IGNORECASE):
            cadence = "annual"
        elif re.search(r"\b(quarterly|per quarter|a quarter|/qtr)\b", clean_msg, re.IGNORECASE):
            cadence = "quarterly"
        elif re.search(r"\b(weekly|per week|a week|/wk)\b", clean_msg, re.IGNORECASE):
            cadence = "weekly"

        # Amount extraction: $XX.XX or $XX or XX dollars or XX/mo
        amount = 0.0
        amt_match = re.search(r"\$([0-9]+(?:\.[0-9]{1,2})?)", clean_msg)
        if not amt_match:
            amt_match = re.search(r"([0-9]+(?:\.[0-9]{1,2})?)\s*(?:dollars|usd|\/mo|\/month|\/year|\/yr)", clean_msg, re.IGNORECASE)
        if not amt_match:
            amt_match = re.search(r"\bfor\s+([0-9]+(?:\.[0-9]{1,2})?)\b", clean_msg, re.IGNORECASE)

        if amt_match:
            try:
                amount = float(amt_match.group(1))
            except ValueError:
                amount = 0.0

        # Vendor extraction
        vendor = "Proposed Tool"
        vendor_match = re.search(
            r"(?:afford|buy|subscribe to|get)\s+(?:a |an |new )?([A-Za-z0-9\s\-]+?)\s+(?:for|costing|at|\$)",
            clean_msg,
            re.IGNORECASE
        )
        if vendor_match:
            candidate = vendor_match.group(1).strip()
            # clean noise
            candidate = re.sub(r"^(a|an|new|the|to|subscription|tool)\s+", "", candidate, flags=re.IGNORECASE).strip()
            if candidate and len(candidate) > 1 and len(candidate) < 40:
                vendor = candidate.title()
        else:
            # Check for words before "for $XX"
            v_match2 = re.search(r"([A-Za-z0-9\-]+)\s+for\s+\$", clean_msg, re.IGNORECASE)
            if v_match2:
                vendor = v_match2.group(1).strip().title()

        return {
            "proposed_vendor": vendor,
            "amount": amount,
            "cadence": cadence,
            "business_purpose": "Simulated via SubWise AI Assistant",
        }

    # -------------------------------------------------------------------------
    # Core Query Processing
    # -------------------------------------------------------------------------
    @classmethod
    def process_query(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
        request: AssistantQueryRequest,
    ) -> AssistantQueryResponse:
        """
        Coordinates intent classification, deterministic facts gathering,
        specialized simulation / report routing, and AI or deterministic synthesis.
        """
        message = request.message.strip()
        intent = cls.detect_intent(message)

        # 1. Fetch deterministic financial overview & ground truth facts
        overview = FinancialIntelligenceEngine.generate_overview(
            business=business,
            subscriptions=subscriptions,
            transactions=transactions,
        )
        data_status = overview.data_sufficiency_status
        hist_actuals = overview.historical_actuals
        forward_commit = overview.forward_commitments
        projected = overview.projected_estimates
        health = overview.financial_health_index
        risks = overview.risk_intelligence

        # Also get detailed forecast with calendar schedule
        forecast_data = ForecastEngine.generate_forecast(
            business=business,
            subscriptions=subscriptions,
            transactions=transactions,
            forecast_months=6,
        )

        company_name = business.company_name or "Your Business"
        disclaimer = (
            "SubWise AI is a decision-support assistant. All figures are derived strictly "
            "from connected PayPal transactions and deterministic forecasting formulas, not speculative forecasts."
        )

        # ---------------------------------------------------------------------
        # ROUTE 0A: VENDOR & ALTERNATIVE COMPARISON (Phase 4 AI Discovery)
        # ---------------------------------------------------------------------
        if intent == "VENDOR_ALTERNATIVES":
            matched = VendorComparisonService.search_alternatives(message)
            total_est_save = sum(item.recommended_alternative.estimated_monthly_savings for item in matched)

            card = EvidenceCard(
                title="Vendor Alternative Savings",
                data_type="projected",
                amount=total_est_save,
                currency="USD",
                details={
                    "alternatives_count": len(matched),
                    "annual_savings_potential": total_est_save * 12,
                    "top_match": matched[0].current_service_name if matched else "None",
                },
                navigation_link="/recommendations",
                badge_label=f"Save up to ${total_est_save:.2f}/mo",
                badge_status="success",
            )

            res_md = (
                f"### Economical Vendor Alternatives & Savings Analysis\n\n"
                f"Based on verified Q4 2026 pricing benchmarks, here are high-value alternatives for your recurring expenses:\n\n"
            )

            for item in matched[:3]:
                alt = item.recommended_alternative
                res_md += (
                    f"#### 🔍 **{item.current_service_name}** ({item.category})\n"
                    f"- **Current Reference Tier:** {item.current_tier} at **${item.current_price:.2f}/{item.current_frequency}**\n"
                    f"- **Recommended Alternative:** **{alt.name} — {alt.tier}** at **${alt.price:.2f}/{alt.billing_frequency}** (${alt.monthly_equivalent:.2f}/mo equivalent)\n"
                    f"- **Estimated Monthly Recapture:** **${alt.estimated_monthly_savings:.2f}/mo** (${alt.estimated_annual_savings:.2f}/year)\n"
                    f"- **Trade-offs / Caveats:** {'; '.join(alt.trade_offs)}\n\n"
                )

            res_md += f"> 💡 **Actionable Verdict:** Switching these services frees up an estimated **${total_est_save:.2f}/month** (${total_est_save * 12:.2f}/year) without sacrificing essential capabilities. Review the full catalog in [Savings Opportunities](/recommendations)."

            return AssistantQueryResponse(
                response_text=res_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Vendor Discovery Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Where did most of my money go this month?",
                    "How can I save $100 monthly?",
                    "What are my upcoming renewals?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 0B: SPENDING BREAKDOWN & TOP OUTFLOWS
        # ---------------------------------------------------------------------
        if intent == "SPENDING_BREAKDOWN":
            total_exp = hist_actuals.historical_monthly_operating_expenses
            sub_exp = forward_commit.confirmed_monthly_subscription_commitments
            card = EvidenceCard(
                title="Monthly Outflow Breakdown",
                data_type="actual",
                amount=total_exp,
                currency="USD",
                details={
                    "total_expenses": total_exp,
                    "subscription_expenses": sub_exp,
                    "discretionary_expenses": max(0.0, total_exp - sub_exp),
                },
                navigation_link="/expenses",
                badge_label=f"${total_exp:,.2f}/mo",
                badge_status="neutral",
            )

            sb_md = (
                f"### Spending Analysis & Outflow Allocation for **{company_name}**\n\n"
                f"- **Total Monthly Outflows:** **${total_exp:,.2f}**\n"
                f"- **Confirmed Recurring Subscriptions:** **${sub_exp:,.2f}/mo** ({(sub_exp / total_exp * 100) if total_exp > 0 else 0:.1f}% of outflows)\n"
                f"- **Discretionary & Variable Outflows:** **${max(0.0, total_exp - sub_exp):,.2f}/mo**\n\n"
            )

            if subscriptions:
                top_subs = sorted(subscriptions, key=lambda s: float(getattr(s, 'latest_amount', 0.0) or 0.0), reverse=True)[:5]
                sb_md += "**Top Recurring Commitments:**\n\n| Service | Amount | Cadence |\n| :--- | :--- | :--- |\n"
                for s in top_subs:
                    sb_md += f"| **{s.vendor_name}** | ${float(getattr(s, 'latest_amount', 0.0) or 0.0):.2f} | {s.cadence or 'monthly'} |\n"

            sb_md += "\nView detailed category charts and historical trends on the [Expenses Page](/expenses)."

            return AssistantQueryResponse(
                response_text=sb_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Spending Intelligence",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Find cheaper alternatives for my subscriptions",
                    "Am I exceeding my monthly budget?",
                    "What is my financial health score?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 0C: BUDGET PACING & HEALTH
        # ---------------------------------------------------------------------
        if intent == "BUDGET_STATUS":
            budget_limit = float(business.monthly_baseline_revenue or 3500.0)
            spent = hist_actuals.historical_monthly_operating_expenses
            rem = budget_limit - spent
            pct = (spent / budget_limit * 100) if budget_limit > 0 else 0.0

            card = EvidenceCard(
                title="Budget Utilization",
                data_type="actual",
                amount=spent,
                currency="USD",
                details={
                    "monthly_limit": budget_limit,
                    "remaining_amount": rem,
                    "utilization_percent": pct,
                },
                navigation_link="/expenses",
                badge_label=f"{pct:.1f}% Used",
                badge_status="success" if pct <= 85 else ("warning" if pct <= 100 else "danger"),
            )

            status_str = "Within Budget" if rem >= 0 else "Over Budget"
            b_md = (
                f"### Budget Pacing Status: **{status_str}**\n\n"
                f"- **Target Monthly Budget Limit:** **${budget_limit:,.2f}**\n"
                f"- **Current Month Expenses:** **${spent:,.2f}** ({pct:.1f}% consumed)\n"
                f"- **Remaining Financial Cushion:** **${rem:,.2f}**\n\n"
            )

            if rem >= 0:
                b_md += f"> ✅ You have a **${rem:,.2f}** safety cushion remaining for this billing cycle.\n\n"
            else:
                b_md += f"> ⚠️ Outflows exceed your monthly target ceiling by **${abs(rem):,.2f}**. Consider trimming non-essential subscriptions or takeout orders.\n\n"

            b_md += "Manage individual category limits on the [Budget Manager](/expenses)."

            return AssistantQueryResponse(
                response_text=b_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Budget Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Where did most of my money go this month?",
                    "Find cheaper alternatives for subscriptions",
                    "What is our projected cash runway?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 1: AFFORDABILITY CHECK (SIMULATION)
        # ---------------------------------------------------------------------
        if intent == "AFFORDABILITY_CHECK":
            params = cls._parse_affordability_params(message)
            if params["amount"] <= 0.0:
                return AssistantQueryResponse(
                    response_text=(
                        f"I can evaluate whether {company_name} can afford a new subscription, but I couldn't "
                        f"detect a valid dollar amount in your question. \n\n"
                        f"**Try asking in this format:**\n"
                        f"- *'Can I afford Notion for $20/month?'*\n"
                        f"- *'Can we buy an annual Salesforce license for $1,200/year?'*"
                    ),
                    is_ai_generated=False,
                    generation_model="SubWise Deterministic Intelligence Engine",
                    intent=intent,
                    data_sufficiency_status=data_status,
                    evidence_cards=[],
                    suggested_followups=[
                        "Can I afford a new tool for $50/month?",
                        "What is our projected cash runway?",
                    ],
                    reporting_period=overview.monthly_briefing.reporting_period,
                    disclaimer=disclaimer,
                )

            # Call RecommendationEngine.simulate_purchase deterministically
            sim_req = PurchaseSimulationRequest(
                proposed_vendor=params["proposed_vendor"],
                amount=params["amount"],
                cadence=params["cadence"],
                business_purpose=params["business_purpose"],
            )
            sim_res = RecommendationEngine.simulate_purchase(
                business=business,
                subscriptions=subscriptions,
                transactions=transactions,
                request=sim_req,
            )

            # Format evidence cards
            badge_map = {
                "success": "success",
                "warning": "warning",
                "danger": "danger",
                "neutral": "neutral"
            }
            ev_card = EvidenceCard(
                title=f"Purchase Simulation: {sim_res.proposed_vendor}",
                data_type="simulation",
                amount=sim_res.monthly_equivalent_cost,
                currency="USD",
                details={
                    "cadence": sim_res.cadence,
                    "immediate_cash_impact": sim_res.immediate_cash_impact,
                    "annual_cost": sim_res.annual_cost,
                    "verdict": sim_res.verdict,
                    "current_monthly_burn": sim_res.current_monthly_burn,
                    "simulated_monthly_burn": sim_res.simulated_monthly_burn,
                    "shortfall_detected": sim_res.projected_shortfall_detected,
                    "shortfall_month": sim_res.shortfall_month,
                },
                navigation_link="/recommendations",
                badge_label=sim_res.verdict,
                badge_status=badge_map.get(sim_res.verdict_badge, "neutral"),
            )

            response_md = (
                f"### Purchase Simulation Analysis for **{sim_res.proposed_vendor}**\n\n"
                f"**Verdict:** `{sim_res.verdict}`\n\n"
                f"{sim_res.verdict_explanation}\n\n"
                f"**Financial Impact Details:**\n"
                f"- **Proposed Cost:** ${sim_res.amount:,.2f} ({sim_res.cadence})\n"
                f"- **Monthly Equivalent:** ${sim_res.monthly_equivalent_cost:,.2f}/mo\n"
                f"- **Annual Obligation:** ${sim_res.annual_cost:,.2f}/yr\n"
                f"- **Immediate Cash Outflow:** ${sim_res.immediate_cash_impact:,.2f}\n"
                f"- **Monthly Burn Change:** ${sim_res.current_monthly_burn:,.2f}/mo → **${sim_res.simulated_monthly_burn:,.2f}/mo**\n"
            )
            if sim_res.projected_shortfall_detected and sim_res.shortfall_month:
                response_md += f"\n> ⚠️ **Liquidity Warning:** This purchase triggers a projected cash deficit in **{sim_res.shortfall_month}**.\n\n"
            elif sim_res.renewal_concentration_effect:
                response_md += f"\n- **Calendar Concentration:** {sim_res.renewal_concentration_effect}\n"

            if sim_res.action_advice:
                response_md += "\n**Recommended Action Steps:**\n" + "\n".join(f"- {a}" for a in sim_res.action_advice[:3])

            return AssistantQueryResponse(
                response_text=response_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Purchase Simulator",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[ev_card],
                suggested_followups=[
                    f"What if we pay {sim_res.proposed_vendor} annually instead?",
                    "What is our projected cash runway right now?",
                    "Show my upcoming renewals for the next 30 days",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 2: REPORT SUMMARY
        # ---------------------------------------------------------------------
        if intent == "REPORT_SUMMARY":
            rep = ReportEngine.generate_monthly_financial_report(
                business=business,
                subscriptions=subscriptions,
                transactions=transactions,
                period_preset="all"
            )

            rep_card = EvidenceCard(
                title=f"Monthly Financial Report ({rep.reporting_period})",
                data_type="actual",
                amount=rep.net_operating_cashflow,
                currency="USD",
                details={
                    "total_operating_revenue": rep.total_operating_revenue,
                    "total_operating_expenses": rep.total_operating_expenses,
                    "confirmed_subscription_expenses": rep.total_confirmed_sub_expenses,
                    "verified_available_cash": rep.verified_available_cash,
                    "data_sufficiency_status": rep.data_sufficiency_status,
                },
                navigation_link="/reports",
                badge_label=f"Net: ${rep.net_operating_cashflow:,.2f}",
                badge_status="success" if rep.net_operating_cashflow >= 0 else "danger",
            )

            rep_md = (
                f"### Executive Report Summary: **{company_name}**\n"
                f"**Reporting Period:** {rep.reporting_period} | **Status:** `{rep.data_sufficiency_status.replace('_', ' ').title()}`\n\n"
                f"- **Verified Operating Revenue:** ${rep.total_operating_revenue:,.2f}\n"
                f"- **Non-Subscription Operating Outlays:** ${rep.total_non_sub_expenses:,.2f}\n"
                f"- **Confirmed Recurring Subscriptions:** ${rep.total_confirmed_sub_expenses:,.2f}\n"
                f"- **Total Operating Outflows:** ${rep.total_operating_expenses:,.2f}\n"
                f"- **Net Operating Cash Flow:** **${rep.net_operating_cashflow:,.2f}**\n\n"
                f"**Cash Reserves & Provenance:**\n"
                f"{rep.cash_provenance}\n\n"
                f"You can view and export detailed monthly breakdowns, subscription audit schedules, "
                f"and PDF reports on the [Reports Page](/reports)."
            )

            return AssistantQueryResponse(
                response_text=rep_md,
                is_ai_generated=False,
                generation_model="SubWise Report Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[rep_card],
                suggested_followups=[
                    "What are my upcoming renewals for the next 60 days?",
                    "What are our top subscription expenses?",
                    "What is our financial health score?",
                ],
                reporting_period=rep.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 3: RENEWAL CALENDAR & UPCOMING PAYMENTS
        # ---------------------------------------------------------------------
        if intent == "RENEWAL_CALENDAR":
            upcoming = forecast_data.get("upcoming_subscription_payments", [])
            monthly_sched = forecast_data.get("monthly_scheduled_subscription_totals", [])

            # Filter next 60 days
            now = datetime.date.today()
            horizon = now + datetime.timedelta(days=60)
            next_60_payments = []
            for p in upcoming:
                p_date_str = p.get("expected_payment_date")
                if p_date_str:
                    try:
                        p_date = datetime.date.fromisoformat(p_date_str)
                        if now <= p_date <= horizon:
                            next_60_payments.append(p)
                    except ValueError:
                        next_60_payments.append(p)

            total_next_60 = sum(float(p.get("expected_amount", 0.0)) for p in next_60_payments)
            card = EvidenceCard(
                title="Upcoming Renewals (Next 60 Days)",
                data_type="contractual",
                amount=total_next_60,
                currency="USD",
                details={
                    "renewals_count": len(next_60_payments),
                    "total_upcoming_amount": total_next_60,
                },
                navigation_link="/forecast",
                badge_label=f"{len(next_60_payments)} renewals due",
                badge_status="warning" if len(next_60_payments) > 0 else "neutral",
            )

            if not upcoming:
                cal_md = (
                    f"### Upcoming Subscription Renewals\n\n"
                    f"There are **no upcoming subscription renewals** currently scheduled in your payment calendar. \n\n"
                    f"**Why?** "
                    + (
                        "Your connected PayPal Sandbox account currently has 0 active recurring subscriptions identified in the transaction ledger. "
                        if data_status == "insufficient_data" else
                        "All active subscriptions have been processed or lack future billing dates."
                    )
                    + "\n\nAs soon as recurring vendor disbursements are detected or active subscriptions are synced, "
                    "their renewal dates and expected amounts will be plotted here."
                )
            else:
                cal_md = (
                    f"### Upcoming Subscription Renewals (Next 60 Days)\n\n"
                    f"Tracking **{len(next_60_payments)} contractual renewal(s)** totaling **${total_next_60:,.2f}** over the next 60 days:\n\n"
                    f"| Vendor | Expected Date | Expected Amount | Cadence | Status |\n"
                    f"| :--- | :--- | :--- | :--- | :--- |\n"
                )
                for p in next_60_payments[:8]:
                    cal_md += f"| **{p.get('vendor_name')}** | {p.get('expected_payment_date')} | ${float(p.get('expected_amount', 0)):,.2f} {p.get('currency', 'USD')} | {p.get('billing_frequency')} | `{p.get('is_confirmed') and 'Confirmed' or 'Potential'}` |\n"

                if len(next_60_payments) > 8:
                    cal_md += f"\n*...and {len(next_60_payments) - 8} more renewals.* View the full schedule on the [Payment Calendar](/forecast).\n"

            return AssistantQueryResponse(
                response_text=cal_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Payment Calendar",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What is our projected cash runway?",
                    "Can we afford a new subscription for $50/mo?",
                    "What are our largest recurring vendors?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 4: FORECAST & RUNWAY INQUIRY
        # ---------------------------------------------------------------------
        if intent == "FORECAST_INQUIRY":
            runway_str = f"{projected.estimated_runway_months:.1f} months" if projected.estimated_runway_months is not None else "Indeterminate"
            burn = (hist_actuals.historical_monthly_non_sub_expenses + forward_commit.confirmed_monthly_subscription_commitments) - hist_actuals.historical_monthly_operating_revenue

            card = EvidenceCard(
                title="Projected Cash Runway",
                data_type="projected",
                amount=projected.estimated_runway_months,
                currency="Months",
                details={
                    "runway_status": projected.runway_status,
                    "verified_cash": hist_actuals.verified_available_cash,
                    "monthly_revenue_baseline": projected.projected_monthly_revenue_baseline,
                    "monthly_net_cashflow": projected.projected_monthly_net_cash_flow,
                    "projected_shortfall_month": projected.projected_shortfall_month,
                },
                navigation_link="/forecast",
                badge_label=runway_str,
                badge_status="success" if (projected.estimated_runway_months or 0) >= 6 else ("warning" if (projected.estimated_runway_months or 0) >= 3 else "danger"),
            )

            if data_status == "insufficient_data":
                fc_md = (
                    f"### Cash Flow Forecast & Runway Analysis\n\n"
                    f"**Runway Status:** `Indeterminate (Insufficient Operating History)`\n\n"
                    f"We cannot calculate a cash runway or 6-month forecast for **{company_name}** because the connected "
                    f"PayPal account lacks verified customer operating revenues and regular operating disbursements.\n\n"
                    f"- **Verified Liquid Cash:** ${hist_actuals.verified_available_cash or 0.0:,.2f} ({hist_actuals.cash_provenance})\n"
                    f"- **Monthly Net Burn:** $0.00/mo\n\n"
                    f"Once customer sales transactions settle in your PayPal account, our multi-scenario engine "
                    f"(Optimistic, Baseline, Conservative) will dynamically project month-by-month cash balances."
                )
            else:
                fc_md = (
                    f"### Cash Flow Forecast & Runway Analysis for **{company_name}**\n\n"
                    f"- **Estimated Cash Runway:** **{runway_str}** (`{projected.runway_status}`)\n"
                    f"- **Available Liquid Cash:** ${hist_actuals.verified_available_cash:,.2f} ({hist_actuals.cash_provenance})\n"
                    f"- **Baseline Monthly Revenue:** ${projected.projected_monthly_revenue_baseline:,.2f}/mo\n"
                    f"- **Monthly Net Operating Cash Flow:** ${projected.projected_monthly_net_cash_flow:,.2f}/mo\n"
                )
                if projected.projected_shortfall_month:
                    fc_md += f"\n> ⚠️ **Projected Liquidity Deficit:** Under baseline assumptions, cash reserves may deplete in **{projected.projected_shortfall_month}**.\n\n"
                else:
                    fc_md += "\n> ✅ **Liquidity Solvency:** Cash reserves remain positive throughout the entire 6-month forecast horizon.\n\n"

                fc_md += f"{projected.runway_explanation}\n\nExplore detailed Optimistic (+15%) and Conservative (-20%) scenarios on the [Cash Flow Forecast Page](/forecast)."

            return AssistantQueryResponse(
                response_text=fc_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Forecast Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "Can we afford a new tool for $100/month?",
                    "What are our upcoming renewals next month?",
                    "How can we cut subscription costs?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 5: FINANCIAL HEALTH & RISKS
        # ---------------------------------------------------------------------
        if intent == "HEALTH_AND_RISKS":
            score_label = f"{health.score}/100" if health.score is not None else "N/A"
            card = EvidenceCard(
                title="Financial Health Index",
                data_type="actual",
                amount=float(health.score) if health.score is not None else None,
                currency="Points",
                details={
                    "status_label": health.status_label,
                    "risks_detected": len(risks),
                    "scoring_methodology": health.scoring_methodology,
                },
                navigation_link="/financial-intelligence",
                badge_label=health.status_label,
                badge_status="success" if (health.score or 0) >= 70 else ("warning" if (health.score or 0) >= 45 else "danger"),
            )

            if data_status == "insufficient_data":
                h_md = (
                    f"### Financial Health & Risk Assessment\n\n"
                    f"**Health Score:** `Unestablished (Score Withheld)`\n\n"
                    f"Under SubWise AI governance standards, a financial health score is never fabricated when ledger records are insufficient. "
                    f"The connected account currently has no confirmed subscription commitments or customer revenue.\n\n"
                    f"**Identified Risk Factor:**\n"
                    f"- **Data Visibility:** Inability to project cash runway due to absence of customer receipts and recurring vendor outflows."
                )
            else:
                h_md = (
                    f"### Financial Health & Risk Assessment for **{company_name}**\n\n"
                    f"**Financial Health Score:** **{score_label}** (`{health.status_label}`)\n\n"
                    f"**Methodology:** Evaluates subscription burden vs revenue (30%), cash runway & burn buffer (35%), "
                    f"calendar renewal concentration (20%), and price creep stability (15%).\n\n"
                )
                if risks:
                    h_md += f"**Critical Financial Risks Detected ({len(risks)}):**\n"
                    for r in risks[:4]:
                        h_md += f"- **{r.title}** (`{r.severity.upper()}`): {r.description} *Evidence: {r.supporting_evidence}*\n"
                else:
                    h_md += "> ✅ **No Critical Financial Risks Detected:** Current subscription commitments and burn rates are within standard operating thresholds.\n"

            return AssistantQueryResponse(
                response_text=h_md,
                is_ai_generated=False,
                generation_model="SubWise Financial Intelligence Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What recommendations do you have to improve our score?",
                    "What are our upcoming subscription renewals?",
                    "What is our projected cash runway?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 6: RECOMMENDATIONS
        # ---------------------------------------------------------------------
        if intent == "RECOMMENDATIONS":
            recs = RecommendationEngine.generate_recommendations(
                business=business,
                subscriptions=subscriptions,
                transactions=transactions,
            )
            card = EvidenceCard(
                title="Actionable CFO Recommendations",
                data_type="actual",
                amount=sum(r.potential_monthly_saving for r in recs),
                currency="USD",
                details={
                    "recommendations_count": len(recs),
                    "total_potential_monthly_savings": sum(r.potential_monthly_saving for r in recs),
                    "total_potential_annual_savings": sum(r.potential_annual_saving for r in recs),
                },
                navigation_link="/recommendations",
                badge_label=f"{len(recs)} actions identified",
                badge_status="info",
            )

            rec_md = f"### CFO Recommendations for **{company_name}**\n\n"
            if not recs:
                rec_md += (
                    "No immediate optimization actions required at this time. "
                    "Your subscriptions show consistent billing cadences with no identified duplicate seats or pricing creep.\n"
                )
            else:
                rec_md += f"We identified **{len(recs)} optimization action(s)**:\n\n"
                for r in recs[:5]:
                    rec_md += (
                        f"#### {r.title}\n"
                        f"- **Vendor:** {r.vendor_name or 'General Portfolio'}\n"
                        f"- **Rationale:** {r.rationale}\n"
                        f"- **Potential Savings:** ${r.potential_monthly_saving:,.2f}/mo (${r.potential_annual_saving:,.2f}/yr)\n"
                    )
                    if r.action_plan:
                        rec_md += f"- **Action Plan:** {r.action_plan}\n"
                    rec_md += "\n"

            rec_md += "\nReview details and track applied optimizations on the [Recommendations Page](/recommendations)."

            return AssistantQueryResponse(
                response_text=rec_md,
                is_ai_generated=False,
                generation_model="SubWise Recommendation Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What is our financial health score?",
                    "Can we afford a new subscription for $50/mo?",
                    "What is our projected cash runway?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 7: SPEND OVERVIEW / VENDOR LOOKUP
        # ---------------------------------------------------------------------
        if intent == "SPEND_OVERVIEW":
            # Check if specific vendor is mentioned
            active_subs = [s for s in subscriptions if (s.status or "").lower() == "active"]
            vendor_match = None
            msg_lower = message.lower()
            for s in subscriptions:
                if s.vendor_name and s.vendor_name.lower() in msg_lower:
                    vendor_match = s
                    break

            if vendor_match:
                v_amt = float(getattr(vendor_match, 'latest_amount', None) or getattr(vendor_match, 'average_amount', None) or 0.0)
                amount_str = f"${v_amt:,.2f}" if v_amt > 0 else "Variable"
                cadence = vendor_match.cadence or "monthly"
                next_date = vendor_match.next_billing_date.strftime("%Y-%m-%d") if vendor_match.next_billing_date else "Unscheduled"
                v_card = EvidenceCard(
                    title=f"Vendor: {vendor_match.vendor_name}",
                    data_type="contractual",
                    amount=v_amt,
                    currency="USD",
                    details={
                        "category": vendor_match.category or "General Software",
                        "cadence": cadence,
                        "next_billing_date": next_date,
                        "status": vendor_match.status,
                    },
                    navigation_link="/subscriptions",
                    badge_label=f"{amount_str} / {cadence}",
                    badge_status="neutral",
                )
                v_md = (
                    f"### Subscription Details: **{vendor_match.vendor_name}**\n\n"
                    f"- **Status:** `{vendor_match.status.title() if vendor_match.status else 'Active'}`\n"
                    f"- **Category:** {vendor_match.category or 'Software'}\n"
                    f"- **Billing Cadence:** {cadence.title()}\n"
                    f"- **Billing Amount:** {amount_str}\n"
                    f"- **Next Scheduled Renewal:** {next_date}\n\n"
                    f"Manage subscription details and alert rules on the [Subscriptions Page](/subscriptions)."
                )
                return AssistantQueryResponse(
                    response_text=v_md,
                    is_ai_generated=False,
                    generation_model="SubWise Deterministic Subscription Ledger",
                    intent=intent,
                    data_sufficiency_status=data_status,
                    evidence_cards=[v_card],
                    suggested_followups=[
                        f"Can I afford to upgrade {vendor_match.vendor_name} for an extra $30/mo?",
                        "What are my total subscription expenses?",
                        "What is our cash runway?",
                    ],
                    reporting_period=overview.monthly_briefing.reporting_period,
                    disclaimer=disclaimer,
                )

            # Portfolio spend overview
            card = EvidenceCard(
                title="Monthly Subscription Spend",
                data_type="contractual",
                amount=forward_commit.confirmed_monthly_subscription_commitments,
                currency="USD",
                details={
                    "active_subscriptions_count": len(active_subs),
                    "potential_monthly_commitments": forward_commit.potential_monthly_subscription_commitments,
                    "annual_run_rate": forward_commit.confirmed_annual_subscription_commitments,
                },
                navigation_link="/subscriptions",
                badge_label=f"${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo",
                badge_status="neutral",
            )

            if not active_subs:
                s_md = (
                    f"### Subscription Spend Overview\n\n"
                    f"**Active Recurring Subscriptions:** 0\n"
                    f"**Total Monthly Subscription Commitments:** $0.00/mo\n\n"
                    f"No active recurring software subscriptions were detected in your connected PayPal ledger. "
                    f"When regular vendor transactions occur, SubWise will automatically detect and categorize them."
                )
            else:
                s_md = (
                    f"### Subscription Spend Overview for **{company_name}**\n\n"
                    f"- **Confirmed Monthly Commitments:** **${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo** "
                    f"(${forward_commit.confirmed_annual_subscription_commitments:,.2f}/year)\n"
                    f"- **Active Subscriptions:** {len(active_subs)}\n"
                )
                if forward_commit.potential_monthly_subscription_commitments > 0:
                    s_md += f"- **Potential Trials / Unconfirmed:** ${forward_commit.potential_monthly_subscription_commitments:,.2f}/mo\n"

                s_md += "\n**Active Recurring Vendors:**\n\n| Vendor | Amount | Cadence | Category |\n| :--- | :--- | :--- | :--- |\n"
                for s in active_subs[:6]:
                    amt = float(getattr(s, 'latest_amount', None) or getattr(s, 'average_amount', None) or 0.0)
                    s_md += f"| **{s.vendor_name}** | ${amt:,.2f} | {s.cadence or 'monthly'} | {s.category or 'Software'} |\n"

            return AssistantQueryResponse(
                response_text=s_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Subscription Ledger",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What are our upcoming renewals over the next 30 days?",
                    "Can we afford a new tool for $50/mo?",
                    "What is our cash runway?",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 8: REVENUE INQUIRY
        # ---------------------------------------------------------------------
        if intent == "REVENUE_INQUIRY":
            card = EvidenceCard(
                title="Monthly Operating Revenue",
                data_type="actual",
                amount=hist_actuals.historical_monthly_operating_revenue,
                currency="USD",
                details={
                    "operating_months_analyzed": hist_actuals.operating_months_analyzed,
                    "reporting_period": f"{hist_actuals.reporting_period_start} to {hist_actuals.reporting_period_end}",
                    "non_sub_expenses": hist_actuals.historical_monthly_non_sub_expenses,
                    "net_cash_flow": hist_actuals.historical_monthly_net_cash_flow,
                },
                navigation_link="/reports",
                badge_label=f"${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo",
                badge_status="success" if hist_actuals.historical_monthly_operating_revenue > 0 else "neutral",
            )

            if data_status == "insufficient_data":
                rev_md = (
                    f"### Operating Revenue Analysis\n\n"
                    f"**Verified Operating Revenue:** $0.00/mo\n\n"
                    f"No completed customer sales transactions were identified in your connected PayPal ledger. "
                    f"Under SubWise accounting rules, non-operating wallet top-ups or transfers are strictly excluded from operating revenue."
                )
            else:
                rev_md = (
                    f"### Operating Revenue Analysis for **{company_name}**\n\n"
                    f"- **Monthly Operating Revenue Average:** **${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo**\n"
                    f"- **Operating Months Analyzed:** {hist_actuals.operating_months_analyzed} month(s)\n"
                    f"- **Non-Subscription Operating Expenses:** ${hist_actuals.historical_monthly_non_sub_expenses:,.2f}/mo\n"
                    f"- **Confirmed Subscriptions:** ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n"
                    f"- **Monthly Net Operating Surplus/Deficit:** **${hist_actuals.historical_monthly_net_cash_flow:,.2f}/mo**\n\n"
                    f"View monthly revenue breakdowns on the [Reports Page](/reports)."
                )

            return AssistantQueryResponse(
                response_text=rev_md,
                is_ai_generated=False,
                generation_model="SubWise Deterministic Accounting Engine",
                intent=intent,
                data_sufficiency_status=data_status,
                evidence_cards=[card],
                suggested_followups=[
                    "What are our total subscription costs?",
                    "What is our projected cash runway?",
                    "Summarize our monthly financial report",
                ],
                reporting_period=overview.monthly_briefing.reporting_period,
                disclaimer=disclaimer,
            )

        # ---------------------------------------------------------------------
        # ROUTE 9: GENERAL_FINTECH (AI Augmentation with Deterministic Fallback)
        # ---------------------------------------------------------------------
        # Prepare verified facts string for LLM or deterministic synthesis
        facts_summary = (
            f"Business: {company_name}\n"
            f"Data Sufficiency Status: {data_status}\n"
            f"Operating Revenue: ${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo\n"
            f"Non-Subscription Expenses: ${hist_actuals.historical_monthly_non_sub_expenses:,.2f}/mo\n"
            f"Confirmed Subscription Commitments: ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n"
            f"Available Cash: ${hist_actuals.verified_available_cash or 0.0:,.2f} ({hist_actuals.cash_provenance})\n"
            f"Cash Runway: {projected.estimated_runway_months or 'Indeterminate'} months\n"
            f"Financial Health Score: {health.score if health.score is not None else 'Withheld (Insufficient data)'}\n"
            f"Reporting Period: {overview.monthly_briefing.reporting_period}\n"
        )

        is_llm = cls.is_llm_configured()
        if is_llm:
            api_key = (settings.GEMINI_API_KEY or settings.LLM_API_KEY or "").strip()
            try:
                system_prompt = (
                    "You are SubWise AI, an expert, prudent SMB financial advisor. "
                    "You answer questions from founders and finance leaders about their business's finances. "
                    "CRITICAL RULES:\n"
                    "1. Base your answer EXCLUSIVELY on the provided VERIFIED FINANCIAL FACTS below.\n"
                    "2. DO NOT invent new vendors, transactions, amounts, or savings.\n"
                    "3. If information is not in the facts, state clearly that it is unavailable in the connected PayPal ledger.\n"
                    "4. Distinguish between actual historical data and projected forward estimates.\n"
                    "5. Keep your tone concise, professional, and actionable."
                )
                full_prompt = (
                    f"{system_prompt}\n\n"
                    f"VERIFIED FINANCIAL FACTS:\n{facts_summary}\n\n"
                    f"USER QUESTION: {message}\n\n"
                    f"Provide an evidence-based answer formatted in clean Markdown:"
                )

                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {"contents": [{"parts": [{"text": full_prompt}]}]}
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            ai_text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text")
                            if ai_text:
                                return AssistantQueryResponse(
                                    response_text=ai_text,
                                    is_ai_generated=True,
                                    generation_model="Google Gemini 1.5 Flash (Verified Financial Baseline)",
                                    intent=intent,
                                    data_sufficiency_status=data_status,
                                    evidence_cards=[],
                                    suggested_followups=[
                                        "What are my upcoming subscription renewals?",
                                        "What is our projected cash runway?",
                                        "Can we afford a new tool for $50/mo?",
                                    ],
                                    reporting_period=overview.monthly_briefing.reporting_period,
                                    disclaimer=disclaimer,
                                    llm_provider_configured=True,
                                )
            except Exception:
                pass  # Gracefully fall back to deterministic answer

        # Deterministic General Fallback
        det_md = (
            f"### Financial Overview for **{company_name}**\n\n"
            f"Here is your current verified financial position:\n\n"
            f"- **Data Status:** `{data_status.replace('_', ' ').title()}`\n"
            f"- **Verified Operating Revenue:** ${hist_actuals.historical_monthly_operating_revenue:,.2f}/mo\n"
            f"- **Non-Subscription Outflows:** ${hist_actuals.historical_monthly_non_sub_expenses:,.2f}/mo\n"
            f"- **Confirmed Subscriptions:** ${forward_commit.confirmed_monthly_subscription_commitments:,.2f}/mo\n"
            f"- **Available Liquid Reserves:** ${hist_actuals.verified_available_cash or 0.0:,.2f}\n"
            f"- **Cash Runway:** {projected.estimated_runway_months or 'Indeterminate'} months\n\n"
            f"You can ask me about:\n"
            f"- **Upcoming Renewals:** *'What payments are due in the next 30 days?'*\n"
            f"- **Affordability:** *'Can I afford Slack for $15/month?'*\n"
            f"- **Reports:** *'Summarize our monthly financial report'* \n"
            f"- **Cash Runway:** *'How long will our cash last?'*"
        )

        return AssistantQueryResponse(
            response_text=det_md,
            is_ai_generated=False,
            generation_model="SubWise Deterministic Intelligence Engine",
            intent=intent,
            data_sufficiency_status=data_status,
            evidence_cards=[],
            suggested_followups=[
                "What are my upcoming renewals?",
                "Can I afford a new subscription for $50/mo?",
                "Summarize our monthly report",
            ],
            reporting_period=overview.monthly_briefing.reporting_period,
            disclaimer=disclaimer,
            llm_provider_configured=is_llm,
        )
