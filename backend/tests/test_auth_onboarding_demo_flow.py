"""
Tests for Authentication, Account-Specific Onboarding & Idempotent Demo Mode Preparation
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
from app.models.expense import Expense
from app.models.household_member import HouseholdMember
from app.models.recommendation import Recommendation
from app.services.demo_data_generator import DemoDataGenerator
from app.services.business_service import get_active_business, switch_active_business

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


def test_account_type_preservation_in_demo_creation(db):
    """Verify that creating demo mode preserves the user's registered account type."""
    # 1. Individual User
    ind_user = User(email="individual@subwise.io", hashed_password="pw", full_name="Alex Personal")
    db.add(ind_user)
    db.flush()
    ind_biz = BusinessProfile(user_id=ind_user.id, company_name="Alex Personal", account_type="individual", is_demo=False)
    db.add(ind_biz)
    db.commit()

    demo_ind = DemoDataGenerator.ensure_demo_business(user_id=ind_user.id, db=db)
    assert demo_ind.is_demo is True
    assert demo_ind.account_type == "individual"
    assert "Personal" in demo_ind.company_name

    # 2. Household User
    hh_user = User(email="household@subwise.io", hashed_password="pw", full_name="Miller Family")
    db.add(hh_user)
    db.flush()
    hh_biz = BusinessProfile(user_id=hh_user.id, company_name="Miller Family", account_type="household", is_demo=False)
    db.add(hh_biz)
    db.commit()

    demo_hh = DemoDataGenerator.ensure_demo_business(user_id=hh_user.id, db=db)
    assert demo_hh.is_demo is True
    assert demo_hh.account_type == "household"
    assert "Family" in demo_hh.company_name


def test_demo_initialization_idempotency(db):
    """Verify that repeated generate_demo_dataset calls reuse valid existing datasets without duplicating rows."""
    user = User(email="business@subwise.io", hashed_password="pw", full_name="SaaS Founder")
    db.add(user)
    db.flush()
    biz = BusinessProfile(user_id=user.id, company_name="Cloud Corp", account_type="business", is_demo=False)
    db.add(biz)
    db.commit()

    # First call: creates initial demo records
    res1 = DemoDataGenerator.generate_demo_dataset(user_id=user.id, db=db)
    assert res1["reused"] is False
    tx_count_1 = db.query(Transaction).filter(Transaction.business_id == res1["business_id"]).count()
    sub_count_1 = db.query(Subscription).filter(Subscription.business_id == res1["business_id"]).count()
    assert tx_count_1 > 0
    assert sub_count_1 > 0

    # Second call (idempotent): reuses existing records immediately without re-insertion
    res2 = DemoDataGenerator.generate_demo_dataset(user_id=user.id, db=db, force_reset=False)
    assert res2["reused"] is True
    tx_count_2 = db.query(Transaction).filter(Transaction.business_id == res1["business_id"]).count()
    sub_count_2 = db.query(Subscription).filter(Subscription.business_id == res1["business_id"]).count()
    assert tx_count_2 == tx_count_1
    assert sub_count_2 == sub_count_1


def test_individual_demo_dataset_composition(db):
    """Verify individual demo dataset generates salary income, personal subscriptions and expenses."""
    user = User(email="personal_demo@subwise.io", hashed_password="pw", full_name="Jordan Lee")
    db.add(user)
    db.flush()
    biz = BusinessProfile(user_id=user.id, company_name="Jordan Lee", account_type="individual", is_demo=False)
    db.add(biz)
    db.commit()

    res = DemoDataGenerator.generate_demo_dataset(user_id=user.id, db=db)
    assert res["account_type"] == "individual"

    # Check that subscriptions include consumer services (Netflix, Spotify, etc.)
    subs = db.query(Subscription).filter(Subscription.business_id == res["business_id"]).all()
    sub_vendors = {s.vendor_name for s in subs}
    assert "Netflix" in sub_vendors
    assert "Spotify" in sub_vendors
    assert "Apple iCloud" in sub_vendors

    # Check personal expenses table
    expenses = db.query(Expense).filter(Expense.business_id == res["business_id"]).all()
    assert len(expenses) > 0
    incomes = [e for e in expenses if e.expense_type == "income"]
    outflows = [e for e in expenses if e.expense_type == "expense"]
    assert len(incomes) > 0
    assert len(outflows) > 0


def test_household_demo_dataset_composition(db):
    """Verify household demo dataset generates members, shared income, family subscriptions and shared expenses."""
    user = User(email="household_demo@subwise.io", hashed_password="pw", full_name="The Taylors")
    db.add(user)
    db.flush()
    biz = BusinessProfile(user_id=user.id, company_name="The Taylors", account_type="household", is_demo=False)
    db.add(biz)
    db.commit()

    res = DemoDataGenerator.generate_demo_dataset(user_id=user.id, db=db)
    assert res["account_type"] == "household"

    # Verify household members
    members = db.query(HouseholdMember).filter(HouseholdMember.business_id == res["business_id"]).all()
    assert len(members) == 3
    roles = {m.role for m in members}
    assert "Primary" in roles
    assert "Partner" in roles

    # Verify family subscriptions
    subs = db.query(Subscription).filter(Subscription.business_id == res["business_id"]).all()
    sub_vendors = {s.vendor_name for s in subs}
    assert "Disney+" in sub_vendors
    assert "Verizon Fios" in sub_vendors
    assert "Costco" in sub_vendors


def test_forced_reset_regenerates_cleanly(db):
    """Verify force_reset=True regenerates without duplicates or leftover records."""
    user = User(email="reset_test@subwise.io", hashed_password="pw", full_name="Reset User")
    db.add(user)
    db.flush()
    biz = BusinessProfile(user_id=user.id, company_name="Reset Biz", account_type="business", is_demo=False)
    db.add(biz)
    db.commit()

    res1 = DemoDataGenerator.generate_demo_dataset(user_id=user.id, db=db)
    count1 = db.query(Transaction).filter(Transaction.business_id == res1["business_id"]).count()

    res2 = DemoDataGenerator.generate_demo_dataset(user_id=user.id, db=db, force_reset=True)
    count2 = db.query(Transaction).filter(Transaction.business_id == res2["business_id"]).count()

    assert count1 == count2
    assert res2["reused"] is False
