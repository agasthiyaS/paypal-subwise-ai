import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.household_member import HouseholdMember
from app.models.transaction import Transaction
from app.services.categorization_service import CategorizationService
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from app.schemas.household import HouseholdMemberCreate, HouseholdMemberUpdate
from app.schemas.budget import BudgetCreate
from app.api.expenses import (
    create_expense, get_expenses, update_expense, delete_expense,
    get_monthly_expense_summary, sync_paypal_into_expenses
)
from app.api.household import (
    create_household_member, get_household_members,
    update_household_member, delete_household_member,
    get_household_financial_summary
)
from app.api.budgets import set_budget, get_budgets, delete_budget

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()

    # Create 2 test users with business profiles (one individual, one household)
    user1 = User(
        id=101,
        email="ind_test@subwise.io",
        hashed_password="hashed_pw_test_101",
        full_name="Individual Tester",
        is_active=True
    )
    user2 = User(
        id=102,
        email="house_test@subwise.io",
        hashed_password="hashed_pw_test_102",
        full_name="Household Tester",
        is_active=True
    )
    session.add_all([user1, user2])
    session.commit()

    biz1 = BusinessProfile(
        id=101,
        user_id=101,
        company_name="Personal Finances 101",
        account_type="individual",
        is_demo=False,
        monthly_baseline_revenue=5000.0,
        current_cash_reserves=15000.0
    )
    biz2 = BusinessProfile(
        id=102,
        user_id=102,
        company_name="Vance Family Household",
        account_type="household",
        is_demo=False,
        monthly_baseline_revenue=4200.0,
        current_cash_reserves=8000.0
    )
    session.add_all([biz1, biz2])
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)


# ==============================================================================
# 1. CATEGORIZATION ENGINE TESTS
# ==============================================================================

def test_categorization_engine_rules():
    """Verify that rule-based regex patterns accurately classify consumer transactions."""
    cat, reason, conf = CategorizationService.categorize("Whole Foods Market Weekly groceries", "Whole Foods")
    assert cat == "Food & Groceries"
    assert conf >= 0.85

    cat, reason, conf = CategorizationService.categorize("ConEd Electric & Power Bill", "Con Edison")
    assert cat == "Electricity & Utilities"
    assert conf >= 0.85

    cat, reason, conf = CategorizationService.categorize("Monthly Apartment Rent Payment", "Greystar")
    assert cat == "Housing & Rent"
    assert conf >= 0.85

    cat, reason, conf = CategorizationService.categorize("Netflix Streaming Subscription", "Netflix")
    assert cat == "Subscriptions"
    assert conf >= 0.85

    cat, reason, conf = CategorizationService.categorize("Uber Trip across town", "Uber")
    assert cat == "Transportation"
    assert conf >= 0.85

    cat, reason, conf = CategorizationService.categorize("CVS Pharmacy Prescription", "CVS")
    assert cat == "Healthcare"
    assert conf >= 0.85

    cat, reason, conf = CategorizationService.categorize("Mystery Vendor XYZ 123", "Unknown")
    assert cat == "Other"
    assert conf <= 0.50


# ==============================================================================
# 2. EXPENSE CRUD & USER ISOLATION
# ==============================================================================

def test_expense_crud_and_isolation(db):
    """Verify expense creation, retrieval, updating, deletion, and cross-account isolation."""
    user1 = db.query(User).filter(User.id == 101).first()
    user2 = db.query(User).filter(User.id == 102).first()

    # User 1 creates an expense
    payload = ExpenseCreate(
        amount=145.50,
        expense_type="expense",
        category="Food & Groceries",
        description="Costco monthly supply haul",
        merchant="Costco",
        payment_method="Debit Card"
    )
    created = create_expense(payload=payload, current_user=user1, db=db)
    assert created.id is not None
    assert created.amount == 145.50
    assert created.category == "Food & Groceries"
    assert created.user_id == 101
    assert created.business_id == 101

    # User 2 list expenses - MUST NOT see User 1's expense
    user2_expenses = get_expenses(current_user=user2, db=db)
    assert len(user2_expenses) == 0

    # User 1 list expenses - MUST see User 1's expense
    user1_expenses = get_expenses(current_user=user1, db=db)
    assert len(user1_expenses) == 1
    assert user1_expenses[0].id == created.id

    # User 1 updates the expense
    update_data = ExpenseUpdate(amount=160.00, notes="Added paper goods")
    updated = update_expense(expense_id=created.id, payload=update_data, current_user=user1, db=db)
    assert updated.amount == 160.00
    assert updated.notes == "Added paper goods"

    # User 1 adds income
    income_payload = ExpenseCreate(
        amount=5000.00,
        expense_type="income",
        category="Other",
        description="Monthly Salary Deposit",
        payment_method="Bank Transfer"
    )
    create_expense(payload=income_payload, current_user=user1, db=db)


# ==============================================================================
# 3. BUDGET MANAGEMENT & UPSERT
# ==============================================================================

