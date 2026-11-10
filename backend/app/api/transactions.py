import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.schemas.transaction import TransactionResponse, SyncResultResponse
from app.services.auth_service import get_current_user
from app.services.business_service import (
    get_active_business,
    get_environment_transactions_query,
    get_environment_transactions,
    get_environment_subscriptions
)
from app.services.paypal_client import (
    PayPalClient,
    PayPalError,
    PayPalAuthenticationError,
    PayPalPermissionError,
    PayPalAPIError
)
from app.services.demo_data_generator import DemoDataGenerator
from app.services.normalizer import TransactionNormalizer
from app.services.subscription_detector import SubscriptionDetector
from app.services.recommendation_engine import RecommendationEngine

from app.config import settings

logger = logging.getLogger("subwise_ai.api.transactions")

router = APIRouter(prefix="/transactions", tags=["Transactions & PayPal Sync"])

@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    request: Request = None,
    category: Optional[str] = None,
    vendor: Optional[str] = None,
    sort_by: Optional[str] = "date",
    order: Optional[str] = "desc",
    limit: int = Query(100, le=500),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    query = get_environment_transactions_query(db=db, biz=biz, request=request)
    if category:
        query = query.filter(Transaction.category == category)
    if vendor:
        query = query.filter(Transaction.normalized_vendor.ilike(f"%{vendor}%"))

    # Sorting
    if sort_by in ["amount", "gross_amount"]:
        sort_col = Transaction.gross_amount
    elif sort_by in ["vendor", "normalized_vendor"]:
        sort_col = Transaction.normalized_vendor
    else:
        sort_col = Transaction.transaction_date

    if (order or "desc").lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    return query.offset(offset).limit(limit).all()

