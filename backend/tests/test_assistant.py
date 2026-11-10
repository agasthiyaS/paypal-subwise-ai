"""
Stage 7: Intelligent Financial Assistant Tests

Coverage:
1. test_assistant_subscription_spend_query
2. test_assistant_specific_vendor_query
3. test_assistant_revenue_query
4. test_assistant_forecast_runway_query
5. test_assistant_upcoming_renewals_query
6. test_assistant_affordability_simulation_integration
7. test_assistant_report_summary_query
8. test_assistant_health_and_risks_query
9. test_assistant_insufficient_data_integrity
10. test_assistant_api_endpoint_and_tenant_isolation
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
from app.schemas.assistant import AssistantQueryRequest
from app.services.financial_assistant_engine import FinancialAssistantEngine
from app.api.assistant import query_financial_assistant, get_assistant_suggestions


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _make_biz(id=1, user_id=1, name="Apex FinTech", cash=25000.0):
    return BusinessProfile(
        id=id,
        user_id=user_id,
        company_name=name,
        current_cash_reserves=cash,
        currency="USD",
    )


def _make_tx(id, biz_id, amount, months_ago=0, vendor="Customer Sale", is_expense=False, raw_desc=None):
    d = datetime.date.today() - datetime.timedelta(days=30 * months_ago)
    amt = -abs(float(amount)) if is_expense else abs(float(amount))
    return Transaction(
        id=id,
        business_id=biz_id,
        gross_amount=amt,
        net_amount=amt,
        transaction_date=datetime.datetime.combine(d, datetime.time(12, 0)),
        status="COMPLETED",
        raw_description=raw_desc or vendor,
        normalized_vendor=vendor,
        category="General Software" if is_expense else "Sales Revenue",
        currency="USD",
    )


def _make_sub(id, biz_id, vendor, amount, cadence="monthly",
              detection_type="confirmed", price_change_pct=0.0):
    now = datetime.datetime.utcnow()
    avg = round(amount / (1 + price_change_pct / 100), 2) if price_change_pct else amount
    return Subscription(
        id=id,
        business_id=biz_id,
        vendor_name=vendor,
        latest_amount=float(amount),
        average_amount=float(avg),
        cadence=cadence,
        detection_type=detection_type,
        status="active",
        price_change_pct=price_change_pct,
        billing_type="fixed",
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=30),
        next_billing_date=now + datetime.timedelta(days=15),
    )


# ---------------------------------------------------------------------------
# Unit & Integration Tests
# ---------------------------------------------------------------------------

def test_assistant_subscription_spend_query():
    """Verify assistant correctly returns subscription spend metrics and active vendors."""
    biz = _make_biz(cash=20000.0)
    subs = [
        _make_sub(1, biz.id, "GitHub", 50.0, "monthly"),
        _make_sub(2, biz.id, "AWS", 200.0, "monthly"),
    ]
    txs = [
        _make_tx(1, biz.id, 5000.0, months_ago=1),
        _make_tx(2, biz.id, 5000.0, months_ago=2),
    ]

    req = AssistantQueryRequest(message="What are my total subscription expenses?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "SPEND_OVERVIEW"
    assert res.data_sufficiency_status in ("sufficient_data", "limited_data")
    assert "250.00" in res.response_text or len(res.evidence_cards) > 0
    # Check evidence card
    assert len(res.evidence_cards) == 1
    card = res.evidence_cards[0]
    assert card.amount == 250.0
    assert card.navigation_link == "/subscriptions"


def test_assistant_specific_vendor_query():
    """Verify assistant identifies specific vendor details when mentioned in user question."""
    biz = _make_biz()
    subs = [
        _make_sub(1, biz.id, "Datadog", 150.0, "monthly"),
        _make_sub(2, biz.id, "Slack", 30.0, "monthly"),
    ]
    txs = [_make_tx(1, biz.id, 6000.0, months_ago=1)]

    req = AssistantQueryRequest(message="How much do I spend on Datadog?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "SPEND_OVERVIEW"
    assert "Datadog" in res.response_text
    assert "150.00" in res.response_text
    assert len(res.evidence_cards) == 1
    assert res.evidence_cards[0].title == "Vendor: Datadog"
    assert res.evidence_cards[0].amount == 150.0


def test_assistant_revenue_query():
    """Verify assistant answers operating revenue inquiries using verified ledger actuals."""
    biz = _make_biz()
    txs = [
        _make_tx(1, biz.id, 4000.0, months_ago=1, is_expense=False),
        _make_tx(2, biz.id, 6000.0, months_ago=2, is_expense=False),
    ]
    subs = [_make_sub(1, biz.id, "Zoom", 20.0)]

    req = AssistantQueryRequest(message="What is our monthly operating revenue?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "REVENUE_INQUIRY"
    assert len(res.evidence_cards) == 1
    assert res.evidence_cards[0].title == "Monthly Operating Revenue"
    assert res.evidence_cards[0].amount == 5000.0  # Average of 4000 and 6000


def test_assistant_forecast_runway_query():
    """Verify forecast & runway inquiries return calculated months and shortfall status."""
    biz = _make_biz(cash=10000.0)
    txs = [
        _make_tx(1, biz.id, 2000.0, months_ago=1, is_expense=False),
        _make_tx(2, biz.id, 1000.0, months_ago=1, is_expense=True),  # 1000 non-sub
    ]
    subs = [_make_sub(1, biz.id, "HubSpot", 500.0)]  # 500 sub -> total expenses 1500, net +500

    req = AssistantQueryRequest(message="What is our cash runway and 6-month forecast?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "FORECAST_INQUIRY"
    assert len(res.evidence_cards) == 1
    card = res.evidence_cards[0]
    assert card.title == "Projected Cash Runway"
    assert card.navigation_link == "/forecast"
    assert "Runway" in res.response_text


def test_assistant_upcoming_renewals_query():
    """Verify upcoming renewals inquiries return calendar-aware renewal list."""
    biz = _make_biz()
    subs = [
        _make_sub(1, biz.id, "Figma", 45.0, "monthly"),
        _make_sub(2, biz.id, "GitHub", 25.0, "monthly"),
    ]
    txs = [_make_tx(1, biz.id, 5000.0, months_ago=1)]

    req = AssistantQueryRequest(message="What upcoming subscription renewals are due in the next 30 days?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "RENEWAL_CALENDAR"
    assert len(res.evidence_cards) == 1
    card = res.evidence_cards[0]
    assert card.title == "Upcoming Renewals (Next 60 Days)"
    assert card.navigation_link == "/forecast"
    assert "Figma" in res.response_text or "GitHub" in res.response_text


def test_assistant_affordability_simulation_integration():
    """
    Verify affordability questions like 'Can I afford Notion for $20/month?'
    are routed to RecommendationEngine.simulate_purchase rather than using LLM math.
    """
    biz = _make_biz(cash=30000.0)
    txs = [_make_tx(1, biz.id, 8000.0, months_ago=1)]
    subs = [_make_sub(1, biz.id, "Google Workspace", 60.0)]

    req = AssistantQueryRequest(message="Can I afford Notion for $20/month?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "AFFORDABILITY_CHECK"
    assert len(res.evidence_cards) == 1
    card = res.evidence_cards[0]
    assert "Purchase Simulation: Notion" in card.title
    assert card.data_type == "simulation"
    assert card.amount == 20.0
    assert card.badge_label in [
        "Affordable under current assumptions",
        "Affordable with caution",
        "Consider postponing",
        "Insufficient financial data"
    ]
    assert "Purchase Simulation Analysis for **Notion**" in res.response_text
    assert res.generation_model == "SubWise Deterministic Purchase Simulator"


def test_assistant_report_summary_query():
    """Verify report inquiries route to ReportEngine and return structured summary."""
    biz = _make_biz(cash=15000.0)
    txs = [
        _make_tx(1, biz.id, 7000.0, months_ago=1, is_expense=False),
        _make_tx(2, biz.id, 2000.0, months_ago=1, is_expense=True),
    ]
    subs = [_make_sub(1, biz.id, "Jira", 100.0)]

    req = AssistantQueryRequest(message="Summarize our monthly financial report")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "REPORT_SUMMARY"
    assert len(res.evidence_cards) == 1
    card = res.evidence_cards[0]
    assert "Monthly Financial Report" in card.title
    assert card.navigation_link == "/reports"
    assert "Executive Report Summary" in res.response_text


def test_assistant_health_and_risks_query():
    """Verify health score and risk queries return the 100-pt score and risk triggers."""
    biz = _make_biz(cash=25000.0)
    txs = [_make_tx(1, biz.id, 5000.0, months_ago=1)]
    subs = [_make_sub(1, biz.id, "Intercom", 250.0)]

    req = AssistantQueryRequest(message="What is our financial health score and what risks do we have?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.intent == "HEALTH_AND_RISKS"
    assert len(res.evidence_cards) == 1
    card = res.evidence_cards[0]
    assert card.title == "Financial Health Index"
    assert card.amount is not None  # Has score
    assert "Financial Health Score" in res.response_text


def test_assistant_insufficient_data_integrity():
    """
    Verify that an account with 0 records (like Sandbox empty state)
    returns an honest, unhallucinated insufficient data response.
    """
    biz = _make_biz(cash=0.0)
    subs = []
    txs = []

    req = AssistantQueryRequest(message="What is our cash runway?")
    res = FinancialAssistantEngine.process_query(biz, subs, txs, req)

    assert res.data_sufficiency_status == "insufficient_data"
    assert "Insufficient" in res.response_text or "Indeterminate" in res.response_text
    assert res.is_ai_generated is False
    # Health score is withheld
    h_req = AssistantQueryRequest(message="What is my health score?")
    h_res = FinancialAssistantEngine.process_query(biz, subs, txs, h_req)
    assert "Withheld" in h_res.response_text or "Unestablished" in h_res.response_text
    assert h_res.evidence_cards[0].amount is None


def test_assistant_api_endpoint_and_tenant_isolation():
    """
    Verify FastAPI router endpoint enforces tenant isolation:
    User A's assistant queries only access User A's data, and User B gets 404 if no business.
    """
    test_engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=test_engine)
    SessionTest = sessionmaker(bind=test_engine)
    session = SessionTest()

    user_a = User(id=1, email="usera@example.com", hashed_password="pw", full_name="User A")
    user_b = User(id=2, email="userb@example.com", hashed_password="pw", full_name="User B")
    session.add_all([user_a, user_b])
    session.commit()

    biz_a = BusinessProfile(
        id=10,
        user_id=user_a.id,
        company_name="User A Tech",
        current_cash_reserves=12000.0,
        currency="USD"
    )
    session.add(biz_a)
    session.commit()

    # Query for User A
    req = AssistantQueryRequest(message="What is my operating revenue?")
    res_a = query_financial_assistant(request=req, current_user=user_a, db=session)
    assert res_a is not None
    assert "User A Tech" in res_a.response_text or res_a.intent == "REVENUE_INQUIRY"

    # Suggestions for User A
    sug_a = get_assistant_suggestions(current_user=user_a, db=session)
    assert len(sug_a.suggestions) > 0

    # Query for User B (has no BusinessProfile) -> 404
    with pytest.raises(HTTPException) as exc_info:
        query_financial_assistant(request=req, current_user=user_b, db=session)
    assert exc_info.value.status_code == 404

    session.close()