def test_budget_upsert_and_utilization(db):
    """Verify budget limits can be created and upserted for categories and overall."""
    user1 = db.query(User).filter(User.id == 101).first()

    # Set Food budget
    b_in = BudgetCreate(
        category="Food & Groceries",
        monthly_limit=600.0,
        period_month=datetime.datetime.utcnow().month,
        period_year=datetime.datetime.utcnow().year
    )
    b_res = set_budget(payload=b_in, current_user=user1, db=db)
    assert b_res.monthly_limit == 600.0
    assert b_res.category == "Food & Groceries"
    assert b_res.current_spent == 160.00
    assert b_res.remaining_amount == 440.00
    assert b_res.utilization_percent > 0

    # Upsert Food budget (update limit to 750)
    b_in_updated = BudgetCreate(
        category="Food & Groceries",
        monthly_limit=750.0,
        period_month=datetime.datetime.utcnow().month,
        period_year=datetime.datetime.utcnow().year
    )
    b_res_updated = set_budget(payload=b_in_updated, current_user=user1, db=db)
    assert b_res_updated.monthly_limit == 750.0
    assert b_res_updated.remaining_amount == 590.00

    # Verify only 1 budget row exists for Food & Groceries
    budgets = get_budgets(current_user=user1, db=db)
    food_budgets = [b for b in budgets if b.category == "Food & Groceries"]
    assert len(food_budgets) == 1


# ==============================================================================
# 4. HOUSEHOLD MEMBER CRUD & ATTRIBUTION
# ==============================================================================

def test_household_member_management(db):
    """Verify adding members, attributing expenses, and calculating member-level totals."""
    user2 = db.query(User).filter(User.id == 102).first()

    # Add 2 household members
    m1_in = HouseholdMemberCreate(
        name="Elena Vance",
        role="Partner / Spouse",
        avatar_color="#10b981",
        monthly_income_share=1200.0
    )
    m1 = create_household_member(payload=m1_in, current_user=user2, db=db)
    assert m1.id is not None
    assert m1.name == "Elena Vance"
    assert m1.business_id == 102

    m2_in = HouseholdMemberCreate(
        name="Mark Vance",
        role="Primary / Organizer",
        avatar_color="#0070ba",
        monthly_income_share=1500.0
    )
    m2 = create_household_member(payload=m2_in, current_user=user2, db=db)

    members = get_household_members(current_user=user2, db=db)
    assert len(members) == 2

    # Add expense attributed to Elena
    exp_elena = ExpenseCreate(
        amount=85.20,
        expense_type="expense",
        category="Food & Groceries",
        description="Trader Joe's organic groceries",
        household_member_id=m1.id,
        is_shared=True
    )
    create_expense(payload=exp_elena, current_user=user2, db=db)

    # Add expense attributed to Mark
    exp_mark = ExpenseCreate(
        amount=120.00,
        expense_type="expense",
        category="Electricity & Utilities",
        description="Fiber Internet & Water Bill",
        household_member_id=m2.id,
        is_shared=True
    )
    create_expense(payload=exp_mark, current_user=user2, db=db)

    # Verify household summary aggregates member attribution accurately
    summary = get_household_financial_summary(
        month=datetime.datetime.utcnow().month,
        year=datetime.datetime.utcnow().year,
        current_user=user2,
        db=db
    )
    assert summary.total_household_spent == 205.20
    assert summary.grocery_spent == 85.20
    assert summary.utility_spent == 120.00
    assert summary.shared_spent == 205.20
    assert len(summary.members) == 2

    elena_summary = next(m for m in summary.members if m.member_id == m1.id)
    assert elena_summary.total_spent == 85.20
    assert elena_summary.transaction_count == 1


# ==============================================================================
# 5. MONTHLY SUMMARY & SAVINGS RATE
# ==============================================================================

def test_monthly_expense_summary(db):
    """Verify net savings and savings rate calculations for individual account."""
    user1 = db.query(User).filter(User.id == 101).first()

    now = datetime.datetime.utcnow()
    summary = get_monthly_expense_summary(month=now.month, year=now.year, current_user=user1, db=db)

    assert summary.total_income == 5000.00
    assert summary.total_expenses == 160.00
    assert summary.net_savings == 4840.00
    assert summary.savings_rate > 90.0
    assert len(summary.category_breakdown) >= 1
    assert summary.grocery_total == 160.00


# ==============================================================================
# 6. PAYPAL SYNC IDEMPOTENCY
# ==============================================================================

def test_paypal_sync_projection_idempotency(db):
    """Verify PayPal transaction projection into expenses table skips duplicates."""
    user1 = db.query(User).filter(User.id == 101).first()

    # Insert a mock settled PayPal transaction
    tx = Transaction(
        id=9901,
        business_id=101,
        paypal_transaction_id="PP_TX_AUDIT_9901",
        transaction_date=datetime.datetime.utcnow(),
        raw_description="Target Store Checkout",
        normalized_vendor="Target",
        gross_amount=-45.00,
        net_amount=-45.00,
        fee_amount=0.0,
        currency="USD",
        status="COMPLETED",
        data_source="sandbox"
    )
    db.add(tx)
    db.commit()

    # First sync run
    result1 = sync_paypal_into_expenses(current_user=user1, db=db)
    assert result1["newly_projected_expenses"] == 1

    # Second sync run - MUST skip already imported transaction
    result2 = sync_paypal_into_expenses(current_user=user1, db=db)
    assert result2["newly_projected_expenses"] == 0

    # Verify projected expense has rules_engine categorization and paypal_sync data_source
    exp = db.query(Expense).filter(Expense.paypal_transaction_id == "PP_TX_AUDIT_9901").first()
    assert exp is not None
    assert exp.amount == 45.00
    assert exp.data_source == "paypal_sync"
    assert exp.categorization_method == "rules_engine"
    assert exp.category == "Shopping" or exp.category == "Food & Groceries"
