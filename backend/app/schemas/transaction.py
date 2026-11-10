from pydantic import BaseModel
from typing import Optional, List
import datetime

class TransactionBase(BaseModel):
    transaction_date: datetime.datetime
    raw_description: str
    normalized_vendor: str
    category: str
    gross_amount: float
    fee_amount: float = 0.0
    net_amount: float
    currency: str = "USD"
    status: str = "COMPLETED"
    data_source: str = "demo"

class TransactionResponse(TransactionBase):
    id: int
    business_id: int
    paypal_transaction_id: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class SyncResultResponse(BaseModel):
    status: str
    data_source: str
    transactions_synced: int
    new_subscriptions_identified: int
    message: str
    synced_at: datetime.datetime
    transactions_added: Optional[int] = 0
    transactions_updated: Optional[int] = 0
    transactions_skipped: Optional[int] = 0

class PayPalSyncRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    days_back: Optional[int] = 90

class PayPalSyncResponse(BaseModel):
    status: str
    environment: str
    transactions_fetched: int
    transactions_inserted: int
    transactions_updated: int
    transactions_skipped: int
    total_transactions: int
    subscriptions_identified: int
    synced_at: Optional[datetime.datetime] = None
    message: str

class PayPalStatusResponse(BaseModel):
    configured: bool
    connected: bool
    environment: str
    base_url: str
    client_id_configured: bool
    client_id_preview: Optional[str] = None
    client_secret_configured: bool = False
    oauth_authenticated: bool = False
    transaction_search_accessible: bool = False
    transaction_search_message: Optional[str] = None
    has_reporting_scope: bool
    scopes: List[str] = []
    error: Optional[str] = None
    message: str

class PayPalSyncStatusResponse(BaseModel):
    last_synced_at: Optional[datetime.datetime] = None
    transaction_count: int
    subscription_count: int
    data_source: str
    paypal_connected: bool
    environment: str

class PayPalOrderCreateRequest(BaseModel):
    amount: float = 5.00
    currency: str = "USD"
    description: Optional[str] = "SubWise AI Sandbox Payment Test"
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None

class PayPalOrderCreateResponse(BaseModel):
    order_id: str
    status: str
    approve_url: str
    amount: float
    currency: str
    description: str

class PayPalOrderCaptureRequest(BaseModel):
    order_id: str

class PayPalOrderCaptureResponse(BaseModel):
    status: str
    order_id: str
    capture_id: Optional[str] = None
    capture_status: Optional[str] = None
    gross_amount: float
    fee_amount: float
    net_amount: float
    currency: str
    transaction_id: Optional[int] = None
    synced: bool = False
    message: str
