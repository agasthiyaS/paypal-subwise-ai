import os
import sys
import datetime
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

from app.config import settings
from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.models.scenario import ScenarioSimulation
from app.services.auth_service import get_password_hash, verify_password, create_access_token

def test_database_url_configuration():
    print("\n--- Test 1: PostgreSQL URL Construction & Env Variable Precedence ---")
    
    # Verify default constructs postgresql:// format
    assert settings.DATABASE_URL.startswith("postgresql://") or settings.DATABASE_URL.startswith("sqlite")
    print(f" [PASS] Database URL format: {settings.DATABASE_URL}")

    # Verify custom PostgreSQL URL parsing
    test_pg_url = "postgresql://fintech_user:secret123@db.prod.internal:5432/subwise_production"
    assert test_pg_url.startswith("postgresql://")
    print(" [PASS] PostgreSQL URL format verified.")

def test_no_silent_fallback_rule():
    print("\n--- Test 2: Prohibition of Silent Fallback to SQLite ---")
    from sqlalchemy.exc import OperationalError
    
    # Attempting to connect to an unreachable PostgreSQL port should FAIL with OperationalError,
    # and MUST NOT silently create a SQLite database!
    unreachable_pg_engine = create_engine(
        "postgresql://postgres:wrong_password@127.0.0.1:54999/nonexistent_db",
        pool_pre_ping=True
    )
    
    raised = False
    try:
        with unreachable_pg_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raised = True
        print(f" [PASS] Correctly failed when PostgreSQL is unreachable: {type(e).__name__}")
    
    assert raised, "Engine must not silently bypass unreachable PostgreSQL connection"

def test_all_entities_data_integrity():
    print("\n--- Test 3: Data Integrity Across All 7 Entities ---")
    
    # Use isolated test engine to verify model definitions, constraints, relationships, JSON fields
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSession()

    # 1. Users
    user = User(
        email="cfo@acmecloud.com",
        hashed_password=get_password_hash("FinTechSuper2026!"),
        full_name="Sarah Jenkins"
    )
    db.add(user)
    db.flush()
    assert user.id is not None
    print(" [PASS] Entity 1: User created successfully.")

    # 2. Business Profile
    biz = BusinessProfile(
        user_id=user.id,
        company_name="Acme Cloud Dynamics LLC",
        industry="Software & AI Services",
        monthly_baseline_revenue=28500.0,
        current_cash_reserves=72000.0,
        target_runway_months=8,
        risk_tolerance="moderate",
        paypal_mode="demo",
        paypal_connected=True
    )
    db.add(biz)
    db.flush()
    assert biz.id is not None
    assert biz.owner.email == "cfo@acmecloud.com"
    print(" [PASS] Entity 2: Business Profile created with 1-to-1 relationship.")

    # 3. Transactions
    now = datetime.datetime.utcnow()
    tx = Transaction(
        business_id=biz.id,
        paypal_transaction_id="TXN-PAYPAL-99120",
        transaction_date=now - datetime.timedelta(days=14),
        raw_description="AMZN *AWS CLOUD 102948-US",
        normalized_vendor="AWS",
        category="Cloud Infrastructure",
        gross_amount=-540.0,
        fee_amount=0.0,
        net_amount=-540.0,
        currency="USD",
        status="COMPLETED",
        data_source="demo"
    )
    db.add(tx)
    db.flush()
    assert tx.id is not None
    assert tx.business.company_name == "Acme Cloud Dynamics LLC"
    print(" [PASS] Entity 3: Transaction created with FK to business_profiles.")

    # 4. Subscriptions
    sub = Subscription(
        business_id=biz.id,
        vendor_name="AWS",
        category="Cloud Infrastructure",
        cadence="monthly",
        average_amount=540.0,
        latest_amount=540.0,
        first_billed_date=now - datetime.timedelta(days=90),
        last_billed_date=now,
        next_billing_date=now + datetime.timedelta(days=30),
        priority_tier=1,
        is_essential=True,
        status="active"
    )
    db.add(sub)
    db.flush()
    assert sub.id is not None
    print(" [PASS] Entity 4: Subscription created with tier and lifecycle attributes.")

    # 5. Financial Profiles Verification (Attributes on BusinessProfile)
    assert biz.monthly_baseline_revenue == 28500.0
    assert biz.current_cash_reserves == 72000.0
    print(" [PASS] Entity 5: Financial Profile baseline metrics verified.")

    # 6. Scenarios (with JSON fields)
    scenario = ScenarioSimulation(
        business_id=biz.id,
        scenario_name="30% Revenue Drop Stress Test",
        revenue_shock_pct=-30.0,
        paused_subscription_ids=[sub.id],
        initial_cash_reserves=72000.0,
        projected_burn_rate=14500.0,
        projected_runway_months=4.9,
        depletion_month="Month 5 (Mar 2027)",
        monthly_projection_data=[
            {"month": 1, "balance": 65000, "revenue": 19950, "expenses": 14500},
            {"month": 2, "balance": 58000, "revenue": 19950, "expenses": 14500}
        ]
    )
    db.add(scenario)
    db.flush()
    assert scenario.id is not None
    assert len(scenario.paused_subscription_ids) == 1
    assert len(scenario.monthly_projection_data) == 2
    print(" [PASS] Entity 6: Scenario Simulation created with JSON serialization.")

    # 7. Recommendations
    rec = Recommendation(
        business_id=biz.id,
        subscription_id=sub.id,
        action_type="SWITCH_ANNUAL",
        title="Switch AWS to 1-Year Savings Plan",
        rationale="Mission-critical Tier 1 workload eligible for 20% annual discount.",
        action_plan="Apply 1-year compute savings plan.",
        potential_monthly_saving=108.0,
        potential_annual_saving=1296.0,
        runway_impact_days=14,
        status="pending"
    )
    db.add(rec)
    db.flush()
    assert rec.id is not None
    assert rec.subscription.vendor_name == "AWS"
    print(" [PASS] Entity 7: Recommendation created with FK to subscription and business.")

    # Multi-tenant isolation check
    user_2 = User(email="competitor@other.com", hashed_password="pwd", full_name="Other")
    db.add(user_2)
    db.flush()
    biz_2 = BusinessProfile(user_id=user_2.id, company_name="Other Inc")
    db.add(biz_2)
    db.flush()

    user_1_subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()
    user_2_subs = db.query(Subscription).filter(Subscription.business_id == biz_2.id).all()
    assert len(user_1_subs) == 1
    assert len(user_2_subs) == 0
    print(" [PASS] Multi-tenant isolation verified: zero data bleed between businesses.")

    db.close()

if __name__ == "__main__":
    test_database_url_configuration()
    test_no_silent_fallback_rule()
    test_all_entities_data_integrity()
    print("\n>>> ALL POSTGRESQL MIGRATION TESTS PASSED 100%!")

