
import datetime
import pytest
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.recommendation import PurchaseSimulationRequest
from app.services.recommendation_engine import RecommendationEngine


@pytest.fixture
def business_healthy():
    return BusinessProfile(
        id=1,
        user_id=1,
        company_name="Apex Global Tech",
        monthly_baseline_revenue=10000.0,
        current_cash_reserves=50000.0
    )


@pytest.fixture
def business_lean():
    return BusinessProfile(
        id=2,
        user_id=2,
        company_name="Lean Early Startup",
        monthly_baseline_revenue=2000.0,
        current_cash_reserves=1500.0
    )


def test_upcoming_renewal_risk_annual(business_healthy):
    """
    Test that a large confirmed annual renewal due in month 1/2 generates
    a calendar-aware RENEWAL_RISK recommendation.
    """
    now = datetime.datetime.utcnow()
    # 2 months of verified revenue txs
    tx1 = Transaction(
        id=1, business_id=1, transaction_date=now - datetime.timedelta(days=45),
        status="COMPLETED", gross_amount=8000.0, net_amount=7800.0,
        normalized_vendor="Client Wire", raw_description="Operating revenue invoice",
        category="Sales Revenue"
    )
    tx2 = Transaction(
        id=2, business_id=1, transaction_date=now - datetime.timedelta(days=15),
        status="COMPLETED", gross_amount=8500.0, net_amount=8300.0,
        normalized_vendor="Client Wire", raw_description="Operating revenue invoice",
        category="Sales Revenue"
    )

    # Annual subscription due in 20 days (Month 1)
    sub_annual = Subscription(
        id=10, business_id=1, vendor_name="Salesforce CRM", category="Sales & Marketing",
        cadence="annual", latest_amount=3600.0, average_amount=3600.0,
        status="active", detection_type="confirmed", priority_tier=1,
        next_billing_date=now + datetime.timedelta(days=20),
        first_billed_date=now - datetime.timedelta(days=345),
        last_billed_date=now - datetime.timedelta(days=345)
    )

    recs = RecommendationEngine.generate_recommendations(business_healthy, [sub_annual], [tx1, tx2])
    annual_risk_recs = [r for r in recs if r.action_type == "RENEWAL_RISK" and "Salesforce CRM" in r.title]

    assert len(annual_risk_recs) == 1
    rec = annual_risk_recs[0]
    assert "Salesforce CRM" in rec.title
    assert "3600.00" in rec.supporting_evidence or "3,600" in rec.supporting_evidence
    assert rec.confidence == "high"
    assert "liquid reserves" in rec.action_plan.lower() or "audit team license" in rec.action_plan.lower()


def test_multiple_renewal_concentration(business_healthy):
    """
    Test that multiple subscriptions renewing in the same month triggers a
    staggering / renewal concentration alert.
    """
    now = datetime.datetime.utcnow()
    tx1 = Transaction(
        id=1, business_id=1, transaction_date=now - datetime.timedelta(days=40),
        status="COMPLETED", gross_amount=5000.0, net_amount=4900.0,
        normalized_vendor="Customer", raw_description="Sales payment",
        category="Sales Revenue"
    )
    tx2 = Transaction(
        id=2, business_id=1, transaction_date=now - datetime.timedelta(days=10),
        status="COMPLETED", gross_amount=5000.0, net_amount=4900.0,
        normalized_vendor="Customer", raw_description="Sales payment",
        category="Sales Revenue"
    )

    # Two monthly subscriptions both renewing in Month 1
    sub1 = Subscription(
        id=1, business_id=1, vendor_name="HubSpot", category="Sales & Marketing",
        cadence="monthly", latest_amount=300.0, average_amount=300.0,
        status="active", detection_type="confirmed", priority_tier=2,
        next_billing_date=now + datetime.timedelta(days=10),
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=20)
    )
    sub2 = Subscription(
        id=2, business_id=1, vendor_name="Zendesk", category="Customer Support",
        cadence="monthly", latest_amount=250.0, average_amount=250.0,
        status="active", detection_type="confirmed", priority_tier=2,
        next_billing_date=now + datetime.timedelta(days=12),
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=18)
    )

    recs = RecommendationEngine.generate_recommendations(business_healthy, [sub1, sub2], [tx1, tx2])
    concentration_recs = [r for r in recs if r.action_type == "RENEWAL_RISK" and "Concentration" in r.title]

    assert len(concentration_recs) >= 1
    rec = concentration_recs[0]
    assert "Renewal Clustering" in rec.identified_issue or "renew" in rec.identified_issue
    assert "HubSpot" in rec.supporting_evidence or "Zendesk" in rec.supporting_evidence


