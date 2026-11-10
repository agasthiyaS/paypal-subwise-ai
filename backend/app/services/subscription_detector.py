import datetime
import numpy as np
from typing import List, Dict, Any, Tuple
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.services.normalizer import TransactionNormalizer

class SubscriptionDetector:
    """
    Hybrid Subscription Detection Engine for PayPal SubWise AI.
    Features:
    1. Known SaaS Provider Detection via canonical MERCHANT_REGISTRY.
       Single payments to recognized SaaS vendors are classified as 'potential' subscriptions.
    2. Interval-based Recurrence Detection (Weekly, Monthly, Quarterly, Annual)
       using inter-arrival time deltas and cadence variance analysis.
    3. Variable Billing Detection for usage-based cloud and API services (AWS, Twilio, OpenAI).
    4. Strict Transaction Direction Filtering (ignores incoming sales revenue, account funding,
       and internal sandbox test transactions).
    5. Multi-level Confidence & Human-Readable Classification (confirmed, potential, uncertain).
    """

    CADENCE_DAYS = {
        "weekly": 7,
        "monthly": 30,
        "quarterly": 90,
        "annual": 365
    }

    NON_SUBSCRIPTION_KEYWORDS = [
        "initial balance", "account funding", "balance adjustment", "general funding",
        "deposit", "bank transfer", "wallet funding", "reserve deposit", "top up",
        "reversal", "adjustment", "paypal balance", "subwise",
        "currency conversion", "conversion leg", "exchange rate", "paypal transaction", "paypal transfer"
    ]

    @staticmethod
    def detect_cadence(dates: List[datetime.datetime]) -> Tuple[str, float]:
        """
        Determines the billing cadence and cadence confidence based on inter-arrival intervals.
        """
        if len(dates) < 2:
            return "monthly", 0.70

        deltas = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        median_delta = float(np.median(deltas))
        std_delta = float(np.std(deltas)) if len(deltas) > 1 else 0.0

        if 5 <= median_delta <= 9:
            cadence = "weekly"
        elif 25 <= median_delta <= 35:
            cadence = "monthly"
        elif 80 <= median_delta <= 100:
            cadence = "quarterly"
        elif 340 <= median_delta <= 390:
            cadence = "annual"
        else:
            cadence = "monthly"  # default fallback for monthly billing with date shifts

        confidence = max(0.60, min(0.99, 1.0 - (std_delta / 15.0)))
        return cadence, round(confidence, 2)

    @classmethod
    def identify_subscriptions(cls, transactions: List[Transaction], business_id: int) -> List[Subscription]:
        """
        Identifies recurring subscriptions using the Hybrid Detection algorithm.
        Distinguishes between confirmed recurring subscriptions, potential known SaaS subscriptions,
        and uncertain recurrence patterns.
        """
        if not transactions:
            return []

        # 1. Filter outbound expense transactions only
        # Excludes:
        # - Incoming sales revenue / positive receipts (gross_amount >= 0)
        # - Account funding, initial balances, and balance adjustments
        # - SubWise AI's own Sandbox testing transactions
        expenses: List[Transaction] = []
        for tx in transactions:
            # Rule: Only outbound expenses can be software subscription costs
            if tx.gross_amount >= 0:
                continue

            desc_lower = (tx.raw_description or "").lower()
            vendor_lower = (tx.normalized_vendor or "").lower()
            category_lower = (tx.category or "").lower()

            # Ignore funding, adjustment, transfer, and internal SubWise test transactions
            if any(kw in desc_lower or kw in vendor_lower or kw in category_lower for kw in cls.NON_SUBSCRIPTION_KEYWORDS):
                continue

            expenses.append(tx)

        # 2. Group expenses by normalized vendor using canonical TransactionNormalizer
        grouped: Dict[str, List[Transaction]] = {}
        for tx in expenses:
            meta = TransactionNormalizer.normalize_vendor_and_category(tx.raw_description)
            if meta.get("is_currency_conversion") or meta.get("is_funding"):
                continue
            vendor_key = meta.get("normalized_vendor") or tx.normalized_vendor or "Unknown Vendor"
            grouped.setdefault(vendor_key, []).append(tx)

        subscriptions: List[Subscription] = []
        max_tx_date = max((tx.transaction_date for tx in transactions), default=datetime.datetime.utcnow())
        eval_date = max_tx_date

        for vendor_name, tx_list in grouped.items():
            tx_count = len(tx_list)
            # Sort ascending by transaction date
            tx_list.sort(key=lambda x: x.transaction_date)
            dates = [tx.transaction_date for tx in tx_list]
            amounts = [abs(float(tx.gross_amount)) for tx in tx_list]

            # Normalize vendor metadata from first descriptor
            vendor_meta = TransactionNormalizer.normalize_vendor_and_category(tx_list[0].raw_description)
            is_known_saas = vendor_meta.get("is_known_saas", False)
            known_var_billing = vendor_meta.get("variable_billing", False)

            # Amount metrics
            avg_amount = round(float(np.mean(amounts)), 2)
            latest_amount = round(amounts[-1], 2)
            earliest_amount = round(amounts[0], 2)
            std_amount = float(np.std(amounts)) if tx_count > 1 else 0.0
            cv_amount = (std_amount / avg_amount) if avg_amount > 0 else 0.0

            first_billed = dates[0]
            last_billed = dates[-1]

            # -------------------------------------------------------------
            # CASE A: Single Payment (Cold-Start Detection)
            # -------------------------------------------------------------
            if tx_count == 1:
                # If from a recognized software provider, classify as Potential Subscription
                if is_known_saas:
                    cadence = "monthly"
                    confidence = 0.70
                    cadence_step = 30
                    next_billing = last_billed + datetime.timedelta(days=cadence_step)
                    detection_type = "potential"
                    billing_type = "variable" if known_var_billing else "fixed"
                    status = "active"
                    detection_reason = (
                        f"Single payment detected for recognized SaaS provider ({vendor_name}). "
                        f"Classified as potential {cadence} subscription awaiting second billing cycle."
                    )
                else:
                    # Single payment to an unverified vendor is NOT assumed to be recurring
                    continue

            # -------------------------------------------------------------
            # CASE B: Multiple Payments (Recurring Payment Detection)
            # -------------------------------------------------------------
            else:
                deltas = [(dates[i] - dates[i-1]).days for i in range(1, tx_count)]
                median_delta = float(np.median(deltas))
                std_delta = float(np.std(deltas)) if len(deltas) > 1 else 0.0

                cadence, base_confidence = cls.detect_cadence(dates)
                cadence_step = cls.CADENCE_DAYS.get(cadence, 30)
                next_billing = last_billed + datetime.timedelta(days=cadence_step)

                # Variable Billing Assessment
                # Flagged if known consumption provider or if amounts fluctuate by > 15%
                is_variable = known_var_billing or (cv_amount > 0.15 and is_known_saas)
                billing_type = "variable" if is_variable else "fixed"

                # Price Creep Detection (only applicable to fixed-seat SaaS)
                price_change_pct = 0.0
                if not is_variable and earliest_amount > 0:
                    price_change_pct = round(((latest_amount - earliest_amount) / earliest_amount) * 100, 1)

                # Determine Classification & Confidence
                if 5 <= median_delta <= 9 or 25 <= median_delta <= 35 or 80 <= median_delta <= 100 or 340 <= median_delta <= 390:
                    detection_type = "confirmed"
                    confidence = base_confidence
                    if is_variable:
                        detection_reason = (
                            f"Confirmed {cadence} subscription with variable usage billing ({vendor_name}). "
                            f"{tx_count} billing cycles detected (avg: ${avg_amount:.2f}, range: ${min(amounts):.2f} - ${max(amounts):.2f})."
                        )
                    elif price_change_pct >= 20.0:
                        detection_reason = (
                            f"Confirmed {cadence} subscription with {price_change_pct:+.1f}% price creep alert over {tx_count} cycles."
                        )
                    elif abs(price_change_pct) >= 5.0:
                        trend_word = "increase" if price_change_pct > 0 else "decrease"
                        detection_reason = (
                            f"Confirmed {cadence} subscription with {price_change_pct:+.1f}% price {trend_word} detected over {tx_count} cycles."
                        )
                    else:
                        detection_reason = (
                            f"Confirmed {cadence} subscription supported by {tx_count} recurring payments with steady cadence."
                        )
                elif is_known_saas:
                    if median_delta < 5:
                        # Multiple payments on same or adjacent days: cold-start testing, not a recurring cadence
                        detection_type = "potential"
                        confidence = 0.70
                        detection_reason = (
                            f"Multiple payments detected on the same or adjacent days for recognized SaaS provider ({vendor_name}) "
                            f"(median delta {median_delta:.0f} days). Classified as potential {cadence} subscription awaiting recurring billing cycle."
                        )
                    else:
                        # Recognized SaaS provider with flexible/usage intervals
                        detection_type = "confirmed"
                        confidence = 0.78
                        detection_reason = (
                            f"Recurring payments to recognized SaaS provider ({vendor_name}) with flexible interval "
                            f"(median {median_delta:.0f} days). Classified as {cadence} subscription."
                        )
                else:
                    # Unknown vendor with highly irregular intervals
                    detection_type = "uncertain"
                    confidence = 0.52
                    detection_reason = (
                        f"Uncertain recurrence: payment intervals vary widely (median {median_delta:.0f} days, std dev {std_delta:.1f} days)."
                    )

                # Determine Lifecycle Status
                days_since_last = (eval_date - last_billed).days
                if days_since_last > cadence_step * 2.5:
                    status = "cancelled"
                    detection_reason += f" Inactive: No payment detected in {days_since_last} days."
                elif vendor_meta.get("priority_tier", 2) == 3 and avg_amount >= 80.0:
                    status = "zombie"
                    detection_reason += " High-cost discretionary zombie tool."
                elif price_change_pct >= 20.0 and not is_variable:
                    status = "at_risk"
                else:
                    status = "active"

            # Instantiate Subscription object
            sub = Subscription(
                business_id=business_id,
                vendor_name=vendor_name,
                category=vendor_meta.get("category", "General SaaS"),
                cadence=cadence,
                average_amount=avg_amount,
                latest_amount=latest_amount,
                currency=tx_list[-1].currency or "USD",
                first_billed_date=first_billed,
                last_billed_date=last_billed,
                next_billing_date=next_billing,
                price_change_pct=price_change_pct if tx_count > 1 else 0.0,
                confidence_score=round(confidence, 2),
                priority_tier=vendor_meta.get("priority_tier", 2),
                redundancy_group=vendor_meta.get("redundancy_group"),
                status=status,
                detection_type=detection_type,
                detection_reason=detection_reason,
                billing_type=billing_type,
                utilization_score=0.9 if vendor_meta.get("priority_tier") == 1 else 0.65,
                is_essential=vendor_meta.get("is_essential", True)
            )
            subscriptions.append(sub)

        return subscriptions
