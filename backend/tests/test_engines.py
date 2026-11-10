import datetime
import pytest
from app.services.normalizer import TransactionNormalizer
from app.services.subscription_detector import SubscriptionDetector
from app.services.cashflow_simulator import CashFlowSimulator
from app.services.recommendation_engine import RecommendationEngine
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.business import BusinessProfile

def test_normalizer_known_vendors():
    res1 = TransactionNormalizer.normalize_vendor_and_category("AMZN *AWS CLOUD 102938")
    assert res1["normalized_vendor"] == "AWS"
    assert res1["category"] == "Cloud Infrastructure"

    res2 = TransactionNormalizer.normalize_vendor_and_category("SLACK TECH INC MO PYMT")
    assert res2["normalized_vendor"] == "Slack"
    assert res2["category"] == "Team Collaboration"

    res3 = TransactionNormalizer.normalize_vendor_and_category("ZOOM.US 888-799-9666")
    assert res3["normalized_vendor"] == "Zoom"
    assert res3["category"] == "Video Conferencing"

def test_subscription_detection():
    # Construct 3 monthly transactions for Slack
    d1 = datetime.datetime(2026, 1, 15, 10, 0, 0)
    d2 = datetime.datetime(2026, 2, 15, 10, 0, 0)
    d3 = datetime.datetime(2026, 3, 15, 10, 0, 0)

    txs = [
        Transaction(business_id=1, raw_description="SLACK TECH INC MO PYMT", normalized_vendor="Slack", gross_amount=-180.0, net_amount=-180.0, transaction_date=d1),
        Transaction(business_id=1, raw_description="SLACK TECH INC MO PYMT", normalized_vendor="Slack", gross_amount=-180.0, net_amount=-180.0, transaction_date=d2),
        Transaction(business_id=1, raw_description="SLACK TECH INC MO PYMT", normalized_vendor="Slack", gross_amount=-225.0, net_amount=-225.0, transaction_date=d3),
    ]

    subs = SubscriptionDetector.identify_subscriptions(txs, business_id=1)
    assert len(subs) == 1
    sub = subs[0]
    assert sub.vendor_name == "Slack"
    assert sub.cadence == "monthly"
    assert sub.latest_amount == 225.0
    assert sub.price_change_pct > 20.0 # Price creep detected
    assert sub.status == "at_risk"

def test_cashflow_simulator_baseline_and_shock():
    biz = BusinessProfile(
        id=1,
        company_name="Acme AI",
        monthly_baseline_revenue=20000.0,
        current_cash_reserves=50000.0
    )

    now = datetime.datetime.utcnow()
    subs = [
        Subscription(id=1, business_id=1, vendor_name="AWS", latest_amount=500.0, cadence="monthly", priority_tier=1, status="active", first_billed_date=now, last_billed_date=now, next_billing_date=now),
        Subscription(id=2, business_id=1, vendor_name="Zoom", latest_amount=100.0, cadence="monthly", priority_tier=3, status="active", first_billed_date=now, last_billed_date=now, next_billing_date=now),
    ]

    # Baseline simulation
    res_base = CashFlowSimulator.run_simulation(biz, subs, revenue_shock_pct=0.0)
    assert res_base["monthly_recurring_subscriptions"] == 600.0
    assert len(res_base["timeline"]) == 12

    # Stress test: 50% revenue shock
    res_shock = CashFlowSimulator.run_simulation(biz, subs, revenue_shock_pct=-50.0)
    assert res_shock["revenue_shock_pct"] == -50.0

    # Pause Tier 3
    res_paused = CashFlowSimulator.run_simulation(biz, subs, revenue_shock_pct=-50.0, pause_tier_3=True)
    assert res_paused["optimized_recurring_subscriptions"] == 500.0
    assert res_paused["monthly_savings_from_paused"] == 100.0

def test_recommendation_redundancy():
    biz = BusinessProfile(id=1, company_name="Acme AI", monthly_baseline_revenue=20000.0, current_cash_reserves=50000.0)
    now = datetime.datetime.utcnow()
    subs = [
        Subscription(id=1, business_id=1, vendor_name="Zoom", category="Video Conferencing", redundancy_group="video_conferencing", latest_amount=65.0, cadence="monthly", priority_tier=3, status="active", first_billed_date=now, last_billed_date=now, next_billing_date=now),
        Subscription(id=2, business_id=1, vendor_name="Google Meet", category="Video Conferencing", redundancy_group="video_conferencing", latest_amount=72.0, cadence="monthly", priority_tier=1, status="active", first_billed_date=now, last_billed_date=now, next_billing_date=now),
    ]

    recs = RecommendationEngine.generate_recommendations(biz, subs)
    consolidate_recs = [r for r in recs if r.action_type == "CONSOLIDATE"]
    assert len(consolidate_recs) >= 1
    assert "Zoom" in consolidate_recs[0].title

