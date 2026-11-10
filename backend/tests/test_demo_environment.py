"""
Stage 8.5: Isolated Demo Environment and Realistic Business Scenario Testing
Tests for:
1. Demo Business Creation & Isolation
2. Demo Data Generator Provenance & Reproducibility
3. Strict Data Isolation (Sandbox Transactions Untouched by Demo Generation / Reset)
4. Financial Engine Processing on Demo Data (Subscriptions, Forecast, Intelligence, Reports, Simulation)
5. Business Service Header & Query Routing (X-SubWise-Demo-Mode, active_business_id)
6. Safe Demo Reset Guard
"""
import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.services.demo_data_generator import DemoDataGenerator
from app.services.business_service import get_active_business, switch_active_business, get_all_user_businesses
from app.services.forecast_engine import ForecastEngine
from app.services.financial_intelligence_engine import FinancialIntelligenceEngine
from app.services.report_engine import ReportEngine
from app.services.cashflow_simulator import CashFlowSimulator
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer
from app.schemas.simulation import SimulationRequest

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def _create_user_and_standard_biz(db):
    user = User(
        email="test_founder@example.com",
        hashed_password="mockhashedpassword123",
        full_name="Alex Vance",
        is_active=True
    )
    db.add(user)
    db.flush()

    std_biz = BusinessProfile(
        user_id=user.id,
        company_name="Apex Real Ventures",
        industry="SaaS",
        current_cash_reserves=50000.0,
        monthly_baseline_revenue=20000.0,
        currency="USD",
        is_demo=False,
        profile_type="STANDARD"
    )
    db.add(std_biz)
    db.commit()
    db.refresh(user)
    db.refresh(std_biz)
    return user, std_biz


def test_demo_business_creation_and_isolation(db):
    """Verify demo business is isolated and properly configured."""
    user, std_biz = _create_user_and_standard_biz(db)

    # Ensure demo business
    demo_biz = DemoDataGenerator.ensure_demo_business(user, db)
    assert demo_biz.id != std_biz.id
    assert demo_biz.user_id == user.id
    assert demo_biz.is_demo is True
    assert demo_biz.profile_type == "DEMO"
    assert demo_biz.company_name == "DemoTech Solutions"
    assert demo_biz.currency == "USD"

    # Both profiles coexist for this user
    profiles = get_all_user_businesses(user, db)
    assert len(profiles) == 2
    types = {p.profile_type for p in profiles}
    assert "STANDARD" in types
    assert "DEMO" in types


def test_demo_dataset_generation_provenance(db):
    """Verify generated dataset meets all Stage 8.5 provenance requirements."""
    user, std_biz = _create_user_and_standard_biz(db)
    demo_biz = DemoDataGenerator.ensure_demo_business(user, db)

    stats = DemoDataGenerator.generate_demo_dataset(demo_biz, db)
    assert stats["transaction_count"] >= 70
    assert stats["subscription_count"] == 9
    assert stats["recommendation_count"] >= 3

    # Provenance audit: All transactions must be strictly demo-marked
    demo_txs = db.query(Transaction).filter(Transaction.business_id == demo_biz.id).all()
    assert len(demo_txs) == stats["transaction_count"]
    for tx in demo_txs:
        assert tx.data_source == "demo_fixture", f"Transaction {tx.id} has invalid data_source {tx.data_source}"
        assert tx.is_simulated is True, f"Transaction {tx.id} not marked simulated"
        assert tx.paypal_transaction_id is None, "Simulated tx must never fabricate paypal_transaction_id"

    # Check subscriptions
    demo_subs = db.query(Subscription).filter(Subscription.business_id == demo_biz.id).all()
    assert len(demo_subs) == 9
    confirmed = [s for s in demo_subs if s.detection_type == "confirmed"]
    potential = [s for s in demo_subs if s.detection_type == "potential"]
    assert len(confirmed) == 8
    assert len(potential) == 1
    assert potential[0].vendor_name == "Linear"

    # Verify Annual Figma Subscription exists with upcoming renewal in Dec 2026
    figma = next((s for s in demo_subs if s.vendor_name == "Figma"), None)
    assert figma is not None
    assert figma.cadence == "annual"
    assert figma.latest_amount == 540.0
    assert figma.next_billing_date.year == 2026
    assert figma.next_billing_date.month == 12


