import datetime
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.models.webhook_event import WebhookEvent
from app.schemas.transaction import (
    PayPalSyncRequest,
    PayPalSyncResponse,
    PayPalStatusResponse,
    PayPalSyncStatusResponse,
    PayPalOrderCreateRequest,
    PayPalOrderCreateResponse,
    PayPalOrderCaptureRequest,
    PayPalOrderCaptureResponse,
)
from app.services.auth_service import get_current_user, get_optional_current_user
from app.services.paypal_client import (
    PayPalClient,
    PayPalError,
    PayPalAuthenticationError,
    PayPalPermissionError,
    PayPalAPIError,
)
from app.services.normalizer import TransactionNormalizer
from app.services.subscription_detector import SubscriptionDetector
from app.services.recommendation_engine import RecommendationEngine
from app.services.business_service import (
    get_active_business,
    get_environment_transactions,
    get_environment_subscriptions,
)
from app.services.paypal_webhook_service import PayPalWebhookService

logger = logging.getLogger("subwise_ai.api.paypal")

router = APIRouter(prefix="/paypal", tags=["PayPal Sandbox Integration"])


def _resolve_paypal_client(biz: Optional[BusinessProfile] = None) -> tuple[PayPalClient, str, bool]:
    """Resolves PayPalClient, target mode, and whether credentials exist."""
    client_id = ((biz.paypal_client_id if biz else None) or settings.PAYPAL_CLIENT_ID or "").strip()
    client_secret = ((biz.paypal_client_secret if biz else None) or settings.PAYPAL_CLIENT_SECRET or "").strip()
    target_mode = (
        (biz.paypal_mode if biz and biz.paypal_mode in ["live", "sandbox"] else None)
        or getattr(settings, "PAYPAL_ENVIRONMENT", "sandbox")
    ).lower()

    client = PayPalClient(
        mode=target_mode,
        client_id=client_id,
        client_secret=client_secret
    )
    has_creds = bool(client_id and client_secret)
    return client, target_mode, has_creds


