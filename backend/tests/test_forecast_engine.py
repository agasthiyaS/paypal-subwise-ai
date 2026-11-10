import datetime
import pytest
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.forecast_engine import ForecastEngine

@pytest.fixture
def empty_business():
    return BusinessProfile(
        id=1,
        user_id=1,
        company_name="Test SMB",
        monthly_baseline_revenue=0.0,
        current_cash_reserves=0.0
    )

@pytest.fixture
def business_with_reserves():
    return BusinessProfile(
        id=2,
        user_id=2,
        company_name="Funded SMB",
        monthly_baseline_revenue=0.0,
        current_cash_reserves=10000.0
    )

def test_funding_transactions_excluded(empty_business):
    """
    Test 1: Non-operating capital funding or balance adjustment transactions
    (such as PayPal Initial Balance) must be excluded from operating revenue.
    """
    now = datetime.datetime.utcnow()
    tx = Transaction(
        id=1,
        business_id=1,
        transaction_date=now,
        raw_description="Initial balance",
        normalized_vendor="PayPal Balance Adjustment",
        category="Account Funding / Balance Adjustment",
        gross_amount=5000.0,
        net_amount=5000.0,
        status="COMPLETED"
    )
    assert ForecastEngine.is_non_operating(tx) is True
    assert ForecastEngine.is_valid_operating(tx) is False

    forecast = ForecastEngine.generate_forecast(empty_business, [], [tx], forecast_months=6)
    assert forecast["historical_monthly_operating_revenue"] == 0.0
    assert forecast["status"] == "insufficient_data"

def test_subwise_test_transactions_excluded(empty_business):
    """
    Test 2: Internal SubWise AI Sandbox test transactions must be excluded
    from operating cash flow forecasting.
    """
    now = datetime.datetime.utcnow()
    tx = Transaction(
        id=2,
        business_id=1,
        transaction_date=now,
        raw_description="SubWise AI Sandbox Payment Test",
        normalized_vendor="Subwise",
        category="General SaaS / Operations",
        gross_amount=-5.0,
        net_amount=-5.59,
        status="COMPLETED"
    )
    assert ForecastEngine.is_subwise_test(tx) is True
    assert ForecastEngine.is_valid_operating(tx) is False

    forecast = ForecastEngine.generate_forecast(empty_business, [], [tx], forecast_months=6)
    assert forecast["historical_monthly_non_sub_expenses"] == 0.0
    assert forecast["status"] == "insufficient_data"

def test_pending_failed_refunded_transactions_excluded(empty_business):
    """
    Test 3: Only COMPLETED transactions are used; pending, failed, or reversed ones must be excluded.
    """
    now = datetime.datetime.utcnow()
    tx_pending = Transaction(
        id=3,
        business_id=1,
        transaction_date=now,
        raw_description="Customer SaaS Invoice #101",
        normalized_vendor="Acme Client",
        category="Sales Revenue",
        gross_amount=1200.0,
        status="PENDING"
    )
    tx_failed = Transaction(
        id=4,
        business_id=1,
        transaction_date=now,
        raw_description="Customer Payment Failed",
        normalized_vendor="Acme Client",
        category="Sales Revenue",
        gross_amount=1500.0,
        status="FAILED"
    )
    assert ForecastEngine.is_valid_operating(tx_pending) is False
    assert ForecastEngine.is_valid_operating(tx_failed) is False

    forecast = ForecastEngine.generate_forecast(empty_business, [], [tx_pending, tx_failed], forecast_months=6)
    assert forecast["historical_monthly_operating_revenue"] == 0.0
    assert forecast["status"] == "insufficient_data"

