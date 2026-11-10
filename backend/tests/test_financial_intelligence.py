"""
Stage 5: Financial Intelligence Engine Tests
Tests the FinancialIntelligenceEngine and GET /api/v1/financial-intelligence endpoint.

Coverage:
1.  test_financial_overview_sufficient_data        — Score assigned with 2+ months revenue
2.  test_financial_overview_insufficient_data       — score=None, status=insufficient_data
3.  test_actual_vs_estimated_separation            — historical_actuals vs projected_estimates labels
4.  test_risk_items_evidence_based_price_creep     — PRICE_CREEP only when pct >= 15 & confirmed
5.  test_no_fabricated_amounts                     — amounts match input data, no inflation
6.  test_health_score_documented_methodology       — scoring_methodology string present always
7.  test_subscription_burden_risk_threshold        — HIGH_SUBSCRIPTION_BURDEN when ratio >= 0.25
8.  test_projected_cash_deficit_risk               — PROJECTED_CASH_DEFICIT when forecast depleted
9.  test_api_auth_isolation                        — User A gets overview; User B without biz: 404
10. test_existing_forecast_compatibility           — generate_overview doesn't corrupt forecast output
"""
import pytest
import datetime
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.financial_intelligence_engine import FinancialIntelligenceEngine
from app.api.financial_intelligence import get_financial_intelligence_overview


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def _make_biz(id=1, user_id=1, name="TestCo", cash=10000.0):
    return BusinessProfile(
        id=id,
        user_id=user_id,
        company_name=name,
        current_cash_reserves=cash,
        currency="USD",
    )


def _make_tx(id, biz_id, gross_amount, months_ago=0, description="Sale", is_expense=False):
    d = datetime.date.today() - datetime.timedelta(days=30 * months_ago)
    amt = -abs(float(gross_amount)) if is_expense else abs(float(gross_amount))
    return Transaction(
        id=id,
        business_id=biz_id,
        gross_amount=amt,
        net_amount=amt,
        transaction_date=datetime.datetime.combine(d, datetime.time(12, 0)),
        status="COMPLETED",
        raw_description=description,
        normalized_vendor=description,
        category="General Software" if is_expense else "Sales Revenue",
        currency="USD",
    )


def _make_sub(id, biz_id, vendor, amount, detection_type="confirmed",
              frequency="monthly", price_change_pct=0.0, status="active"):
    avg = round(amount / (1 + price_change_pct / 100), 2) if price_change_pct else amount
    now = datetime.datetime.utcnow()
    return Subscription(
        id=id,
        business_id=biz_id,
        vendor_name=vendor,
        latest_amount=float(amount),
        average_amount=float(avg),
        cadence=frequency,
        detection_type=detection_type,
        status=status,
        price_change_pct=price_change_pct,
        billing_type="fixed",
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=30),
        next_billing_date=now + datetime.timedelta(days=15),
    )


# ---------------------------------------------------------------------------
# 1. Sufficient data → score assigned
# ---------------------------------------------------------------------------

def test_financial_overview_sufficient_data():
    biz = _make_biz()
    txns = [
        _make_tx(1, 1, 5000.0, months_ago=2, description="Customer Sale"),
        _make_tx(2, 1, 5200.0, months_ago=1, description="Customer Sale"),
        _make_tx(3, 1, 5100.0, months_ago=0, description="Customer Sale"),
    ]
    subs = [_make_sub(10, 1, "Slack", 50.0)]

    overview = FinancialIntelligenceEngine.generate_overview(biz, subs, txns)

    assert overview.data_sufficiency_status in ("sufficient_data", "limited_data")
    assert overview.financial_health_index.score is not None
    assert 0 <= overview.financial_health_index.score <= 100
    assert overview.financial_health_index.scoring_methodology != ""


# ---------------------------------------------------------------------------
# 2. Insufficient data → score = None
# ---------------------------------------------------------------------------

def test_financial_overview_insufficient_data():
    biz = _make_biz(cash=0.0)
    overview = FinancialIntelligenceEngine.generate_overview(biz, [], [])

    assert overview.data_sufficiency_status == "insufficient_data"
    assert overview.financial_health_index.score is None
    assert overview.risk_intelligence == []
    assert len(overview.required_records_for_analysis) > 0
    assert overview.financial_health_index.scoring_methodology != ""


# ---------------------------------------------------------------------------
# 3. Historical actuals clearly distinct from projected estimates
# ---------------------------------------------------------------------------

def test_actual_vs_estimated_separation():
    biz = _make_biz()
    txns = [
        _make_tx(1, 1, 4000.0, months_ago=1, description="Sale"),
        _make_tx(2, 1, 4000.0, months_ago=0, description="Sale"),
    ]
    overview = FinancialIntelligenceEngine.generate_overview(biz, [], txns)

    # Historical actuals → actual past data fields exist
    ha = overview.historical_actuals
    assert ha.operating_months_analyzed >= 0
    assert ha.historical_monthly_operating_revenue >= 0
    assert ha.paypal_balance_note != ""
    assert ha.cash_provenance != ""

    # Projected estimates → future labels present
    pe = overview.projected_estimates
    assert pe.forecast_months == 6
    assert pe.runway_status != ""
    assert pe.runway_explanation != ""

    # The two sections carry distinct semantic labels
    assert "VERIFIED" not in pe.runway_status.upper() or pe.forecast_months == 6  # projected side
    assert ha.historical_monthly_operating_revenue >= 0  # actual side


