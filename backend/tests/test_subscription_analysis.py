import datetime
import pytest
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer

def test_cadence_conversion_equivalents():
    # Weekly: $10.00/wk -> ~$43.33/mo, $520.00/yr
    m_eq, a_eq = SubscriptionExpenseAnalyzer.calculate_cadence_equivalents(10.0, "weekly")
    assert round(m_eq, 2) == 43.33
    assert a_eq == 520.0

    # Monthly: $100.00/mo -> $100.00/mo, $1200.00/yr
    m_eq, a_eq = SubscriptionExpenseAnalyzer.calculate_cadence_equivalents(100.0, "monthly")
    assert m_eq == 100.0
    assert a_eq == 1200.0

    # Quarterly: $300.00/qtr -> $100.00/mo, $1200.00/yr
    m_eq, a_eq = SubscriptionExpenseAnalyzer.calculate_cadence_equivalents(300.0, "quarterly")
    assert m_eq == 100.0
    assert a_eq == 1200.0

    # Annual: $1200.00/yr -> $100.00/mo, $1200.00/yr
    m_eq, a_eq = SubscriptionExpenseAnalyzer.calculate_cadence_equivalents(1200.0, "annual")
    assert m_eq == 100.0
    assert a_eq == 1200.0

def test_standardize_category():
    assert SubscriptionExpenseAnalyzer.standardize_category("Cloud Infrastructure") == "Cloud Infrastructure"
    assert SubscriptionExpenseAnalyzer.standardize_category("DevOps & Monitoring") == "Cloud Infrastructure"
    assert SubscriptionExpenseAnalyzer.standardize_category("Cloud Storage") == "Cloud Infrastructure"
    assert SubscriptionExpenseAnalyzer.standardize_category("Developer Tools") == "Development Tools"
    assert SubscriptionExpenseAnalyzer.standardize_category("AI & Machine Learning") == "Development Tools"
    assert SubscriptionExpenseAnalyzer.standardize_category("Team Collaboration") == "Communication"
    assert SubscriptionExpenseAnalyzer.standardize_category("Video Conferencing") == "Communication"
    assert SubscriptionExpenseAnalyzer.standardize_category("Communications API & SMS") == "Communication"
    assert SubscriptionExpenseAnalyzer.standardize_category("Design & Prototyping") == "Design"
    assert SubscriptionExpenseAnalyzer.standardize_category("Design & Media") == "Design"
    assert SubscriptionExpenseAnalyzer.standardize_category("CRM & Marketing") == "Marketing"
    assert SubscriptionExpenseAnalyzer.standardize_category("Email Marketing") == "Marketing"
    assert SubscriptionExpenseAnalyzer.standardize_category("Productivity & Email") == "Productivity"
    assert SubscriptionExpenseAnalyzer.standardize_category("Accounting & Finance") == "Productivity"
    assert SubscriptionExpenseAnalyzer.standardize_category("Project Management") == "Productivity"
    assert SubscriptionExpenseAnalyzer.standardize_category("Unknown SaaS Category") == "Other SaaS"

def test_vendor_and_category_analysis_commitments():
    now = datetime.datetime.utcnow()
    d1 = now - datetime.timedelta(days=60)
    d2 = now - datetime.timedelta(days=30)

    subs = [
        Subscription(
            id=1, business_id=1, vendor_name="AWS", category="Cloud Infrastructure",
            cadence="monthly", average_amount=250.0, latest_amount=300.0,
            status="active", detection_type="confirmed", billing_type="variable",
            first_billed_date=d1, last_billed_date=d2, next_billing_date=now
        ),
        Subscription(
            id=2, business_id=1, vendor_name="Slack", category="Team Collaboration",
            cadence="monthly", average_amount=100.0, latest_amount=125.0,
            price_change_pct=25.0, status="at_risk", detection_type="confirmed", billing_type="fixed",
            first_billed_date=d1, last_billed_date=d2, next_billing_date=now
        ),
        Subscription(
            id=3, business_id=1, vendor_name="Figma", category="Design & Prototyping",
            cadence="annual", average_amount=180.0, latest_amount=180.0,
            status="active", detection_type="potential", billing_type="fixed",
            first_billed_date=d2, last_billed_date=d2, next_billing_date=now
        ),
    ]

    txns = [
        Transaction(
            id=1, business_id=1, transaction_date=d1, raw_description="AWS CLOUD DEBIT",
            normalized_vendor="AWS", category="Cloud Infrastructure", gross_amount=-250.0, net_amount=-250.0
        ),
        Transaction(
            id=2, business_id=1, transaction_date=d2, raw_description="AWS CLOUD DEBIT",
            normalized_vendor="AWS", category="Cloud Infrastructure", gross_amount=-300.0, net_amount=-300.0
        ),
        Transaction(
            id=3, business_id=1, transaction_date=d1, raw_description="SLACK TECHNOLOGIES",
            normalized_vendor="Slack", category="Team Collaboration", gross_amount=-100.0, net_amount=-100.0
        ),
        Transaction(
            id=4, business_id=1, transaction_date=d2, raw_description="SLACK TECHNOLOGIES",
            normalized_vendor="Slack", category="Team Collaboration", gross_amount=-125.0, net_amount=-125.0
        ),
        Transaction(
            id=5, business_id=1, transaction_date=d2, raw_description="FIGMA DESIGN ANNUAL",
            normalized_vendor="Figma", category="Design & Prototyping", gross_amount=-180.0, net_amount=-180.0
        ),
    ]

    analysis = SubscriptionExpenseAnalyzer.analyze(subscriptions=subs, transactions=txns)

    assert analysis["has_data"] is True
    assert analysis["has_subscriptions"] is True
    # Monthly commitments: AWS ($300) + Slack ($125) + Figma ($180/12 = $15) = $440.00
    assert analysis["total_monthly_commitment"] == 440.0
    # Confirmed monthly commitment: AWS ($300) + Slack ($125) = $425.0
    assert analysis["confirmed_monthly_commitment"] == 425.0
    # Potential monthly commitment: Figma ($15.0)
    assert analysis["potential_monthly_commitment"] == 15.0
    # Annual commitments: $425 * 12 + $180 = $5280.0
    assert analysis["total_annual_commitment"] == 5280.0

    # Vendor analysis
    v_map = {v["vendor_name"]: v for v in analysis["vendor_analysis"]}
    assert "AWS" in v_map
    assert v_map["AWS"]["monthly_equivalent"] == 300.0
    assert v_map["AWS"]["annual_equivalent"] == 3600.0
    assert v_map["AWS"]["historical_spend_total"] == 550.0
    assert v_map["AWS"]["standard_category"] == "Cloud Infrastructure"

    assert "Figma" in v_map
    assert v_map["Figma"]["monthly_equivalent"] == 15.0
    assert v_map["Figma"]["annual_equivalent"] == 180.0
    assert v_map["Figma"]["standard_category"] == "Design"
    assert v_map["Figma"]["detection_type"] == "potential"

    # Category breakdown
    cat_map = {c["category"]: c for c in analysis["category_analysis"]}
    assert "Cloud Infrastructure" in cat_map
    assert cat_map["Cloud Infrastructure"]["monthly_spend"] == 300.0
    assert "Communication" in cat_map
    assert cat_map["Communication"]["monthly_spend"] == 125.0
    assert "Design" in cat_map
    assert cat_map["Design"]["monthly_spend"] == 15.0

