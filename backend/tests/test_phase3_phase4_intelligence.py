import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.subscription import Subscription
from app.models.transaction import Transaction

from app.services.smart_spending_service import SmartSpendingService
from app.services.financial_health_service import FinancialHealthService
from app.services.multi_scenario_forecast_service import MultiScenarioForecastService
from app.services.consumer_recommendation_engine import ConsumerRecommendationEngine
from app.services.vendor_comparison_service import VendorComparisonService
from app.services.financial_assistant_engine import FinancialAssistantEngine
from app.schemas.assistant import AssistantQueryRequest
from app.api.financial_intelligence import get_unified_financial_intelligence, get_spending_analysis, get_financial_health_score, get_multi_scenario_forecast
from app.api.savings_discovery import get_personalized_savings_opportunities, get_vendor_comparison_catalog, search_vendor_alternatives

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # User & Business Profile
    user = User(
        id=201,
        email="consumer_test@subwise.io",
        hashed_password="pw_consumer_201",
        full_name="Consumer Tester",
        is_active=True
    )
    session.add(user)
    session.commit()

    biz = BusinessProfile(
        id=201,
        user_id=201,
        company_name="Consumer Test Profile",
        account_type="individual",
        is_demo=False,
        monthly_baseline_revenue=6000.0,
        current_cash_reserves=12000.0,
        paypal_mode="sandbox"
    )
    session.add(biz)
    session.commit()

    yield session
    session.close()


def test_smart_spending_empty_data(db):
    biz = db.query(BusinessProfile).filter_by(id=201).first()
    res = SmartSpendingService.analyze_spending(business=biz, db=db, month=11, year=2026)
    assert res.has_sufficient_data is False
    assert res.total_expenses == 0.0
    assert "No expenses recorded this month" in (res.notes or "")


def test_smart_spending_with_mom_and_spikes(db):
    biz = db.query(BusinessProfile).filter_by(id=201).first()

    # Add prior month expenses (Oct 2026)
    exp_oct1 = Expense(
        business_id=biz.id,
        user_id=biz.user_id,
        description="Supermarket Oct",
        amount=200.0,
        category="Food & Groceries",
        expense_date=datetime.datetime(2026, 10, 15, 12, 0),
        data_source="manual"
    )
    exp_oct2 = Expense(
        business_id=biz.id,
        user_id=biz.user_id,
        description="Electric Bill Oct",
        amount=80.0,
        category="Electricity & Utilities",
        expense_date=datetime.datetime(2026, 10, 20, 14, 0),
        data_source="manual"
    )
    # Add current month expenses (Nov 2026)
    # Food: 200 -> 220 (10% increase, not a spike)
    exp_nov1 = Expense(
        business_id=biz.id,
        user_id=biz.user_id,
        description="Supermarket Nov",
        amount=220.0,
        category="Food & Groceries",
        expense_date=datetime.datetime(2026, 11, 5, 10, 0),
        data_source="manual"
    )
    # Utilities: 80 -> 180 (>25% and >$40 increase -> SPIKE)
    exp_nov2 = Expense(
        business_id=biz.id,
        user_id=biz.user_id,
        description="Electric Bill Nov",
        amount=180.0,
        category="Electricity & Utilities",
        expense_date=datetime.datetime(2026, 11, 8, 11, 0),
        data_source="manual"
    )
    # Income in Nov
    inc_nov = Expense(
        business_id=biz.id,
        user_id=biz.user_id,
        description="Monthly Salary",
        amount=4000.0,
        category="Other",
        expense_type="income",
        expense_date=datetime.datetime(2026, 11, 1, 9, 0),
        data_source="manual"
    )
    db.add_all([exp_oct1, exp_oct2, exp_nov1, exp_nov2, inc_nov])
    db.commit()

    res = SmartSpendingService.analyze_spending(business=biz, db=db, month=11, year=2026)
    assert res.has_sufficient_data is True
    assert res.total_expenses == 400.0  # 220 + 180
    assert res.total_income == 4000.0
    assert res.net_savings == 3600.0
    assert res.savings_rate_percent == 90.0

    # Verify spike detection
    util_spike = next((s for s in res.unusual_spikes if "Electricity & Utilities" in s), None)
    assert util_spike is not None