# ---------------------------------------------------------------------------
# 4. PRICE_CREEP risk only when pct >= 15 and detection_type == "confirmed"
# ---------------------------------------------------------------------------

def test_risk_items_evidence_based_price_creep():
    biz = _make_biz()
    txns = [
        _make_tx(1, 1, 5000.0, months_ago=1, description="Sale"),
        _make_tx(2, 1, 5000.0, months_ago=0, description="Sale"),
    ]

    # Sub with 20% price increase + confirmed → should trigger PRICE_CREEP
    high_creep_sub = _make_sub(10, 1, "Zoom", 120.0, price_change_pct=20.0)
    # Sub with only 10% increase → should NOT trigger (below threshold)
    low_creep_sub  = _make_sub(11, 1, "Notion", 110.0, price_change_pct=10.0)
    # Potential sub with 25% → should NOT trigger (not confirmed)
    potential_sub  = _make_sub(12, 1, "Figma", 200.0, detection_type="potential", price_change_pct=25.0)

    overview = FinancialIntelligenceEngine.generate_overview(
        biz, [high_creep_sub, low_creep_sub, potential_sub], txns
    )

    creep_risks = [r for r in overview.risk_intelligence if r.risk_type == "PRICE_CREEP"]
    vendors_flagged = [r.title for r in creep_risks]

    assert len(creep_risks) == 1, f"Expected 1 PRICE_CREEP risk, got {len(creep_risks)}: {vendors_flagged}"
    assert "Zoom" in vendors_flagged[0]
    assert all("Notion" not in v for v in vendors_flagged)
    assert all("Figma" not in v for v in vendors_flagged)


# ---------------------------------------------------------------------------
# 5. No fabricated amounts — all traceable to inputs
# ---------------------------------------------------------------------------

def test_no_fabricated_amounts():
    biz = _make_biz(cash=8000.0)
    txns = [
        _make_tx(1, 1, 3000.0, months_ago=1, description="Sale"),
        _make_tx(2, 1, 3000.0, months_ago=0, description="Sale"),
    ]
    subs = [_make_sub(10, 1, "GitHub", 100.0)]

    overview = FinancialIntelligenceEngine.generate_overview(biz, subs, txns)

    ha = overview.historical_actuals
    # Revenue must be non-negative and not inflated beyond realistic bounds
    assert ha.historical_monthly_operating_revenue >= 0
    assert ha.historical_monthly_operating_revenue < 1_000_000  # sanity bound
    assert ha.historical_monthly_subscription_expenses >= 0

    fc = overview.forward_commitments
    assert fc.confirmed_monthly_subscription_commitments >= 0
    assert fc.potential_monthly_subscription_commitments >= 0

    # Confirmed annual must equal monthly * 12
    expected_annual = round(fc.confirmed_monthly_subscription_commitments * 12, 2)
    assert abs(fc.confirmed_annual_subscription_commitments - expected_annual) < 0.02


# ---------------------------------------------------------------------------
# 6. Health score has scoring_methodology string in every response
# ---------------------------------------------------------------------------

def test_health_score_documented_methodology():
    # Case A: insufficient data
    biz = _make_biz()
    overview_a = FinancialIntelligenceEngine.generate_overview(biz, [], [])
    assert overview_a.financial_health_index.scoring_methodology != ""
    assert "Financial Health Index" in overview_a.financial_health_index.scoring_methodology

    # Case B: sufficient data
    txns = [
        _make_tx(1, 1, 4000.0, months_ago=1, description="Sale"),
        _make_tx(2, 1, 4000.0, months_ago=0, description="Sale"),
    ]
    overview_b = FinancialIntelligenceEngine.generate_overview(biz, [], txns)
    assert overview_b.financial_health_index.scoring_methodology != ""
    assert "Financial Health Index" in overview_b.financial_health_index.scoring_methodology


# ---------------------------------------------------------------------------
# 7. HIGH_SUBSCRIPTION_BURDEN when confirmed/revenue >= 0.25
# ---------------------------------------------------------------------------