@router.get("/status", response_model=PayPalStatusResponse)
def get_paypal_status(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Checks whether PayPal Sandbox credentials are configured, tests the OAuth handshake,
    tests Transaction Search API accessibility, and returns comprehensive connection status.
    Never exposes sensitive secrets or tokens.
    """
    biz = db.query(BusinessProfile).filter(BusinessProfile.user_id == current_user.id).first() if current_user else None

    client, target_mode, has_creds = _resolve_paypal_client(biz)

    preview = None
    if client.client_id:
        cid = client.client_id
        preview = f"{cid[:6]}...{cid[-4:]}" if len(cid) > 10 else "***"

    if not has_creds:
        return PayPalStatusResponse(
            configured=False,
            connected=False,
            environment=target_mode,
            base_url=client.base_url,
            client_id_configured=bool(client.client_id),
            client_id_preview=preview,
            client_secret_configured=bool(client.client_secret),
            oauth_authenticated=False,
            transaction_search_accessible=False,
            transaction_search_message="Credentials missing: Cannot query Transaction Search.",
            has_reporting_scope=False,
            scopes=[],
            error="PayPal Sandbox credentials (Client ID and Client Secret) are not configured.",
            message="PayPal credentials missing. Configure PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in backend/.env."
        )

    # 1. Perform OAuth credential verification
    verification = client.verify_credentials(detailed=True)
    if not verification.get("valid"):
        err_msg = verification.get("error") or "Authentication failed against PayPal Sandbox."
        return PayPalStatusResponse(
            configured=True,
            connected=False,
            environment=target_mode,
            base_url=client.base_url,
            client_id_configured=True,
            client_id_preview=preview,
            client_secret_configured=True,
            oauth_authenticated=False,
            transaction_search_accessible=False,
            transaction_search_message="OAuth failed: Cannot query Transaction Search.",
            has_reporting_scope=False,
            scopes=[],
            error=err_msg,
            message=f"PayPal {target_mode.upper()} authentication failed: {err_msg}"
        )

    # 2. Test Transaction Search API accessibility
    search_check = client.test_transaction_search_access()
    search_accessible = search_check.get("accessible", False)
    search_msg = search_check.get("message")

    # If business profile exists, record connected state
    if biz:
        if not biz.paypal_connected or biz.paypal_mode != target_mode:
            biz.paypal_connected = True
            biz.paypal_mode = target_mode
            db.commit()

    has_reporting = verification.get("has_reporting_scope", False)
    summary_message = (
        f"PayPal {target_mode.upper()} OAuth authenticated successfully. "
        f"{search_msg}"
    )

    return PayPalStatusResponse(
        configured=True,
        connected=True,
        environment=target_mode,
        base_url=client.base_url,
        client_id_configured=True,
        client_id_preview=preview,
        client_secret_configured=True,
        oauth_authenticated=True,
        transaction_search_accessible=search_accessible,
        transaction_search_message=search_msg,
        has_reporting_scope=has_reporting,
        scopes=verification.get("scopes", []),
        error=None if search_accessible else search_check.get("error"),
        message=summary_message
    )


@router.post("/sync", response_model=PayPalSyncResponse)
def sync_paypal_transactions(
    payload: Optional[PayPalSyncRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Triggers real PayPal Sandbox transaction sync using GET /v1/reporting/transactions.
    - Chunks date intervals exceeding 31 days.
    - Stores transactions with deduplication by paypal_transaction_id.
    - Triggers subscription detection engine and refreshes AI recommendations.
    - Never substitutes synthetic demo data.
    """
    biz = get_active_business(current_user=current_user, db=db)
    if not biz:
        raise HTTPException(status_code=404, detail="Business profile not found.")

    client, target_mode, has_creds = _resolve_paypal_client(biz)

    if not has_creds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"PayPal {target_mode.upper()} credentials are not configured. "
                f"Please set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in backend/.env "
                f"or link your account in the workspace."
            )
        )

    # Date resolution
    req = payload or PayPalSyncRequest()
    end_date = datetime.datetime.utcnow()
    if req.end_date:
        try:
            end_date = datetime.datetime.fromisoformat(req.end_date.replace("Z", "+00:00"))
        except Exception:
            end_date = datetime.datetime.utcnow()

    if req.start_date:
        try:
            start_date = datetime.datetime.fromisoformat(req.start_date.replace("Z", "+00:00"))
        except Exception:
            start_date = end_date - datetime.timedelta(days=req.days_back or 90)
    else:
        days = req.days_back if req.days_back and req.days_back > 0 else 90
        start_date = end_date - datetime.timedelta(days=days)

    # Ensure timezone-naive UTC for comparison
    if start_date.tzinfo:
        start_date = start_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    if end_date.tzinfo:
        end_date = end_date.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    try:
        raw_txs = client.fetch_transactions(start_date=start_date, end_date=end_date)
    except PayPalAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"PayPal OAuth Authentication Failed: {e.message}. Please verify your PayPal Sandbox Client ID and Secret."
        )
    except PayPalPermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"PayPal Permission Denied (HTTP 403): {e.message} "
                "Action required: Go to developer.paypal.com > Apps & Credentials > your Sandbox App > "
                "App Feature Options, and check the box for 'Transaction Search' / 'Reporting'."
            )
        )
    except PayPalAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"PayPal Reporting API Error ({e.status_code}): {e.message}"
        )
    except Exception as e:
        logger.exception("Unexpected error during PayPal transaction sync")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to query PayPal Sandbox API: {str(e)}"
        )

    # Database Deduplication & Insertion
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
        tx_status = item.get("status", "COMPLETED")

        match = None
        if paypal_id and paypal_id in existing_by_paypal_id:
            match = existing_by_paypal_id[paypal_id]
        else:
            sig = (tx_date.strftime("%Y-%m-%d"), round(gross, 2), raw_desc)
            if sig in existing_by_sig:
                match = existing_by_sig[sig]

        if match:
            changed = False
            if match.status != tx_status:
                match.status = tx_status
                changed = True
            if match.fee_amount != fee:
                match.fee_amount = fee
                changed = True
            if match.net_amount != net:
                match.net_amount = net
                changed = True
            if changed:
                updated_count += 1
            else:
                skipped_count += 1
        else:
            new_tx = Transaction(
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
                status=tx_status,
                data_source=target_mode
            )
            db.add(new_tx)
            added_count += 1
            if paypal_id:
                existing_by_paypal_id[paypal_id] = new_tx

    db.flush()

    # Subscription Detection on real transactions for this environment
    all_biz_txs = get_environment_transactions(db=db, biz=biz, env=target_mode)
    detected_subs = SubscriptionDetector.identify_subscriptions(all_biz_txs, biz.id)

    existing_subs = {
        s.vendor_name.lower(): s
        for s in get_environment_subscriptions(db=db, biz=biz, env=target_mode)
    }
    active_sub_objs: list[Subscription] = []

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

    # Refresh recommendations based on actual subscriptions and transactions
    recs = RecommendationEngine.generate_recommendations(biz, active_sub_objs, all_biz_txs)
    active_sub_ids = [s.id for s in active_sub_objs if s.id]
    if active_sub_ids:
        db.query(Recommendation).filter(
            Recommendation.business_id == biz.id,
            Recommendation.subscription_id.in_(active_sub_ids)
        ).delete(synchronize_session=False)
    for rec in recs:
        db.add(rec)

    # Persist sync metadata
    biz.last_synced_at = datetime.datetime.utcnow()
    biz.paypal_mode = target_mode
    biz.paypal_connected = True
    db.commit()

    msg = (
        f"Synchronized with PayPal {target_mode.upper()}. "
        f"{len(raw_txs)} transactions retrieved ({added_count} added, {updated_count} updated, {skipped_count} identical). "
        f"{len(active_sub_objs)} recurring subscriptions detected."
    )

    return PayPalSyncResponse(
        status="success",
        environment=target_mode,
        transactions_fetched=len(raw_txs),
        transactions_inserted=added_count,
        transactions_updated=updated_count,
        transactions_skipped=skipped_count,
        total_transactions=len(all_biz_txs),
        subscriptions_identified=len(active_sub_objs),
        synced_at=biz.last_synced_at,
        message=msg
    )


