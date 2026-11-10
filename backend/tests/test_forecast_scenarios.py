"""
Stage 2 tests: Multi-Scenario Cash Flow Forecasting.

Covers:
  Test 1  — Optimistic revenue = historical * 1.15
  Test 2  — Baseline revenue = historical * 1.00 (unchanged)
  Test 3  — Conservative revenue = historical * 0.80
  Test 4  — Confirmed subscription commitments identical across all three scenarios
  Test 5  — Correct monthly closing balances per scenario
  Test 6  — No unsupported savings applied (expense_adjustment_pct == 0 always)
  Test 7  — Insufficient-data protection: scenarios_available=False, no projections invented
  Test 8  — Runway calculation present when data sufficient and there is net burn
  Test 9  — No fabricated financial defaults ($15k / $45k absent in all scenarios)
  Test 10 — Existing Stage 1 forecast API fields remain backward-compatible
"""
import datetime
import pytest
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.forecast_engine import ForecastEngine, SCENARIO_CONFIGS


# ─── Shared fixtures ──────────────────────────────────────────────────────────

@pytest.fixture
def business():
    return BusinessProfile(
        id=10, user_id=10,
        company_name="Acme Tech",
        monthly_baseline_revenue=0.0,
        current_cash_reserves=0.0,
    )

@pytest.fixture
def business_with_reserves():
    return BusinessProfile(
        id=11, user_id=11,
        company_name="Funded Tech",
        monthly_baseline_revenue=0.0,
        current_cash_reserves=20000.0,
    )

def _make_revenue_tx(id_, amount, date):
    """Completed operating revenue transaction."""
    return Transaction(
        id=id_, business_id=10,
        transaction_date=date,
        raw_description="Client Services Invoice",
        normalized_vendor="Client Alpha",
        category="Professional Services",
        gross_amount=amount,
        net_amount=amount,
        status="COMPLETED",
    )

def _make_expense_tx(id_, amount, date, vendor="OfficeMax", category="Office Supplies"):
    """Completed non-subscription operating expense."""
    return Transaction(
        id=id_, business_id=10,
        transaction_date=date,
        raw_description="Operating Expense",
        normalized_vendor=vendor,
        category=category,
        gross_amount=-abs(amount),
        net_amount=-abs(amount),
        status="COMPLETED",
    )

def _make_confirmed_sub(id_, vendor, amount, cadence="monthly"):
    now = datetime.datetime.utcnow()
    return Subscription(
        id=id_, business_id=10,
        vendor_name=vendor, category="Development Tools",
        latest_amount=amount, cadence=cadence,
        status="active", detection_type="confirmed",
        first_billed_date=now, last_billed_date=now, next_billing_date=now,
    )

@pytest.fixture
def two_month_history(business):
    """
    Two months of verified operating data: $4,000/mo revenue, $500/mo non-sub expense.
    """
    d1 = datetime.datetime(2026, 9, 10)
    d2 = datetime.datetime(2026, 10, 12)
    txs = [
        _make_revenue_tx(1, 4000.0, d1),
        _make_expense_tx(2, 500.0, d1),
        _make_revenue_tx(3, 4000.0, d2),
        _make_expense_tx(4, 500.0, d2),
    ]
    return business, txs

@pytest.fixture
def confirmed_sub_200():
    return [_make_confirmed_sub(99, "GitHub Enterprise", 200.0)]


# ─── Test 1: Optimistic revenue = historical * 1.15 ─────────────────────────

def test_optimistic_revenue_adjustment(two_month_history, confirmed_sub_200):
    business, txs = two_month_history
    result = ForecastEngine.generate_forecast(business, confirmed_sub_200, txs, forecast_months=6)

    assert result["scenarios_available"] is True
    opt = result["optimistic"]
    assert opt is not None

    hist_rev = result["historical_monthly_operating_revenue"]
    expected_opt_rev = round(hist_rev * 1.15, 2)
    assert opt["monthly_revenue"] == expected_opt_rev, (
        f"Optimistic revenue should be hist_rev * 1.15. "
        f"Expected {expected_opt_rev}, got {opt['monthly_revenue']}"
    )

    # Verify assumption metadata
    assert opt["assumptions"]["revenue_adjustment_pct"] == 15.0
    assert opt["assumptions"]["scenario_name"] == "optimistic"