def test_actual_operating_revenue_calculated(empty_business):
    """
    Test 4: Actual operating revenue is calculated from completed incoming transactions.
    """
    d1 = datetime.datetime(2026, 1, 15)
    d2 = datetime.datetime(2026, 2, 10)
    tx1 = Transaction(
        id=10,
        business_id=1,
        transaction_date=d1,
        raw_description="Client Project Milestone 1",
        normalized_vendor="Client Alpha",
        category="Professional Services",
        gross_amount=3000.0,
        net_amount=2910.0,
        status="COMPLETED"
    )
    tx2 = Transaction(
        id=11,
        business_id=1,
        transaction_date=d2,
        raw_description="Client Project Milestone 2",
        normalized_vendor="Client Alpha",
        category="Professional Services",
        gross_amount=3000.0,
        net_amount=2910.0,
        status="COMPLETED"
    )
    assert ForecastEngine.is_valid_operating(tx1) is True
    assert ForecastEngine.is_valid_operating(tx2) is True

    forecast = ForecastEngine.generate_forecast(empty_business, [], [tx1, tx2], forecast_months=6)
    assert forecast["historical_monthly_operating_revenue"] == 3000.0
    assert forecast["status"] == "limited_data"  # 2 months = limited_data (< 3 months)
    for m in forecast["forecast"]:
        assert m["projected_operating_revenue"] == 3000.0

def test_actual_non_sub_operating_expenses_calculated(empty_business):
    """
    Test 5: Actual non-subscription operating expenses are isolated and calculated from completed outflows.
    """
    d1 = datetime.datetime(2026, 1, 20)
    tx_non_sub = Transaction(
        id=20,
        business_id=1,
        transaction_date=d1,
        raw_description="Office Supplies Store",
        normalized_vendor="OfficeMax",
        category="Office Supplies",
        gross_amount=-450.0,
        net_amount=-450.0,
        status="COMPLETED"
    )
    assert ForecastEngine.is_valid_operating(tx_non_sub) is True

    forecast = ForecastEngine.generate_forecast(empty_business, [], [tx_non_sub], forecast_months=6)
    assert forecast["historical_monthly_non_sub_expenses"] == 450.0

def test_confirmed_vs_potential_subscriptions_segregation(empty_business):
    """
    Test 6 & 7: Confirmed subscriptions are included as baseline forward commitments,
    while potential subscriptions are tracked separately as conditional.
    """
    now = datetime.datetime.utcnow()
    sub_confirmed = Subscription(
        id=1,
        business_id=1,
        vendor_name="GitHub Enterprise",
        category="Development Tools",
        latest_amount=250.0,
        cadence="monthly",
        status="active",
        detection_type="confirmed",
        first_billed_date=now,
        last_billed_date=now,
        next_billing_date=now
    )
    sub_potential = Subscription(
        id=2,
        business_id=1,
        vendor_name="Figma Design",
        category="Design Tools",
        latest_amount=75.0,
        cadence="monthly",
        status="active",
        detection_type="potential",
        first_billed_date=now,
        last_billed_date=now,
        next_billing_date=now
    )

    forecast = ForecastEngine.generate_forecast(empty_business, [sub_confirmed, sub_potential], [], forecast_months=6)
    assert forecast["confirmed_monthly_subscription_commitments"] == 250.0
    assert forecast["potential_monthly_subscription_commitments"] == 75.0

    for m in forecast["forecast"]:
        # Only confirmed is part of projected_confirmed_subscription_expenses
        assert m["projected_confirmed_subscription_expenses"] == 250.0
        assert m["potential_subscription_expenses"] == 75.0
        # Projected net cashflow only deducts confirmed commitment, not potential
        assert m["projected_net_cashflow"] == -250.0

