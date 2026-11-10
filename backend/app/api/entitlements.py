from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.business_service import get_active_business
from app.services.entitlement_service import EntitlementService

router = APIRouter(prefix="/entitlements", tags=["Entitlements & Monetization"])


@router.get("")
def get_user_entitlements(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns user and business tier entitlements and active feature limits.
    """
    try:
        biz = get_active_business(current_user=current_user, db=db, request=request)
    except Exception:
        biz = None
    return EntitlementService.get_entitlements(user=current_user, business=biz)
