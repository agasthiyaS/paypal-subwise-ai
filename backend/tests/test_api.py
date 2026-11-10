import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.schemas.auth import UserRegister
from app.schemas.simulation import SimulationRequest
from app.schemas.subscription import SubscriptionUpdate
from app.api.auth import register
from app.api.business import get_profile, update_profile
from app.api.transactions import sync_transactions, get_transactions
from app.api.subscriptions import get_subscriptions, update_subscription
from app.api.simulation import run_simulation
from app.api.recommendations import get_recommendations, get_ai_briefing

# In-memory test engine for fast, isolated integration testing
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_full_fintech_system_integration(db):
    email = "apex_cfo@subwise.io"

    # 1. Register Business
    reg_data = UserRegister(
        email=email,
        password="FinTechSuperPassword2026!",
        full_name="Alexander Vance",
        company_name="Apex Dynamics AI",
        industry="Enterprise Software & Cloud",
        monthly_baseline_revenue=25000.0,
        current_cash_reserves=60000.0
    )
    reg_result = register(payload=reg_data, db=db)
    assert reg_result["user_id"] is not None
    assert reg_result["email"] == email

    user = db.query(User).filter(User.id == reg_result["user_id"]).first()
    assert user is not None

    # 2. Get and Verify Business Profile
    profile = get_profile(current_user=user, db=db)
    assert profile.company_name == "Apex Dynamics AI"
    assert profile.current_cash_reserves == 60000.0

    # 3. Ingest PayPal Transactions (Verified Demonstration Mode)
    sync_res = sync_transactions(force_demo=True, current_user=user, db=db)
    assert sync_res["status"] == "success"
    assert sync_res["data_source"] == "demo"
    assert sync_res["transactions_synced"] > 0
    assert sync_res["new_subscriptions_identified"] > 0

    # 4. Verify Transactions Listed
    tx_list = get_transactions(limit=50, offset=0, current_user=user, db=db)
    assert len(tx_list) > 0
    assert any(tx.normalized_vendor in ["AWS", "Slack", "Zoom", "Google Workspace"] for tx in tx_list)

    # 5. Fetch Subscription Intelligence & Summary
    sub_summary = get_subscriptions(current_user=user, db=db)
    assert sub_summary["total_active_count"] >= 5
    assert sub_summary["total_monthly_spend"] > 0
    assert sub_summary["potential_monthly_savings"] > 0
    assert len(sub_summary["subscriptions"]) > 0

    # 6. Run Cash Flow Stress Test Simulation (-35% Revenue Dip)
    sim_payload = SimulationRequest(
        revenue_shock_pct=-35.0,
        paused_subscription_ids=[],
        pause_tier_3_discretionary=True,
        additional_monthly_burn=1000.0
    )
    sim_result = run_simulation(payload=sim_payload, current_user=user, db=db)
    assert sim_result["revenue_shock_pct"] == -35.0
    assert len(sim_result["timeline"]) == 12
    assert sim_result["monthly_savings_from_paused"] > 0
    assert sim_result["depletion_status"] is not None

    # 7. Check Recommendations Generated
    recs = get_recommendations(current_user=user, db=db)
    assert len(recs) > 0
    action_types = [r.action_type for r in recs]
    assert any(act in ["CONSOLIDATE", "CANCEL", "DOWNGRADE", "SWITCH_ANNUAL"] for act in action_types)

    # 8. Check AI Contextual Briefing
    briefing = get_ai_briefing(current_user=user, db=db)
    assert "Apex Dynamics AI" in briefing["company_name"]
    assert len(briefing["executive_briefing"]) > 100
    assert briefing["runway_months"] > 0
    print("\n>>> ALL FINTECH INTEGRATION TESTS PASSED 100%!")


if __name__ == "__main__":
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    test_full_fintech_system_integration(session)
    session.close()