def test_insufficient_operating_revenue_protection(business_healthy):
    """
    Test that when historical operating revenue is 0 or transactions are absent,
    no fake renewal risk or cashflow shortfall recommendations are fabricated.
    """
    # Empty transactions list
    recs = RecommendationEngine.generate_recommendations(business_healthy, [], [])
    assert recs == []

    # Only funding transactions
    funding_tx = Transaction(
        id=1, business_id=1, transaction_date=datetime.datetime.utcnow(),
        status="COMPLETED", gross_amount=10000.0, net_amount=10000.0,
        raw_description="PayPal Balance Top Up", normalized_vendor="PayPal Balance",
        category="Account Funding / Balance Adjustment"
    )
    recs = RecommendationEngine.generate_recommendations(business_healthy, [], [funding_tx])
    assert recs == []


def test_new_subscription_affordability_verdict_affordable(business_healthy):
    """
    Test simulator returns 'Affordable under current assumptions' when revenue and cash are strong.
    """
    now = datetime.datetime.utcnow()
    tx1 = Transaction(
        id=1, business_id=1, transaction_date=now - datetime.timedelta(days=45),
        status="COMPLETED", gross_amount=12000.0, net_amount=11800.0,
        normalized_vendor="Client Revenue", raw_description="Product sales", category="Sales Revenue"
    )
    tx2 = Transaction(
        id=2, business_id=1, transaction_date=now - datetime.timedelta(days=15),
        status="COMPLETED", gross_amount=12000.0, net_amount=11800.0,
        normalized_vendor="Client Revenue", raw_description="Product sales", category="Sales Revenue"
    )

    req = PurchaseSimulationRequest(
        proposed_vendor="Notion Enterprise",
        amount=50.0,
        cadence="monthly",
        business_purpose="Team workspace"
    )

    res = RecommendationEngine.simulate_purchase(business_healthy, [], [tx1, tx2], req)
    assert res.verdict == "Affordable under current assumptions"
    assert res.verdict_badge == "success"
    assert res.projected_shortfall_detected is False
    assert res.monthly_equivalent_cost == 50.0
    assert res.annual_cost == 600.0
    assert res.is_hypothetical_simulation is True


def test_new_subscription_affordability_verdict_postpone(business_lean):
    """
    Test simulator returns 'Consider postponing' when proposed purchase causes a cash shortfall.
    """
    now = datetime.datetime.utcnow()
    # Initial balance transaction of $1,500
    funding_tx = Transaction(
        id=99, business_id=2, transaction_date=now - datetime.timedelta(days=60),
        status="COMPLETED", gross_amount=1500.0, net_amount=1500.0,
        raw_description="PayPal initial reserve deposit", normalized_vendor="PayPal Balance",
        category="Account Funding / Balance Adjustment"
    )
    # Lean business has $500 monthly revenue with $800 operating expenses
    tx1 = Transaction(
        id=1, business_id=2, transaction_date=now - datetime.timedelta(days=45),
        status="COMPLETED", gross_amount=500.0, net_amount=480.0,
        normalized_vendor="Customer", raw_description="Client service", category="Sales Revenue"
    )
    tx2 = Transaction(
        id=2, business_id=2, transaction_date=now - datetime.timedelta(days=15),
        status="COMPLETED", gross_amount=500.0, net_amount=480.0,
        normalized_vendor="Customer", raw_description="Client service", category="Sales Revenue"
    )
    # Existing non-sub expense of $800/mo
    exp_tx1 = Transaction(
        id=3, business_id=2, transaction_date=now - datetime.timedelta(days=40),
        status="COMPLETED", gross_amount=-800.0, net_amount=-800.0,
        normalized_vendor="Office Lease", raw_description="Office rent", category="Rent & Facilities"
    )
    exp_tx2 = Transaction(
        id=4, business_id=2, transaction_date=now - datetime.timedelta(days=10),
        status="COMPLETED", gross_amount=-800.0, net_amount=-800.0,
        normalized_vendor="Office Lease", raw_description="Office rent", category="Rent & Facilities"
    )

    # Propose an annual software purchase of $2,000 upfront
    req = PurchaseSimulationRequest(
        proposed_vendor="Enterprise ERP Suite",
        amount=2000.0,
        cadence="annual",
        business_purpose="Accounting ERP"
    )

    res = RecommendationEngine.simulate_purchase(business_lean, [], [funding_tx, tx1, tx2, exp_tx1, exp_tx2], req)
    assert res.verdict == "Consider postponing"
    assert res.verdict_badge == "danger"
    assert res.projected_shortfall_detected is True
    assert "postponing" in res.verdict_explanation.lower()
    assert len(res.action_advice) >= 1


