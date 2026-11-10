import datetime
import pytest
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.recommendation_engine import RecommendationEngine

@pytest.fixture
def business():
    return BusinessProfile(
        id=1,
        user_id=1,
        company_name="Acme Tech Labs",
        monthly_baseline_revenue=5000.0,
        current_cash_reserves=25000.0
    )

def test_insufficient_data_scenarios(business):
    # Empty subscriptions
    recs = RecommendationEngine.generate_recommendations(business, [])
    assert recs == []

    # Only cancelled subscriptions
    now = datetime.datetime.utcnow()
    cancelled_sub = Subscription(
        id=1, business_id=1, vendor_name="Slack", category="Team Collaboration",
        latest_amount=100.0, average_amount=100.0, cadence="monthly",
        status="cancelled", first_billed_date=now, last_billed_date=now, next_billing_date=now
    )
    recs = RecommendationEngine.generate_recommendations(business, [cancelled_sub])
    assert recs == []

    # Non-operating funding transactions should not be treated as business revenue
    funding_tx = Transaction(
        id=1, business_id=1, transaction_date=now, raw_description="Initial balance",
        normalized_vendor="PayPal Balance Adjustment", category="Account Funding / Balance Adjustment",
        gross_amount=5000.0, net_amount=5000.0
    )
    subwise_tx = Transaction(
        id=2, business_id=1, transaction_date=now, raw_description="SubWise AI Sandbox Payment Test",
        normalized_vendor="Subwise", category="General SaaS / Operations",
        gross_amount=-5.0, net_amount=-5.0
    )
    assert RecommendationEngine.is_non_operating(funding_tx) is True
    assert RecommendationEngine.is_non_operating(subwise_tx) is True

def test_price_increase_detection(business):
    now = datetime.datetime.utcnow()
    sub = Subscription(
        id=1, business_id=1, vendor_name="Datadog", category="DevOps & Monitoring",
        cadence="monthly", average_amount=120.0, latest_amount=150.0,
        price_change_pct=25.0, status="at_risk", detection_type="confirmed",
        billing_type="fixed", priority_tier=2,
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )
    recs = RecommendationEngine.generate_recommendations(business, [sub])
    reneg_recs = [r for r in recs if r.action_type == "RENEGOTIATE"]
    
    assert len(reneg_recs) == 1
    rec = reneg_recs[0]
    assert rec.vendor_name == "Datadog"
    assert "+25.0%" in rec.identified_issue
    assert "150.00" in rec.supporting_evidence
    assert rec.potential_monthly_saving >= 25.0
    assert rec.confidence in ["high", "medium"]
    assert rec.negotiation_script is not None
    assert "Datadog" in rec.negotiation_script

def test_redundant_subscription_recommendations(business):
    now = datetime.datetime.utcnow()
    sub_slack = Subscription(
        id=1, business_id=1, vendor_name="Slack", category="Team Collaboration",
        redundancy_group="messaging_collab", latest_amount=120.0, average_amount=120.0,
        cadence="monthly", priority_tier=2, status="active",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )
    sub_teams = Subscription(
        id=2, business_id=1, vendor_name="Microsoft Teams", category="Team Collaboration",
        redundancy_group="messaging_collab", latest_amount=80.0, average_amount=80.0,
        cadence="monthly", priority_tier=2, status="active",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )

    recs = RecommendationEngine.generate_recommendations(business, [sub_slack, sub_teams])
    consolidate_recs = [r for r in recs if r.action_type == "CONSOLIDATE"]

    assert len(consolidate_recs) == 1
    rec = consolidate_recs[0]
    assert "Review Overlap" in rec.title
    assert "Microsoft Teams" in rec.title
    assert "Slack" in rec.title
    # Does NOT recommend immediate blind cancellation
    assert "Conduct user survey" in rec.action_plan or "user survey" in rec.action_plan