def test_financial_health_score(db):
    biz = db.query(BusinessProfile).filter_by(id=201).first()
    spending = SmartSpendingService.analyze_spending(business=biz, db=db, month=11, year=2026)
    health = FinancialHealthService.calculate_health_score(business=biz, analysis=spending, db=db)

    assert 0 <= health.score <= 100
    assert health.rating in ["Excellent", "Good", "Fair", "Needs Attention"]
    assert len(health.factors) == 4
    factor_names = [f.factor_name for f in health.factors]
    assert any("Savings Rate" in fn for fn in factor_names)
    assert any("Budget Adherence" in fn for fn in factor_names)
    assert any("Recurring" in fn for fn in factor_names)
    assert any("Liquidity" in fn for fn in factor_names)
    assert "not a credit score" in health.disclaimer.lower()


def test_financial_health_configured_budget(db):
    """Verify health score uses actual configured budget when present."""
    biz = db.query(BusinessProfile).filter_by(id=201).first()
    # Add an overall budget
    b = Budget(
        business_id=201,
        category="Overall",
        monthly_limit=4500.0,
        period_month=11,
        period_year=2026
    )
    db.add(b)
    db.commit()

    spending = SmartSpendingService.analyze_spending(business=biz, db=db, month=11, year=2026)
    health = FinancialHealthService.calculate_health_score(business=biz, analysis=spending, db=db)

    budget_factor = next(f for f in health.factors if f.factor_name == "Budget Adherence")
    assert "configured monthly budget" in budget_factor.description
    assert "$4,500.00" in budget_factor.description
    assert budget_factor.score > 0
    assert health.has_sufficient_data is True

    # Clean up budget for subsequent tests
    db.delete(b)
    db.commit()


def test_financial_health_available_baseline_revenue(db):
    """Verify health score falls back to baseline revenue ceiling only when appropriate."""
    biz = db.query(BusinessProfile).filter_by(id=201).first()
    assert biz.monthly_baseline_revenue == 6000.0

    spending = SmartSpendingService.analyze_spending(business=biz, db=db, month=11, year=2026)
    health = FinancialHealthService.calculate_health_score(business=biz, analysis=spending, db=db)

    budget_factor = next(f for f in health.factors if f.factor_name == "Budget Adherence")
    assert "monthly baseline revenue ceiling" in budget_factor.description
    assert "$6,000.00" in budget_factor.description
    assert budget_factor.score > 0
    assert health.has_sufficient_data is True


def test_financial_health_neither_budget_nor_baseline(db):
    """Verify health score returns explicit insufficient-data state with no hardcoded $3,500 fallback."""
    user2 = User(id=202, email="nobudget@test.com", hashed_password="pw", full_name="No Budget", is_active=True)
    biz2 = BusinessProfile(
        id=202,
        user_id=202,
        company_name="No Budget Profile",
        account_type="individual",
        monthly_baseline_revenue=None,
        current_cash_reserves=5000.0
    )
    db.add(user2)
    db.add(biz2)
    db.commit()

    spending = SmartSpendingService.analyze_spending(business=biz2, db=db, month=11, year=2026)
    health = FinancialHealthService.calculate_health_score(business=biz2, analysis=spending, db=db)

    budget_factor = next(f for f in health.factors if f.factor_name == "Budget Adherence")
    # Must NOT contain $3,500 or arbitrary numbers
    assert "3500" not in budget_factor.description
    assert "$3,500" not in budget_factor.description
    assert budget_factor.score == 0
    assert budget_factor.impact == "neutral"
    assert "Insufficient Data" in budget_factor.description or "No budget configured" in budget_factor.description
    assert health.has_sufficient_data is False
    assert any("budget" in r.lower() for r in health.missing_data_reasons)
    assert any("budget" in a.lower() for a in health.actionable_improvements)


def test_financial_health_recalculated_against_available_points(db):
    """Verify that when budget is unconfigured, health score is normalized against available 75 pts rather than penalizing by 25 pts."""
    biz = db.query(BusinessProfile).filter_by(id=202).first()
    if not biz:
        user2 = User(id=202, email="nobudget@test.com", hashed_password="pw", full_name="No Budget", is_active=True)
        biz = BusinessProfile(
            id=202,
            user_id=202,
            company_name="No Budget Profile",
            account_type="individual",
            monthly_baseline_revenue=None,
            current_cash_reserves=5000.0
        )
        db.add(user2)
        db.add(biz)
        db.commit()

    from app.schemas.consumer_intelligence import SpendingAnalysisResult
    spending = SpendingAnalysisResult(
        month=11,
        year=2026,
        total_income=5000.0,
        total_expenses=2000.0,
        net_savings=3000.0,
        savings_rate_percent=60.0,
        recurring_expenses_total=200.0,
        discretionary_expenses_total=1800.0,
        has_sufficient_data=True
    )
    health = FinancialHealthService.calculate_health_score(business=biz, analysis=spending, db=db)
    # 30 (savings) + 25 (recurring) + 12 (liquidity) = 67 / 75 -> 89% Excellent
    assert health.score == 89
    assert health.rating == "Excellent"
    assert health.has_sufficient_data is False
    assert any("normalized against available" in r.lower() for r in health.missing_data_reasons)


