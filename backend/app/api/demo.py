"""
Stage 8.5: Demo Environment API Router
Endpoints to check demo status, generate reproducible demo data,
reset demo data safely, and switch between Real Sandbox and Demo profiles.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.services.auth_service import get_current_user
from app.services.demo_data_generator import DemoDataGenerator
from app.services.business_service import get_active_business, switch_active_business

router = APIRouter(prefix="/demo", tags=["Demo Environment"])


class SwitchModeRequest(BaseModel):
    mode: str  # 'demo' or 'sandbox'


@router.get("/status")
def get_demo_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current demo environment status, active business profile mode,
    and dataset metrics.
    """
    demo_biz = (
        db.query(BusinessProfile)
        .filter(
            BusinessProfile.user_id == current_user.id,
            BusinessProfile.is_demo == True,
        )
        .first()
    )

    std_biz = (
        db.query(BusinessProfile)
        .filter(
            BusinessProfile.user_id == current_user.id,
            BusinessProfile.is_demo == False,
        )
        .first()
    )

    active_is_demo = False
    if current_user.active_business_id:
        active_is_demo = bool(demo_biz and current_user.active_business_id == demo_biz.id)

    if not demo_biz:
        return {
            "demo_profile_exists": False,
            "active_mode": "sandbox" if not active_is_demo else "demo",
            "active_business_id": std_biz.id if std_biz else None,
            "active_company_name": std_biz.company_name if std_biz else "None",
            "transaction_count": 0,
            "subscription_count": 0,
            "is_demo_active": False,
        }

    tx_count = db.query(Transaction).filter(
        Transaction.business_id == demo_biz.id,
        Transaction.data_source == "demo_fixture"
    ).count()

    sub_count = db.query(Subscription).filter(
        Subscription.business_id == demo_biz.id
    ).count()

    return {
        "demo_profile_exists": True,
        "demo_business_id": demo_biz.id,
        "demo_company_name": demo_biz.company_name,
        "active_mode": "demo" if active_is_demo else "sandbox",
        "active_business_id": current_user.active_business_id or (demo_biz.id if active_is_demo else (std_biz.id if std_biz else demo_biz.id)),
        "active_company_name": demo_biz.company_name if active_is_demo else (std_biz.company_name if std_biz else demo_biz.company_name),
        "is_demo_active": active_is_demo,
        "transaction_count": tx_count,
        "subscription_count": sub_count,
        "starting_cash": demo_biz.current_cash_reserves,
        "currency": demo_biz.currency,
    }


@router.post("/generate")
def generate_demo_dataset(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a realistic 6-month historical dataset for DemoTech Solutions.
    Switches active profile to Demo mode.
    """
    res = DemoDataGenerator.generate_demo_dataset(user_id=current_user.id, db=db)
    # Switch active business to demo
    current_user.active_business_id = res["business_id"]
    db.commit()

    return {
        "status": "success",
        "message": "Realistic 6-month demo dataset successfully generated for DemoTech Solutions.",
        "active_mode": "demo",
        **res,
    }


@router.post("/reset")
def reset_demo_dataset(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Safely resets and regenerates the demo dataset for DemoTech Solutions.
    Safety guarantee: NEVER deletes real sandbox transactions.
    """
    demo_biz = (
        db.query(BusinessProfile)
        .filter(
            BusinessProfile.user_id == current_user.id,
            BusinessProfile.is_demo == True,
        )
        .first()
    )
    if not demo_biz:
        demo_biz = DemoDataGenerator.ensure_demo_business(user_id=current_user.id, db=db)

    res = DemoDataGenerator.generate_demo_dataset(user_id=current_user.id, db=db)
    current_user.active_business_id = demo_biz.id
    db.commit()

    return {
        "status": "success",
        "message": "Demo data safely reset to initial reproducible baseline.",
        "active_mode": "demo",
        **res,
    }


@router.post("/switch")
def switch_environment_mode(
    payload: SwitchModeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Switches the user's active business profile between:
    - 'demo' (DemoTech Solutions, isolated simulated records)
    - 'sandbox' / 'standard' (Real connected PayPal sandbox account)
    """
    biz = switch_active_business(user=current_user, db=db, mode=payload.mode)

    return {
        "status": "success",
        "active_mode": "demo" if biz.is_demo else "sandbox",
        "active_business_id": biz.id,
        "company_name": biz.company_name,
        "is_demo": biz.is_demo,
        "currency": biz.currency,
    }