def test_revenue_based_recommendations(business):
    now = datetime.datetime.utcnow()
    # Monthly subscription commitment = $400
    sub = Subscription(
        id=1, business_id=1, vendor_name="AWS", category="Cloud Infrastructure",
        cadence="monthly", latest_amount=400.0, average_amount=400.0,
        priority_tier=1, status="active", detection_type="confirmed",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )

    # Operating revenue is $1,000 -> 40% ratio (exceeds 25% threshold)
    tx_revenue = Transaction(
        id=1, business_id=1, transaction_date=now, raw_description="Customer Contract Inflow",
        normalized_vendor="Customer Inc", category="Operating Revenue",
        gross_amount=1000.0, net_amount=970.0
    )

    recs = RecommendationEngine.generate_recommendations(business, [sub], [tx_revenue])
    rev_recs = [r for r in recs if r.action_type == "REVENUE_AUDIT"]

    assert len(rev_recs) == 1
    rec = rev_recs[0]
    assert "High Subscription Burden" in rec.identified_issue
    assert "40.0%" in rec.identified_issue
    assert rec.confidence == "high"

    # When revenue is 0 or only non-operating funding exists, REVENUE_AUDIT should NOT be triggered
    tx_funding = Transaction(
        id=2, business_id=1, transaction_date=now, raw_description="Initial balance",
        normalized_vendor="PayPal Balance Adjustment", category="Account Funding / Balance Adjustment",
        gross_amount=5000.0, net_amount=5000.0
    )
    recs_funding = RecommendationEngine.generate_recommendations(business, [sub], [tx_funding])
    rev_recs_funding = [r for r in recs_funding if r.action_type == "REVENUE_AUDIT"]
    assert len(rev_recs_funding) == 0

def test_high_cost_not_cancelled_and_annual_switch(business):
    now = datetime.datetime.utcnow()
    # High-cost mission-critical subscription ($300/mo)
    sub_aws = Subscription(
        id=1, business_id=1, vendor_name="AWS", category="Cloud Infrastructure",
        cadence="monthly", latest_amount=300.0, average_amount=300.0,
        priority_tier=1, status="active", detection_type="confirmed",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )

    recs = RecommendationEngine.generate_recommendations(business, [sub_aws])
    # High cost must NOT be cancelled
    cancel_recs = [r for r in recs if r.action_type == "CANCEL"]
    assert len(cancel_recs) == 0

    # Instead should have REVIEW for plan tier and/or SWITCH_ANNUAL for mission critical
    review_recs = [r for r in recs if r.action_type in ["REVIEW", "SWITCH_ANNUAL"]]
    assert len(review_recs) >= 1

def test_evidence_based_cancellation_only_for_zombie(business):
    now = datetime.datetime.utcnow()
    # Active tool should NOT be cancelled
    sub_active = Subscription(
        id=1, business_id=1, vendor_name="Notion", category="Productivity",
        cadence="monthly", latest_amount=50.0, average_amount=50.0,
        priority_tier=3, status="active", detection_type="confirmed",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )
    recs = RecommendationEngine.generate_recommendations(business, [sub_active])
    assert len([r for r in recs if r.action_type == "CANCEL"]) == 0

    # Verified zombie discretionary tool CAN be recommended for cancellation
    sub_zombie = Subscription(
        id=2, business_id=1, vendor_name="Loom", category="Video Messaging",
        cadence="monthly", latest_amount=60.0, average_amount=60.0,
        priority_tier=3, status="zombie", detection_type="confirmed",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )
    recs_zombie = RecommendationEngine.generate_recommendations(business, [sub_zombie])
    cancel_recs = [r for r in recs_zombie if r.action_type == "CANCEL"]
    assert len(cancel_recs) == 1
    assert "Loom" in cancel_recs[0].title
    assert "Verified Inactive" in cancel_recs[0].identified_issue

def test_potential_subscription_cautious_review(business):
    now = datetime.datetime.utcnow()
    # Potential subscription (single charge from recognized SaaS awaiting confirmation)
    sub_potential = Subscription(
        id=1, business_id=1, vendor_name="Canva", category="Design",
        cadence="monthly", latest_amount=15.0, average_amount=15.0,
        priority_tier=3, status="active", detection_type="potential",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )
    recs = RecommendationEngine.generate_recommendations(business, [sub_potential])
    # Must NOT recommend cancellation
    assert len([r for r in recs if r.action_type == "CANCEL"]) == 0
    # Should recommend cautious review of trial/first cycle
    review_recs = [r for r in recs if r.action_type == "REVIEW"]
    assert len(review_recs) == 1
    assert "Verify Trial" in review_recs[0].title
    assert review_recs[0].confidence == "low"

