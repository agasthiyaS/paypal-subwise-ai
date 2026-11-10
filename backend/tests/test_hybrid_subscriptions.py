import datetime
import pytest
from app.models.transaction import Transaction
from app.services.subscription_detector import SubscriptionDetector
from app.services.normalizer import TransactionNormalizer

def test_known_saas_single_payment_detected_as_potential():
    now = datetime.datetime.utcnow()
    # Single payment to GitHub
    tx = Transaction(
        business_id=1,
        raw_description="GITHUB *TEAM PLAN 123",
        normalized_vendor="GitHub",
        category="Developer Tools",
        gross_amount=-21.0,
        net_amount=-21.0,
        transaction_date=now
    )
    subs = SubscriptionDetector.identify_subscriptions([tx], business_id=1)
    assert len(subs) == 1
    sub = subs[0]
    assert sub.vendor_name == "GitHub"
    assert sub.detection_type == "potential"
    assert sub.confidence_score == 0.70
    assert "potential" in sub.detection_reason.lower()
    assert sub.status == "active"
    assert sub.cadence == "monthly"

def test_unknown_vendor_single_payment_not_classified_as_subscription():
    now = datetime.datetime.utcnow()
    # Single payment to a local coffee shop or random merchant
    tx = Transaction(
        business_id=1,
        raw_description="CORNER CAFE DOWNTOWN",
        normalized_vendor="Corner",
        category="General SaaS / Operations",
        gross_amount=-14.50,
        net_amount=-14.50,
        transaction_date=now
    )
    subs = SubscriptionDetector.identify_subscriptions([tx], business_id=1)
    # A single payment to an unknown vendor must NOT be assumed to be a subscription
    assert len(subs) == 0

def test_recurring_fixed_subscription_confirmed():
    d1 = datetime.datetime(2026, 1, 10, 12, 0, 0)
    d2 = datetime.datetime(2026, 2, 10, 12, 0, 0)
    d3 = datetime.datetime(2026, 3, 10, 12, 0, 0)
    txs = [
        Transaction(business_id=1, raw_description="SLACK TECHNOLOGIES", normalized_vendor="Slack", gross_amount=-150.0, net_amount=-150.0, transaction_date=d1),
        Transaction(business_id=1, raw_description="SLACK TECHNOLOGIES", normalized_vendor="Slack", gross_amount=-150.0, net_amount=-150.0, transaction_date=d2),
        Transaction(business_id=1, raw_description="SLACK TECHNOLOGIES", normalized_vendor="Slack", gross_amount=-150.0, net_amount=-150.0, transaction_date=d3),
    ]
    subs = SubscriptionDetector.identify_subscriptions(txs, business_id=1)
    assert len(subs) == 1
    sub = subs[0]
    assert sub.vendor_name == "Slack"
    assert sub.cadence == "monthly"
    assert sub.detection_type == "confirmed"
    assert sub.billing_type == "fixed"
    assert sub.confidence_score >= 0.85
    assert "steady cadence" in sub.detection_reason.lower()

def test_variable_billing_detection_aws_and_openai():
    # AWS monthly payments with fluctuating usage amounts
    d1 = datetime.datetime(2026, 1, 5, 0, 0, 0)
    d2 = datetime.datetime(2026, 2, 5, 0, 0, 0)
    d3 = datetime.datetime(2026, 3, 5, 0, 0, 0)
    txs = [
        Transaction(business_id=1, raw_description="AMZN *AWS CLOUD 102938", normalized_vendor="AWS", gross_amount=-210.45, net_amount=-210.45, transaction_date=d1),
        Transaction(business_id=1, raw_description="AMZN *AWS CLOUD 102938", normalized_vendor="AWS", gross_amount=-340.10, net_amount=-340.10, transaction_date=d2),
        Transaction(business_id=1, raw_description="AMZN *AWS CLOUD 102938", normalized_vendor="AWS", gross_amount=-280.90, net_amount=-280.90, transaction_date=d3),
    ]
    subs = SubscriptionDetector.identify_subscriptions(txs, business_id=1)
    assert len(subs) == 1
    sub = subs[0]
    assert sub.vendor_name == "AWS"
    assert sub.cadence == "monthly"
    assert sub.detection_type == "confirmed"
    assert sub.billing_type == "variable"
    assert "variable usage" in sub.detection_reason.lower()

def test_transaction_direction_and_subwise_exclusion():
    now = datetime.datetime.utcnow()
    txs = [
        # Incoming revenue
        Transaction(business_id=1, raw_description="Payment from customer Acme Corp", normalized_vendor="Acme", gross_amount=2500.0, net_amount=2450.0, transaction_date=now),
        # Initial balance
        Transaction(business_id=1, raw_description="Initial balance", normalized_vendor="PayPal Balance Adjustment", gross_amount=5000.0, net_amount=5000.0, transaction_date=now),
        # SubWise Sandbox Test Payment
        Transaction(business_id=1, raw_description="SubWise AI Sandbox Payment Test", normalized_vendor="Subwise", gross_amount=5.0, net_amount=4.41, transaction_date=now),
    ]
    subs = SubscriptionDetector.identify_subscriptions(txs, business_id=1)
    # Revenue, funding, and SubWise test payments must NEVER be classified as subscriptions
    assert len(subs) == 0

def test_adobe_and_twilio_in_normalizer():
    res_adobe = TransactionNormalizer.normalize_vendor_and_category("ADOBE *CREATIVE CLOUD 408-536-6000")
    assert res_adobe["normalized_vendor"] == "Adobe Creative Cloud"
    assert res_adobe["is_known_saas"] is True
    assert res_adobe["category"] == "Design & Media"

    res_twilio = TransactionNormalizer.normalize_vendor_and_category("TWILIO INC SAN FRANCISCO CA")
    assert res_twilio["normalized_vendor"] == "Twilio"
    assert res_twilio["is_known_saas"] is True
    assert res_twilio["variable_billing"] is True

