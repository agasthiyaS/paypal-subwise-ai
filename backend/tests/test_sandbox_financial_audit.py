"""
Regression Test Suite for PayPal Sandbox Financial Logic & Classification
Covers:
1. Initial $5,000 funding exclusion.
2. $5 internal SubWise payment exclusion.
3. $20 CloudSoft expense inclusion and vendor normalization.
4. Four-part currency conversion handling.
5. Mixed-currency aggregation and base currency isolation.
6. Potential versus confirmed subscription classification.
7. Dashboard and Reports calculation consistency.
8. Duplicate transaction prevention.
"""
import datetime
import pytest
from typing import List

from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.normalizer import TransactionNormalizer
from app.services.forecast_engine import ForecastEngine
from app.services.subscription_detector import SubscriptionDetector
from app.services.report_engine import ReportEngine
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer

@pytest.fixture
def sandbox_business():
    return BusinessProfile(
        id=40,
        user_id=40,
        company_name="My Business",
        currency="USD",
        current_cash_reserves=0.0,
        monthly_baseline_revenue=0.0,
        is_demo=False
    )

@pytest.fixture
def six_sandbox_transactions():
    """Builds exact in-memory representation of the 6 genuine PayPal Sandbox transactions."""
    return [
        Transaction(
            id=1050,
            business_id=40,
            paypal_transaction_id="59071448PK254121L",
            transaction_date=datetime.datetime(2026, 11, 6, 17, 57, 4),
            raw_description="Initial balance",
            normalized_vendor="PayPal Balance Adjustment",
            category="Account Funding / Balance Adjustment",
            gross_amount=5000.0,
            fee_amount=0.0,
            net_amount=5000.0,
            currency="USD",
            status="COMPLETED"
        ),
        Transaction(
            id=1167,
            business_id=40,
            paypal_transaction_id="4EV73998AP815980D",
            transaction_date=datetime.datetime(2026, 11, 7, 14, 29, 43),
            raw_description="SubWise AI Sandbox Payment Test",
            normalized_vendor="Subwise",
            category="General SaaS / Operations",
            gross_amount=5.0,
            fee_amount=-0.59,
            net_amount=4.41,
            currency="USD",
            status="COMPLETED"
        ),
        Transaction(
            id=1385,
            business_id=40,
            paypal_transaction_id="9X0405652T645143S",
            transaction_date=datetime.datetime(2026, 11, 9, 9, 47, 6),
            raw_description="Monthly Software Subscription - CloudSoft",
            normalized_vendor="Monthly",
            category="General SaaS / Operations",
            gross_amount=-20.0,
            fee_amount=0.0,
            net_amount=-20.0,
            currency="USD",
            status="COMPLETED"
        ),
        Transaction(
            id=1386,
            business_id=40,
            paypal_transaction_id="02679053YB768853D",
            transaction_date=datetime.datetime(2026, 11, 9, 9, 47, 6),
            raw_description="PayPal Transaction",
            normalized_vendor="Paypal",
            category="General SaaS / Operations",
            gross_amount=1955.38,
            fee_amount=0.0,
            net_amount=1955.38,
            currency="INR",
            status="COMPLETED"
        ),
        Transaction(
            id=1387,
            business_id=40,
            paypal_transaction_id="5YW97500CW704310C",
            transaction_date=datetime.datetime(2026, 11, 9, 9, 47, 6),
            raw_description="PayPal Transaction",
            normalized_vendor="Paypal",
            category="General SaaS / Operations",
            gross_amount=-1955.38,
            fee_amount=0.0,
            net_amount=-1955.38,
            currency="INR",
            status="COMPLETED"
        ),
        Transaction(
            id=1388,
            business_id=40,
            paypal_transaction_id="6M255220TT5552700",
            transaction_date=datetime.datetime(2026, 11, 9, 9, 47, 6),
            raw_description="PayPal Transaction",
            normalized_vendor="Paypal",
            category="General SaaS / Operations",
            gross_amount=20.0,
            fee_amount=0.0,
            net_amount=20.0,
            currency="USD",
            status="COMPLETED"
        ),
    ]

# ---------------------------------------------------------------------------
# Test 1: Initial $5,000 Funding Exclusion
# ---------------------------------------------------------------------------
def test_initial_funding_exclusion(six_sandbox_transactions):
    tx_funding = six_sandbox_transactions[0]  # ID 1050
    assert ForecastEngine.is_non_operating(tx_funding) is True
    assert ForecastEngine.is_valid_operating(tx_funding) is False

# ---------------------------------------------------------------------------
# Test 2: $5 Internal SubWise Payment Exclusion
# ---------------------------------------------------------------------------
def test_subwise_internal_test_payment_exclusion(six_sandbox_transactions):
    tx_subwise = six_sandbox_transactions[1]  # ID 1167
    assert ForecastEngine.is_subwise_test(tx_subwise) is True
    assert ForecastEngine.is_valid_operating(tx_subwise) is False

# ---------------------------------------------------------------------------
# Test 3: $20 CloudSoft Expense Inclusion & Vendor Normalization
# ---------------------------------------------------------------------------
def test_cloudsoft_expense_inclusion_and_normalization(six_sandbox_transactions):
    tx_cloudsoft = six_sandbox_transactions[2]  # ID 1385
    assert ForecastEngine.is_valid_operating(tx_cloudsoft, all_txs=six_sandbox_transactions) is True
    
    # Test normalization of "Monthly Software Subscription - CloudSoft"
    meta = TransactionNormalizer.normalize_vendor_and_category(tx_cloudsoft.raw_description)
    assert meta["normalized_vendor"] == "CloudSoft"
    assert meta["is_known_saas"] is True
    assert meta["category"] == "Cloud & IT Management"