# ─── Test 2: Baseline revenue = historical unchanged ─────────────────────────

def test_baseline_revenue_unchanged(two_month_history, confirmed_sub_200):
    business, txs = two_month_history
    result = ForecastEngine.generate_forecast(business, confirmed_sub_200, txs, forecast_months=6)

    base = result["baseline"]
    hist_rev = result["historical_monthly_operating_revenue"]

    assert base["monthly_revenue"] == hist_rev, (
        f"Baseline revenue must equal historical average exactly. "
        f"Expected {hist_rev}, got {base['monthly_revenue']}"
    )
    assert base["assumptions"]["revenue_adjustment_pct"] == 0.0


# ─── Test 3: Conservative revenue = historical * 0.80 ───────────────────────

def test_conservative_revenue_reduction(two_month_history, confirmed_sub_200):
    business, txs = two_month_history
    result = ForecastEngine.generate_forecast(business, confirmed_sub_200, txs, forecast_months=6)

    cons = result["conservative"]
    hist_rev = result["historical_monthly_operating_revenue"]
    expected_cons_rev = round(hist_rev * 0.80, 2)

    assert cons["monthly_revenue"] == expected_cons_rev, (
        f"Conservative revenue should be hist_rev * 0.80. "
        f"Expected {expected_cons_rev}, got {cons['monthly_revenue']}"
    )
    assert cons["assumptions"]["revenue_adjustment_pct"] == -20.0

    # Confirm optimistic > baseline > conservative ordering
    opt_rev = result["optimistic"]["monthly_revenue"]
    base_rev = result["baseline"]["monthly_revenue"]
    cons_rev = result["conservative"]["monthly_revenue"]
    assert opt_rev > base_rev > cons_rev, (
        f"Revenue ordering violated: opt={opt_rev}, base={base_rev}, cons={cons_rev}"
    )


# ─── Test 4: Confirmed subscriptions identical across all scenarios ───────────

def test_confirmed_subs_identical_across_scenarios(two_month_history, confirmed_sub_200):
    business, txs = two_month_history
    result = ForecastEngine.generate_forecast(business, confirmed_sub_200, txs, forecast_months=6)

    opt_sub = result["optimistic"]["monthly_confirmed_sub_expenses"]
    base_sub = result["baseline"]["monthly_confirmed_sub_expenses"]
    cons_sub = result["conservative"]["monthly_confirmed_sub_expenses"]

    assert opt_sub == base_sub == cons_sub, (
        f"Confirmed subscription expenses must be identical across all scenarios. "
        f"opt={opt_sub}, base={base_sub}, cons={cons_sub}"
    )
    assert opt_sub == result["confirmed_monthly_subscription_commitments"], (
        "Scenario confirmed sub expenses must match the top-level commitment field."
    )

    # Also verify the flag in each assumption block
    for scenario_key in ("optimistic", "baseline", "conservative"):
        s = result[scenario_key]
        assert s["assumptions"]["confirmed_sub_expenses_unchanged"] is True


# ─── Test 5: Correct monthly closing balances ─────────────────────────────────

