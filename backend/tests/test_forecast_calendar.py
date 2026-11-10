"""
Stage 3 Tests: Calendar-Aware Subscription Forecasting.

Covers:
  1. Monthly renewal scheduling.
  2. Weekly renewal scheduling.
  3. Quarterly renewal scheduling.
  4. Annual renewal scheduling.
  5. Unknown renewal dates handling.
  6. Confirmed vs. potential subscriptions segregation.
  7. Multiple renewals in one month & concentration analysis.
  8. No historical transaction double-counting.
  9. Correct monthly closing balances based on actual renewal schedule.
  10. Insufficient-data protection (Business Profile 40).
  11. Existing scenario compatibility (Optimistic, Baseline, Conservative).
"""
import datetime
import pytest
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.forecast_engine import ForecastEngine


@pytest.fixture
def business():
    return BusinessProfile(
        id=50, user_id=50,
        company_name="SaaS Metrics Corp",
        monthly_baseline_revenue=0.0,
        current_cash_reserves=10000.0,
    )


def _make_revenue_tx(id_, amount, date):
    return Transaction(
        id=id_, business_id=50,
        transaction_date=date,
        raw_description="Client Monthly Service",
        normalized_vendor="Client Alpha",
        category="Professional Services",
        gross_amount=amount,
        net_amount=amount,
        status="COMPLETED",
    )


def _make_expense_tx(id_, amount, date):
    return Transaction(
        id=id_, business_id=50,
        transaction_date=date,
        raw_description="Office Utilities",
        normalized_vendor="City Power",
        category="Utilities",
        gross_amount=-abs(amount),
        net_amount=-abs(amount),
        status="COMPLETED",
    )


@pytest.fixture
def two_month_history(business):
    d1 = datetime.datetime(2026, 9, 15)
    d2 = datetime.datetime(2026, 10, 15)
    txs = [
        _make_revenue_tx(1, 6000.0, d1),
        _make_expense_tx(2, 1000.0, d1),
        _make_revenue_tx(3, 6000.0, d2),
        _make_expense_tx(4, 1000.0, d2),
    ]
    return business, txs


# ─── Test 1: Monthly Renewal Scheduling ───────────────────────────────────────
def test_monthly_renewal_scheduling(two_month_history):
    business, txs = two_month_history
    # Next billing on 10th of next month (Nov 10, 2026)
    sub = Subscription(
        id=1, business_id=50, vendor_name="Slack", category="Communication",
        latest_amount=50.0, average_amount=50.0, cadence="monthly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 10),
        last_billed_date=datetime.datetime(2026, 10, 10),
        next_billing_date=datetime.datetime(2026, 11, 10),
    )

    result = ForecastEngine.generate_forecast(business, [sub], txs, forecast_months=6)

    calendar = result["payment_calendar"]
    assert len(calendar) == 6
    for idx, pmt in enumerate(calendar):
        assert pmt["vendor_name"] == "Slack"
        assert pmt["expected_payment_amount"] == 50.0
        assert pmt["billing_frequency"] == "monthly"
        assert pmt["is_contractual_commitment"] is True
        assert pmt["month_index"] == idx + 1
        # Day of month is preserved on the 10th
        assert pmt["expected_payment_date"].endswith("-10")

    # Each forecast month has exactly 1 renewal of $50
    for m in result["monthly_scheduled_subscription_totals"]:
        assert m["total_confirmed_amount"] == 50.0
        assert m["confirmed_renewals_count"] == 1


# ─── Test 2: Weekly Renewal Scheduling ────────────────────────────────────────
def test_weekly_renewal_scheduling(two_month_history):
    business, txs = two_month_history
    sub = Subscription(
        id=2, business_id=50, vendor_name="Weekly Standup Tool", category="Productivity",
        latest_amount=25.0, average_amount=25.0, cadence="weekly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 10, 1),
        last_billed_date=datetime.datetime(2026, 10, 15),
        next_billing_date=datetime.datetime(2026, 11, 5),
    )

    result = ForecastEngine.generate_forecast(business, [sub], txs, forecast_months=6)

    calendar = result["payment_calendar"]
    # 6 months = ~26 weeks
    assert len(calendar) >= 24
    for pmt in calendar:
        assert pmt["vendor_name"] == "Weekly Standup Tool"
        assert pmt["expected_payment_amount"] == 25.0
        assert pmt["billing_frequency"] == "weekly"

    # In each month, total payments are either $100 (4 weeks) or $125 (5 weeks)
    for m in result["monthly_scheduled_subscription_totals"]:
        assert m["total_confirmed_amount"] in (100.0, 125.0)
        assert m["confirmed_renewals_count"] in (4, 5)


