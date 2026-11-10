import datetime
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.webhook_event import WebhookEvent
from app.services.auth_service import get_current_admin_user

router = APIRouter(prefix="/admin", tags=["Admin Portal"])


class AdminStatsResponse(BaseModel):
    total_users: int
    account_types: Dict[str, int]
    connected_paypals: int
    total_transactions: int
    total_subscriptions: int
    webhook_health: Dict[str, int]
    system_status: str
    timestamp: str


@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_platform_stats(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns platform-wide operations and metrics. Strictly protected by admin privileges.
    """
    total_users = db.query(User).count()

    # Account types breakdown
    account_type_counts = (
        db.query(BusinessProfile.account_type, func.count(BusinessProfile.id))
        .filter(BusinessProfile.is_demo == False)
        .group_by(BusinessProfile.account_type)
        .all()
    )
    account_types = {"individual": 0, "household": 0, "business": 0}
    for acct_type, count in account_type_counts:
        key = acct_type or "business"
        account_types[key] = count

    connected_paypals = (
        db.query(BusinessProfile)
        .filter(
            BusinessProfile.is_demo == False,
            BusinessProfile.paypal_connected == True
        )
        .count()
    )

    total_transactions = db.query(Transaction).count()
    total_subscriptions = db.query(Subscription).count()

    total_webhooks = db.query(WebhookEvent).count()
    verified_webhooks = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.verification_status == "verified")
        .count()
    )
    failed_webhooks = (
        db.query(WebhookEvent)
        .filter(WebhookEvent.status.in_(["failed", "rejected"]))
        .count()
    )

    return AdminStatsResponse(
        total_users=total_users,
        account_types=account_types,
        connected_paypals=connected_paypals,
        total_transactions=total_transactions,
        total_subscriptions=total_subscriptions,
        webhook_health={
            "total_received": total_webhooks,
            "verified": verified_webhooks,
            "failed_or_rejected": failed_webhooks,
        },
        system_status="HEALTHY",
        timestamp=datetime.datetime.utcnow().isoformat(),
    )


@router.get("/users")
def get_admin_users(
    limit: int = 50,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Returns system users overview for administration.
    """
    users = db.query(User).order_by(User.id.asc()).limit(limit).all()
    result = []
    for u in users:
        primary_biz = db.query(BusinessProfile).filter_by(user_id=u.id, is_demo=False).first()
        result.append({
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "is_admin": bool(getattr(u, "is_admin", False)),
            "account_type": primary_biz.account_type if primary_biz else "unconfigured",
            "company_name": primary_biz.company_name if primary_biz else "None",
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return result


@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    is_admin: bool,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Promotes or demotes user admin privileges.
    """
    target = db.query(User).filter_by(id=user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_admin = is_admin
    db.commit()
    return {"message": f"User {target.email} is_admin updated to {is_admin}"}