def test_revenue_vs_subscription_comparison_and_zero_revenue():
    now = datetime.datetime.utcnow()
    sub = Subscription(
        id=1, business_id=1, vendor_name="GitHub", category="Developer Tools",
        cadence="monthly", average_amount=100.0, latest_amount=100.0,
        status="active", detection_type="confirmed",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )

    # Case 1: Operating revenue exists ($1,000/mo -> 10% ratio = healthy)
    tx_rev = Transaction(
        id=1, business_id=1, transaction_date=now, raw_description="Customer payment",
        normalized_vendor="Customer Corp", category="Operating Revenue", gross_amount=1000.0, net_amount=970.0
    )
    analysis_healthy = SubscriptionExpenseAnalyzer.analyze(subscriptions=[sub], transactions=[tx_rev])
    rev_comp = analysis_healthy["revenue_comparison"]
    assert rev_comp["has_sufficient_revenue_data"] is True
    assert rev_comp["revenue_percentage"] == 10.0
    assert rev_comp["burden_level"] == "healthy"

    # Case 2: Zero revenue (e.g. only funding transaction)
    tx_funding = Transaction(
        id=2, business_id=1, transaction_date=now, raw_description="Initial balance",
        normalized_vendor="PayPal Balance Adjustment", category="Account Funding / Balance Adjustment", gross_amount=5000.0, net_amount=5000.0
    )
    analysis_zero = SubscriptionExpenseAnalyzer.analyze(subscriptions=[sub], transactions=[tx_funding])
    rev_comp_zero = analysis_zero["revenue_comparison"]
    assert rev_comp_zero["has_sufficient_revenue_data"] is False
    assert rev_comp_zero["revenue_percentage"] is None
    assert rev_comp_zero["burden_level"] == "insufficient_data"
    assert "No operating revenue" in rev_comp_zero["explanation"]

def test_spending_trends_and_price_creep_alerts():
    now = datetime.datetime.utcnow()
    sub_creep = Subscription(
        id=1, business_id=1, vendor_name="Datadog", category="DevOps & Monitoring",
        cadence="monthly", average_amount=120.0, latest_amount=150.0,
        price_change_pct=25.0, status="at_risk", detection_type="confirmed", billing_type="fixed",
        first_billed_date=now, last_billed_date=now, next_billing_date=now
    )
    analysis = SubscriptionExpenseAnalyzer.analyze(subscriptions=[sub_creep], transactions=[])
    trends = analysis["spending_trends"]
    assert len(trends["price_creep_alerts"]) == 1
    assert trends["price_creep_alerts"][0]["vendor"] == "Datadog"
    assert trends["price_creep_alerts"][0]["type"] == "price_creep"
    assert trends["price_creep_alerts"][0]["change_pct"] == 25.0

def test_non_operating_and_subwise_exclusion():
    now = datetime.datetime.utcnow()
    tx_initial = Transaction(
        id=1, business_id=1, transaction_date=now, raw_description="Initial balance",
        normalized_vendor="PayPal Balance Adjustment", category="Account Funding / Balance Adjustment", gross_amount=5000.0, net_amount=5000.0
    )
    tx_subwise = Transaction(
        id=2, business_id=1, transaction_date=now, raw_description="SubWise AI Sandbox Payment Test",
        normalized_vendor="Subwise", category="General SaaS / Operations", gross_amount=-5.0, net_amount=-5.0
    )
    # Both are non-operating / excluded
    assert SubscriptionExpenseAnalyzer.is_non_operating(tx_initial) is True
    assert SubscriptionExpenseAnalyzer.is_non_operating(tx_subwise) is True

    analysis = SubscriptionExpenseAnalyzer.analyze(subscriptions=[], transactions=[tx_initial, tx_subwise])
    assert analysis["has_subscriptions"] is False
    assert analysis["status"] == "insufficient_data"
    assert analysis["total_monthly_commitment"] == 0.0
    assert analysis["actual_historical_spend_total"] == 0.0