# ─── Test 3: Quarterly Renewal Scheduling ─────────────────────────────────────
def test_quarterly_renewal_scheduling(two_month_history):
    business, txs = two_month_history
    # Renews in Month 2 (Dec 2026) and Month 5 (Mar 2027)
    sub = Subscription(
        id=3, business_id=50, vendor_name="Zoom Enterprise", category="Communication",
        latest_amount=300.0, average_amount=300.0, cadence="quarterly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 20),
        last_billed_date=datetime.datetime(2026, 9, 20),
        next_billing_date=datetime.datetime(2026, 12, 20),
    )

    result = ForecastEngine.generate_forecast(business, [sub], txs, forecast_months=6)

    calendar = result["payment_calendar"]
    # Over 6 months, a quarterly subscription charges twice (separated by 3 months)
    assert len(calendar) == 2
    assert calendar[0]["expected_payment_date"] == "2026-12-20"
    assert calendar[0]["month_index"] == 2
    assert calendar[0]["expected_payment_amount"] == 300.0

    assert calendar[1]["expected_payment_date"] == "2027-03-20"
    assert calendar[1]["month_index"] == 5
    assert calendar[1]["expected_payment_amount"] == 300.0

    # Non-renewal months must have $0 scheduled
    totals = result["monthly_scheduled_subscription_totals"]
    assert totals[0]["total_confirmed_amount"] == 0.0  # Month 1
    assert totals[1]["total_confirmed_amount"] == 300.0 # Month 2 (Renewal)
    assert totals[2]["total_confirmed_amount"] == 0.0  # Month 3
    assert totals[3]["total_confirmed_amount"] == 0.0  # Month 4
    assert totals[4]["total_confirmed_amount"] == 300.0 # Month 5 (Renewal)
    assert totals[5]["total_confirmed_amount"] == 0.0  # Month 6


# ─── Test 4: Annual Renewal Scheduling ────────────────────────────────────────
def test_annual_renewal_scheduling(two_month_history):
    business, txs = two_month_history
    # Renews once in Month 3 (Jan 2027) for $1,200
    sub = Subscription(
        id=4, business_id=50, vendor_name="Salesforce CRM", category="Productivity",
        latest_amount=1200.0, average_amount=1200.0, cadence="annual",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 1, 15),
        last_billed_date=datetime.datetime(2026, 1, 15),
        next_billing_date=datetime.datetime(2027, 1, 15),
    )

    result = ForecastEngine.generate_forecast(business, [sub], txs, forecast_months=6)

    calendar = result["payment_calendar"]
    # Only 1 payment in the 6-month horizon
    assert len(calendar) == 1
    assert calendar[0]["expected_payment_amount"] == 1200.0
    assert calendar[0]["month_index"] == 3
    assert calendar[0]["expected_payment_date"] == "2027-01-15"

    totals = result["monthly_scheduled_subscription_totals"]
    assert totals[0]["total_confirmed_amount"] == 0.0
    assert totals[1]["total_confirmed_amount"] == 0.0
    assert totals[2]["total_confirmed_amount"] == 1200.0 # Month 3 renewal spike!
    assert totals[3]["total_confirmed_amount"] == 0.0
    assert totals[4]["total_confirmed_amount"] == 0.0
    assert totals[5]["total_confirmed_amount"] == 0.0

    # In Month 3, projected_confirmed_subscription_expenses is 1200.0, not smoothed 100.0
    month_items = result["forecast"]
    assert month_items[2]["projected_confirmed_subscription_expenses"] == 1200.0
    assert month_items[0]["projected_confirmed_subscription_expenses"] == 0.0


# ─── Test 5: Unknown Renewal Dates ────────────────────────────────────────────
def test_unknown_renewal_dates(two_month_history):
    business, txs = two_month_history
    sub_no_date = Subscription(
        id=5, business_id=50, vendor_name="Mystery Tool", category="Other SaaS",
        latest_amount=75.0, average_amount=75.0, cadence="monthly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 1, 1),
        last_billed_date=datetime.datetime(2026, 1, 1),
        next_billing_date=None,  # Unknown next billing date
    )

    result = ForecastEngine.generate_forecast(business, [sub_no_date], txs, forecast_months=6)

    # Unknown date count is reported
    assert result["unknown_renewal_date_count"] == 1
    # No payment invented in the calendar
    assert len(result["payment_calendar"]) == 0