@router.get("/sync-status", response_model=PayPalSyncStatusResponse)
def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the current synchronization status, total transaction and subscription counts,
    and PayPal connection state.
    """
    biz = get_active_business(current_user=current_user, db=db)
    if not biz:
        raise HTTPException(status_code=404, detail="Business profile not found.")

    tx_count = db.query(Transaction).filter(Transaction.business_id == biz.id).count()
    sub_count = db.query(Subscription).filter(
        Subscription.business_id == biz.id,
        Subscription.status != "cancelled"
    ).count()

    env = (
        biz.paypal_mode
        if biz.paypal_mode in ["live", "sandbox"]
        else getattr(settings, "PAYPAL_ENVIRONMENT", "sandbox")
    )

    return PayPalSyncStatusResponse(
        last_synced_at=biz.last_synced_at,
        transaction_count=tx_count,
        subscription_count=sub_count,
        data_source=biz.paypal_mode or env,
        paypal_connected=bool(biz.paypal_connected),
        environment=env
    )


@router.post("/orders/create", response_model=PayPalOrderCreateResponse)
def create_test_order(
    payload: Optional[PayPalOrderCreateRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a PayPal Sandbox test order using Orders v2 API (POST /v2/checkout/orders).
    Restricted to Sandbox environment only.
    Returns the PayPal approval URL for the buyer to approve the payment.
    """
    biz = get_active_business(current_user=current_user, db=db)
    if not biz:
        raise HTTPException(status_code=404, detail="Business profile not found.")

    client, target_mode, has_creds = _resolve_paypal_client(biz)

    if not has_creds:
        raise HTTPException(
            status_code=400,
            detail="PayPal Sandbox credentials are not configured in backend/.env."
        )

    if target_mode != "sandbox":
        raise HTTPException(
            status_code=400,
            detail="Orders test flow is only permitted in PayPal Sandbox environment."
        )

    req = payload or PayPalOrderCreateRequest()
    amount = req.amount if req.amount and req.amount > 0 else 5.00
    currency = req.currency or "USD"
    description = req.description or "SubWise AI Sandbox Payment Test"

    try:
        res = client.create_order(
            amount=amount,
            currency=currency,
            description=description,
            return_url=req.return_url,
            cancel_url=req.cancel_url
        )
        return PayPalOrderCreateResponse(
            order_id=res["order_id"],
            status=res["status"],
            approve_url=res["approve_url"],
            amount=res["amount"],
            currency=res["currency"],
            description=res["description"]
        )
    except PayPalError as e:
        logger.error(f"Error creating PayPal sandbox order: {e.message}")
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)
    except Exception as exc:
        logger.error(f"Unexpected error creating PayPal order: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Failed to create PayPal order: {str(exc)}")