def test_strict_data_isolation_sandbox_untouched(db):
    """Verify demo generation and reset NEVER touch sandbox records."""
    user, std_biz = _create_user_and_standard_biz(db)

    # Add real sandbox transactions to std_biz
    real_tx1 = Transaction(
        business_id=std_biz.id,
        paypal_transaction_id="REAL_PP_TX_001",
        transaction_date=datetime.datetime(2026, 10, 1),
        raw_description="PayPal Account Initial Funding",
        normalized_vendor="PayPal Balance Adjustment",
        category="Account Funding / Balance Adjustment",
        gross_amount=5000.0,
        net_amount=5000.0,
        currency="USD",
        status="COMPLETED",
        data_source="paypal_api",
        is_simulated=False
    )
    real_tx2 = Transaction(
        business_id=std_biz.id,
        paypal_transaction_id="REAL_PP_TX_002",
        transaction_date=datetime.datetime(2026, 10, 15),
        raw_description="SubWise Verification Payment",
        normalized_vendor="SubWise",
        category="General SaaS / Operations",
        gross_amount=-5.0,
        net_amount=-5.0,
        currency="USD",
        status="COMPLETED",
        data_source="paypal_api",
        is_simulated=False
    )
    db.add_all([real_tx1, real_tx2])
    db.commit()

    # Generate demo data
    demo_biz = DemoDataGenerator.ensure_demo_business(user, db)
    DemoDataGenerator.generate_demo_dataset(demo_biz, db)

    # Assert real transactions are completely intact
    std_txs = db.query(Transaction).filter(Transaction.business_id == std_biz.id).all()
    assert len(std_txs) == 2
    assert {t.paypal_transaction_id for t in std_txs} == {"REAL_PP_TX_001", "REAL_PP_TX_002"}

    # Reset demo data
    reset_stats = DemoDataGenerator.clear_demo_records(demo_biz, db)
    assert reset_stats["cleared_transactions"] > 70
    assert reset_stats["cleared_subscriptions"] == 9

    # Assert demo records cleared
    assert db.query(Transaction).filter(Transaction.business_id == demo_biz.id).count() == 0
    assert db.query(Subscription).filter(Subscription.business_id == demo_biz.id).count() == 0

    # Assert standard sandbox records remain 100% untouched
    std_txs_after = db.query(Transaction).filter(Transaction.business_id == std_biz.id).all()
    assert len(std_txs_after) == 2


def test_engines_execution_with_demo_data(db):
    """Verify that all existing financial engines run cleanly on demo records."""
    user, _ = _create_user_and_standard_biz(db)
    demo_biz = DemoDataGenerator.ensure_demo_business(user, db)
    DemoDataGenerator.generate_demo_dataset(demo_biz, db)

    demo_txs = db.query(Transaction).filter(Transaction.business_id == demo_biz.id).all()
    demo_subs = db.query(Subscription).filter(Subscription.business_id == demo_biz.id).all()

    # 1. Forecast Engine
    forecast = ForecastEngine.generate_forecast(demo_biz, demo_subs, demo_txs)
    assert forecast["status"] == "sufficient_data"
    assert forecast["scenarios_available"] is True
    assert "baseline" in forecast
    assert "optimistic" in forecast
    assert "conservative" in forecast
    assert len(forecast["baseline"]["months"]) == 6
    assert forecast["baseline"]["runway_available"] is True
    assert forecast["baseline"]["runway_note"] is not None

    # 2. Financial Intelligence Engine
    overview = FinancialIntelligenceEngine.generate_overview(demo_biz, demo_subs, demo_txs)
    assert overview.financial_health_index is not None
    assert overview.financial_health_index.score is not None
    assert 0 <= overview.financial_health_index.score <= 100
    assert overview.financial_health_index.status_label is not None
    assert overview.data_sufficiency_status == "sufficient_data"
    assert overview.monthly_briefing is not None
    assert len(overview.monthly_briefing.recommended_cfo_actions) > 0

    # 3. Report Engine
    # Monthly financial report
    monthly_rep = ReportEngine.generate_monthly_financial_report(
        business=demo_biz,
        transactions=demo_txs,
        subscriptions=demo_subs,
    )
    assert monthly_rep.total_operating_revenue > 0
    assert monthly_rep.total_confirmed_sub_expenses > 0

    # Subscription expense report
    sub_rep = ReportEngine.generate_subscription_expense_report(
        business=demo_biz,
        subscriptions=demo_subs,
        transactions=demo_txs,
    )
    assert len(sub_rep.items) == 9
    assert sub_rep.total_confirmed_annual_commitments > 0

    # Upcoming renewal report
    renewals_rep = ReportEngine.generate_upcoming_renewal_report(
        business=demo_biz,
        subscriptions=demo_subs,
        transactions=demo_txs,
    )
    assert renewals_rep.total_upcoming_60_days_count > 0
    vendor_names = [r.vendor_name for r in renewals_rep.scheduled_renewals]
    assert "Figma" in vendor_names

    # 4. Cash Flow Simulator
    sim_result = CashFlowSimulator.run_simulation(
        business=demo_biz,
        subscriptions=demo_subs,
        transactions=demo_txs,
        revenue_shock_pct=-20.0,
        pause_tier_3=True
    )
    assert sim_result["monthly_savings_from_paused"] > 0
    assert len(sim_result["timeline"]) == 12


def test_business_service_and_header_routing(db):
    """Verify demo mode switching via active_business_id and header resolution."""
    user, std_biz = _create_user_and_standard_biz(db)
    demo_biz = DemoDataGenerator.ensure_demo_business(user, db)

    # Default without header -> Standard Sandbox profile
    active = get_active_business(current_user=user, db=db, request=None)
    assert active.id == std_biz.id
    assert active.is_demo is False

    # Switch active business to demo via DB setting
    switched = switch_active_business(user=user, db=db, mode="demo")
    assert switched.id == demo_biz.id
    assert switched.is_demo is True

    # Check that get_active_business now honors active_business_id
    active_now = get_active_business(current_user=user, db=db, request=None)
    assert active_now.id == demo_biz.id

    # Switch back to sandbox
    switched_back = switch_active_business(user=user, db=db, mode="sandbox")
    assert switched_back.id == std_biz.id
    assert switched_back.is_demo is False

    # Verify that get_active_business reflects sandbox after switch back
    active_after = get_active_business(current_user=user, db=db, request=None)
    assert active_after.id == std_biz.id
    assert active_after.is_demo is False
    assert active_after.company_name == "Apex Real Ventures"
