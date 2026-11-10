import datetime
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.vendor import Vendor, VendorPlan
from app.services.auth_service import create_access_token, get_password_hash
from app.services.entitlement_service import EntitlementService, EntitlementTier
from app.services.report_engine import ReportEngine, sanitize_csv_cell

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def regular_user(db: Session):
    email = "phase6_reg_user@example.com"
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash("testpass123"),
            full_name="Regular Test User",
            is_admin=False,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.is_admin = False
        db.commit()
    return user


@pytest.fixture
def admin_user(db: Session):
    email = "phase6_admin_user@example.com"
    user = db.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash("adminpass123"),
            full_name="Platform Administrator",
            is_admin=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.is_admin = True
        db.commit()
    return user


def _auth_header(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. ADMIN RBAC & OPERATIONS TESTS
# ==============================================================================
def test_admin_stats_access_forbidden_for_regular_user(regular_user: User):
    resp = client.get("/api/v1/admin/stats", headers=_auth_header(regular_user))
    assert resp.status_code == 403
    assert "Admin privileges required" in resp.json()["detail"]


def test_admin_stats_access_allowed_for_admin_user(admin_user: User):
    resp = client.get("/api/v1/admin/stats", headers=_auth_header(admin_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "account_types" in data
    assert "connected_paypals" in data
    assert "total_transactions" in data
    assert "webhook_health" in data
    assert data["system_status"] == "HEALTHY"


def test_admin_user_directory_and_role_update(admin_user: User, regular_user: User):
    # 1. List users
    resp = client.get("/api/v1/admin/users", headers=_auth_header(admin_user))
    assert resp.status_code == 200
    users = resp.json()
    assert any(u["id"] == regular_user.id for u in users)

    # 2. Promote regular user to admin
    promote_resp = client.put(
        f"/api/v1/admin/users/{regular_user.id}/role?is_admin=true",
        headers=_auth_header(admin_user)
    )
    assert promote_resp.status_code == 200

    # 3. Demote back to regular user
    demote_resp = client.put(
        f"/api/v1/admin/users/{regular_user.id}/role?is_admin=false",
        headers=_auth_header(admin_user)
    )
    assert demote_resp.status_code == 200


# ==============================================================================
# 2. VENDOR MANAGEMENT SYSTEM TESTS
# ==============================================================================
def test_vendor_public_search(db: Session):
    resp = client.get("/api/v1/vendors")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

    cat_resp = client.get("/api/v1/vendors/categories")
    assert cat_resp.status_code == 200
    assert len(cat_resp.json()) >= 1


def test_vendor_create_forbidden_for_regular_user(regular_user: User):
    payload = {
        "name": "Unauthorized Vendor",
        "category": "Security",
    }
    resp = client.post("/api/v1/vendors", json=payload, headers=_auth_header(regular_user))
    assert resp.status_code == 403


def test_vendor_admin_crud_lifecycle(admin_user: User, db: Session):
    vendor_name = f"TestVendor-{int(datetime.datetime.utcnow().timestamp())}"
    payload = {
        "name": vendor_name,
        "category": "DevOps & Cloud",
        "description": "High performance cloud hosting alternative",
        "website_url": "https://example.com/testvendor",
        "rating": 4.8,
        "plans": [
            {
                "plan_name": "Standard Starter",
                "price": 29.0,
                "cadence": "monthly",
                "currency": "USD",
                "features": "100GB SSD, Unlimited Bandwidth"
            }
        ]
    }

    # 1. Create vendor
    create_resp = client.post("/api/v1/vendors", json=payload, headers=_auth_header(admin_user))
    assert create_resp.status_code == 201
    created = create_resp.json()
    vendor_id = created["id"]
    assert created["name"] == vendor_name
    assert len(created["plans"]) == 1

    # 2. Update vendor
    update_resp = client.put(
        f"/api/v1/vendors/{vendor_id}",
        json={"description": "Updated description by admin"},
        headers=_auth_header(admin_user)
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "Updated description by admin"

    # 3. Add plan
    plan_resp = client.post(
        f"/api/v1/vendors/{vendor_id}/plans",
        json={"plan_name": "Enterprise Pro", "price": 99.0, "cadence": "monthly"},
        headers=_auth_header(admin_user)
    )
    assert plan_resp.status_code == 201
    plan_id = plan_resp.json()["id"]

    # 4. Delete plan
    del_plan_resp = client.delete(f"/api/v1/vendors/{vendor_id}/plans/{plan_id}", headers=_auth_header(admin_user))
    assert del_plan_resp.status_code == 204

    # 5. Delete vendor
    del_vendor_resp = client.delete(f"/api/v1/vendors/{vendor_id}", headers=_auth_header(admin_user))
    assert del_vendor_resp.status_code == 204


# ==============================================================================
# 3. ENTITLEMENTS & MONETIZATION TESTS
# ==============================================================================
def test_entitlements_resolution():
    # Individual user
    ind_biz = BusinessProfile(account_type="individual")
    ind_tier = EntitlementService.resolve_tier(user=User(is_admin=False), business=ind_biz)
    assert ind_tier == EntitlementTier.PRO_INDIVIDUAL

    # Household user
    hh_biz = BusinessProfile(account_type="household")
    hh_tier = EntitlementService.resolve_tier(user=User(is_admin=False), business=hh_biz)
    assert hh_tier == EntitlementTier.HOUSEHOLD_SHARED

    # Business user
    biz_profile = BusinessProfile(account_type="business")
    biz_tier = EntitlementService.resolve_tier(user=User(is_admin=False), business=biz_profile)
    assert biz_tier == EntitlementTier.BUSINESS_ENTERPRISE

    # Admin override
    admin_tier = EntitlementService.resolve_tier(user=User(is_admin=True), business=ind_biz)
    assert admin_tier == EntitlementTier.BUSINESS_ENTERPRISE


def test_entitlements_api_endpoint(regular_user: User):
    resp = client.get("/api/v1/entitlements", headers=_auth_header(regular_user))
    assert resp.status_code == 200
    data = resp.json()
    assert "tier" in data
    assert "features" in data
    assert data["features"]["can_connect_paypal"] is True


# ==============================================================================
# 4. ADVANCED REPORTING SECURITY & SANITIZATION TESTS
# ==============================================================================
def test_csv_formula_injection_sanitization():
    # Formula injection test vectors
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    assert sanitize_csv_cell("-10+5") == "'-10+5"
    assert sanitize_csv_cell("@SUM(1,2)") == "'@SUM(1,2)"
    # Clean text unchanged
    assert sanitize_csv_cell("AWS Cloud Services") == "AWS Cloud Services"
    assert sanitize_csv_cell(145.50) == 145.50
    assert sanitize_csv_cell(None) == ""