def test_monthly_vs_annual_payment_comparison(business_healthy):
    """
    Test accurate calculation of monthly vs annual payment metrics.
    """
    req = PurchaseSimulationRequest(
        proposed_vendor="CloudWatch Pro",
        amount=100.0,
        cadence="monthly"
    )

    res = RecommendationEngine.simulate_purchase(business_healthy, [], [], req)
    comp = res.annual_vs_monthly
    assert comp is not None
    assert comp.monthly_payment_amount == 100.0
    assert comp.annual_payment_amount == 1200.0
    assert comp.annualized_monthly_cost == 100.0
    assert comp.immediate_cash_outflow_difference == 1100.0  # $1200 - $100
    assert comp.has_verified_discount is False
    assert "Never assume an annual discount is guaranteed" in comp.discount_disclosure


def test_verified_vs_hypothetical_discount(business_healthy):
    """
    Test that verified discounts are applied only when user explicitly provides them.
    """
    # 1. With verified discount of 20%
    req_with_discount = PurchaseSimulationRequest(
        proposed_vendor="Figma Enterprise",
        amount=100.0,
        cadence="monthly",
        verified_annual_discount_pct=20.0
    )
    res1 = RecommendationEngine.simulate_purchase(business_healthy, [], [], req_with_discount)
    comp1 = res1.annual_vs_monthly
    assert comp1.has_verified_discount is True
    assert comp1.discount_pct == 20.0
    # $100 * 12 * 0.8 = $960
    assert comp1.annual_payment_amount == 960.0
    assert comp1.annualized_monthly_cost == 80.0
    assert "Verified discount of 20.0%" in comp1.discount_disclosure

    # 2. Without verified discount
    req_no_discount = PurchaseSimulationRequest(
        proposed_vendor="Figma Enterprise",
        amount=100.0,
        cadence="monthly",
        verified_annual_discount_pct=None
    )
    res2 = RecommendationEngine.simulate_purchase(business_healthy, [], [], req_no_discount)
    comp2 = res2.annual_vs_monthly
    assert comp2.has_verified_discount is False
    assert comp2.annual_payment_amount == 1200.0
    assert comp2.annualized_monthly_cost == 100.0


def test_potential_vs_confirmed_subscriptions_separation(business_healthy):
    """
    Test that potential subscriptions are tracked separately and not counted
    as contractual fixed liabilities.
    """
    now = datetime.datetime.utcnow()
    tx1 = Transaction(
        id=1, business_id=1, transaction_date=now - datetime.timedelta(days=40),
        status="COMPLETED", gross_amount=5000.0, net_amount=4900.0,
        normalized_vendor="Client", raw_description="Payment", category="Sales Revenue"
    )
    tx2 = Transaction(
        id=2, business_id=1, transaction_date=now - datetime.timedelta(days=10),
        status="COMPLETED", gross_amount=5000.0, net_amount=4900.0,
        normalized_vendor="Client", raw_description="Payment", category="Sales Revenue"
    )

    pot_sub = Subscription(
        id=99, business_id=1, vendor_name="Canva Pro", category="Design & Creative",
        cadence="monthly", latest_amount=30.0, average_amount=30.0,
        status="active", detection_type="potential", priority_tier=3,
        first_billed_date=now - datetime.timedelta(days=10),
        last_billed_date=now - datetime.timedelta(days=10),
        next_billing_date=now + datetime.timedelta(days=20)
    )

    # In purchase simulator, potential subscriptions are NOT added to current_monthly_burn
    req = PurchaseSimulationRequest(proposed_vendor="Loom", amount=15.0, cadence="monthly")
    res = RecommendationEngine.simulate_purchase(business_healthy, [pot_sub], [tx1, tx2], req)
    assert res.current_monthly_burn == 0.0  # Confirmed subs = 0, so baseline burn is 0