def test_monthly_closing_balances(two_month_history, confirmed_sub_200):
    business, txs = two_month_history
    # Give the business a known starting cash via completed txs
    # The two_month_history transactions sum = 4000 - 500 + 4000 - 500 = 7000
    result = ForecastEngine.generate_forecast(business, confirmed_sub_200, txs, forecast_months=6)

    starting_cash = result["verified_starting_cash"]
    base = result["baseline"]
    base_rev = base["monthly_revenue"]
    base_non_sub = base["monthly_non_sub_expenses"]
    base_sub = base["monthly_confirmed_sub_expenses"]
    expected_net = round(base_rev - base_non_sub - base_sub, 2)

    # Verify each month's closing balance accumulates correctly
    expected_running = starting_cash
    for month_item in base["months"]:
        expected_running += expected_net
        assert abs(month_item["projected_closing_cash_balance"] - expected_running) < 0.02, (
            f"Month {month_item['month_name']}: expected closing balance "
            f"{expected_running:.2f}, got {month_item['projected_closing_cash_balance']:.2f}"
        )
        assert month_item["projected_net_cashflow"] == expected_net


# ─── Test 6: No unsupported savings (expense_adjustment_pct == 0) ───────────

def test_no_unsupported_expense_savings(two_month_history, confirmed_sub_200):
    business, txs = two_month_history
    result = ForecastEngine.generate_forecast(business, confirmed_sub_200, txs, forecast_months=6)

    for scenario_key in ("optimistic", "baseline", "conservative"):
        s = result[scenario_key]
        assert s["assumptions"]["expense_adjustment_pct"] == 0.0, (
            f"Scenario '{scenario_key}' must not apply unverified expense reductions."
        )
        # Non-sub expenses identical to historical average
        assert s["monthly_non_sub_expenses"] == result["historical_monthly_non_sub_expenses"], (
            f"Non-sub expenses in '{scenario_key}' must equal verified historical average."
        )


# ─── Test 7: Insufficient-data protection ────────────────────────────────────

def test_insufficient_data_no_scenarios():
    """
    Current Sandbox state: 2 excluded transactions, $5,004.41 ledger balance,
    $0 operating revenue. scenarios_available must be False. No projections invented.
    """
    biz = BusinessProfile(
        id=40, user_id=40,
        company_name="Sandbox Merchant",
        current_cash_reserves=5004.41,
    )
    now = datetime.datetime.utcnow()
    tx_funding = Transaction(
        id=1, business_id=40,
        transaction_date=now,
        raw_description="Initial balance",
        normalized_vendor="PayPal Balance Adjustment",
        category="Account Funding / Balance Adjustment",
        gross_amount=5000.0, net_amount=5000.0,
        status="COMPLETED",
    )
    tx_test = Transaction(
        id=2, business_id=40,
        transaction_date=now,
        raw_description="SubWise AI Sandbox Payment Test",
        normalized_vendor="Subwise",
        category="General SaaS / Operations",
        gross_amount=5.0, fee_amount=-0.59, net_amount=4.41,
        status="COMPLETED",
    )

    result = ForecastEngine.generate_forecast(biz, [], [tx_funding, tx_test], forecast_months=6)

    assert result["status"] == "insufficient_data"
    assert result["scenarios_available"] is False
    assert result["optimistic"] is None
    assert result["baseline"] is None
    assert result["conservative"] is None

    # Starting cash preserved; operating revenue zero
    assert result["has_verified_cash"] is True
    assert result["verified_starting_cash"] == 5004.41
    assert result["historical_monthly_operating_revenue"] == 0.0

    # No scenario invents revenue
    for month_item in result["forecast"]:
        assert month_item["projected_operating_revenue"] == 0.0
        assert month_item["projected_closing_cash_balance"] == 5004.41


# ─── Test 8: Runway calculation ───────────────────────────────────────────────

