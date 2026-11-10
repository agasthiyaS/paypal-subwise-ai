import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.schemas.business import BusinessProfileUpdate, BusinessProfileResponse, PayPalConnectRequest
from app.services.auth_service import get_current_user
from app.services.paypal_client import PayPalClient, PayPalAuthenticationError, PayPalPermissionError, PayPalError
from app.services.business_service import get_active_business, get_all_user_businesses, switch_active_business

logger = logging.getLogger("subwise_ai.api.business")

router = APIRouter(prefix="/business", tags=["Business Profile"])


class SwitchProfileRequest(BaseModel):
    mode: str  # 'demo' or 'sandbox'


@router.get("/profile", response_model=BusinessProfileResponse)
def get_profile(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    
    # Compute total transactions count for this specific profile
    tx_count = db.query(Transaction).filter(Transaction.business_id == biz.id).count()
    biz.total_transactions = tx_count
    return biz


@router.get("/profiles", response_model=List[BusinessProfileResponse])
def get_profiles(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all businesses owned by user (Standard Sandbox and Isolated Demo)."""
    businesses = get_all_user_businesses(user=current_user, db=db)
    for b in businesses:
        b.total_transactions = db.query(Transaction).filter(Transaction.business_id == b.id).count()
    return businesses


@router.post("/switch-profile", response_model=BusinessProfileResponse)
def switch_profile(
    payload: SwitchProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Switches active business between Sandbox and Demo."""
    biz = switch_active_business(user=current_user, db=db, mode=payload.mode)
    biz.total_transactions = db.query(Transaction).filter(Transaction.business_id == biz.id).count()
    return biz


@router.put("/profile", response_model=BusinessProfileResponse)
def update_profile(
    payload: BusinessProfileUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    for field, val in payload.dict(exclude_unset=True).items():
        setattr(biz, field, val)

    db.commit()
    db.refresh(biz)
    biz.total_transactions = db.query(Transaction).filter(Transaction.business_id == biz.id).count()
    return biz


@router.post("/paypal-connect")
def connect_paypal(
    payload: PayPalConnectRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    mode = payload.paypal_mode.lower()
    if mode not in ["live", "sandbox", "demo"]:
        raise HTTPException(status_code=400, detail="Invalid PayPal mode. Must be 'live', 'sandbox', or 'demo'.")

    # If demo mode, seamlessly switch without credentials
    if mode == "demo":
        biz.paypal_mode = "demo"
        biz.paypal_connected = True
        db.commit()
        db.refresh(biz)
        return {
            "status": "connected",
            "mode": "demo",
            "message": "Connected in Demonstration mode with verified test stream.",
            "paypal_connected": True
        }

    # For live or sandbox, validate credentials
    client_id = (payload.paypal_client_id or "").strip()
    client_secret = (payload.paypal_client_secret or "").strip()

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail=f"Both Client ID and Secret are required to connect PayPal in {mode.upper()} mode."
        )

    client = PayPalClient(mode=mode, client_id=client_id, client_secret=client_secret)
    verification = client.verify_credentials(detailed=True)

    if not verification["valid"]:
        error_msg = verification.get("error") or "Authentication failed."
        raise HTTPException(
            status_code=400,
            detail=f"Could not authenticate with PayPal {mode.upper()}: {error_msg}"
        )

    # Store encrypted or isolated credentials on business profile
    biz.paypal_client_id = client_id
    biz.paypal_client_secret = client_secret
    biz.paypal_mode = mode
    biz.paypal_connected = True
    db.commit()
    db.refresh(biz)

    return {
        "status": "connected",
        "mode": mode,
        "message": f"Successfully authenticated and linked PayPal {mode.upper()} account.",
        "paypal_connected": True,
        "has_reporting_scope": verification.get("has_reporting_scope", False),
        "scopes": verification.get("scopes", [])
    }


@router.post("/paypal-disconnect")
def disconnect_paypal(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    biz.paypal_connected = False
    biz.paypal_mode = "demo"
    biz.paypal_client_id = None
    biz.paypal_client_secret = None
    db.commit()
    db.refresh(biz)

    return {
        "status": "disconnected",
        "mode": "demo",
        "message": "PayPal integration disconnected. Switched to demo mode.",
        "paypal_connected": False
    }
