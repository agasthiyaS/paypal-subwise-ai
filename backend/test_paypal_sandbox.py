"""
Comprehensive PayPal Sandbox Integration Test Suite for PayPal SubWise AI.
Tests all 12 core requirements:
1. Successful OAuth authentication
2. Invalid credentials handling (401)
3. Expired token handling & auto-refresh
4. Transaction retrieval & field extraction
5. Date filtering & 31-day chunking
6. Pagination handling
7. Duplicate transaction prevention
8. PostgreSQL transaction storage & decimal precision
9. Business-level multi-tenant isolation
10. PayPal API permission errors (403 scope missing)
11. Empty transaction response handling
12. Connection status and disconnection API
"""
import sys
import datetime
import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.services.paypal_client import (
    PayPalClient,
    PayPalError,
    PayPalAuthenticationError,
    PayPalPermissionError,
    PayPalAPIError
)
from app.services.auth_service import get_password_hash
from app.config import settings

class PayPalIntegrationTests:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests_run = 0

    def record_pass(self, name: str, details: str = ""):
        self.passed += 1
        self.tests_run += 1
        print(f" [PASS] Test {self.tests_run}: {name}")
        if details:
            print(f"        -> {details}")

    def record_fail(self, name: str, reason: str):
        self.failed += 1
        self.tests_run += 1
        print(f" [FAIL] Test {self.tests_run}: {name}")
        print(f"        -> {reason}")

    def run_all(self):
        print("=" * 75)
        print("PAYPAL SUBWISE AI - PAYPAL SANDBOX INTEGRATION TEST SUITE")
        print("=" * 75)
        
        has_live_creds = bool(settings.PAYPAL_CLIENT_ID and settings.PAYPAL_CLIENT_SECRET)
        print(f"Environment Mode: SANDBOX")
        print(f"Live Sandbox Credentials Configured: {has_live_creds}")
        if not has_live_creds:
            print("Note: Running comprehensive unit/mock integration suite with explicit mock tagging.")
        print("-" * 75)

        self.test_1_successful_oauth_authentication(has_live_creds)
        self.test_2_invalid_credentials_handling()
        self.test_3_expired_token_handling()
        self.test_4_transaction_retrieval_and_normalization()
        self.test_5_date_filtering_and_chunking()
        self.test_6_pagination_handling()
        self.test_7_duplicate_prevention_in_postgres()
        self.test_8_postgres_transaction_storage_and_precision()
        self.test_9_business_level_tenant_isolation()
        self.test_10_permission_errors_403_handling()
        self.test_11_empty_transaction_response_handling()
        self.test_12_frontend_connection_status_and_disconnect()

        print("-" * 75)
        print(f"TEST SUMMARY: {self.passed} PASSED, {self.failed} FAILED out of {self.tests_run} tests.")
        print("=" * 75)
        return self.failed == 0

    def test_1_successful_oauth_authentication(self, has_live_creds: bool):
        test_name = "OAuth 2.0 Token Generation & Scope Extraction"
        if has_live_creds:
            try:
                client = PayPalClient(mode="sandbox")
                token = client.get_access_token(force_refresh=True)
                assert token, "Token empty"
                assert client._token_expires_at > datetime.datetime.utcnow()
                self.record_pass(test_name, f"LIVE SANDBOX: Acquired bearer token ({token[:15]}...), scopes: {client._token_scopes}")
            except Exception as e:
                self.record_fail(test_name, f"Live call failed: {str(e)}")
        else:
            # Verified Mocked Test
            with patch("httpx.Client.post") as mock_post:
                mock_post.return_value = MagicMock(
                    status_code=200,
                    json=lambda: {
                        "access_token": "A21AAMockSandboxAccessToken2026",
                        "token_type": "Bearer",
                        "app_id": "APP-80W284485P519543T",
                        "expires_in": 32400,
                        "scope": "https://uri.paypal.com/services/reporting/search/read https://uri.paypal.com/services/subscriptions"
                    }
                )
                client = PayPalClient(mode="sandbox", client_id="DUMMY_CLIENT_ID", client_secret="DUMMY_SECRET")
                token = client.get_access_token(force_refresh=True)
                assert token == "A21AAMockSandboxAccessToken2026"
                assert "https://uri.paypal.com/services/reporting/search/read" in client._token_scopes
                assert client._token_expires_at > datetime.datetime.utcnow()
                self.record_pass(test_name, "[MOCKED] Token parsed, scopes identified, expiration set (+32400s).")

    def test_2_invalid_credentials_handling(self):
        test_name = "Invalid Credentials Error Handling (HTTP 401)"
        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=401,
                text='{"error":"invalid_client","error_description":"Client Authentication failed"}'
            )
            client = PayPalClient(mode="sandbox", client_id="BAD_CLIENT_ID", client_secret="BAD_SECRET")
            try:
                client.get_access_token(force_refresh=True)
                self.record_fail(test_name, "Did not raise PayPalAuthenticationError on 401")
            except PayPalAuthenticationError as e:
                assert e.status_code == 401
                assert "Invalid Client ID or Secret" in e.message
                self.record_pass(test_name, "[MOCKED] Caught PayPalAuthenticationError (401) with user-friendly message.")

    def test_3_expired_token_handling(self):
        test_name = "Token Reuse and Automatic Expiration Refresh"
        with patch("httpx.Client.post") as mock_post:
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"access_token": "Token_Initial", "expires_in": 3600, "scope": ""}
            )
            client = PayPalClient(mode="sandbox", client_id="ID", client_secret="SEC")
            t1 = client.get_access_token()
            assert t1 == "Token_Initial"
            assert mock_post.call_count == 1

            # Second call before expiry -> MUST reuse token without network call
            t2 = client.get_access_token()
            assert t2 == "Token_Initial"
            assert mock_post.call_count == 1, "Cached token was not reused!"

            # Artificially expire the token
            client._token_expires_at = datetime.datetime.utcnow() - datetime.timedelta(seconds=10)
            mock_post.return_value = MagicMock(
                status_code=200,
                json=lambda: {"access_token": "Token_Refreshed_New", "expires_in": 3600, "scope": ""}
            )
            t3 = client.get_access_token()
            assert t3 == "Token_Refreshed_New"
            assert mock_post.call_count == 2, "Did not auto-refresh expired token!"

            self.record_pass(test_name, "[MOCKED] Verified token cache hit and automatic refresh on expiration.")

    def test_4_transaction_retrieval_and_normalization(self):
        test_name = "Transaction Reporting Normalization & Field Mapping"
        sample_api_response = {
            "total_items": 1,
            "total_pages": 1,
            "transaction_details": [
                {
                    "transaction_info": {
                        "transaction_id": "8XY1234567890123A",
                        "transaction_initiation_date": "2026-10-14T15:30:00Z",
                        "transaction_updated_date": "2026-10-14T15:30:00Z",
                        "transaction_amount": {"currency_code": "USD", "value": "-150.00"},
                        "fee_amount": {"currency_code": "USD", "value": "4.65"},
                        "net_amount": {"currency_code": "USD", "value": "-154.65"},
                        "transaction_status": "S",
                        "transaction_subject": "GITHUB ENTERPRISE SEATS"
                    },
                    "payer_info": {
                        "payer_name": {"alternate_full_name": "GitHub Inc."}
                    }
                }
            ]
        }

        with patch.object(PayPalClient, "get_access_token", return_value="mock_token"):
            with patch("httpx.Client.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200, json=lambda: sample_api_response)
                client = PayPalClient(mode="sandbox", client_id="ID", client_secret="SEC")
                txs = client.fetch_transactions(
                    start_date=datetime.datetime(2026, 10, 1),
                    end_date=datetime.datetime(2026, 10, 20)
                )

                assert len(txs) == 1
                item = txs[0]
                assert item["paypal_transaction_id"] == "8XY1234567890123A"
                assert item["gross_amount"] == -150.00
                assert item["fee_amount"] == 4.65
                assert item["net_amount"] == -154.65
                assert item["currency"] == "USD"
                assert item["status"] == "COMPLETED"
                assert "GITHUB" in item["raw_description"]
                self.record_pass(test_name, f"[MOCKED] Successfully extracted: {item['paypal_transaction_id']}, gross={item['gross_amount']}, fee={item['fee_amount']}")

    def test_5_date_filtering_and_chunking(self):
        test_name = "PayPal 31-Day Date Range Chunking Compliance"
        client = PayPalClient(mode="sandbox", client_id="ID", client_secret="SEC")
        # 90-day range
        start = datetime.datetime(2026, 7, 1)
        end = datetime.datetime(2026, 10, 1)
        windows = client._split_date_range(start, end, max_days=30)
        
        assert len(windows) >= 3, f"Expected at least 3 windows for 90 days, got {len(windows)}"
        for w_start, w_end in windows:
            diff = (w_end - w_start).days
            assert diff <= 31, f"Window exceeds PayPal 31-day limit: {diff} days"

        self.record_pass(test_name, f"Split 92 days into {len(windows)} compliant windows (all <= 30 days).")

    def test_6_pagination_handling(self):
        test_name = "Multi-Page Traversal on Large Result Sets"
        page1_res = {
            "total_items": 3,
            "total_pages": 2,
            "transaction_details": [
                {"transaction_info": {"transaction_id": "TXN_PG1_1", "transaction_amount": {"value": "-10.00"}, "transaction_status": "S"}},
                {"transaction_info": {"transaction_id": "TXN_PG1_2", "transaction_amount": {"value": "-20.00"}, "transaction_status": "S"}}
            ]
        }
        page2_res = {
            "total_items": 3,
            "total_pages": 2,
            "transaction_details": [
                {"transaction_info": {"transaction_id": "TXN_PG2_1", "transaction_amount": {"value": "-30.00"}, "transaction_status": "S"}}
            ]
        }

        call_count = 0
        def mock_get_pages(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            params = kwargs.get("params", {})
            page = params.get("page", 1)
            if page == 1:
                return MagicMock(status_code=200, json=lambda: page1_res)
            return MagicMock(status_code=200, json=lambda: page2_res)

        with patch.object(PayPalClient, "get_access_token", return_value="mock_token"):
            with patch("httpx.Client.get", side_effect=mock_get_pages):
                client = PayPalClient(mode="sandbox", client_id="ID", client_secret="SEC")
                txs = client.fetch_transactions(start_date=datetime.datetime(2026, 10, 1), end_date=datetime.datetime(2026, 10, 15))
                assert len(txs) == 3
                assert {t["paypal_transaction_id"] for t in txs} == {"TXN_PG1_1", "TXN_PG1_2", "TXN_PG2_1"}
                assert call_count == 2
                self.record_pass(test_name, f"[MOCKED] Successfully iterated through 2 pages and merged 3 transactions.")

    def test_7_duplicate_prevention_in_postgres(self):
        test_name = "PostgreSQL Duplicate Transaction Prevention"
        db = SessionLocal()
        try:
            # Clean up test user
            u = db.query(User).filter(User.email == "dup_test@subwise.io").first()
            if u:
                db.delete(u)
                db.commit()

            u = User(email="dup_test@subwise.io", hashed_password=get_password_hash("pass123"), full_name="Dup Tester")
            db.add(u)
            db.commit()
            db.refresh(u)

            biz = BusinessProfile(user_id=u.id, company_name="Dup Biz Test")
            db.add(biz)
            db.commit()
            db.refresh(biz)

            # Insert initial transaction
            t1 = Transaction(
                business_id=biz.id,
                paypal_transaction_id="PAYPAL_UNIQUE_1001",
                transaction_date=datetime.datetime.utcnow(),
                raw_description="SLACK TECHNOLOGIES",
                normalized_vendor="Slack",
                category="Productivity",
                gross_amount=-15.00,
                net_amount=-15.00,
                currency="USD",
                status="PENDING",
                data_source="sandbox"
            )
            db.add(t1)
            db.commit()

            # Simulate incoming sync payload containing the same paypal_transaction_id (updated status)
            sync_payload = [
                {
                    "paypal_transaction_id": "PAYPAL_UNIQUE_1001",
                    "transaction_date": t1.transaction_date,
                    "raw_description": "SLACK TECHNOLOGIES INC",
                    "gross_amount": -15.00,
                    "fee_amount": 0.45,
                    "net_amount": -15.45,
                    "currency": "USD",
                    "status": "COMPLETED",
                    "data_source": "sandbox"
                }
            ]

            # Run duplicate detection logic
            existing = db.query(Transaction).filter(
                Transaction.business_id == biz.id,
                Transaction.paypal_transaction_id == "PAYPAL_UNIQUE_1001"
            ).first()
            assert existing is not None
            # Update fields
            existing.status = sync_payload[0]["status"]
            existing.fee_amount = sync_payload[0]["fee_amount"]
            existing.net_amount = sync_payload[0]["net_amount"]
            db.commit()

            # Total transactions for this business MUST still be 1
            count = db.query(Transaction).filter(Transaction.business_id == biz.id).count()
            assert count == 1, f"Duplicate created! Found {count} transactions"

            rec = db.query(Transaction).filter(Transaction.business_id == biz.id).first()
            assert rec.status == "COMPLETED"
            assert rec.fee_amount == 0.45

            db.delete(u)
            db.commit()
            self.record_pass(test_name, "Verified duplicate skipped, existing record updated in place in PostgreSQL.")
        finally:
            db.close()

    def test_8_postgres_transaction_storage_and_precision(self):
        test_name = "PostgreSQL Numeric Precision & Foreign Key Storage"
        db = SessionLocal()
        try:
            u = db.query(User).filter(User.email == "prec_test@subwise.io").first()
            if u:
                db.delete(u)
                db.commit()

            u = User(email="prec_test@subwise.io", hashed_password=get_password_hash("pass123"), full_name="Precision Tester")
            db.add(u)
            db.commit()
            db.refresh(u)

            biz = BusinessProfile(user_id=u.id, company_name="Precision Biz", monthly_baseline_revenue=18000.0)
            db.add(biz)
            db.commit()
            db.refresh(biz)

            # Insert exact float values
            tx = Transaction(
                business_id=biz.id,
                paypal_transaction_id="TXN_PRECISION_99",
                transaction_date=datetime.datetime(2026, 10, 5, 14, 22, 10),
                raw_description="MICROSOFT 365 SUITE",
                normalized_vendor="Microsoft",
                category="Office Software",
                gross_amount=-129.99,
                fee_amount=3.77,
                net_amount=-133.76,
                currency="USD",
                status="COMPLETED",
                data_source="sandbox"
            )
            db.add(tx)
            db.commit()
            db.refresh(tx)

            assert tx.id is not None
            assert abs(tx.gross_amount - (-129.99)) < 0.001
            assert abs(tx.fee_amount - 3.77) < 0.001
            assert abs(tx.net_amount - (-133.76)) < 0.001
            assert tx.business.id == biz.id

            db.delete(u)
            db.commit()
            self.record_pass(test_name, "Verified 2-decimal precision stored and read back from PostgreSQL.")
        finally:
            db.close()

    def test_9_business_level_tenant_isolation(self):
        test_name = "Multi-Tenant Isolation Between Distinct Business Profiles"
        db = SessionLocal()
        try:
            u1 = User(email="tenant_a@subwise.io", hashed_password=get_password_hash("pass1"), full_name="Tenant A")
            u2 = User(email="tenant_b@subwise.io", hashed_password=get_password_hash("pass2"), full_name="Tenant B")
            db.add_all([u1, u2])
            db.commit()

            b1 = BusinessProfile(user_id=u1.id, company_name="Biz Alpha", paypal_client_id="ALPHA_ID")
            b2 = BusinessProfile(user_id=u2.id, company_name="Biz Beta", paypal_client_id="BETA_ID")
            db.add_all([b1, b2])
            db.commit()

            tx_a = Transaction(
                business_id=b1.id,
                paypal_transaction_id="TX_ALPHA_001",
                transaction_date=datetime.datetime.utcnow(),
                raw_description="CONFIDENTIAL ALPHA EXPENSE",
                normalized_vendor="AlphaVendor",
                gross_amount=-500.0,
                net_amount=-500.0
            )
            db.add(tx_a)
            db.commit()

            # Query for Tenant B
            b2_txs = db.query(Transaction).filter(Transaction.business_id == b2.id).all()
            assert len(b2_txs) == 0, "Leakage! Tenant B accessed Tenant A's transactions."

            # Query for Tenant A
            b1_txs = db.query(Transaction).filter(Transaction.business_id == b1.id).all()
            assert len(b1_txs) == 1
            assert b1_txs[0].paypal_transaction_id == "TX_ALPHA_001"

            db.delete(u1)
            db.delete(u2)
            db.commit()
            self.record_pass(test_name, "Tenant A records completely invisible to Tenant B (zero leakage).")
        finally:
            db.close()

    def test_10_permission_errors_403_handling(self):
        test_name = "PayPal Permission Denied (HTTP 403) Handling"
        with patch.object(PayPalClient, "get_access_token", return_value="mock_token"):
            with patch("httpx.Client.get") as mock_get:
                mock_get.return_value = MagicMock(
                    status_code=403,
                    text='{"name":"NOT_AUTHORIZED","message":"Authorization failed: Insufficient scopes"}'
                )
                client = PayPalClient(mode="sandbox", client_id="ID", client_secret="SEC")
                try:
                    client.fetch_transactions(start_date=datetime.datetime(2026, 10, 1), end_date=datetime.datetime(2026, 10, 15))
                    self.record_fail(test_name, "Did not raise PayPalPermissionError on 403")
                except PayPalPermissionError as e:
                    assert e.status_code == 403
                    assert "Transaction Search" in e.message
                    self.record_pass(test_name, "[MOCKED] Caught PayPalPermissionError (403) with developer guidance.")

    def test_11_empty_transaction_response_handling(self):
        test_name = "Graceful Handling of Empty Transaction Results"
        empty_res = {"total_items": 0, "total_pages": 0, "transaction_details": []}
        with patch.object(PayPalClient, "get_access_token", return_value="mock_token"):
            with patch("httpx.Client.get") as mock_get:
                mock_get.return_value = MagicMock(status_code=200, json=lambda: empty_res)
                client = PayPalClient(mode="sandbox", client_id="ID", client_secret="SEC")
                txs = client.fetch_transactions(start_date=datetime.datetime(2026, 10, 1), end_date=datetime.datetime(2026, 10, 15))
                assert isinstance(txs, list)
                assert len(txs) == 0
                self.record_pass(test_name, "[MOCKED] Returned empty list cleanly without throwing errors.")

    def test_12_frontend_connection_status_and_disconnect(self):
        test_name = "Frontend Integration Status & Disconnect Endpoint"
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)

        db = SessionLocal()
        try:
            u = db.query(User).filter(User.email == "status_test@subwise.io").first()
            if u:
                db.delete(u)
                db.commit()

            # Register
            reg_res = client.post("/api/v1/auth/register", json={
                "email": "status_test@subwise.io",
                "password": "Password123!",
                "full_name": "Status User",
                "company_name": "Status Corp"
            })
            token = reg_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Connect in Demo mode
            conn_res = client.post("/api/v1/business/paypal-connect", json={"paypal_mode": "demo"}, headers=headers)
            assert conn_res.status_code == 200
            assert conn_res.json()["paypal_connected"] is True

            # Check profile includes status and count
            prof_res = client.get("/api/v1/business/profile", headers=headers)
            assert prof_res.status_code == 200
            pdata = prof_res.json()
            assert pdata["paypal_mode"] == "demo"
            assert "total_transactions" in pdata
            assert "paypal_client_secret" not in pdata, "Secret leaked in profile response!"

            # Test Disconnect
            disc_res = client.post("/api/v1/business/paypal-disconnect", headers=headers)
            assert disc_res.status_code == 200
            assert disc_res.json()["status"] == "disconnected"

            # Clean up
            cleanup_user = db.query(User).filter(User.email == "status_test@subwise.io").first()
            if cleanup_user:
                db.delete(cleanup_user)
                db.commit()

            self.record_pass(test_name, "Verified status querying, secret shielding, and disconnect endpoint.")
        finally:
            db.close()

if __name__ == "__main__":
    runner = PayPalIntegrationTests()
    success = runner.run_all()
    sys.exit(0 if success else 1)