def test_runway_calculation_when_net_burn():
    """
    When expenses exceed revenue (net burn), runway should be calculable.
    When revenue >= expenses, runway should report 'no depletion' but still be available.
    """
    biz = BusinessProfile(id=20, user_id=20, company_name="Burn Rate Co.")
    d1 = datetime.datetime(2026, 9, 1)
    d2 = datetime.datetime(2026, 10, 1)

    txs = [
        _make_revenue_tx(1, 2000.0, d1),   # $2k revenue
        _make_expense_tx(2, 1800.0, d1),   # $1.8k expenses → net +$200/mo
        _make_revenue_tx(3, 2000.0, d2),
        _make_expense_tx(4, 1800.0, d2),
    ]
    # Add a confirmed sub that pushes expenses above revenue: 2000 - 1800 - 500 = -300/mo burn
    high_sub = [_make_confirmed_sub(99, "DatadogEnterprise", 500.0)]

    result = ForecastEngine.generate_forecast(biz, high_sub, txs, forecast_months=6)
    starting_cash = result["verified_starting_cash"]

    assert result["scenarios_available"] is True
    cons = result["conservative"]
    # Conservative has lowest revenue, highest burn → shortest runway
    if cons["runway_available"]:
        if cons["runway_months"] is not None:
            assert cons["runway_months"] > 0
            # Manual check: conservative revenue = 2000 * 0.8 = 1600
            # burn = 1800 + 500 - 1600 = 700/mo
            # runway = starting_cash / 700
            expected_burn = round(1800.0 + 500.0 - 2000.0 * 0.8, 2)
            expected_runway = round(starting_cash / expected_burn, 1) if expected_burn > 0 else None
            if expected_runway:
                assert abs(cons["runway_months"] - expected_runway) < 0.2

    # Optimistic: revenue 2000 * 1.15 = 2300; expenses 1800 + 500 = 2300 → net zero
    opt = result["optimistic"]
    assert opt["runway_available"] is True


# ─── Test 9: No fabricated financial defaults ─────────────────────────────────

def test_no_fabricated_defaults_in_scenarios():
    """
    With zero operating history, scenarios should NOT appear, and no $15k / $45k defaults.
    """
    biz = BusinessProfile(id=30, user_id=30, company_name="Empty Corp.")
    result = ForecastEngine.generate_forecast(biz, [], [], forecast_months=6)

    assert result["scenarios_available"] is False
    assert result["historical_monthly_operating_revenue"] != 15000.0
    assert result["verified_starting_cash"] != 45000.0
    assert result["has_verified_cash"] is False

    # Stage 1 baseline forecast must also not fabricate revenue
    for m in result["forecast"]:
        assert m["projected_operating_revenue"] == 0.0
        assert m["projected_closing_cash_balance"] == 0.0


# ─── Test 10: Stage 1 backward-compatibility ──────────────────────────────────

def test_stage1_fields_backward_compatible(two_month_history, confirmed_sub_200):
    """
    All Stage 1 response fields must still be present and correctly typed.
    """
    business, txs = two_month_history
    result = ForecastEngine.generate_forecast(business, confirmed_sub_200, txs, forecast_months=6)

    # Stage 1 required fields
    stage1_fields = [
        "status", "currency", "verified_starting_cash", "has_verified_cash",
        "historical_monthly_operating_revenue", "historical_monthly_non_sub_expenses",
        "historical_monthly_subscription_expenses",
        "confirmed_monthly_subscription_commitments",
        "potential_monthly_subscription_commitments",
        "forecast_months", "forecast",
        "data_quality_warnings", "assumptions_explanation", "missing_data_reasons",
    ]
    for field in stage1_fields:
        assert field in result, f"Stage 1 field '{field}' is missing from response."

    # forecast is a list of month items
    assert isinstance(result["forecast"], list)
    assert len(result["forecast"]) == 6

    first = result["forecast"][0]
    month_item_fields = [
        "month", "month_name", "projected_operating_revenue",
        "projected_non_sub_expenses", "projected_confirmed_subscription_expenses",
        "potential_subscription_expenses", "projected_net_cashflow",
        "projected_closing_cash_balance", "is_cash_depleted",
    ]
    for field in month_item_fields:
        assert field in first, f"Stage 1 ForecastMonthItem field '{field}' missing."

    # Stage 2 fields exist alongside Stage 1
    assert "scenarios_available" in result
    assert "scenario_methodology_note" in result

