"""
Regression Test Suite for PayPal Signed Fee Calculation & Balance Verification.

Verifies:
1. Positive gross with signed negative fee (incoming payment: $5.00 gross + -$0.59 fee = $4.41 net).
2. Negative gross with zero fee (outgoing payment: -$20.00 gross + $0.00 fee = -$20.00 net).
3. Positive gross with zero fee (account funding: $5000.00 gross + $0.00 fee = $5000.00 net).
4. Negative gross with signed fee (outgoing payment with fee: -$100.00 gross + -$3.00 fee = -$103.00 net).
5. PayPalClient normalization respects signed fees.
6. Available USD balance calculation correctly equals $4,984.41 without double-counting currency conversion legs.
7. CloudSoft payment remains -$20.00 net and classified as SaaS expense.
"""

import datetime
import pytest
from unittest.mock import MagicMock

from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.services.paypal_client import PayPalClient
from app.services.forecast_engine import ForecastEngine
from app.services.normalizer import TransactionNormalizer


# ---------------------------------------------------------------------------
# Test 1: Calculation Formula for Signed Fees
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "gross, fee, expected_net",
    [
        # Incoming with signed negative fee ($5 test payment)
        (5.00, -0.59, 4.41),
        # Outgoing with zero fee ($20 CloudSoft payment)
        (-20.00, 0.0, -20.00),
        # Account funding with zero fee ($5000 initial balance)
        (5000.00, 0.0, 5000.00),
        # Outgoing with negative fee (sender pays transaction fee)
        (-100.00, -3.20, -103.20),
        # Large incoming transaction with percentage fee
        (1200.00, -35.10, 1164.90),
        # Zero gross with fee (e.g. chargeback fee)
        (0.00, -15.00, -15.00),
    ]
)
def test_signed_fee_calculation_formula(gross, fee, expected_net):
    # Standard signed fee formula: net = gross + fee
    computed_net = round(gross + fee, 2)
    assert computed_net == expected_net


# ---------------------------------------------------------------------------
# Test 2: PayPalClient Normalization Handles Signed Fees
# ---------------------------------------------------------------------------
def test_paypal_client_normalize_signed_fee():
    client = PayPalClient(mode="sandbox", client_id="dummy", client_secret="dummy")
    
    # Raw PayPal Reporting API item representing $5 incoming payment with -$0.59 signed fee
    raw_item = {
        "transaction_info": {
            "transaction_id": "4EV73998AP815980D",
            "transaction_initiation_date": "2026-11-07T14:29:43+0000",
            "transaction_event_code": "T0000",
            "transaction_status": "S",
            "transaction_amount": {
                "currency_code": "USD",
                "value": "5.00"
            },
            "fee_amount": {
                "currency_code": "USD",
                "value": "-0.59"
            },
            "transaction_note": "SubWise AI Sandbox Payment Test"
        },
        "payer_info": {
            "payer_name": {
                "given_name": "Test",
                "surname": "Buyer"
            }
        }
    }

    normalized = client._normalize_transaction_item(raw_item)
    assert normalized is not None
    assert normalized["paypal_transaction_id"] == "4EV73998AP815980D"
    assert normalized["gross_amount"] == 5.00
    assert normalized["fee_amount"] == -0.59
    assert normalized["net_amount"] == 4.41
    assert normalized["currency"] == "USD"
    assert normalized["status"] == "COMPLETED"


def test_paypal_client_normalize_outgoing_payment():
    client = PayPalClient(mode="sandbox", client_id="dummy", client_secret="dummy")
    
    raw_item = {
        "transaction_info": {
            "transaction_id": "9X0405652T645143S",
            "transaction_initiation_date": "2026-11-09T09:47:06+0000",
            "transaction_event_code": "T0006",
            "transaction_status": "S",
            "transaction_amount": {
                "currency_code": "USD",
                "value": "-20.00"
            },
            "fee_amount": {
                "currency_code": "USD",
                "value": "0.00"
            },
            "transaction_note": "Monthly Software Subscription - CloudSoft"
        }
    }

    normalized = client._normalize_transaction_item(raw_item)
    assert normalized is not None
    assert normalized["paypal_transaction_id"] == "9X0405652T645143S"
    assert normalized["gross_amount"] == -20.00
    assert normalized["fee_amount"] == 0.00
    assert normalized["net_amount"] == -20.00
    assert normalized["currency"] == "USD"


