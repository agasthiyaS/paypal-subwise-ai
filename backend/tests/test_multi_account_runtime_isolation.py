"""
Stage 4 Multi-Account Runtime Verification (Individual, Household, Business)
"""
import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.expense import Expense
from app.models.household_member import HouseholdMember
from app.models.transaction import Transaction
from app.schemas.assistant import AssistantQueryRequest
from app.services.financial_assistant_engine import FinancialAssistantEngine


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_individual_runtime_isolation(db_session):
    # 1. Create Individual User
    u_ind = User(id=101, email="ind@subwise.io", hashed_password="pw", is_active=True)
    b_ind = BusinessProfile(id=201, user_id=101, company_name="Individual Budget", account_type="individual", currency="USD")
    db_session.add_all([u_ind, b_ind])
    db_session.flush()

    # Individual expenses
    now = datetime.datetime.utcnow()
    e1 = Expense(business_id=b_ind.id, user_id=u_ind.id, amount=85.50, expense_type="expense", category="Food & Groceries", description="Supermarket", expense_date=now)
    e2 = Expense(business_id=b_ind.id, user_id=u_ind.id, amount=45.00, expense_type="expense", category="Transportation", description="Metro & Rides", expense_date=now)
    db_session.add_all([e1, e2])
    db_session.commit()

    req = AssistantQueryRequest(message="Where did my money go this month?")
    res = FinancialAssistantEngine.process_query(business=b_ind, subscriptions=[], transactions=[], request=req, db=db_session)
    assert res.intent == "SPENDING_BREAKDOWN"
    assert "Food & Groceries" in res.response_text
    assert "$85.50" in res.response_text
    assert "Transportation" in res.response_text
    assert "$130.50" in res.response_text


def test_household_runtime_isolation(db_session):
    # 2. Create Household User
    u_hh = User(id=102, email="household@subwise.io", hashed_password="pw", is_active=True)
    b_hh = BusinessProfile(id=202, user_id=102, company_name="Greenwood Household", account_type="household", currency="USD")
    db_session.add_all([u_hh, b_hh])
    db_session.flush()

    # Members
    m1 = HouseholdMember(business_id=b_hh.id, name="Jordan", role="Primary", is_active=True)
    m2 = HouseholdMember(business_id=b_hh.id, name="Sam", role="Partner", is_active=True)
    db_session.add_all([m1, m2])
    db_session.flush()

    # Expenses
    now = datetime.datetime.utcnow()
    e1 = Expense(business_id=b_hh.id, user_id=u_hh.id, household_member_id=m1.id, amount=400.0, expense_type="expense", category="Utilities", description="Electricity & Heat", expense_date=now)
    e2 = Expense(business_id=b_hh.id, user_id=u_hh.id, household_member_id=m2.id, amount=220.0, expense_type="expense", category="Groceries", description="Costco Run", expense_date=now)
    db_session.add_all([e1, e2])
    db_session.commit()

    req = AssistantQueryRequest(message="How much did each household member spend?")
    res = FinancialAssistantEngine.process_query(business=b_hh, subscriptions=[], transactions=[], request=req, db=db_session)
    assert res.intent == "HOUSEHOLD_SPENDING"
    assert "Jordan" in res.response_text
    assert "Sam" in res.response_text
    assert "$400.00" in res.response_text
    assert "$220.00" in res.response_text
    assert "$620.00" in res.response_text


def test_business_runtime_isolation(db_session):
    # 3. Create Business User
    u_biz = User(id=103, email="cfo@apex.com", hashed_password="pw", is_active=True)
    b_biz = BusinessProfile(id=203, user_id=103, company_name="Apex Global Technologies", account_type="business", current_cash_reserves=75000.0, currency="USD")
    db_session.add_all([u_biz, b_biz])
    db_session.flush()

    # Operating Sales transactions
    now = datetime.datetime.utcnow()
    t1 = Transaction(business_id=b_biz.id, gross_amount=5000.0, net_amount=4850.0, transaction_date=now, status="COMPLETED", raw_description="Customer Subscription Payment", normalized_vendor="Customer Direct", category="Sales Revenue")
    db_session.add(t1)
    db_session.commit()

    req = AssistantQueryRequest(message="What is our operating revenue?")
    res = FinancialAssistantEngine.process_query(business=b_biz, subscriptions=[], transactions=[t1], request=req, db=db_session)
    assert res.intent == "REVENUE_INQUIRY"
    assert "$5,000.00" in res.response_text
    assert "Apex Global Technologies" in res.response_text
