import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.schemas.auth import UserRegister
from app.api.auth import register
from app.api.business import get_profile

test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

def test_individual_account_registration(db):
    """Test individual account creation with automatic name resolution and account_type persistence."""
    email = "individual_user@subwise.io"
    reg_data = UserRegister(
        email=email,
        password="IndividualPassword2026!",
        full_name="Sarah Miller",
        company_name="Sarah Miller's Finances",
        account_type="individual",
        industry="Personal: Unused Subscriptions",
        monthly_baseline_revenue=4500.0,
        current_cash_reserves=12000.0
    )
    result = register(payload=reg_data, db=db)
    assert result["account_type"] == "individual"
    assert result["company_name"] == "Sarah Miller's Finances"
    assert result["user_id"] is not None

    user = db.query(User).filter(User.id == result["user_id"]).first()
    assert user is not None
    profile = db.query(BusinessProfile).filter(BusinessProfile.id == result["business_id"]).first()
    assert profile.account_type == "individual"
    assert profile.monthly_baseline_revenue == 4500.0

def test_household_account_registration(db):
    """Test household account creation with shared name and household account_type."""
    email = "household_user@subwise.io"
    reg_data = UserRegister(
        email=email,
        password="HouseholdPassword2026!",
        full_name="Mark & Elena Vance",
        company_name="The Vance Household",
        account_type="household",
        industry="Household: Supermarket Price Creep (4 members)",
        monthly_baseline_revenue=3800.0,
        current_cash_reserves=5000.0
    )
    result = register(payload=reg_data, db=db)
    assert result["account_type"] == "household"
    assert result["company_name"] == "The Vance Household"

    profile = db.query(BusinessProfile).filter(BusinessProfile.id == result["business_id"]).first()
    assert profile.account_type == "household"
    assert "Household:" in profile.industry

def test_business_account_default_backward_compatibility(db):
    """Test that omitting account_type defaults strictly to 'business' for zero regression."""
    email = "legacy_business@subwise.io"
    reg_data = UserRegister(
        email=email,
        password="BusinessPassword2026!",
        full_name="Legacy Founder",
        company_name="Legacy Corp Inc",
        # account_type omitted, should default to 'business'
        industry="SaaS / Technology",
        monthly_baseline_revenue=15000.0,
        current_cash_reserves=40000.0
    )
    result = register(payload=reg_data, db=db)
    assert result["account_type"] == "business"
    assert result["company_name"] == "Legacy Corp Inc"

    profile = db.query(BusinessProfile).filter(BusinessProfile.id == result["business_id"]).first()
    assert profile.account_type == "business"
