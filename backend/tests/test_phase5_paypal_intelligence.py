import datetime
import pytest
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.webhook_event import WebhookEvent
from app.services.currency_service import CurrencyService
from app.services.paypal_webhook_service import PayPalWebhookService
from app.services.reconciliation_service import ReconciliationService, FinancialReconciliationReport
from app.testing.synthetic_finance_fixtures import SyntheticFinanceFixtures


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_business(db: Session):
    user = db.query(User).filter_by(email="phase5_test_user@example.com").first()
    if not user:
        user = User(email="phase5_test_user@example.com", hashed_password="pw", full_name="Phase 5 Tester")
        db.add(user)
        db.commit()
        db.refresh(user)

    biz = db.query(BusinessProfile).filter_by(user_id=user.id).first()
    if not biz:
        biz = BusinessProfile(
            user_id=user.id,
            company_name="Phase5 Test Corp",
            account_type="business",
            currency="USD",
        )
        db.add(biz)
        db.commit()
        db.refresh(biz)
    return biz


# ==============================================================================
# 1. CURRENCY SERVICE TESTS
# ==============================================================================
def test_currency_conversion_same_currency():
    res = CurrencyService.convert(100.0, "USD", "USD")
    assert res.converted_amount == 100.0
    assert res.conversion_rate == 1.0


def test_currency_conversion_known_rates():
    eur_to_usd = CurrencyService.convert(100.0, "EUR", "USD")
    assert eur_to_usd.converted_amount > 100.0
    assert eur_to_usd.conversion_rate > 1.0

    usd_to_eur = CurrencyService.convert(100.0, "USD", "EUR")
    assert usd_to_eur.converted_amount < 100.0
    assert round(usd_to_eur.conversion_rate * eur_to_usd.conversion_rate, 2) == 1.0


def test_currency_conversion_unknown_currency_fallback():
    res = CurrencyService.convert(50.0, "XYZ", "USD")
    # Falls back to 1.0 rate
    assert res.converted_amount == 50.0
    assert res.conversion_rate == 1.0


# ==============================================================================
# 2. PAYPAL WEBHOOK SERVICE TESTS
# ==============================================================================
def test_webhook_invalid_payload(db: Session):
    res = PayPalWebhookService.process_webhook_event(
        event_payload={"invalid": "payload"},
        headers={},
        db=db,
    )
    assert res["status"] == "rejected"


def test_webhook_idempotency_and_duplicate_prevention(db: Session, test_business: BusinessProfile):
    event_id = f"WH-TEST-IDEM-{int(datetime.datetime.utcnow().timestamp())}"
    payload = {
        "id": event_id,
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource_type": "capture",
        "resource": {
            "id": f"CAP-{event_id}",
            "amount": {"value": "45.00", "currency_code": "USD"},
            "seller_receivable_breakdown": {
                "paypal_fee": {"value": "1.50"}
            },
            "status": "COMPLETED",
            "custom_id": str(test_business.id),
        }
    }
    headers = {"x-subwise-webhook-simulation": "true"}

    # First attempt: should succeed and record event
    res1 = PayPalWebhookService.process_webhook_event(payload, headers, db)
    assert res1["status"] == "processed"

    # Verify event stored in DB
    ev = db.query(WebhookEvent).filter_by(paypal_event_id=event_id).first()
    assert ev is not None
    assert ev.status == "processed"

    # Second attempt with same event ID: should be recognized as duplicate
    res2 = PayPalWebhookService.process_webhook_event(payload, headers, db)
    assert res2["status"] == "duplicate_ignored"

    # Clean up test event & transaction
    db.query(Transaction).filter_by(paypal_transaction_id=f"CAP-{event_id}").delete()
    db.delete(ev)
    db.commit()


def test_webhook_subscription_cancellation(db: Session, test_business: BusinessProfile):
    # Setup test subscription
    now = datetime.datetime.utcnow()
    sub = Subscription(
        business_id=test_business.id,
        vendor_name="Webhook Cancel Test SaaS",
        category="Software",
        cadence="monthly",
        latest_amount=89.0,
        average_amount=89.0,
        currency="USD",
        status="active",
        detection_type="confirmed",
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=30),
        next_billing_date=now + datetime.timedelta(days=1),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    event_id = f"WH-TEST-CANCEL-{int(datetime.datetime.utcnow().timestamp())}"
    payload = {
        "id": event_id,
        "event_type": "BILLING.SUBSCRIPTION.CANCELLED",
        "resource_type": "subscription",
        "resource": {
            "id": f"I-TEST-{sub.id}",
            "plan_name": "Webhook Cancel Test SaaS",
            "status": "CANCELLED",
            "custom_id": str(test_business.id),
        }
    }
    headers = {"x-subwise-webhook-simulation": "true"}

    res = PayPalWebhookService.process_webhook_event(payload, headers, db)
    assert res["status"] == "processed"

    # Verify subscription marked cancelled
    db.refresh(sub)
    assert sub.status == "cancelled"

    # Cleanup
    db.query(WebhookEvent).filter_by(paypal_event_id=event_id).delete()
    db.delete(sub)
    db.commit()


# ==============================================================================
# 3. RECONCILIATION SERVICE TESTS
# ==============================================================================
def test_reconciliation_service_report_structure(db: Session, test_business: BusinessProfile):
    report = ReconciliationService.reconcile(business=test_business, db=db)
    assert isinstance(report, FinancialReconciliationReport)
    assert report.business_id == test_business.id
    assert report.company_name == test_business.company_name
    assert 0.0 <= report.reconciliation_score <= 100.0
    assert isinstance(report.discrepancies, list)
    assert report.summary_verdict is not None


# ==============================================================================
# 4. SYNTHETIC FINANCE FIXTURES TESTS
# ==============================================================================
def test_synthetic_scenarios_isolation():
    ind_data = SyntheticFinanceFixtures.create_individual_scenario(user_id=99901, business_id=99901)
    assert ind_data["business"].account_type == "individual"
    assert len(ind_data["expenses"]) >= 4
    assert len(ind_data["budgets"]) >= 2

    hh_data = SyntheticFinanceFixtures.create_household_scenario(user_id=99902, business_id=99902)
    assert hh_data["business"].account_type == "household"
    assert len(hh_data["members"]) >= 2
    assert len(hh_data["expenses"]) >= 2

    biz_data = SyntheticFinanceFixtures.create_business_multicurrency_scenario(user_id=99903, business_id=99903)
    assert biz_data["business"].account_type == "business"
    assert len(biz_data["transactions"]) >= 5
    # Verify currencies present
    currencies = {t.currency for t in biz_data["transactions"]}
    assert "USD" in currencies
    assert "EUR" in currencies or "GBP" in currencies