def test_paypal_client_normalize_with_explicit_net():
    """If PayPal API provides an explicit net_amount object, it is preserved."""
    client = PayPalClient(mode="sandbox", client_id="dummy", client_secret="dummy")
    
    raw_item = {
        "transaction_info": {
            "transaction_id": "TEST_NET_EXPLICIT",
            "transaction_initiation_date": "2026-11-07T12:00:00+0000",
            "transaction_status": "S",
            "transaction_amount": {"currency_code": "USD", "value": "100.00"},
            "fee_amount": {"currency_code": "USD", "value": "-3.20"},
            "net_amount": {"currency_code": "USD", "value": "96.80"}
        }
    }

    normalized = client._normalize_transaction_item(raw_item)
    assert normalized["net_amount"] == 96.80


# ---------------------------------------------------------------------------
# Test 3: Verified Cash Balance Equals $4,984.41
# ---------------------------------------------------------------------------
def test_verified_cash_balance_equals_4984_41():
    """
    Validates that:
    - 59071448PK254121L: +$5,000.00 USD (initial balance)
    - 4EV73998AP815980D: +$4.41 USD net (test payment)
    - 9X0405652T645143S: -$20.00 USD net (CloudSoft)
    - 02679053YB768853D: +$1955.38 INR (conversion leg - excluded)
    - 5YW97500CW704310C: -$1955.38 INR (conversion leg - excluded)
    - 6M255220TT5552700: +$20.00 USD (conversion leg - excluded)
    Result = $4,984.41 USD exactly.
    """
    biz = BusinessProfile(
        id=40,
        user_id=40,
        company_name="My Business",
        currency="USD",
        current_cash_reserves=0.0
    )

    transactions = [
        Transaction(
            id=1050,
            business_id=40,
            paypal_transaction_id="59071448PK254121L",
            gross_amount=5000.0,
            fee_amount=0.0,
            net_amount=5000.0,
            currency="USD",
            status="COMPLETED",
            raw_description="Initial balance",
            normalized_vendor="PayPal Balance Adjustment",
            category="Account Funding / Balance Adjustment"
        ),
        Transaction(
            id=1167,
            business_id=40,
            paypal_transaction_id="4EV73998AP815980D",
            gross_amount=5.0,
            fee_amount=-0.59,
            net_amount=4.41,
            currency="USD",
            status="COMPLETED",
            raw_description="SubWise AI Sandbox Payment Test",
            normalized_vendor="Subwise",
            category="General SaaS / Operations"
        ),
        Transaction(
            id=1385,
            business_id=40,
            paypal_transaction_id="9X0405652T645143S",
            gross_amount=-20.0,
            fee_amount=0.0,
            net_amount=-20.0,
            currency="USD",
            status="COMPLETED",
            raw_description="Monthly Software Subscription - CloudSoft",
            normalized_vendor="CloudSoft",
            category="Cloud & IT Management"
        ),
        Transaction(
            id=1386,
            business_id=40,
            paypal_transaction_id="02679053YB768853D",
            gross_amount=1955.38,
            fee_amount=0.0,
            net_amount=1955.38,
            currency="INR",
            status="COMPLETED",
            raw_description="PayPal Transaction",
            normalized_vendor="Paypal",
            category="Payment Transfer / Currency Conversion"
        ),
        Transaction(
            id=1387,
            business_id=40,
            paypal_transaction_id="5YW97500CW704310C",
            gross_amount=-1955.38,
            fee_amount=0.0,
            net_amount=-1955.38,
            currency="INR",
            status="COMPLETED",
            raw_description="PayPal Transaction",
            normalized_vendor="Paypal",
            category="Payment Transfer / Currency Conversion"
        ),
        Transaction(
            id=1388,
            business_id=40,
            paypal_transaction_id="6M255220TT5552700",
            gross_amount=20.0,
            fee_amount=0.0,
            net_amount=20.0,
            currency="USD",
            status="COMPLETED",
            raw_description="PayPal Transaction",
            normalized_vendor="Paypal",
            category="Payment Transfer / Currency Conversion"
        ),
    ]

    balance, is_verified = ForecastEngine.calculate_verified_cash_balance(biz, transactions)
    assert is_verified is True
    assert balance == 4984.41


# ---------------------------------------------------------------------------
# Test 4: CloudSoft Classification Unaffected
# ---------------------------------------------------------------------------
def test_cloudsoft_expense_remains_negative_20():
    tx = Transaction(
        id=1385,
        business_id=40,
        paypal_transaction_id="9X0405652T645143S",
        gross_amount=-20.0,
        fee_amount=0.0,
        net_amount=-20.0,
        currency="USD",
        status="COMPLETED",
        raw_description="Monthly Software Subscription - CloudSoft"
    )

    assert tx.gross_amount == -20.0
    assert tx.fee_amount == 0.0
    assert tx.net_amount == -20.0
    assert ForecastEngine.is_valid_operating(tx) is True

    meta = TransactionNormalizer.normalize_vendor_and_category(tx.raw_description)
    assert meta["normalized_vendor"] == "CloudSoft"
    assert meta["is_known_saas"] is True