def test_financial_health_zero_expenses(db):
    """Verify health score gracefully handles zero expenses without arbitrary burn rate assumptions."""
    biz = db.query(BusinessProfile).filter_by(id=201).first()
    # Mock zero-expense spending analysis
    from app.schemas.consumer_intelligence import SpendingAnalysisResult
    zero_spending = SpendingAnalysisResult(
        month=11,
        year=2026,
        total_income=4000.0,
        total_expenses=0.0,
        net_savings=4000.0,
        savings_rate_percent=100.0,
        recurring_expenses_total=0.0,
        discretionary_expenses_total=0.0,
        has_sufficient_data=True
    )
    health = FinancialHealthService.calculate_health_score(business=biz, analysis=zero_spending, db=db)

    budget_factor = next(f for f in health.factors if f.factor_name == "Budget Adherence")
    assert budget_factor.score == 25
    assert budget_factor.impact == "positive"
    assert "0% utilized" in budget_factor.description

    liquidity_factor = next(f for f in health.factors if f.factor_name == "Liquidity & Safety Buffer")
    assert liquidity_factor.score == 20
    assert "zero active monthly burn" in liquidity_factor.description or "zero recorded monthly burn" in liquidity_factor.description


def test_financial_health_insufficient_historical_data(db):
    """Verify health score reflects insufficient historical data honestly."""
    biz = db.query(BusinessProfile).filter_by(id=202).first()
    from app.schemas.consumer_intelligence import SpendingAnalysisResult
    insufficient_spending = SpendingAnalysisResult(
        month=11,
        year=2026,
        total_income=0.0,
        total_expenses=0.0,
        net_savings=0.0,
        savings_rate_percent=0.0,
        recurring_expenses_total=0.0,
        discretionary_expenses_total=0.0,
        has_sufficient_data=False
    )
    health = FinancialHealthService.calculate_health_score(business=biz, analysis=insufficient_spending, db=db)

    assert health.has_sufficient_data is False
    assert len(health.missing_data_reasons) > 0
    savings_factor = next(f for f in health.factors if f.factor_name == "Monthly Savings Rate")
    assert savings_factor.impact == "neutral"
    assert "No income or expense" in savings_factor.description


def test_assistant_gemini_provider_detection_and_fallback():
    """Verify AI assistant safely checks GEMINI_API_KEY without leaking or calling if unconfigured."""
    is_configured = FinancialAssistantEngine.is_llm_configured()
    assert isinstance(is_configured, bool)

    biz = BusinessProfile(
        id=299,
        company_name="Safe Provider Test",
        current_cash_reserves=10000.0,
        monthly_baseline_revenue=5000.0
    )

    # Check starter suggestions reflect correct engine
    sug = FinancialAssistantEngine.get_starter_suggestions(biz, [], [])
    if not is_configured:
        assert sug.llm_provider_configured is False
        assert "Deterministic" in sug.active_engine

    # Check general fintech query routes safely to deterministic fallback
    req = AssistantQueryRequest(message="Can you explain how SubWise tracks financial risk?")
    res = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=req
    )

    # Must be deterministic when no key is configured
    if not is_configured:
        assert res.is_ai_generated is False
        assert "Deterministic" in res.generation_model
        assert res.llm_provider_configured is False
        assert "key" not in res.response_text.lower()
        assert "secret" not in res.response_text.lower()


def test_multi_scenario_forecast(db):
    biz = db.query(BusinessProfile).filter_by(id=201).first()
    spending = SmartSpendingService.analyze_spending(business=biz, db=db, month=11, year=2026)
    forecast = MultiScenarioForecastService.generate_forecast(business=biz, analysis=spending, days=90)

    assert forecast.days_projected == 90
    assert forecast.current_cash == 12000.0
    assert len(forecast.timeline) > 0

    # Verify Day 30, 60, 90 snapshots contain all three scenarios
    for period in [forecast.day_30_balance, forecast.day_60_balance, forecast.day_90_balance]:
        assert "baseline" in period
        assert "conservative" in period
        assert "optimistic" in period
        assert period["conservative"] <= period["baseline"] <= period["optimistic"]