@router.post("/sync", response_model=SyncResultResponse)
def sync_transactions(
    request: Request = None,
    force_demo: bool = False,
    days_back: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synchronizes transactions from PayPal Sandbox/Live Reporting API or Demo dataset.
    Features:
    - PayPal OAuth 2.0 and Transaction Reporting API integration.
    - Automatic date-range chunking for intervals exceeding 31 days.
    - Duplicate detection and prevention by paypal_transaction_id.
    - Automatic subscription detection and AI recommendation generation.
    """
    biz = get_active_business(current_user=current_user, db=db, request=request)

    if force_demo:
        target_mode = "demo"
        months_back = max(round(days_back / 30), 1)
        raw_txs = DemoDataGenerator.generate_demo_transactions(months_back=months_back)
    else:
        target_mode = (
            biz.paypal_mode
            if biz.paypal_mode in ["live", "sandbox"]
            else getattr(settings, "PAYPAL_ENVIRONMENT", "sandbox")
        ).lower()

        client_id = (biz.paypal_client_id or settings.PAYPAL_CLIENT_ID or "").strip()
        client_secret = (biz.paypal_client_secret or settings.PAYPAL_CLIENT_SECRET or "").strip()

        client = PayPalClient(
            mode=target_mode,
            client_id=client_id,
            client_secret=client_secret
        )

        if not client.has_credentials:
            raise HTTPException(
                status_code=400,
                detail=f"PayPal {target_mode.upper()} Client ID and Secret are not configured. "
                       f"Please configure your credentials in backend/.env or Integration Settings."
            )

        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days_back)
        try:
            raw_txs = client.fetch_transactions(start_date=start_date, end_date=end_date)
        except PayPalAuthenticationError as e:
            raise HTTPException(status_code=401, detail=f"PayPal OAuth Authentication Failed: {e.message}")
        except PayPalPermissionError as e:
            raise HTTPException(
                status_code=403,
                detail=f"PayPal Permission Denied (HTTP 403): {e.message} "
                       f"Action required: Go to developer.paypal.com > Apps & Credentials > your Sandbox App > "
                       f"App Feature Options, and check the box for 'Transaction Search' / 'Reporting'."
            )
        except PayPalError as e:
            raise HTTPException(status_code=502, detail=f"PayPal API Error: {e.message}")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to fetch from PayPal {target_mode.upper()} API: {str(e)}")

    # Duplicate Prevention: Fetch existing transactions for this business
    existing_records = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    existing_by_paypal_id = {
        tx.paypal_transaction_id: tx for tx in existing_records if tx.paypal_transaction_id
    }
    existing_by_sig = {
        (tx.transaction_date.strftime("%Y-%m-%d"), round(tx.gross_amount, 2), tx.raw_description): tx
        for tx in existing_records
    }

    added_count = 0
    updated_count = 0
    skipped_count = 0

    for item in raw_txs:
        meta = TransactionNormalizer.normalize_vendor_and_category(item["raw_description"])
        paypal_id = item.get("paypal_transaction_id")
        tx_date = item["transaction_date"]
        gross = float(item["gross_amount"])
        fee = float(item.get("fee_amount", 0.0))
        net = float(item.get("net_amount", round(gross + fee, 2)))
        raw_desc = item["raw_description"]
        currency = item.get("currency", "USD")
        status = item.get("status", "COMPLETED")

        # Check existing by paypal_id
        match = None
        if paypal_id and paypal_id in existing_by_paypal_id:
            match = existing_by_paypal_id[paypal_id]
        else:
            sig = (tx_date.strftime("%Y-%m-%d"), round(gross, 2), raw_desc)
            if sig in existing_by_sig:
                match = existing_by_sig[sig]

        if match:
            # Update existing record if status or amounts changed
            changed = False
            if match.status != status:
                match.status = status
                changed = True
            if match.fee_amount != fee:
                match.fee_amount = fee
                changed = True
            if match.net_amount != net:
                match.net_amount = net
                changed = True
            if match.normalized_vendor != meta["normalized_vendor"]:
                match.normalized_vendor = meta["normalized_vendor"]
                changed = True
            if match.category != meta["category"]:
                match.category = meta["category"]
                changed = True
            if changed:
                updated_count += 1
            else:
                skipped_count += 1
        else:
            # Create new transaction
            tx = Transaction(
                business_id=biz.id,
                paypal_transaction_id=paypal_id,
                transaction_date=tx_date,
                raw_description=raw_desc,
                normalized_vendor=meta["normalized_vendor"],
                category=meta["category"],
                gross_amount=gross,
                fee_amount=fee,
                net_amount=net,
                currency=currency,
                status=status,
                data_source=target_mode
            )
            db.add(tx)
            added_count += 1
            if paypal_id:
                existing_by_paypal_id[paypal_id] = tx

    db.flush()

    # Retrieve all transactions for this environment for subscription detection
    all_biz_txs = get_environment_transactions(db=db, biz=biz, request=request, env=target_mode)

    # Trigger Subscription Identification Engine
    detected_subs = SubscriptionDetector.identify_subscriptions(all_biz_txs, biz.id)

    # Upsert Subscriptions
    existing_subs = {s.vendor_name.lower(): s for s in get_environment_subscriptions(db=db, biz=biz, request=request, env=target_mode)}
    active_sub_objs: List[Subscription] = []

    for sub_candidate in detected_subs:
        key = sub_candidate.vendor_name.lower()
        if key in existing_subs:
            existing = existing_subs[key]
            existing.average_amount = sub_candidate.average_amount
            existing.latest_amount = sub_candidate.latest_amount
            existing.price_change_pct = sub_candidate.price_change_pct
            existing.last_billed_date = sub_candidate.last_billed_date
            existing.next_billing_date = sub_candidate.next_billing_date
            existing.confidence_score = sub_candidate.confidence_score
            existing.detection_type = sub_candidate.detection_type
            existing.detection_reason = sub_candidate.detection_reason
            existing.billing_type = sub_candidate.billing_type
            active_sub_objs.append(existing)
        else:
            db.add(sub_candidate)
            active_sub_objs.append(sub_candidate)

    db.flush()

    # Trigger Recommendation Engine
    recs = RecommendationEngine.generate_recommendations(biz, active_sub_objs, all_biz_txs)
    # Refresh recommendations for active environment
    active_sub_ids = [s.id for s in active_sub_objs if s.id]
    if active_sub_ids:
        db.query(Recommendation).filter(
            Recommendation.business_id == biz.id,
            Recommendation.subscription_id.in_(active_sub_ids)
        ).delete(synchronize_session=False)
    for rec in recs:
        db.add(rec)

    # Update business profile metadata
    biz.last_synced_at = datetime.datetime.utcnow()
    biz.paypal_mode = target_mode
    biz.paypal_connected = True
    db.commit()

    total_active_txs = len(all_biz_txs)
    msg = (
        f"Successfully synchronized with PayPal ({target_mode.upper()} mode). "
        f"{added_count} new transactions added, {updated_count} updated. "
        f"{len(active_sub_objs)} recurring subscriptions tracked."
    )

    return {
        "status": "success",
        "data_source": target_mode,
        "transactions_synced": total_active_txs,
        "new_subscriptions_identified": len(active_sub_objs),
        "transactions_added": added_count,
        "transactions_updated": updated_count,
        "transactions_skipped": skipped_count,
        "message": msg,
        "synced_at": biz.last_synced_at
    }