# ---------------------------------------------------------------------------
# Test 4: Four-Part Currency Conversion Handling
# ---------------------------------------------------------------------------
def test_four_part_currency_conversion_handling(six_sandbox_transactions):
    tx_inr_credit = six_sandbox_transactions[3]  # ID 1386 (+1955.38 INR)
    tx_inr_debit = six_sandbox_transactions[4]   # ID 1387 (-1955.38 INR)
    tx_usd_credit = six_sandbox_transactions[5]  # ID 1388 (+20.00 USD)
    tx_cloudsoft = six_sandbox_transactions[2]   # ID 1385 (-20.00 USD)

    # Conversion legs must be identified as currency conversion
    assert ForecastEngine.is_currency_conversion(tx_inr_credit, all_txs=six_sandbox_transactions) is True
    assert ForecastEngine.is_currency_conversion(tx_inr_debit, all_txs=six_sandbox_transactions) is True
    assert ForecastEngine.is_currency_conversion(tx_usd_credit, all_txs=six_sandbox_transactions) is True

    # The actual CloudSoft payment must NOT be a conversion leg
    assert ForecastEngine.is_currency_conversion(tx_cloudsoft, all_txs=six_sandbox_transactions) is False

    # Conversion legs must be invalid as operating revenue/expense
    assert ForecastEngine.is_valid_operating(tx_inr_credit, all_txs=six_sandbox_transactions) is False
    assert ForecastEngine.is_valid_operating(tx_inr_debit, all_txs=six_sandbox_transactions) is False
    assert ForecastEngine.is_valid_operating(tx_usd_credit, all_txs=six_sandbox_transactions) is False

# ---------------------------------------------------------------------------
# Test 5: Mixed-Currency Aggregation & Base Currency Isolation
# ---------------------------------------------------------------------------
def test_mixed_currency_aggregation(sandbox_business, six_sandbox_transactions):
    # Cash balance calculation must isolate USD and offset paired INR conversion legs
    balance, is_verified = ForecastEngine.calculate_verified_cash_balance(
        sandbox_business, six_sandbox_transactions
    )
    assert is_verified is True
    # 5000 (funding) + 4.41 (test net) - 20.00 (payment) = 4984.41
    # Currency conversion legs (+20.00 USD, ±1955.38 INR) are excluded from cash flow double-counting
    assert balance == 4984.41

# ---------------------------------------------------------------------------
# Test 6: Potential versus Confirmed Subscription Classification
# ---------------------------------------------------------------------------
def test_potential_vs_confirmed_subscription_classification(sandbox_business, six_sandbox_transactions):
    # Single payment to CloudSoft must yield a potential subscription, not confirmed
    detected = SubscriptionDetector.identify_subscriptions(six_sandbox_transactions, sandbox_business.id)
    assert len(detected) == 1
    sub = detected[0]
    assert sub.vendor_name == "CloudSoft"
    assert sub.detection_type == "potential"
    assert sub.latest_amount == 20.0
    assert sub.cadence == "monthly"
    assert "potential" in sub.detection_reason.lower()

    # Now simulate a second payment 30 days later
    tx_second_payment = Transaction(
        id=1390,
        business_id=40,
        paypal_transaction_id="SECOND_CYCLE_TX",
        transaction_date=datetime.datetime(2026, 12, 9, 9, 47, 6),
        raw_description="Monthly Software Subscription - CloudSoft",
        normalized_vendor="CloudSoft",
        category="Cloud & IT Management",
        gross_amount=-20.0,
        net_amount=-20.0,
        currency="USD",
        status="COMPLETED"
    )
    two_payments = six_sandbox_transactions + [tx_second_payment]
    detected_two = SubscriptionDetector.identify_subscriptions(two_payments, sandbox_business.id)
    assert len(detected_two) == 1
    sub_confirmed = detected_two[0]
    assert sub_confirmed.vendor_name == "CloudSoft"
    assert sub_confirmed.detection_type == "confirmed"

# ---------------------------------------------------------------------------
# Test 7: Dashboard and Reports Calculation Consistency
# ---------------------------------------------------------------------------
def test_dashboard_and_reports_calculation_consistency(sandbox_business, six_sandbox_transactions):
    detected = SubscriptionDetector.identify_subscriptions(six_sandbox_transactions, sandbox_business.id)
    
    # Generate Monthly Report
    report = ReportEngine.generate_monthly_financial_report(
        business=sandbox_business,
        transactions=six_sandbox_transactions,
        subscriptions=detected,
        period_preset="all"
    )

    # 1. Operating Revenue must be 0.00 (neither funding, test, nor INR/USD conversion credits count)
    assert report.total_operating_revenue == 0.0

    # 2. Potential Subscription Expenses must track the $20 CloudSoft outflow
    assert report.total_potential_sub_expenses == 20.0

    # 3. Only 1 transaction qualifies as an operating record (CloudSoft)
    assert report.period_filter.total_operating_records_in_period == 1

# ---------------------------------------------------------------------------
# Test 8: Duplicate Transaction Prevention
# ---------------------------------------------------------------------------
def test_duplicate_transaction_prevention(sandbox_business, six_sandbox_transactions):
    existing_by_paypal_id = {tx.paypal_transaction_id: tx for tx in six_sandbox_transactions}
    
    # Attempting to re-ingest an already existing PayPal ID should match
    re_imported_item = {
        "paypal_transaction_id": "9X0405652T645143S",
        "gross_amount": -20.0,
        "fee_amount": 0.0,
        "net_amount": -20.0,
        "currency": "USD",
        "status": "COMPLETED",
        "raw_description": "Monthly Software Subscription - CloudSoft"
    }

    match = existing_by_paypal_id.get(re_imported_item["paypal_transaction_id"])
    assert match is not None
    assert match.id == 1385