def test_vendor_comparison_service():
    catalog = VendorComparisonService.get_catalog()
    assert len(catalog) >= 5

    # Check search functionality
    streaming_matches = VendorComparisonService.search_alternatives("streaming")
    assert len(streaming_matches) > 0
    categories = [m.category.lower() for m in streaming_matches]
    assert any("streaming" in c for c in categories)

    # Check opportunity matching against user subscriptions
    user_subs = ["Netflix", "Spotify"]
    opportunities = VendorComparisonService.match_user_opportunities(user_subs)
    assert opportunities.total_identified_monthly_savings > 0
    assert opportunities.total_identified_annual_savings > 0
    assert len(opportunities.ranked_opportunities) >= 2
    matched_services = [o.current_service_name for o in opportunities.ranked_opportunities]
    assert any("Netflix" in s for s in matched_services)
    assert any("Spotify" in s for s in matched_services)


def test_consumer_recommendation_engine(db):
    biz = db.query(BusinessProfile).filter_by(id=201).first()
    spending = SmartSpendingService.analyze_spending(business=biz, db=db, month=11, year=2026)

    now = datetime.datetime.utcnow()
    sub1 = Subscription(
        business_id=biz.id,
        vendor_name="Netflix 4K",
        category="Entertainment",
        cadence="monthly",
        average_amount=22.99,
        latest_amount=22.99,
        first_billed_date=now - datetime.timedelta(days=90),
        last_billed_date=now - datetime.timedelta(days=10),
        next_billing_date=now + datetime.timedelta(days=20),
        status="active"
    )
    sub2 = Subscription(
        business_id=biz.id,
        vendor_name="Hulu Bundle",
        category="Entertainment",
        cadence="monthly",
        average_amount=17.99,
        latest_amount=17.99,
        first_billed_date=now - datetime.timedelta(days=90),
        last_billed_date=now - datetime.timedelta(days=15),
        next_billing_date=now + datetime.timedelta(days=15),
        status="active"
    )
    db.add_all([sub1, sub2])
    db.commit()

    subs = [sub1, sub2]
    recs = ConsumerRecommendationEngine.generate_recommendations(business=biz, analysis=spending, subscriptions=subs, db=db)
    assert len(recs) > 0
    rec_types = [r.action_type for r in recs]
    assert "CANCEL_OVERLAP" in rec_types or "SWITCH_TIER" in rec_types


def test_unified_financial_intelligence_direct(db):
    user = db.query(User).filter_by(id=201).first()
    res = get_unified_financial_intelligence(request=None, current_user=user, db=db)

    assert res.account_type == "individual"
    assert res.company_or_family_name == "Consumer Test Profile"
    assert res.spending_analysis is not None
    assert res.health_score is not None
    assert res.forecast is not None
    assert isinstance(res.total_potential_monthly_savings, float)


def test_savings_discovery_endpoints_direct(db):
    user = db.query(User).filter_by(id=201).first()

    # Personalized
    opps = get_personalized_savings_opportunities(request=None, current_user=user, db=db)
    assert hasattr(opps, "ranked_opportunities")
    assert hasattr(opps, "total_identified_monthly_savings")

    # Catalog
    catalog = get_vendor_comparison_catalog()
    assert len(catalog) >= 5

    # Search
    search_res = search_vendor_alternatives(query="storage")
    assert len(search_res) > 0
    assert any("storage" in (s.category.lower() + s.current_service_name.lower()) for s in search_res)


def test_assistant_extended_intents(db):
    biz = db.query(BusinessProfile).filter_by(id=201).first()

    # 1. Vendor Alternatives query
    query1 = "Can you suggest cheaper alternatives for Netflix and streaming?"
    intent1 = FinancialAssistantEngine.detect_intent(query1)
    assert intent1 == "VENDOR_ALTERNATIVES"

    req1 = AssistantQueryRequest(message=query1)
    res1 = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=req1
    )
    assert "Alternative" in res1.response_text or "Savings" in res1.response_text
    assert res1.intent == "VENDOR_ALTERNATIVES"

    # 2. Spending Breakdown query
    query2 = "Where did my money go this month?"
    intent2 = FinancialAssistantEngine.detect_intent(query2)
    assert intent2 == "SPENDING_BREAKDOWN"

    req2 = AssistantQueryRequest(message=query2)
    res2 = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=req2
    )
    assert res2.intent == "SPENDING_BREAKDOWN"

    # 3. Budget Status query
    query3 = "Am I over budget or exceeding my spending limit?"
    intent3 = FinancialAssistantEngine.detect_intent(query3)
    assert intent3 == "BUDGET_STATUS"

    req3 = AssistantQueryRequest(message=query3)
    res3 = FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=[],
        transactions=[],
        request=req3
    )
    assert res3.intent == "BUDGET_STATUS"