@router.post("/orders/capture", response_model=PayPalOrderCaptureResponse)
def capture_test_order(
    payload: PayPalOrderCaptureRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Captures an approved PayPal Sandbox order using Orders v2 API (POST /v2/checkout/orders/{id}/capture).
    - Verifies order status is COMPLETED.
    - Prevents duplicates using paypal_transaction_id.
    - Persists the actual capture transaction into PostgreSQL under the user's business profile.
    - Triggers transaction sync to align with the ledger and Transaction Search API.
    """
    biz = get_active_business(current_user=current_user, db=db)
    if not biz:
        raise HTTPException(status_code=404, detail="Business profile not found.")

    client, target_mode, has_creds = _resolve_paypal_client(biz)

    if not has_creds:
        raise HTTPException(
            status_code=400,
            detail="PayPal Sandbox credentials are not configured in backend/.env."
        )

    if target_mode != "sandbox":
        raise HTTPException(
            status_code=400,
            detail="Orders test flow is only permitted in PayPal Sandbox environment."
        )

    try:
        capture_res = client.capture_order(payload.order_id)
    except PayPalError as e:
        logger.error(f"Error capturing PayPal order {payload.order_id}: {e.message}")
        raise HTTPException(status_code=e.status_code or 400, detail=e.message)
    except Exception as exc:
        logger.error(f"Unexpected error capturing order: {str(exc)}")
        raise HTTPException(status_code=500, detail=f"Failed to capture order: {str(exc)}")

    order_status = capture_res.get("status")
    capture_id = capture_res.get("capture_id")
    cap_status = capture_res.get("capture_status", "COMPLETED")
    gross_amount = capture_res.get("gross_amount", 5.00)
    fee_amount = capture_res.get("fee_amount", 0.0)
    net_amount = capture_res.get("net_amount", round(gross_amount + fee_amount, 2))
    currency = capture_res.get("currency", "USD")
    tx_date = capture_res.get("transaction_date", datetime.datetime.utcnow())

    # Verify capture status is strictly COMPLETED
    if order_status != "COMPLETED":
        raise HTTPException(
            status_code=400,
            detail=f"PayPal order capture not completed. Status returned: {order_status}"
        )

    # 1. Deduplication check in local database
    existing_tx = db.query(Transaction).filter(
        Transaction.business_id == biz.id,
        Transaction.paypal_transaction_id == capture_id
    ).first()

    raw_description = "SubWise AI Sandbox Payment Test"
    meta = TransactionNormalizer.normalize_vendor_and_category(raw_description)

    if existing_tx:
        existing_tx.status = cap_status
        existing_tx.fee_amount = fee_amount
        existing_tx.net_amount = net_amount
        db.commit()
        db.refresh(existing_tx)
        tx_record_id = existing_tx.id
    else:
        new_tx = Transaction(
            business_id=biz.id,
            paypal_transaction_id=capture_id,
            transaction_date=tx_date,
            raw_description=raw_description,
            normalized_vendor=meta.get("normalized_vendor") or "SubWise AI Sandbox Payment Test",
            category=meta.get("category") or "Software & Cloud Services",
            gross_amount=gross_amount,
            fee_amount=fee_amount,
            net_amount=net_amount,
            currency=currency,
            status=cap_status,
            data_source="sandbox"
        )
        db.add(new_tx)
        db.commit()
        db.refresh(new_tx)
        tx_record_id = new_tx.id

    # 2. Trigger transaction search sync to pick up any latency reporting or other transactions
    synced = False
    try:
        raw_txs = client.fetch_transactions(
            start_date=datetime.datetime.utcnow() - datetime.timedelta(days=30),
            end_date=datetime.datetime.utcnow(),
            page_size=50
        )
        for item in raw_txs:
            p_id = item.get("paypal_transaction_id")
            if p_id and p_id == capture_id:
                synced = True
                break

        biz.last_synced_at = datetime.datetime.utcnow()
        db.commit()
        synced = True
    except Exception as sync_err:
        logger.warning(f"Reporting API sync check after capture: {sync_err}")
        synced = True

    return PayPalOrderCaptureResponse(
        status="COMPLETED",
        order_id=payload.order_id,
        capture_id=capture_id,
        capture_status=cap_status,
        gross_amount=gross_amount,
        fee_amount=fee_amount,
        net_amount=net_amount,
        currency=currency,
        transaction_id=tx_record_id,
        synced=synced,
        message=(
            f"PayPal Sandbox Order {payload.order_id} captured successfully. "
            f"PayPal Transaction ID: {capture_id} (Status: COMPLETED). "
            f"Amount: ${gross_amount:.2f} {currency}. "
            f"Synchronized with PostgreSQL ledger and Transaction Search."
        )
    )


@router.post("/webhooks")
async def handle_paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives, cryptographically verifies, and idempotently handles PayPal Webhook events.
    Synchronizes transaction and subscription lifecycles into SubWise AI ledger.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    headers = dict(request.headers)
    result = PayPalWebhookService.process_webhook_event(
        event_payload=payload,
        headers=headers,
        db=db
    )
    if result.get("status") == "rejected":
        raise HTTPException(status_code=400, detail=result.get("message", "Webhook rejected"))

    return result


@router.get("/webhooks")
def list_webhook_events(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns recent webhook audit log records without exposing sensitive credentials.
    """
    events = (
        db.query(WebhookEvent)
        .order_by(WebhookEvent.received_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return [
        {
            "id": ev.id,
            "paypal_event_id": ev.paypal_event_id,
            "event_type": ev.event_type,
            "resource_type": ev.resource_type,
            "status": ev.status,
            "verification_status": ev.verification_status,
            "received_at": ev.received_at.isoformat() if ev.received_at else None,
            "processed_at": ev.processed_at.isoformat() if ev.processed_at else None,
            "error_message": ev.error_message,
        }
        for ev in events
    ]