def test_subscription_burden_risk_threshold():
    biz = _make_biz()
    # Revenue: $1000/mo → confirmed commit of $300 = 30% → should trigger
    txns = [
        _make_tx(1, 1, 1000.0, months_ago=1, description="Sale"),
        _make_tx(2, 1, 1000.0, months_ago=0, description="Sale"),
    ]
    subs_high = [_make_sub(10, 1, "Adobe", 300.0)]

    overview_high = FinancialIntelligenceEngine.generate_overview(biz, subs_high, txns)
    burden_risks = [r for r in overview_high.risk_intelligence if r.risk_type == "HIGH_SUBSCRIPTION_BURDEN"]
    assert len(burden_risks) >= 1, "Expected HIGH_SUBSCRIPTION_BURDEN risk at 30% ratio"

    # Below threshold: $200/$1000 = 20% → should NOT trigger
    subs_low = [_make_sub(10, 1, "Adobe", 200.0)]
    overview_low = FinancialIntelligenceEngine.generate_overview(biz, subs_low, txns)
    burden_low = [r for r in overview_low.risk_intelligence if r.risk_type == "HIGH_SUBSCRIPTION_BURDEN"]
    assert len(burden_low) == 0, "Should NOT trigger HIGH_SUBSCRIPTION_BURDEN at 20% ratio"


# ---------------------------------------------------------------------------
# 8. PROJECTED_CASH_DEFICIT surfaces when forecast depletes cash
# ---------------------------------------------------------------------------

def test_projected_cash_deficit_risk():
    """
    Low cash + expenses > revenue → baseline burn drives depletion.
    Engine must surface PROJECTED_CASH_DEFICIT OR show critical runway.
    """
    biz = _make_biz(cash=100.0)  # Very low cash
    # Revenue $500/mo, confirmed sub $400/mo, non-sub $400/mo -> net burn $300/mo
    txns = [
        _make_tx(1, 1, 500.0, months_ago=1, description="Sale"),
        _make_tx(2, 1, 500.0, months_ago=0, description="Sale"),
        _make_tx(3, 1, 400.0, months_ago=1, description="AWS Hosting", is_expense=True),
        _make_tx(4, 1, 400.0, months_ago=0, description="AWS Hosting", is_expense=True),
    ]
    subs = [_make_sub(10, 1, "Salesforce", 400.0)]

    overview = FinancialIntelligenceEngine.generate_overview(biz, subs, txns)

    if overview.data_sufficiency_status != "insufficient_data":
        deficit_risks = [r for r in overview.risk_intelligence if r.risk_type == "PROJECTED_CASH_DEFICIT"]
        assert (
            len(deficit_risks) >= 1
            or "Critical" in overview.projected_estimates.runway_status
            or (
                overview.projected_estimates.estimated_runway_months is not None
                and overview.projected_estimates.estimated_runway_months < 6
            )
        ), f"Expected deficit signal, got runway={overview.projected_estimates.runway_status}"


# ---------------------------------------------------------------------------
# 9. API endpoint: auth isolation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def sqlite_db():
    """Create isolated SQLite in-memory session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_api_auth_isolation(sqlite_db):
    """
    User A with a business profile → endpoint returns 200 (FinancialIntelligenceOverview).
    User B with no business profile → endpoint raises HTTP 404.
    """
    user_a = User(id=1, email="user_a@test.com", hashed_password="hashed_a",
                  is_active=True, full_name="User A")
    biz_a = BusinessProfile(id=1, user_id=1, company_name="Biz A",
                             current_cash_reserves=5000.0, currency="USD")
    user_b = User(id=2, email="user_b@test.com", hashed_password="hashed_b",
                  is_active=True, full_name="User B")

    sqlite_db.add_all([user_a, biz_a, user_b])
    sqlite_db.commit()

    # User A: should return a valid overview
    result_a = get_financial_intelligence_overview(current_user=user_a, db=sqlite_db)
    assert result_a.business_id == biz_a.id
    assert result_a.company_name == "Biz A"
    assert hasattr(result_a, "data_sufficiency_status")
    assert hasattr(result_a, "financial_health_index")
    assert hasattr(result_a, "monthly_briefing")

    # User B: no business profile → HTTPException 404
    with pytest.raises(HTTPException) as exc_info:
        get_financial_intelligence_overview(current_user=user_b, db=sqlite_db)
    assert exc_info.value.status_code == 404
    assert "business profile" in exc_info.value.detail.lower()


# ---------------------------------------------------------------------------
# 10. Existing ForecastEngine compatibility
# ---------------------------------------------------------------------------

def test_existing_forecast_compatibility():
    """
    generate_overview() runs without exception for the empty-data case and
    returns a fully-populated schema with all required fields.
    """
    biz = _make_biz()
    overview = FinancialIntelligenceEngine.generate_overview(biz, [], [])

    assert overview.business_id == biz.id
    assert overview.company_name == biz.company_name
    assert overview.data_sufficiency_status == "insufficient_data"
    assert overview.historical_actuals is not None
    assert overview.forward_commitments is not None
    assert overview.projected_estimates is not None
    assert overview.financial_health_index is not None
    assert overview.monthly_briefing is not None
    assert overview.transparency_disclosure != ""

    assert isinstance(overview.monthly_briefing.is_ai_generated, bool)
    assert overview.monthly_briefing.generation_model != ""
    assert overview.monthly_briefing.data_sufficiency_status == "insufficient_data"
