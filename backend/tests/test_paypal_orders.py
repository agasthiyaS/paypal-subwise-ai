import pytest
from app.services.paypal_client import PayPalClient, PayPalAPIError

def test_paypal_client_create_order_structure():
    client = PayPalClient(mode="sandbox")
    assert client.has_credentials
    # Test creation against sandbox API
    order = client.create_order(
        amount=5.00,
        currency="USD",
        description="SubWise AI Sandbox Payment Test"
    )
    assert order["order_id"] is not None
    assert order["status"] == "CREATED"
    assert "https://www.sandbox.paypal.com/checkoutnow?token=" in order["approve_url"]
    assert order["amount"] == 5.00
    assert order["currency"] == "USD"

def test_paypal_client_capture_unapproved_order_fails():
    client = PayPalClient(mode="sandbox")
    order = client.create_order(
        amount=5.00,
        currency="USD",
        description="SubWise AI Sandbox Payment Test"
    )
    # Attempting to capture without buyer approval must raise PayPalAPIError (HTTP 422 UNPROCESSABLE_ENTITY)
    with pytest.raises(PayPalAPIError) as exc_info:
        client.capture_order(order["order_id"])
    assert exc_info.value.status_code == 422
    assert "ORDER_NOT_APPROVED" in str(exc_info.value)

