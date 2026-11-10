from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.schemas.vendor_comparison import (
    VendorComparisonItem,
    SavingsDiscoverySummary
)
from app.services.auth_service import get_current_user
from app.services.business_service import (
    get_active_business,
    get_environment_subscriptions
)
from app.services.vendor_comparison_service import VendorComparisonService

router = APIRouter(prefix="/savings-discovery", tags=["Smart Savings Discovery"])

@router.get("", response_model=SavingsDiscoverySummary)
def get_personalized_savings_opportunities(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns personalized vendor and subscription alternatives ranked by potential savings,
    calculated against the user's active subscriptions and expense commitments.
    """
    biz = get_active_business(current_user=current_user, db=db, request=request)
    subs = get_environment_subscriptions(db=db, biz=biz, request=request)
    sub_names = [s.vendor_name for s in subs if s.vendor_name]

    return VendorComparisonService.match_user_opportunities(subscription_names=sub_names)

@router.get("/catalog", response_model=List[VendorComparisonItem])
def get_vendor_comparison_catalog():
    """
    Returns the complete verified market catalog of recurring service alternatives.
    """
    return VendorComparisonService.get_catalog()

@router.get("/search", response_model=List[VendorComparisonItem])
def search_vendor_alternatives(
    query: str = Query(..., min_length=2, description="Service, software, or category keyword"),
):
    """
    Searches available economical alternatives matching user keywords.
    """
    return VendorComparisonService.search_alternatives(query=query)

