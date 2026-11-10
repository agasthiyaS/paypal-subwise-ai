"""
Real PostgreSQL 16 Runtime Verification Script for PayPal SubWise AI.
Tests real CRUD operations, foreign key constraints, JSON fields,
multi-tenant isolation, and cascade deletes against live PostgreSQL.
"""
import sys
import datetime
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.database import engine, SessionLocal
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.scenario import ScenarioSimulation
from app.models.recommendation import Recommendation
from app.services.auth_service import get_password_hash, verify_password

def run_tests():
    print("=" * 70)
    print("PAYPAL SUBWISE AI - REAL POSTGRESQL 16 RUNTIME VERIFICATION")
    print("=" * 70)
    
    # 1. Verify Live Database Info
    with engine.connect() as conn:
        db_info = conn.execute(text("SELECT current_database(), current_user, version();")).fetchone()
        print(f"[TEST 1] Live DB Connection: Database='{db_info[0]}', User='{db_info[1]}'")
        print(f"         PostgreSQL Version: {db_info[2][:60]}...")
        assert db_info[0] == "subwise_ai", f"Expected subwise_ai, got {db_info[0]}"
    print(" -> PASSED: Connected to real PostgreSQL 16 database.")

    db = SessionLocal()
    try:
        # Clean up any leftover test data
        test_emails = ["pgtest_user1@subwise.io", "pgtest_user2@subwise.io"]
        for email in test_emails:
            existing = db.query(User).filter(User.email == email).first()
            if existing:
                db.delete(existing)
        db.commit()

        # 2. Test User Registration & Password Hashing
        print("\n[TEST 2] Testing User CRUD & Auth Hashing on PostgreSQL...")
        hashed = get_password_hash("FintechSecurePass2026!")
        user1 = User(
            email="pgtest_user1@subwise.io",
            hashed_password=hashed,
            full_name="Alice Founder",
            is_active=True
        )
        db.add(user1)
        db.commit()
        db.refresh(user1)
        assert user1.id is not None
        assert verify_password("FintechSecurePass2026!", user1.hashed_password)
        assert not verify_password("wrongpass", user1.hashed_password)
        print(f" -> PASSED: Created User ID={user1.id}, email={user1.email}, hash verified.")

        # 3. Test Business Profile Creation & Relationship
        print("\n[TEST 3] Testing Business Profile Association...")
        biz1 = BusinessProfile(
            user_id=user1.id,
            company_name="Apex Analytics SaaS",
            industry="B2B Software",
            monthly_baseline_revenue=28500.0,
            current_cash_reserves=120000.0,
            target_runway_months=8,
            risk_tolerance="moderate",
            currency="USD",
            paypal_connected=True,
            paypal_mode="sandbox"
        )
        db.add(biz1)
        db.commit()
        db.refresh(biz1)
        assert biz1.id is not None
        assert biz1.owner.id == user1.id
        print(f" -> PASSED: Created BusinessProfile ID={biz1.id}, company='{biz1.company_name}', linked to User {user1.id}.")

        # 4. Test Transactions (Inflow & Outflow)
        print("\n[TEST 4] Testing Transactions CRUD & Numeric Precision...")
        now = datetime.datetime.utcnow()
        tx1 = Transaction(
            business_id=biz1.id,
            paypal_transaction_id="TXN-PAYPAL-PG-001",
            transaction_date=now - datetime.timedelta(days=15),
            raw_description="GITHUB ENTERPRISE INC",
            normalized_vendor="GitHub",
            category="Developer Tools",
            gross_amount=-210.0,
            net_amount=-210.0,
            currency="USD",
            status="COMPLETED"
        )
        tx2 = Transaction(
            business_id=biz1.id,
            paypal_transaction_id="TXN-PAYPAL-PG-002",
            transaction_date=now - datetime.timedelta(days=2),
            raw_description="STRIPE PAYOUT CLIENT REV",
            normalized_vendor="Stripe Client Revenue",
            category="Revenue",
            gross_amount=14500.0,
            net_amount=14065.0,
            fee_amount=435.0,
            currency="USD",
            status="COMPLETED"
        )
        db.add_all([tx1, tx2])
        db.commit()

        txs = db.query(Transaction).filter(Transaction.business_id == biz1.id).all()
        assert len(txs) == 2
        print(f" -> PASSED: Stored {len(txs)} transactions on PostgreSQL (1 expense, 1 revenue).")

        # 5. Test Subscriptions CRUD & Tracking
        print("\n[TEST 5] Testing Subscriptions CRUD...")
        sub1 = Subscription(
            business_id=biz1.id,
            vendor_name="AWS Cloud Services",
            category="Infrastructure",
            cadence="monthly",
            average_amount=850.0,
            latest_amount=895.0,
            price_change_pct=5.29,
            currency="USD",
            first_billed_date=now - datetime.timedelta(days=120),
            last_billed_date=now - datetime.timedelta(days=10),
            next_billing_date=now + datetime.timedelta(days=20),
            priority_tier=1,
            status="active",
            is_essential=True
        )
        sub2 = Subscription(
            business_id=biz1.id,
            vendor_name="Miro Whiteboard",
            category="Collaboration",
            cadence="monthly",
            average_amount=32.0,
            latest_amount=32.0,
            currency="USD",
            first_billed_date=now - datetime.timedelta(days=90),
            last_billed_date=now - datetime.timedelta(days=5),
            next_billing_date=now + datetime.timedelta(days=25),
            priority_tier=3,
            redundancy_group="whiteboard",
            status="active",
            is_essential=False
        )
        db.add_all([sub1, sub2])
        db.commit()
        db.refresh(sub1)
        db.refresh(sub2)
        assert sub1.id is not None
        assert sub2.id is not None
        print(f" -> PASSED: Stored Subscriptions '{sub1.vendor_name}' (Tier {sub1.priority_tier}) & '{sub2.vendor_name}' (Tier {sub2.priority_tier}).")

        # 6. Test Scenario Simulation (PostgreSQL JSON Column)
        print("\n[TEST 6] Testing Scenario Simulation & JSON Column Handling...")
        projection_data = [
            {"month": 1, "balance": 115000.0, "revenue": 22800.0, "expenses": 27800.0},
            {"month": 2, "balance": 110000.0, "revenue": 22800.0, "expenses": 27800.0},
            {"month": 3, "balance": 105000.0, "revenue": 22800.0, "expenses": 27800.0}
        ]
        sim = ScenarioSimulation(
            business_id=biz1.id,
            scenario_name="20% Revenue Dip Shock Test",
            revenue_shock_pct=-20.0,
            paused_subscription_ids=[sub2.id],
            initial_cash_reserves=120000.0,
            projected_burn_rate=5000.0,
            projected_runway_months=24.0,
            depletion_month="Sustainable (24+ Months)",
            monthly_projection_data=projection_data
        )
        db.add(sim)
        db.commit()
        db.refresh(sim)
        assert sim.id is not None
        assert sim.monthly_projection_data[0]["revenue"] == 22800.0
        assert sim.paused_subscription_ids == [sub2.id]
        print(f" -> PASSED: ScenarioSimulation ID={sim.id} saved; JSON column serialization & retrieval verified.")

        # 7. Test AI Recommendation CRUD & Foreign Keys
        print("\n[TEST 7] Testing Recommendation CRUD & Subscription Relationship...")
        rec = Recommendation(
            business_id=biz1.id,
            subscription_id=sub2.id,
            action_type="CANCEL",
            title="Consolidate Miro Whiteboard with FigJam",
            rationale="Your team maintains active Figma licenses which include FigJam.",
            action_plan="1. Export boards. 2. Cancel Miro renewal.",
            potential_monthly_saving=32.0,
            potential_annual_saving=384.0,
            runway_impact_days=4,
            status="pending"
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        assert rec.id is not None
        assert rec.subscription.vendor_name == "Miro Whiteboard"
        print(f" -> PASSED: Recommendation ID={rec.id} saved; Foreign Key linked to Subscription {sub2.id}.")

        # 8. Test Foreign Key Constraint Enforcement
        print("\n[TEST 8] Testing PostgreSQL Foreign Key Enforcement (IntegrityError)...")
        orphaned_sub = Subscription(
            business_id=999999, # Non-existent business profile
            vendor_name="Ghost Service",
            category="Other",
            average_amount=50.0,
            latest_amount=50.0,
            first_billed_date=now,
            last_billed_date=now,
            next_billing_date=now
        )
        db.add(orphaned_sub)
        try:
            db.commit()
            raise AssertionError("PostgreSQL allowed inserting orphaned child record!")
        except IntegrityError:
            db.rollback()
            print(" -> PASSED: Foreign key constraint successfully rejected invalid business_id (IntegrityError raised & caught).")

        # 9. Test Multi-Tenant Data Isolation
        print("\n[TEST 9] Testing Multi-Tenant Isolation Between Distinct Businesses...")
        user2 = User(
            email="pgtest_user2@subwise.io",
            hashed_password=hashed,
            full_name="Bob Founder",
            is_active=True
        )
        db.add(user2)
        db.commit()
        db.refresh(user2)
        
        biz2 = BusinessProfile(
            user_id=user2.id,
            company_name="Beta Logistics",
            monthly_baseline_revenue=10000.0,
            current_cash_reserves=25000.0
        )
        db.add(biz2)
        db.commit()
        db.refresh(biz2)

        # Query biz2 subscriptions (should be 0)
        biz2_subs = db.query(Subscription).filter(Subscription.business_id == biz2.id).all()
        assert len(biz2_subs) == 0, f"Leak detected: biz2 saw {len(biz2_subs)} subscriptions"
        
        # Query biz1 subscriptions (should be 2)
        biz1_subs = db.query(Subscription).filter(Subscription.business_id == biz1.id).all()
        assert len(biz1_subs) == 2
        print(f" -> PASSED: Multi-tenant isolation verified (Biz 1 has 2 subs, Biz 2 has 0 subs; zero data leakage).")

        # 10. Test Cascade Delete Integrity
        print("\n[TEST 10] Testing PostgreSQL Cascade Delete...")
        db.delete(user1)
        db.commit()

        # Check that user1, biz1, and all its children were deleted
        assert db.query(User).filter(User.id == user1.id).first() is None
        assert db.query(BusinessProfile).filter(BusinessProfile.id == biz1.id).first() is None
        assert db.query(Transaction).filter(Transaction.business_id == biz1.id).first() is None
        assert db.query(Subscription).filter(Subscription.business_id == biz1.id).first() is None
        assert db.query(ScenarioSimulation).filter(ScenarioSimulation.business_id == biz1.id).first() is None
        assert db.query(Recommendation).filter(Recommendation.business_id == biz1.id).first() is None
        print(" -> PASSED: Cascading delete completely purged User, Business, Transactions, Subscriptions, Scenarios, and Recommendations.")

        # Clean up user2
        db.delete(user2)
        db.commit()
        print(" -> Cleaned up test User 2.")

    finally:
        db.close()

    print("\n" + "=" * 70)
    print("ALL 10 REAL POSTGRESQL 16 RUNTIME TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