# ─── Test 6: Confirmed vs. Potential Subscriptions ───────────────────────────
def test_confirmed_vs_potential_subscriptions(two_month_history):
    business, txs = two_month_history
    sub_confirmed = Subscription(
        id=6, business_id=50, vendor_name="GitHub", category="Development Tools",
        latest_amount=100.0, average_amount=100.0, cadence="monthly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 10),
        last_billed_date=datetime.datetime(2026, 10, 10),
        next_billing_date=datetime.datetime(2026, 11, 10),
    )
    sub_potential = Subscription(
        id=7, business_id=50, vendor_name="Figma", category="Design",
        latest_amount=45.0, average_amount=45.0, cadence="monthly",
        status="active", detection_type="potential",  # Potential, unconfirmed
        first_billed_date=datetime.datetime(2026, 10, 10),
        last_billed_date=datetime.datetime(2026, 10, 10),
        next_billing_date=datetime.datetime(2026, 11, 10),
    )

    result = ForecastEngine.generate_forecast(business, [sub_confirmed, sub_potential], txs, forecast_months=6)

    # In calendar, both appear but with clear distinction
    calendar = result["payment_calendar"]
    gh_pmts = [p for p in calendar if p["vendor_name"] == "GitHub"]
    figma_pmts = [p for p in calendar if p["vendor_name"] == "Figma"]

    assert len(gh_pmts) == 6
    assert len(figma_pmts) == 6

    assert all(p["is_contractual_commitment"] is True for p in gh_pmts)
    assert all(p["is_contractual_commitment"] is False for p in figma_pmts)

    # In monthly totals, potential amounts are segregated
    for m in result["monthly_scheduled_subscription_totals"]:
        assert m["total_confirmed_amount"] == 100.0
        assert m["total_potential_amount"] == 45.0

    # In forecast forward cash flow, net cash flow ONLY deducts confirmed (100.0), NOT potential (45.0)
    for m in result["forecast"]:
        assert m["projected_confirmed_subscription_expenses"] == 100.0
        assert m["potential_subscription_expenses"] == 45.0
        # Revenue (6000) - Non-Sub (1000) - Confirmed (100) = 4900
        assert m["projected_net_cashflow"] == 4900.0


# ─── Test 7: Multiple Renewals in One Month & Concentration Analysis ───────────
def test_multiple_renewals_in_one_month(two_month_history):
    business, txs = two_month_history
    # Multiple renewals concentrated in Month 1 (Nov 2026)
    sub1 = Subscription(
        id=8, business_id=50, vendor_name="AWS Cloud", category="Cloud Infrastructure",
        latest_amount=1500.0, average_amount=1500.0, cadence="monthly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 5),
        last_billed_date=datetime.datetime(2026, 10, 5),
        next_billing_date=datetime.datetime(2026, 11, 5),
    )
    sub2 = Subscription(
        id=9, business_id=50, vendor_name="Datadog", category="Development Tools",
        latest_amount=600.0, average_amount=600.0, cadence="monthly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 12),
        last_billed_date=datetime.datetime(2026, 10, 12),
        next_billing_date=datetime.datetime(2026, 11, 12),
    )
    sub3 = Subscription(
        id=10, business_id=50, vendor_name="Slack", category="Communication",
        latest_amount=200.0, average_amount=200.0, cadence="monthly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 15),
        last_billed_date=datetime.datetime(2026, 10, 15),
        next_billing_date=datetime.datetime(2026, 11, 15),
    )

    result = ForecastEngine.generate_forecast(business, [sub1, sub2, sub3], txs, forecast_months=6)

    totals = result["monthly_scheduled_subscription_totals"]
    m1 = totals[0]
    # Sum = 1500 + 600 + 200 = 2300
    assert m1["total_confirmed_amount"] == 2300.0
    assert m1["confirmed_renewals_count"] == 3
    assert m1["largest_individual_payment"] == 1500.0
    assert m1["largest_payment_vendor"] == "AWS Cloud"

    # Revenue is 6000.0, so 2300 / 6000 = 38.3% -> high concentration triggered!
    assert m1["revenue_commitment_pct"] == 38.3
    assert m1["is_high_concentration"] is True
    assert len(result["renewal_concentration_warnings"]) > 0


# ─── Test 8: No Historical Transaction Double-Counting ────────────────────────
def test_no_historical_transaction_double_counting(two_month_history):
    business, txs = two_month_history
    # A subscription that had billing in Sept and Oct
    sub = Subscription(
        id=11, business_id=50, vendor_name="Jira", category="Productivity",
        latest_amount=80.0, average_amount=80.0, cadence="monthly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 10),
        last_billed_date=datetime.datetime(2026, 10, 10),
        next_billing_date=datetime.datetime(2026, 11, 10),
    )

    result = ForecastEngine.generate_forecast(business, [sub], txs, forecast_months=6)

    # Calendar must only schedule future dates (>= Nov 2026), never historical Sept/Oct dates
    calendar = result["payment_calendar"]
    for pmt in calendar:
        dt = datetime.datetime.strptime(pmt["expected_payment_date"], "%Y-%m-%d")
        assert dt >= datetime.datetime(2026, 11, 1)


