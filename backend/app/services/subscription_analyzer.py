import datetime
from typing import Optional, List, Dict, Any, Tuple
from app.models.subscription import Subscription
from app.models.transaction import Transaction

class SubscriptionExpenseAnalyzer:
    """
    Subscription Expense Analysis Engine for PayPal SubWise AI.
    Features:
    1. Monthly & Annual Subscription Commitments (converts weekly, monthly, quarterly, annual cadences).
    2. Distinction between verified historical spending and estimated future commitments.
    3. Vendor-wise Analysis with monthly/annual equivalent costs, status, and classification.
    4. Canonical 7-Category grouping (Cloud Infrastructure, Development Tools, Communication,
       Productivity, Design, Marketing, Other SaaS).
    5. Operating Revenue vs Subscription Expense impact & ratio (with safe zero-revenue handling).
    6. Spending Trends, Month-over-Month changes, and Price Creep alerts.
    7. Exclusion of account funding, initial balance, and internal sandbox test payments.
    8. Full insufficient-data handling without fabricated metrics.
    """

    NON_OPERATING_KEYWORDS = [
        "initial balance", "account funding", "balance adjustment", "general funding",
        "deposit", "bank transfer", "wallet funding", "reserve deposit", "top up",
        "reversal", "adjustment", "paypal balance", "subwise",
        "currency conversion", "conversion leg", "exchange rate", "paypal transaction", "paypal transfer"
    ]

    CADENCE_CONVERSIONS = {
        "weekly": {
            "to_monthly": 52.0 / 12.0,   # 4.3333 weeks/month
            "to_annual": 52.0,
        },
        "monthly": {
            "to_monthly": 1.0,
            "to_annual": 12.0,
        },
        "quarterly": {
            "to_monthly": 1.0 / 3.0,
            "to_annual": 4.0,
        },
        "annual": {
            "to_monthly": 1.0 / 12.0,
            "to_annual": 1.0,
        }
    }

    CANONICAL_CATEGORIES = [
        "Cloud Infrastructure",
        "Development Tools",
        "Communication",
        "Productivity",
        "Design",
        "Marketing",
        "Other SaaS"
    ]

    @classmethod
    def calculate_cadence_equivalents(cls, amount: float, cadence: str) -> Tuple[float, float]:
        """
        Converts any billing cadence into standardized monthly and annual equivalent costs.
        """
        cadence_lower = (cadence or "monthly").lower().strip()
        conv = cls.CADENCE_CONVERSIONS.get(cadence_lower, cls.CADENCE_CONVERSIONS["monthly"])
        monthly_eq = round(amount * conv["to_monthly"], 2)
        annual_eq = round(amount * conv["to_annual"], 2)
        return monthly_eq, annual_eq

    @classmethod
    def standardize_category(cls, raw_category: Optional[str]) -> str:
        """
        Maps granular merchant registry categories into the canonical 7 business SaaS categories.
        """
        if not raw_category:
            return "Other SaaS"
        cat = raw_category.strip().lower()

        # 1. Communication (check before dev tools so "Communications API" maps to Communication)
        if any(k in cat for k in ["communication", "collaboration", "video", "sms", "messaging", "teams", "slack", "zoom", "telecom"]):
            return "Communication"

        # 2. Cloud Infrastructure
        if any(k in cat for k in ["cloud", "hosting", "devops", "monitoring", "infrastructure", "observability", "storage", "aws", "gcp", "azure"]):
            return "Cloud Infrastructure"

        # 3. Development Tools
        if any(k in cat for k in ["developer", "version_control", "git", "api", "ai & machine learning", "ai & ml"]):
            return "Development Tools"

        # 4. Design
        if any(k in cat for k in ["design", "prototyping", "graphics", "media", "creative"]):
            return "Design"

        # 5. Marketing
        if any(k in cat for k in ["marketing", "crm", "sales", "email marketing", "hubspot", "mailchimp"]):
            return "Marketing"

        # 6. Productivity
        if any(k in cat for k in ["productivity", "docs", "wiki", "office", "project management", "accounting", "finance", "security", "identity"]):
            return "Productivity"

        # 7. Fallback
        return "Other SaaS"

    @classmethod
    def is_non_operating(cls, tx: Transaction) -> bool:
        """
        Checks whether a transaction is non-operating capital, funding, adjustment, or internal test.
        """
        desc = (tx.raw_description or "").lower()
        vendor = (tx.normalized_vendor or "").lower()
        cat = (tx.category or "").lower()
        return any(kw in desc or kw in vendor or kw in cat for kw in cls.NON_OPERATING_KEYWORDS)

    @classmethod
    def analyze(
        cls,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """
        Performs end-to-end subscription expense analysis using verified DB records.
        """
        # Exclude cancelled subscriptions from future commitments
        active_subs = [s for s in subscriptions if s.status != "cancelled"]
        has_subscriptions = len(active_subs) > 0
        has_transactions = len(transactions) > 0

        # Separate confirmed vs potential subscriptions
        confirmed_subs = [s for s in active_subs if getattr(s, "detection_type", "confirmed") == "confirmed"]
        potential_subs = [s for s in active_subs if getattr(s, "detection_type", "confirmed") == "potential"]

        # -------------------------------------------------------------
        # 1. Vendor-wise Analysis & Commitments
        # -------------------------------------------------------------
        vendor_analysis_list: List[Dict[str, Any]] = []
        vendor_spend_map: Dict[str, float] = {}

        # Precompute actual historical spend from transactions for each vendor
        for tx in transactions:
            if tx.gross_amount < 0 and not cls.is_non_operating(tx):
                vendor_key = (tx.normalized_vendor or "").lower().strip()
                amt = abs(float(tx.gross_amount))
                vendor_spend_map[vendor_key] = round(vendor_spend_map.get(vendor_key, 0.0) + amt, 2)

        confirmed_monthly_commit = 0.0
        confirmed_annual_commit = 0.0
        potential_monthly_commit = 0.0
        potential_annual_commit = 0.0

        for sub in active_subs:
            m_eq, a_eq = cls.calculate_cadence_equivalents(sub.latest_amount, sub.cadence)
            det_type = getattr(sub, "detection_type", "confirmed") or "confirmed"

            if det_type == "confirmed":
                confirmed_monthly_commit += m_eq
                confirmed_annual_commit += a_eq
            else:
                potential_monthly_commit += m_eq
                potential_annual_commit += a_eq

            # Historical actual spend for this vendor
            v_key = (sub.vendor_name or "").lower().strip()
            hist_spend = vendor_spend_map.get(v_key, 0.0)
            tx_count = sum(
                1 for tx in transactions
                if tx.gross_amount < 0 and not cls.is_non_operating(tx) and (tx.normalized_vendor or "").lower().strip() == v_key
            )

            vendor_analysis_list.append({
                "vendor_name": sub.vendor_name,
                "category": sub.category,
                "standard_category": cls.standardize_category(sub.category),
                "cadence": sub.cadence,
                "billing_type": getattr(sub, "billing_type", "fixed") or "fixed",
                "latest_amount": round(float(sub.latest_amount), 2),
                "average_amount": round(float(sub.average_amount), 2),
                "monthly_equivalent": m_eq,
                "annual_equivalent": a_eq,
                "status": sub.status,
                "detection_type": det_type,
                "detection_reason": getattr(sub, "detection_reason", None),
                "confidence_score": round(float(sub.confidence_score or 0.9), 2),
                "historical_spend_total": hist_spend,
                "transaction_count": tx_count,
                "price_change_pct": round(float(sub.price_change_pct or 0.0), 1),
                "first_billed_date": sub.first_billed_date.isoformat() if sub.first_billed_date else None,
                "last_billed_date": sub.last_billed_date.isoformat() if sub.last_billed_date else None,
                "next_billing_date": sub.next_billing_date.isoformat() if sub.next_billing_date else None,
            })

        # Sort vendor analysis by monthly equivalent descending
        vendor_analysis_list.sort(key=lambda x: x["monthly_equivalent"], reverse=True)

        total_monthly_commit = round(confirmed_monthly_commit + potential_monthly_commit, 2)
        total_annual_commit = round(confirmed_annual_commit + potential_annual_commit, 2)
        confirmed_monthly_commit = round(confirmed_monthly_commit, 2)
        confirmed_annual_commit = round(confirmed_annual_commit, 2)
        potential_monthly_commit = round(potential_monthly_commit, 2)
        potential_annual_commit = round(potential_annual_commit, 2)

        # -------------------------------------------------------------
        # 2. Category-wise Analysis
        # -------------------------------------------------------------
        cat_buckets: Dict[str, Dict[str, Any]] = {
            c: {"monthly": 0.0, "annual": 0.0, "count": 0, "vendors": []}
            for c in cls.CANONICAL_CATEGORIES
        }

        for v in vendor_analysis_list:
            sc = v["standard_category"]
            cat_buckets[sc]["monthly"] += v["monthly_equivalent"]
            cat_buckets[sc]["annual"] += v["annual_equivalent"]
            cat_buckets[sc]["count"] += 1
            cat_buckets[sc]["vendors"].append(v["vendor_name"])

        category_analysis_list: List[Dict[str, Any]] = []
        for cat_name in cls.CANONICAL_CATEGORIES:
            b = cat_buckets[cat_name]
            m_spend = round(b["monthly"], 2)
            pct = round((m_spend / total_monthly_commit * 100), 1) if total_monthly_commit > 0 else 0.0
            category_analysis_list.append({
                "category": cat_name,
                "monthly_spend": m_spend,
                "annual_spend": round(b["annual"], 2),
                "percentage_of_total": pct,
                "subscription_count": b["count"],
                "vendors": b["vendors"]
            })

        # Sort category list descending by monthly spend
        category_analysis_list.sort(key=lambda x: x["monthly_spend"], reverse=True)

        # -------------------------------------------------------------
        # 3. Monthly Spend History & MoM Comparison
        # -------------------------------------------------------------
        # Aggregate real operating transactions into monthly buckets (YYYY-MM)
        month_map: Dict[str, Dict[str, Any]] = {}
        for tx in transactions:
            if not tx.transaction_date or cls.is_non_operating(tx):
                continue

            d = tx.transaction_date
            key = f"{d.year}-{d.month:02d}"
            label = d.strftime("%b %Y")

            if key not in month_map:
                month_map[key] = {
                    "month": key,
                    "month_label": label,
                    "operating_revenue": 0.0,
                    "operating_expenses": 0.0,
                    "subscription_spend": 0.0,
                    "vendor_breakdown": {}
                }

            amt = float(tx.gross_amount)
            if amt > 0:
                month_map[key]["operating_revenue"] += amt
            else:
                expense_amt = abs(amt)
                month_map[key]["operating_expenses"] += expense_amt

                # Check if this expense matches a detected subscription or known SaaS
                v_clean = (tx.normalized_vendor or "").lower().strip()
                matches_sub = any(
                    (s.vendor_name or "").lower().strip() == v_clean
                    for s in active_subs
                )
                if matches_sub:
                    month_map[key]["subscription_spend"] += expense_amt
                    month_map[key]["vendor_breakdown"][tx.normalized_vendor] = round(
                        month_map[key]["vendor_breakdown"].get(tx.normalized_vendor, 0.0) + expense_amt, 2
                    )

        sorted_months = sorted(month_map.keys())
        monthly_history_list: List[Dict[str, Any]] = []
        prev_sub_spend: Optional[float] = None

        for k in sorted_months:
            entry = month_map[k]
            sub_spend = round(entry["subscription_spend"], 2)
            rev = round(entry["operating_revenue"], 2)
            exp = round(entry["operating_expenses"], 2)

            # Revenue ratio (with zero-revenue protection)
            sub_rev_pct = round((sub_spend / rev * 100), 1) if rev > 0 else None

            # Spending change from previous month
            change_amt = round(sub_spend - prev_sub_spend, 2) if prev_sub_spend is not None else None
            change_pct = round(((sub_spend - prev_sub_spend) / prev_sub_spend) * 100, 1) if (prev_sub_spend and prev_sub_spend > 0) else None

            monthly_history_list.append({
                "month": entry["month"],
                "month_label": entry["month_label"],
                "total_subscription_spend": sub_spend,
                "operating_revenue": rev,
                "operating_expenses": exp,
                "subscription_to_revenue_pct": sub_rev_pct,
                "vendor_breakdown": entry["vendor_breakdown"],
                "spending_change_from_prev": change_amt,
                "spending_change_pct_from_prev": change_pct
            })
            prev_sub_spend = sub_spend

        # Total actual historical spend on subscriptions
        actual_historical_spend_total = round(
            sum(m["total_subscription_spend"] for m in monthly_history_list), 2
        )

        # -------------------------------------------------------------
        # 4. Spending Trends & Price Creep Alerts
        # -------------------------------------------------------------
        price_alerts: List[Dict[str, Any]] = []
        for v in vendor_analysis_list:
            if v["price_change_pct"] >= 10.0 and v["billing_type"] != "variable":
                price_alerts.append({
                    "vendor": v["vendor_name"],
                    "type": "price_creep",
                    "change_pct": v["price_change_pct"],
                    "monthly_amount": v["latest_amount"],
                    "message": f"{v['vendor_name']} cost increased by +{v['price_change_pct']}% compared to initial cycle."
                })
            elif v["billing_type"] == "variable" and v["transaction_count"] > 1:
                price_alerts.append({
                    "vendor": v["vendor_name"],
                    "type": "variable_usage",
                    "change_pct": 0.0,
                    "monthly_amount": v["latest_amount"],
                    "message": f"{v['vendor_name']} is billed on variable consumption. Amounts fluctuate per cycle."
                })

        if len(monthly_history_list) >= 2:
            curr_month = monthly_history_list[-1]["total_subscription_spend"]
            prev_month = monthly_history_list[-2]["total_subscription_spend"]
            spend_change = round(curr_month - prev_month, 2)
            spend_pct = round(((curr_month - prev_month) / prev_month) * 100, 1) if prev_month > 0 else None

            if spend_change > 5.0:
                trend_dir = "increasing"
                is_sig = spend_pct is not None and spend_pct >= 10.0
                summary_text = f"Subscription spending rose by ${spend_change:.2f} ({'+' if spend_pct else ''}{spend_pct or 0}%) this month."
            elif spend_change < -5.0:
                trend_dir = "decreasing"
                is_sig = False
                summary_text = f"Subscription spending dropped by ${abs(spend_change):.2f} this month."
            else:
                trend_dir = "stable"
                is_sig = False
                summary_text = "Subscription expenses have remained steady across recent billing cycles."
        elif len(monthly_history_list) == 1:
            curr_month = monthly_history_list[0]["total_subscription_spend"]
            prev_month = 0.0
            spend_change = 0.0
            spend_pct = None
            trend_dir = "stable"
            is_sig = False
            summary_text = f"Single month recorded (${curr_month:.2f}). Awaiting next cycle to track spending trends."
        else:
            curr_month = total_monthly_commit
            prev_month = 0.0
            spend_change = 0.0
            spend_pct = None
            trend_dir = "insufficient_data"
            is_sig = False
            summary_text = "Insufficient historical billing cycles to calculate spending trends."

        spending_trends = {
            "current_month_spend": curr_month,
            "previous_month_spend": prev_month,
            "spending_change_amount": spend_change,
            "spending_change_pct": spend_pct,
            "trend_direction": trend_dir,
            "is_significant_increase": is_sig,
            "price_creep_alerts": price_alerts,
            "trend_summary": summary_text
        }

        # -------------------------------------------------------------
        # 5. Revenue vs Subscription Expense Comparison
        # -------------------------------------------------------------
        # Calculate recent operating revenue (from history if available)
        total_operating_rev = sum(m["operating_revenue"] for m in monthly_history_list)
        active_months = len(monthly_history_list)
        avg_monthly_rev = round(total_operating_rev / active_months, 2) if active_months > 0 else 0.0

        if avg_monthly_rev > 0:
            rev_pct = round((total_monthly_commit / avg_monthly_rev) * 100, 1)
            has_suff_rev = True
            if rev_pct <= 15.0:
                burden = "healthy"
                explanation = f"Healthy: Software expenses represent {rev_pct}% of average monthly operating revenue (<15%)."
            elif rev_pct <= 30.0:
                burden = "moderate"
                explanation = f"Moderate: Software expenses represent {rev_pct}% of revenue. Review discretionary tools."
            else:
                burden = "high"
                explanation = f"High: Software expenses consume {rev_pct}% of operating revenue (>30%). High subscription burden."
        else:
            rev_pct = None
            has_suff_rev = False
            burden = "insufficient_data"
            explanation = "No operating revenue recorded in transaction ledger. Percentage cannot be calculated without operating income."

        revenue_comparison = {
            "monthly_operating_revenue": avg_monthly_rev,
            "monthly_subscription_spend": total_monthly_commit,
            "revenue_percentage": rev_pct,
            "burden_level": burden,
            "has_sufficient_revenue_data": has_suff_rev,
            "explanation": explanation
        }

        # Overall Status & Message
        if not has_subscriptions:
            status = "insufficient_data"
            message = "No recurring software subscriptions detected yet. Sync PayPal Sandbox transactions to analyze subscription commitments."
        else:
            status = "active"
            message = f"Analyzed {len(active_subs)} active subscriptions ({len(confirmed_subs)} confirmed, {len(potential_subs)} potential)."

        return {
            "has_data": has_transactions or has_subscriptions,
            "has_subscriptions": has_subscriptions,
            "status": status,
            "message": message,
            "currency": currency,
            "total_monthly_commitment": total_monthly_commit,
            "total_annual_commitment": total_annual_commit,
            "confirmed_monthly_commitment": confirmed_monthly_commit,
            "confirmed_annual_commitment": confirmed_annual_commit,
            "potential_monthly_commitment": potential_monthly_commit,
            "potential_annual_commitment": potential_annual_commit,
            "actual_historical_spend_total": actual_historical_spend_total,
            "vendor_analysis": vendor_analysis_list,
            "category_analysis": category_analysis_list,
            "monthly_history": monthly_history_list,
            "spending_trends": spending_trends,
            "revenue_comparison": revenue_comparison,
        }
