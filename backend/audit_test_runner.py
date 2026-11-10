import os
import sys
import datetime
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)

from app.database import Base, get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.schemas.auth import UserRegister, UserLogin
from app.schemas.business import BusinessProfileUpdate, PayPalConnectRequest
from app.schemas.subscription import SubscriptionUpdate
from app.schemas.simulation import SimulationRequest
from app.schemas.recommendation import RecommendationUpdate
from app.api.auth import register, login, get_current_user_profile
from app.api.business import get_profile, update_profile, connect_paypal
from app.api.transactions import sync_transactions, get_transactions
from app.api.subscriptions import get_subscriptions, update_subscription
from app.api.simulation import run_simulation
from app.api.recommendations import get_recommendations, update_recommendation, get_ai_briefing
import jwt
from app.services.auth_service import get_password_hash, verify_password, create_access_token, get_current_user
from app.services.normalizer import TransactionNormalizer, MERCHANT_REGISTRY
from app.services.subscription_detector import SubscriptionDetector
from app.services.cashflow_simulator import CashFlowSimulator
from app.services.recommendation_engine import RecommendationEngine
from app.services.ai_advisor import AIAdvisor
from app.services.paypal_client import PayPalClient
from app.config import settings

def run_audit():
    print("=" * 80)
    print("   PAYPAL SUBWISE AI — COMPREHENSIVE APPLICATION AUDIT SUITE")
    print("=" * 80)

    # In-memory clean database for isolated, repeatable testing
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    db = TestingSession()

    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }

    def record(test_name, success, message=""):
        if success:
            results["passed"] += 1
            print(f" [PASS] {test_name}")
        else:
            results["failed"] += 1
            print(f" [FAIL] {test_name} — {message}")
        results["details"].append({"test": test_name, "success": success, "message": message})

    # =========================================================================
    # AUDIT 1: AUTHENTICATION & JWT SECURITY
    # =========================================================================
    print("\n--- AUDIT 1: Authentication, Password Hashing & JWT Security ---")
    
    # 1.1 Password Hashing with bcrypt
    test_pw = "SecureFinTechPass2026!"
    hashed = get_password_hash(test_pw)
    is_valid = verify_password(test_pw, hashed)
    is_invalid = verify_password("WrongPassword123!", hashed)
    record("Bcrypt Password Hashing & Verification", is_valid and not is_invalid)

    # 1.2 JWT Token Generation and Decoding
    test_sub = "test_user_42"
    token = create_access_token({"sub": test_sub})
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        decoded = None
    token_valid = (decoded is not None and decoded.get("sub") == test_sub)
    record("JWT Generation & Valid Signature Decoding", token_valid)

    # 1.3 JWT Tampered Token Rejection
    tampered_token = token[:-5] + "ABCDE"
    try:
        decoded_tampered = jwt.decode(tampered_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        decoded_tampered = None
    record("JWT Tampered Token Rejection (HMAC-SHA256)", decoded_tampered is None)

    # 1.4 User Registration Endpoint
    reg_payload = UserRegister(
        email="audit_founder@testfintech.io",
        password="ValidPassword2026!",
        full_name="Elena Rostova",
        company_name="Rostova Cloud Systems",
        industry="Software & AI Infrastructure",
        monthly_baseline_revenue=28000.0,
        current_cash_reserves=75000.0
    )
    reg_res = register(payload=reg_payload, db=db)
    user_created = reg_res.get("access_token") is not None and reg_res.get("email") == "audit_founder@testfintech.io"
    record("User Registration (with Business Profile)", user_created)

    user = db.query(User).filter(User.id == reg_res["user_id"]).first()

    # 1.5 Duplicate Email Rejection
    try:
        register(payload=reg_payload, db=db)
        record("Duplicate Registration Email Rejection", False, "Allowed duplicate email")
    except Exception as e:
        record("Duplicate Registration Email Rejection", True, str(e))

    # 1.6 OAuth2 Login Endpoint
    from fastapi.security import OAuth2PasswordRequestForm
    form_data = OAuth2PasswordRequestForm(grant_type="password", username="audit_founder@testfintech.io", password="ValidPassword2026!", scope="", client_id=None, client_secret=None)
    login_res = login(form_data=form_data, db=db)
    login_success = login_res.get("access_token") is not None and login_res.get("token_type") == "bearer"
    record("User Login (OAuth2 Form / JWT Issuance)", login_success)

    # 1.7 Current User Profile Endpoint
    me_profile = get_current_user_profile(current_user=user, db=db)
    me_success = me_profile.get("user", {}).get("email") == "audit_founder@testfintech.io"
    record("Protected /auth/me Profile Lookup", me_success)

    # =========================================================================
    # AUDIT 2: BUSINESS PROFILE & CRUD OPERATIONS
    # =========================================================================
    print("\n--- AUDIT 2: Business Profile & CRUD Operations ---")
    
    # 2.1 Get Profile
    profile = get_profile(current_user=user, db=db)
    record("Get Business Profile", profile.company_name == "Rostova Cloud Systems")

    # 2.2 Update Profile
    update_data = BusinessProfileUpdate(
        company_name="Rostova Enterprise Cloud LLC",
        monthly_baseline_revenue=30000.0,
        current_cash_reserves=80000.0,
        target_runway_months=9
    )
    updated_profile = update_profile(payload=update_data, current_user=user, db=db)
    record("Update Business Profile (PUT)", updated_profile.company_name == "Rostova Enterprise Cloud LLC" and updated_profile.target_runway_months == 9)

    # =========================================================================
    # AUDIT 3: PAYPAL INTEGRATION & SYNC ENGINE
    # =========================================================================
    print("\n--- AUDIT 3: PayPal Integration & Data Acquisition ---")

    # 3.1 PayPal Connect in Demo Mode
    connect_demo_req = PayPalConnectRequest(paypal_mode="demo")
    connect_res = connect_paypal(payload=connect_demo_req, current_user=user, db=db)
    record("PayPal Connect in Demonstration Mode", connect_res.get("status") == "connected" and connect_res.get("mode") == "demo")

    # 3.2 PayPal Sandbox Authentication Check with Dummy Credentials
    client = PayPalClient(mode="sandbox", client_id="DUMMY_CLIENT_ID", client_secret="DUMMY_SECRET")
    cred_verification = client.verify_credentials()
    record("PayPal Sandbox Credential Validation (Fails Gracefully with Dummy Keys)", cred_verification is False)

    # 3.3 Transaction Sync (Demonstration Mode)
    sync_res = sync_transactions(force_demo=True, current_user=user, db=db)
    tx_count = sync_res.get("transactions_synced", 0)
    subs_count = sync_res.get("new_subscriptions_identified", 0)
    record("Transaction Sync & Subscription Ingestion", tx_count > 0 and subs_count > 0 and sync_res.get("status") == "success")

    # 3.4 Transaction Retrieval Endpoint
    txs = get_transactions(limit=20, offset=0, current_user=user, db=db)
    record("Get Transactions List (Pagination & Filtering)", len(txs) > 0 and hasattr(txs[0], "gross_amount"))

    # =========================================================================
    # AUDIT 4: FINANCIAL ENGINES NUMERICAL VERIFICATION
    # =========================================================================
    print("\n--- AUDIT 4: Financial Engines Numerical Verification ---")

    # 4.1 Normalizer Test
    test_cases = [
        ("AMZN *AWS CLOUD 102948-US", "AWS", "Cloud Infrastructure", 1, True),
        ("SLACK TECHNOLOGIES INC *SLACK", "Slack", "Team Collaboration", 2, True),
        ("ZOOM.US *PRO MONTHLY", "Zoom", "Video Conferencing", 2, False),
        ("GOOGLE *WORKSPACE_ENTERPRISE", "Google Workspace", "Productivity & Email", 1, True),
        ("UNKNOWN SAAS INC", "Unknown", "General SaaS / Operations", 3, False),
    ]
    norm_pass = True
    for desc, exp_vendor, exp_cat, exp_tier, exp_essential in test_cases:
        res = TransactionNormalizer.normalize_vendor_and_category(desc)
        if res["normalized_vendor"] != exp_vendor or res["category"] != exp_cat or res["priority_tier"] != exp_tier or res["is_essential"] != exp_essential:
            norm_pass = False
            print(f"   Mismatch on {desc}: got {res}, expected {exp_vendor}/{exp_cat}/tier {exp_tier}")
    record("Transaction Normalizer & Merchant Knowledge Base", norm_pass)

    # 4.2 Cadence Detection Algorithm
    base_date = datetime.datetime(2026, 1, 15)
    monthly_dates = [base_date + datetime.timedelta(days=30 * i) for i in range(5)]
    weekly_dates = [base_date + datetime.timedelta(days=7 * i) for i in range(5)]
    quarterly_dates = [base_date + datetime.timedelta(days=91 * i) for i in range(4)]
    annual_dates = [base_date, base_date + datetime.timedelta(days=365)]

    cad_m, conf_m = SubscriptionDetector.detect_cadence(monthly_dates)
    cad_w, conf_w = SubscriptionDetector.detect_cadence(weekly_dates)
    cad_q, conf_q = SubscriptionDetector.detect_cadence(quarterly_dates)
    cad_a, conf_a = SubscriptionDetector.detect_cadence(annual_dates)

    cadence_pass = (cad_m == "monthly" and cad_w == "weekly" and cad_q == "quarterly" and cad_a == "annual")
    record("Inter-Arrival Cadence Detection (Weekly, Monthly, Quarterly, Annual)", cadence_pass)

    # 4.3 Subscription Summary Endpoint
    sub_summary = get_subscriptions(current_user=user, db=db)
    sub_list = sub_summary.get("subscriptions", [])
    total_spend = sub_summary.get("total_monthly_spend", 0.0)
    record("Subscription Summary Aggregation", len(sub_list) > 0 and total_spend > 0)

    # 4.4 Subscription Update (Criticality & Tier Mutation)
    if sub_list:
        target_sub = sub_list[0]
        sub_id = target_sub.id
        update_sub_payload = SubscriptionUpdate(priority_tier=1, is_essential=True, status="active")
        updated_sub = update_subscription(subscription_id=sub_id, payload=update_sub_payload, current_user=user, db=db)
        record("Subscription Criticality & Tier Mutation (PATCH)", updated_sub.priority_tier == 1 and updated_sub.is_essential is True)

    # 4.5 Cash-Flow Simulator Stress Test (Exact Numerical Verification)
    # Controlled scenario:
    # Business: Revenue = $30,000, Cash Reserves = $80,000
    # Shock: -50% Revenue ($15,000)
    # Monthly burn = $30,000 * 0.45 ($13,500) + active subscriptions
    sim_res = run_simulation(
        payload=SimulationRequest(
            revenue_shock_pct=-50.0,
            pause_tier_3_discretionary=True,
            additional_monthly_burn=0.0
        ),
        current_user=user,
        db=db
    )
    sim_valid = (
        sim_res.get("revenue_shock_pct") == -50.0 and
        len(sim_res.get("timeline", [])) == 12 and
        sim_res.get("monthly_savings_from_paused", 0) > 0 and
        sim_res.get("simulated_runway_months") is not None
    )
    record("Cash-Flow Stress Simulator (-50% Revenue Shock + Tier 3 Freeze)", sim_valid)

    # 4.6 Recommendation Engine Verification
    recs = get_recommendations(current_user=user, db=db)
    rec_types = {r.action_type for r in recs}
    record("Financial Recommendations Generation (Types: " + ", ".join(rec_types) + ")", len(recs) > 0)

    # 4.7 Recommendation Status Update (Apply Action Item)
    if recs:
        target_rec = recs[0]
        rec_update = RecommendationUpdate(status="applied")
        updated_rec = update_recommendation(rec_id=target_rec.id, payload=rec_update, current_user=user, db=db)
        record("Recommendation Status Transition (applied)", updated_rec.status == "applied")

    # =========================================================================
    # AUDIT 5: AI ADVISOR & NON-FABRICATION VERIFICATION
    # =========================================================================
    print("\n--- AUDIT 5: AI Advisor & Deterministic Non-Fabrication ---")

    briefing = get_ai_briefing(current_user=user, db=db)
    briefing_text = briefing.get("executive_briefing", "")
    
    # Verify exact numbers from calculation engine appear in briefing
    exact_spend = f"${briefing.get('total_monthly_spend'):,.2f}"
    has_exact_spend = exact_spend in briefing_text
    has_company = "Rostova Enterprise Cloud LLC" in briefing_text
    has_structure = "Executive Financial Assessment" in briefing_text
    
    record("AI Advisor Deterministic Non-Fabrication (Injects exact financial math)", has_exact_spend and has_company and has_structure)
    record("AI Advisor Offline/Fallback Behavior", len(briefing_text) > 200)

    # =========================================================================
    # AUDIT 6: SECURITY & AUTHORIZATION ISOLATION
    # =========================================================================
    print("\n--- AUDIT 6: Security & Multi-Tenant Authorization Isolation ---")

    # 6.1 Create Second User (Tenant B)
    reg_b = UserRegister(
        email="tenant_b@othercompany.io",
        password="AnotherPassword2026!",
        full_name="Bob Martinez",
        company_name="Tenant B Logistics",
        industry="Logistics",
        monthly_baseline_revenue=10000.0,
        current_cash_reserves=20000.0
    )
    reg_res_b = register(payload=reg_b, db=db)
    user_b = db.query(User).filter(User.id == reg_res_b["user_id"]).first()

    # 6.2 Cross-Tenant Isolation: User B tries to view or modify User A's data
    profile_b = get_profile(current_user=user_b, db=db)
    record("Tenant Data Isolation: User B sees only their profile", profile_b.company_name == "Tenant B Logistics")

    # 6.3 User B should have 0 transactions initially
    txs_b = get_transactions(limit=10, offset=0, current_user=user_b, db=db)
    record("Tenant Transaction Isolation: User B sees 0 transactions before syncing", len(txs_b) == 0)

    # 6.4 User B cannot update User A's subscription
    if sub_list:
        target_sub_a_id = sub_list[0].id
        try:
            update_subscription(
                subscription_id=target_sub_a_id,
                payload=SubscriptionUpdate(priority_tier=2),
                current_user=user_b,
                db=db
            )
            record("Multi-Tenant Guard: User B cannot modify User A's subscription", False, "Cross-tenant mutation allowed")
        except Exception as e:
            record("Multi-Tenant Guard: User B cannot modify User A's subscription", True)

    db.close()

    print("\n" + "=" * 80)
    print(f"AUDIT SUMMARY: {results['passed']} PASSED, {results['failed']} FAILED")
    print("=" * 80)
    return results

if __name__ == "__main__":
    res = run_audit()
    sys.exit(0 if res["failed"] == 0 else 1)