def test_no_double_counting_subscription_expenses(empty_business):
    """
    Test 8: Subscription debits from historical transactions are not double counted with confirmed commitments.
    """
    d1 = datetime.datetime(2026, 1, 15)
    tx_sub = Transaction(
        id=30,
        business_id=1,
        transaction_date=d1,
        raw_description="GitHub recurring subscription payment",
        normalized_vendor="GitHub",
        category="Development Tools",
        gross_amount=-21.0,
        net_amount=-21.0,
        status="COMPLETED"
    )
    sub_gh = Subscription(
        id=1,
        business_id=1,
        vendor_name="GitHub",
        category="Development Tools",
        latest_amount=21.0,
        cadence="monthly",
        status="active",
        detection_type="confirmed",
        first_billed_date=d1,
        last_billed_date=d1,
        next_billing_date=d1
    )

    forecast = ForecastEngine.generate_forecast(empty_business, [sub_gh], [tx_sub], forecast_months=6)
    # The transaction to GitHub should be identified as subscription and NOT added to non-sub expenses
    assert forecast["historical_monthly_non_sub_expenses"] == 0.0
    assert forecast["historical_monthly_subscription_expenses"] == 21.0
    assert forecast["confirmed_monthly_subscription_commitments"] == 21.0
    # In forward projection, month expense is confirmed commitment ($21.0), not 21 + 21 = 42
    for m in forecast["forecast"]:
        assert m["projected_non_sub_expenses"] == 0.0
        assert m["projected_confirmed_subscription_expenses"] == 21.0
        assert m["projected_net_cashflow"] == -21.0

def test_insufficient_historical_data_handling(empty_business):
    """
    Test 9: When no valid historical operating transactions exist, status is 'insufficient_data'
    with transparent warnings.
    """
    forecast = ForecastEngine.generate_forecast(empty_business, [], [], forecast_months=6)
    assert forecast["status"] == "insufficient_data"
    assert len(forecast["missing_data_reasons"]) > 0
    assert "No verified operating revenue transactions" in forecast["missing_data_reasons"][0]

def test_no_fabricated_fallback_financial_values(empty_business):
    """
    Test 10: Ensures no hardcoded legacy fallbacks ($15,000 revenue or $45,000 cash balance) appear.
    """
    forecast = ForecastEngine.generate_forecast(empty_business, [], [], forecast_months=6)
    assert forecast["historical_monthly_operating_revenue"] != 15000.0
    assert forecast["verified_starting_cash"] != 45000.0
    assert forecast["has_verified_cash"] is False

    for m in forecast["forecast"]:
        assert m["projected_operating_revenue"] == 0.0
        assert m["projected_closing_cash_balance"] == 0.0

def test_current_sandbox_db_transactions_scenario():
    """
    Test 11: Simulates the exact state of Business Profile 40 in PostgreSQL:
    1. 59071448PK254121L - Initial balance ($5,000 gross / net)
    2. 4EV73998AP815980D - SubWise AI Sandbox Payment Test ($5 gross, -$0.59 fee, $4.41 net)
    Both are excluded from operating revenue/expenses.
    Verified starting cash is computed as 5000 + 4.41 = 5004.41.
    Status is 'insufficient_data' because there is zero operational revenue history.
    """
    biz = BusinessProfile(
        id=40,
        user_id=40,
        company_name="PayPal Sandbox Merchant",
        current_cash_reserves=5004.41
    )
    now = datetime.datetime.utcnow()
    tx_funding = Transaction(
        id=1,
        business_id=40,
        transaction_date=now,
        raw_description="Initial balance",
        normalized_vendor="PayPal Balance Adjustment",
        category="Account Funding / Balance Adjustment",
        gross_amount=5000.0,
        net_amount=5000.0,
        status="COMPLETED"
    )
    tx_subwise_test = Transaction(
        id=2,
        business_id=40,
        transaction_date=now,
        raw_description="SubWise AI Sandbox Payment Test",
        normalized_vendor="Subwise",
        category="General SaaS / Operations",
        gross_amount=5.0,
        fee_amount=-0.59,
        net_amount=4.41,
        status="COMPLETED"
    )

    forecast = ForecastEngine.generate_forecast(biz, [], [tx_funding, tx_subwise_test], forecast_months=6)
    assert forecast["status"] == "insufficient_data"
    assert forecast["has_verified_cash"] is True
    assert forecast["verified_starting_cash"] == 5004.41
    assert forecast["historical_monthly_operating_revenue"] == 0.0
    assert forecast["historical_monthly_non_sub_expenses"] == 0.0
    # Starting cash remains preserved at 5004.41 since there are no operating inflows/outflows
    for m in forecast["forecast"]:
        assert m["projected_closing_cash_balance"] == 5004.41
        assert m["is_cash_depleted"] is False