# ─── Test 9: Correct Monthly Closing Balances ──────────────────────────────────
def test_correct_monthly_closing_balances(two_month_history):
    business, txs = two_month_history
    # Annual sub of $600 charged only in Month 2 (Dec 2026)
    sub = Subscription(
        id=12, business_id=50, vendor_name="Annual Security Audit", category="Other SaaS",
        latest_amount=600.0, average_amount=600.0, cadence="annual",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2025, 12, 10),
        last_billed_date=datetime.datetime(2025, 12, 10),
        next_billing_date=datetime.datetime(2026, 12, 10),
    )

    result = ForecastEngine.generate_forecast(business, [sub], txs, forecast_months=6)
    starting_cash = result["verified_starting_cash"]
    # Starting cash from completed txs: (6000 - 1000) * 2 = 10000.0
    assert starting_cash == 10000.0

    forecast = result["forecast"]
    # Month 1 (Nov 2026): rev 6000 - non_sub 1000 - sub 0 = +5000 -> balance 15000
    assert forecast[0]["projected_confirmed_subscription_expenses"] == 0.0
    assert forecast[0]["projected_net_cashflow"] == 5000.0
    assert forecast[0]["projected_closing_cash_balance"] == 15000.0

    # Month 2 (Dec 2026): rev 6000 - non_sub 1000 - sub 600 = +4400 -> balance 19400
    assert forecast[1]["projected_confirmed_subscription_expenses"] == 600.0
    assert forecast[1]["projected_net_cashflow"] == 4400.0
    assert forecast[1]["projected_closing_cash_balance"] == 19400.0

    # Month 3 (Jan 2027): rev 6000 - non_sub 1000 - sub 0 = +5000 -> balance 24400
    assert forecast[2]["projected_confirmed_subscription_expenses"] == 0.0
    assert forecast[2]["projected_net_cashflow"] == 5000.0
    assert forecast[2]["projected_closing_cash_balance"] == 24400.0


# ─── Test 10: Insufficient-Data Protection (Business 40) ──────────────────────
def test_insufficient_data_protection():
    biz = BusinessProfile(
        id=40, user_id=40,
        company_name="Sandbox Merchant",
        current_cash_reserves=5004.41,
    )
    now = datetime.datetime.utcnow()
    tx_funding = Transaction(
        id=1, business_id=40, transaction_date=now,
        raw_description="Initial balance", normalized_vendor="PayPal Balance Adjustment",
        gross_amount=5000.0, net_amount=5000.0, status="COMPLETED",
    )
    tx_test = Transaction(
        id=2, business_id=40, transaction_date=now,
        raw_description="SubWise AI Sandbox Payment Test", normalized_vendor="Subwise",
        gross_amount=5.0, fee_amount=-0.59, net_amount=4.41, status="COMPLETED",
    )

    result = ForecastEngine.generate_forecast(biz, [], [tx_funding, tx_test], forecast_months=6)

    assert result["status"] == "insufficient_data"
    assert result["payment_calendar"] == []
    assert result["upcoming_subscription_payments"] == []
    assert result["unknown_renewal_date_count"] == 0
    assert result["renewal_concentration_warnings"] == []
    for m in result["monthly_scheduled_subscription_totals"]:
        assert m["total_confirmed_amount"] == 0.0


# ─── Test 11: Existing Scenario Compatibility ─────────────────────────────────
def test_existing_scenario_compatibility(two_month_history):
    business, txs = two_month_history
    # Quarterly renewal in Month 2 ($300)
    sub = Subscription(
        id=13, business_id=50, vendor_name="Zoom Enterprise", category="Communication",
        latest_amount=300.0, average_amount=300.0, cadence="quarterly",
        status="active", detection_type="confirmed",
        first_billed_date=datetime.datetime(2026, 9, 20),
        last_billed_date=datetime.datetime(2026, 9, 20),
        next_billing_date=datetime.datetime(2026, 12, 20),
    )

    result = ForecastEngine.generate_forecast(business, [sub], txs, forecast_months=6)

    assert result["scenarios_available"] is True
    opt = result["optimistic"]
    base = result["baseline"]
    cons = result["conservative"]

    # In all 3 scenarios, Month 2 reflects the $300 quarterly renewal obligation identically
    assert opt["months"][1]["projected_confirmed_subscription_expenses"] == 300.0
    assert base["months"][1]["projected_confirmed_subscription_expenses"] == 300.0
    assert cons["months"][1]["projected_confirmed_subscription_expenses"] == 300.0

    # In non-renewal months (Month 1), all 3 scenarios reflect $0 for this sub
    assert opt["months"][0]["projected_confirmed_subscription_expenses"] == 0.0
    assert base["months"][0]["projected_confirmed_subscription_expenses"] == 0.0
    assert cons["months"][0]["projected_confirmed_subscription_expenses"] == 0.0