def test_cashflow_shortfall_detection(business_lean):
    """
    Test that when ongoing burn depletes cash in forward timeline,
    a CASHFLOW_PROTECTION alert is generated.
    """
    now = datetime.datetime.utcnow()
    # Initial balance transaction of $2,500
    funding_tx = Transaction(
        id=99, business_id=2, transaction_date=now - datetime.timedelta(days=60),
        status="COMPLETED", gross_amount=2500.0, net_amount=2500.0,
        raw_description="PayPal initial reserve deposit", normalized_vendor="PayPal Balance",
        category="Account Funding / Balance Adjustment"
    )
    # Lean business has $1,000 revenue/mo, but $1,800/mo operating expenses
    tx1 = Transaction(
        id=1, business_id=2, transaction_date=now - datetime.timedelta(days=45),
        status="COMPLETED", gross_amount=1000.0, net_amount=980.0,
        normalized_vendor="Sales", raw_description="Sales", category="Sales Revenue"
    )
    tx2 = Transaction(
        id=2, business_id=2, transaction_date=now - datetime.timedelta(days=15),
        status="COMPLETED", gross_amount=1000.0, net_amount=980.0,
        normalized_vendor="Sales", raw_description="Sales", category="Sales Revenue"
    )
    exp1 = Transaction(
        id=3, business_id=2, transaction_date=now - datetime.timedelta(days=40),
        status="COMPLETED", gross_amount=-1800.0, net_amount=-1800.0,
        normalized_vendor="Rent", raw_description="Rent", category="Rent & Facilities"
    )
    exp2 = Transaction(
        id=4, business_id=2, transaction_date=now - datetime.timedelta(days=10),
        status="COMPLETED", gross_amount=-1800.0, net_amount=-1800.0,
        normalized_vendor="Rent", raw_description="Rent", category="Rent & Facilities"
    )

    # Confirmed sub of $200/mo
    sub = Subscription(
        id=1, business_id=2, vendor_name="Slack", category="Team Collaboration",
        cadence="monthly", latest_amount=200.0, average_amount=200.0,
        status="active", detection_type="confirmed", priority_tier=2,
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=20),
        next_billing_date=now + datetime.timedelta(days=10)
    )

    recs = RecommendationEngine.generate_recommendations(business_lean, [sub], [funding_tx, tx1, tx2, exp1, exp2])
    shortfall_recs = [r for r in recs if r.action_type == "CASHFLOW_PROTECTION" and "Liquidity Deficit" in r.title]

    assert len(shortfall_recs) >= 1
    rec = shortfall_recs[0]
    assert "Depletion" in rec.title or "Deficit" in rec.title
    assert rec.confidence == "high"


def test_single_month_revenue_overcommitment(business_healthy):
    """
    Test that when scheduled renewals consume >= 35% of monthly revenue in a month,
    a CASHFLOW_PROTECTION alert is generated.
    """
    now = datetime.datetime.utcnow()
    # $2,000 monthly revenue
    tx1 = Transaction(
        id=1, business_id=1, transaction_date=now - datetime.timedelta(days=45),
        status="COMPLETED", gross_amount=2000.0, net_amount=1950.0,
        normalized_vendor="Client", raw_description="Client", category="Sales Revenue"
    )
    tx2 = Transaction(
        id=2, business_id=1, transaction_date=now - datetime.timedelta(days=15),
        status="COMPLETED", gross_amount=2000.0, net_amount=1950.0,
        normalized_vendor="Client", raw_description="Client", category="Sales Revenue"
    )

    # Subscriptions in Month 1 total $800 ($800 / $2000 = 40% of revenue)
    sub = Subscription(
        id=1, business_id=1, vendor_name="Oracle Cloud", category="Cloud Infrastructure",
        cadence="monthly", latest_amount=800.0, average_amount=800.0,
        status="active", detection_type="confirmed", priority_tier=1,
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=20),
        next_billing_date=now + datetime.timedelta(days=15)
    )

    recs = RecommendationEngine.generate_recommendations(business_healthy, [sub], [tx1, tx2])
    overcommit_recs = [r for r in recs if r.action_type == "CASHFLOW_PROTECTION" and "Commitment" in r.title]

    assert len(overcommit_recs) >= 1
    rec = overcommit_recs[0]
    assert "Excessive Subscription Commitment" in rec.title
    assert "40.0%" in rec.title or "40.0%" in rec.identified_issue


def test_simulate_purchase_api_endpoint_auth_and_isolation():
    """
    Test POST /api/v1/recommendations/simulate-purchase endpoint:
    - Verifies endpoint responds properly with typed schema.
    - Verifies business profile isolation (User A cannot access User B data).
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.database import Base
    from app.api.recommendations import simulate_purchase
    from fastapi import HTTPException

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Create User A and Business A
        user_a = User(id=101, email="cfo_a@test.com", hashed_password="dummy")
        db.add(user_a)
        biz_a = BusinessProfile(id=201, user_id=101, company_name="Company A", monthly_baseline_revenue=5000.0)
        db.add(biz_a)

        # Create User B without business profile
        user_b = User(id=102, email="cfo_b@test.com", hashed_password="dummy")
        db.add(user_b)
        db.commit()

        req = PurchaseSimulationRequest(
            proposed_vendor="Docker Pro",
            amount=25.0,
            cadence="monthly"
        )

        # User A call succeeds
        resp_a = simulate_purchase(payload=req, current_user=user_a, db=db)
        assert resp_a.proposed_vendor == "Docker Pro"
        assert resp_a.monthly_equivalent_cost == 25.0
        assert resp_a.verdict is not None

        # User B has no business profile -> raises 404
        with pytest.raises(HTTPException) as exc_info:
            simulate_purchase(payload=req, current_user=user_b, db=db)
        assert exc_info.value.status_code == 404
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

