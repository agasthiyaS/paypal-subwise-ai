"""
PayPal REST API Client for PayPal SubWise AI.
Handles OAuth 2.0 token management, credential verification, and
Transaction Reporting API integration against PayPal Developer Sandbox.
"""
import base64
import datetime
import logging
from typing import Dict, Any, List, Optional, Tuple
import httpx
from app.config import settings

logger = logging.getLogger("subwise_ai.paypal")

class PayPalError(Exception):
    """Base exception for all PayPal integration errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

class PayPalAuthenticationError(PayPalError):
    """Raised when Client ID or Secret are missing, invalid, or unauthorized (HTTP 401)."""
    pass

class PayPalPermissionError(PayPalError):
    """Raised when OAuth token lacks required scopes (e.g. Transaction Reporting / HTTP 403)."""
    pass

class PayPalAPIError(PayPalError):
    """Raised when PayPal returns HTTP 4xx (except 401/403) or 5xx."""
    pass


class PayPalClient:
    """
    Official PayPal REST Client for Developer Sandbox & Live Reporting.
    Features:
    - OAuth 2.0 Client Credentials token management with expiration cache and auto-refresh.
    - Transaction Reporting API (/v1/reporting/transactions).
    - Automatic date-range chunking (enforcing PayPal's 31-day max limit per query).
    - Multi-page pagination support.
    - Defensive error mapping and scope inspection.
    """
    SANDBOX_URL = "https://api-m.sandbox.paypal.com"
    LIVE_URL = "https://api-m.paypal.com"
    MAX_DATE_RANGE_DAYS = 31

    def __init__(
        self,
        mode: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 25.0
    ):
        self.mode = (mode or getattr(settings, "PAYPAL_ENVIRONMENT", None) or getattr(settings, "PAYPAL_MODE", None) or "sandbox").lower()
        self.client_id = (client_id or settings.PAYPAL_CLIENT_ID or "").strip()
        self.client_secret = (client_secret or settings.PAYPAL_CLIENT_SECRET or "").strip()
        
        if base_url:
            self.base_url = base_url.rstrip("/")
        elif self.mode == "live":
            self.base_url = self.LIVE_URL
        else:
            self.base_url = (getattr(settings, "PAYPAL_BASE_URL", None) or self.SANDBOX_URL).rstrip("/")
            
        self.timeout = timeout
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime.datetime] = None
        self._token_scopes: List[str] = []

    @property
    def has_credentials(self) -> bool:
        """Returns True if non-empty client_id and client_secret are configured."""
        return bool(self.client_id and self.client_secret)

    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Obtains OAuth 2.0 Bearer token from PayPal /v1/oauth2/token.
        Reuses cached token until 60 seconds before expiration.
        """
        if not self.has_credentials:
            raise PayPalAuthenticationError(
                f"PayPal {self.mode.upper()} Client ID and Secret are not configured. "
                "Provide credentials via settings or the PayPal Connection modal."
            )

        now = datetime.datetime.utcnow()
        if not force_refresh and self._access_token and self._token_expires_at and now < self._token_expires_at:
            return self._access_token

        auth_str = f"{self.client_id}:{self.client_secret}"
        encoded_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        data = {"grant_type": "client_credentials"}

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/v1/oauth2/token", headers=headers, data=data)
        except httpx.RequestError as exc:
            raise PayPalError(f"Network error connecting to PayPal OAuth: {str(exc)}") from exc

        if resp.status_code == 401:
            raise PayPalAuthenticationError(
                f"PayPal OAuth Authentication Failed (HTTP 401): Invalid Client ID or Secret for {self.mode.upper()} mode.",
                status_code=401,
                details=resp.text
            )
        elif resp.status_code == 403:
            raise PayPalPermissionError(
                f"PayPal OAuth Forbidden (HTTP 403): Account lacks permission to access {self.mode.upper()} tokens.",
                status_code=403,
                details=resp.text
            )
        elif resp.status_code != 200:
            raise PayPalAPIError(
                f"PayPal OAuth Token Request failed ({resp.status_code}): {resp.text}",
                status_code=resp.status_code,
                details=resp.text
            )

        res_json = resp.json()
        token = res_json.get("access_token")
        if not token:
            raise PayPalAPIError("PayPal OAuth response missing 'access_token'.", details=res_json)

        self._access_token = token
        expires_in = int(res_json.get("expires_in", 3600))
        # 60-second safety window before expiration
        self._token_expires_at = now + datetime.timedelta(seconds=max(expires_in - 60, 30))
        
        # Parse scopes
        scope_str = res_json.get("scope", "")
        self._token_scopes = [s.strip() for s in scope_str.split() if s.strip()]

        logger.info(
            "Acquired PayPal %s OAuth token (expires in %ds, %d scopes granted)",
            self.mode.upper(), expires_in, len(self._token_scopes)
        )
        return self._access_token

    def verify_credentials(self, detailed: bool = False) -> Any:
        """
        Verifies credentials by performing an OAuth handshake.
        If detailed=False (default), returns bool for compatibility with existing tests.
        If detailed=True, returns a structured dictionary with scopes and error details.
        """
        if not self.has_credentials:
            if detailed:
                return {
                    "valid": False,
                    "mode": self.mode,
                    "error": "Client ID or Secret is empty.",
                    "scopes": []
                }
            return False

        try:
            self.get_access_token(force_refresh=True)
            has_reporting = any("reporting" in s.lower() or "transaction" in s.lower() for s in self._token_scopes)
            if detailed:
                return {
                    "valid": True,
                    "mode": self.mode,
                    "scopes": self._token_scopes,
                    "has_reporting_scope": has_reporting,
                    "expires_at": self._token_expires_at.isoformat() if self._token_expires_at else None,
                    "error": None
                }
            return True
        except Exception as e:
            if detailed:
                return {
                    "valid": False,
                    "mode": self.mode,
                    "error": getattr(e, "message", str(e)),
                    "scopes": []
                }
            return False

    def test_transaction_search_access(self) -> Dict[str, Any]:
        """
        Tests whether the PayPal Transaction Search / Reporting API (/v1/reporting/transactions)
        is accessible with current credentials.
        Returns a dict: {"accessible": bool, "status_code": int, "transaction_count": int, "message": str, "error": Optional[str]}
        """
        if not self.has_credentials:
            return {
                "accessible": False,
                "status_code": 400,
                "transaction_count": 0,
                "message": f"PayPal {self.mode.upper()} Client ID and Secret are not configured.",
                "error": "Missing Client ID or Client Secret"
            }
        try:
            token = self.get_access_token()
        except Exception as e:
            return {
                "accessible": False,
                "status_code": getattr(e, "status_code", 401),
                "transaction_count": 0,
                "message": f"OAuth failed: {getattr(e, 'message', str(e))}",
                "error": str(e)
            }

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        now = datetime.datetime.utcnow()
        yesterday = now - datetime.timedelta(days=1)
        params = {
            "start_date": yesterday.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end_date": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "page_size": 1,
            "page": 1
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/v1/reporting/transactions", headers=headers, params=params)

            if resp.status_code == 200:
                data = resp.json()
                tx_list = data.get("transaction_details", [])
                return {
                    "accessible": True,
                    "status_code": 200,
                    "transaction_count": len(tx_list),
                    "message": "Transaction Search API is active and accessible.",
                    "error": None
                }
            elif resp.status_code == 403:
                return {
                    "accessible": False,
                    "status_code": 403,
                    "transaction_count": 0,
                    "message": "Permission Denied (HTTP 403): Transaction Search feature is not enabled for this Sandbox app in PayPal Developer Portal.",
                    "error": resp.text
                }
            else:
                return {
                    "accessible": False,
                    "status_code": resp.status_code,
                    "transaction_count": 0,
                    "message": f"Transaction Search API returned HTTP {resp.status_code}.",
                    "error": resp.text
                }
        except Exception as exc:
            return {
                "accessible": False,
                "status_code": 500,
                "transaction_count": 0,
                "message": f"Network error contacting Transaction Search API: {str(exc)}",
                "error": str(exc)
            }

    def fetch_transactions(
        self,
        start_date: Any,
        end_date: Optional[Any] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Fetches permitted transaction history from the PayPal Transaction Reporting API.
        Automatically chunks queries exceeding PayPal's 31-day window limit.
        Handles pagination and normalizes response payloads.
        """
        if isinstance(start_date, str):
            try:
                start_date = datetime.datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except Exception:
                start_date = datetime.datetime.utcnow() - datetime.timedelta(days=90)
        if isinstance(end_date, str):
            try:
                end_date = datetime.datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except Exception:
                end_date = datetime.datetime.utcnow()

        if end_date is None:
            end_date = datetime.datetime.utcnow()

        # Normalize to naive UTC datetimes for comparison and queries
        if getattr(start_date, "tzinfo", None):
            start_date = start_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if getattr(end_date, "tzinfo", None):
            end_date = end_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)

        if start_date > end_date:
            raise ValueError("start_date must be earlier than or equal to end_date.")

        # Chunk into sub-ranges of up to 30 days
        windows = self._split_date_range(start_date, end_date, max_days=30)
        all_transactions: List[Dict[str, Any]] = []
        seen_tx_ids = set()

        for win_start, win_end in windows:
            window_txs = self._fetch_window(win_start, win_end, page_size=page_size)
            for tx in window_txs:
                tx_id = tx.get("paypal_transaction_id")
                if tx_id:
                    if tx_id in seen_tx_ids:
                        continue
                    seen_tx_ids.add(tx_id)
                all_transactions.append(tx)

        # Sort descending by transaction_date
        all_transactions.sort(key=lambda x: x["transaction_date"], reverse=True)
        return all_transactions

    def _split_date_range(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        max_days: int = 30
    ) -> List[Tuple[datetime.datetime, datetime.datetime]]:
        """Splits an arbitrary date range into chunks not exceeding max_days."""
        windows = []
        cur_start = start_date
        while cur_start < end_date:
            cur_end = min(cur_start + datetime.timedelta(days=max_days), end_date)
            windows.append((cur_start, cur_end))
            cur_start = cur_end + datetime.timedelta(seconds=1)
        return windows

    def _fetch_window(
        self,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetches transactions for a single date window across all paginated pages."""
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        page = 1
        window_results: List[Dict[str, Any]] = []

        while True:
            params = {
                "start_date": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": end_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "fields": "transaction_info,payer_info",
                "page_size": min(page_size, 500),
                "page": page
            }

            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"{self.base_url}/v1/reporting/transactions", headers=headers, params=params)
            except httpx.RequestError as exc:
                raise PayPalError(f"Network error querying PayPal Reporting API: {str(exc)}") from exc

            # Token expired mid-sync check
            if resp.status_code == 401:
                token = self.get_access_token(force_refresh=True)
                headers["Authorization"] = f"Bearer {token}"
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.get(f"{self.base_url}/v1/reporting/transactions", headers=headers, params=params)

            if resp.status_code == 403:
                raise PayPalPermissionError(
                    "PayPal Reporting API Permission Denied (HTTP 403). "
                    "Ensure the Sandbox App has 'Transaction Search' / 'Reporting' permission enabled in PayPal Developer Portal.",
                    status_code=403,
                    details=resp.text
                )
            elif resp.status_code == 400:
                raise PayPalAPIError(
                    f"PayPal Reporting API Bad Request (HTTP 400): {resp.text}",
                    status_code=400,
                    details=resp.text
                )
            elif resp.status_code != 200:
                raise PayPalAPIError(
                    f"PayPal Reporting API Error ({resp.status_code}): {resp.text}",
                    status_code=resp.status_code,
                    details=resp.text
                )

            data = resp.json()
            raw_details = data.get("transaction_details", [])
            total_pages = int(data.get("total_pages", 1))

            for item in raw_details:
                normalized = self._normalize_transaction_item(item)
                if normalized:
                    window_results.append(normalized)

            if page >= total_pages or not raw_details:
                break
            page += 1
            if page > 10:  # Safety cap on pagination per window
                break

        return window_results

    def _normalize_transaction_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extracts standardized transaction properties from a PayPal Reporting API item."""
        tx_info = item.get("transaction_info", {})
        payer_info = item.get("payer_info", {})
        
        tx_id = tx_info.get("transaction_id")
        if not tx_id:
            return None

        # Amount parsing
        amount_obj = tx_info.get("transaction_amount", {})
        gross_val = float(amount_obj.get("value", "0.0"))
        currency = amount_obj.get("currency_code", "USD")
        
        fee_obj = tx_info.get("fee_amount", {})
        fee_val = float(fee_obj.get("value", "0.0")) if fee_obj else 0.0
        
        net_obj = tx_info.get("net_amount", {})
        if net_obj and "value" in net_obj:
            net_val = float(net_obj.get("value", "0.0"))
        else:
            # Respect PayPal's signed fee values: fee_amount is returned as signed negative (e.g. -0.59)
            if fee_val < 0:
                net_val = round(gross_val + fee_val, 2)
            else:
                net_val = round(gross_val - fee_val, 2)

        # Date parsing
        date_str = tx_info.get("transaction_initiation_date") or tx_info.get("transaction_updated_date")
        if date_str:
            try:
                # PayPal format: 2026-10-15T09:30:00+0000 or 2026-10-15T09:30:00Z
                clean_str = date_str.replace("Z", "+00:00")
                if len(clean_str) >= 24 and (clean_str[-5] in ["+", "-"]):
                    # convert +0000 to +00:00
                    clean_str = clean_str[:-2] + ":" + clean_str[-2:]
                tx_date = datetime.datetime.fromisoformat(clean_str)
                # Normalize to naive UTC for consistent DB storage
                if tx_date.tzinfo:
                    tx_date = tx_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            except Exception:
                tx_date = datetime.datetime.utcnow()
        else:
            tx_date = datetime.datetime.utcnow()

        # Description / Counterparty parsing
        raw_desc = (
            tx_info.get("transaction_note")
            or tx_info.get("transaction_subject")
            or payer_info.get("payer_name", {}).get("alternate_full_name")
            or (f"{payer_info.get('payer_name', {}).get('given_name', '')} {payer_info.get('payer_name', {}).get('surname', '')}").strip()
            or payer_info.get("email_address")
            or "PayPal Transaction"
        )

        status_code = tx_info.get("transaction_status", "S")
        status_map = {
            "S": "COMPLETED",
            "D": "DENIED",
            "P": "PENDING",
            "V": "REVERSED",
            "F": "FAILED"
        }
        status = status_map.get(status_code, status_code)

        return {
            "paypal_transaction_id": tx_id,
            "transaction_date": tx_date,
            "raw_description": raw_desc.strip(),
            "gross_amount": gross_val,
            "fee_amount": fee_val,
            "net_amount": net_val,
            "currency": currency,
            "status": status,
            "data_source": self.mode
        }

    def create_order(
        self,
        amount: float = 5.00,
        currency: str = "USD",
        description: str = "SubWise AI Sandbox Payment Test",
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates an order using PayPal Orders v2 API (POST /v2/checkout/orders).
        Used for Sandbox payment testing with Personal sandbox buyer accounts.
        """
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        default_return = "http://localhost:3000/dashboard?paypal_test=success"
        default_cancel = "http://localhost:3000/dashboard?paypal_test=cancel"

        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": f"subwise_test_{int(datetime.datetime.utcnow().timestamp())}",
                    "description": description,
                    "amount": {
                        "currency_code": currency,
                        "value": f"{amount:.2f}"
                    }
                }
            ],
            "application_context": {
                "brand_name": "PayPal SubWise AI",
                "landing_page": "LOGIN",
                "user_action": "PAY_NOW",
                "return_url": return_url or default_return,
                "cancel_url": cancel_url or default_cancel
            }
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/v2/checkout/orders", headers=headers, json=payload)
        except httpx.RequestError as exc:
            raise PayPalError(f"Network error creating PayPal order: {str(exc)}") from exc

        if resp.status_code not in (200, 201):
            raise PayPalAPIError(
                f"Failed to create PayPal Sandbox order (HTTP {resp.status_code}): {resp.text}",
                status_code=resp.status_code,
                details=resp.text
            )

        data = resp.json()
        order_id = data.get("id")
        status = data.get("status", "CREATED")
        approve_url = None
        for link in data.get("links", []):
            if link.get("rel") == "approve":
                approve_url = link.get("href")
                break

        if not approve_url:
            raise PayPalAPIError("PayPal Orders response missing approval URL.", details=data)

        return {
            "order_id": order_id,
            "status": status,
            "approve_url": approve_url,
            "amount": amount,
            "currency": currency,
            "description": description,
            "raw_response": data
        }

    def capture_order(self, order_id: str) -> Dict[str, Any]:
        """
        Captures an approved PayPal order using Orders v2 API (POST /v2/checkout/orders/{order_id}/capture).
        Verifies that status is COMPLETED and extracts capture payment transaction details.
        """
        token = self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/v2/checkout/orders/{order_id}/capture", headers=headers, json={})
        except httpx.RequestError as exc:
            raise PayPalError(f"Network error capturing PayPal order: {str(exc)}") from exc

        if resp.status_code not in (200, 201):
            raise PayPalAPIError(
                f"Failed to capture PayPal order {order_id} (HTTP {resp.status_code}): {resp.text}",
                status_code=resp.status_code,
                details=resp.text
            )

        data = resp.json()
        order_status = data.get("status")
        if order_status != "COMPLETED":
            raise PayPalAPIError(
                f"PayPal order capture status is '{order_status}' (expected COMPLETED).",
                details=data
            )

        # Extract capture details
        purchase_units = data.get("purchase_units", [])
        captures = []
        if purchase_units:
            payments = purchase_units[0].get("payments", {})
            captures = payments.get("captures", [])

        if not captures:
            raise PayPalAPIError("Capture response contains no capture payment objects.", details=data)

        cap = captures[0]
        capture_id = cap.get("id")
        cap_status = cap.get("status", "COMPLETED")

        # Financial breakdown
        amt_obj = cap.get("amount", {})
        gross_val = float(amt_obj.get("value", 0.0))
        currency = amt_obj.get("currency_code", "USD")

        breakdown = cap.get("seller_receivable_breakdown", {})
        fee_obj = breakdown.get("paypal_fee", {})
        net_obj = breakdown.get("net_amount", {})

        fee_val = float(fee_obj.get("value", 0.0)) if fee_obj else 0.0
        if net_obj and "value" in net_obj:
            net_val = float(net_obj.get("value", 0.0))
        else:
            net_val = round(gross_val + fee_val, 2) if fee_val < 0 else round(gross_val - fee_val, 2)

        create_time_str = cap.get("create_time") or data.get("create_time")
        tx_date = datetime.datetime.utcnow()
        if create_time_str:
            try:
                clean_time = create_time_str.replace("Z", "+00:00")
                tx_date = datetime.datetime.fromisoformat(clean_time)
                if tx_date.tzinfo:
                    tx_date = tx_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            except Exception:
                tx_date = datetime.datetime.utcnow()

        return {
            "order_id": order_id,
            "capture_id": capture_id,
            "status": order_status,
            "capture_status": cap_status,
            "gross_amount": gross_val,
            "fee_amount": fee_val,
            "net_amount": net_val,
            "currency": currency,
            "transaction_date": tx_date,
            "raw_response": data
        }
