from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.recommendation import Recommendation
from app.schemas.subscription import (
    SubscriptionResponse,
    SubscriptionUpdate,
    SubscriptionSummaryResponse,
    SubscriptionAnalysisResponse
)
from app.services.auth_service import get_current_user
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer
from app.services.business_service import get_active_business

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

@router.get("/", response_model=SubscriptionSummaryResponse)
def get_subscriptions(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()
    
    active_subs = [s for s in subs if s.status != "cancelled"]
    monthly_spend = sum(
        (s.latest_amount / 12.0 if s.cadence == "annual" else s.latest_amount)
        for s in active_subs
    )
    annual_spend = monthly_spend * 12.0

    zombies = [s for s in active_subs if s.status == "zombie"]
    at_risk = [s for s in active_subs if s.status == "at_risk" or s.price_change_pct >= 15.0]
    
    # Redundant tool groups
    group_counts = {}
    for s in active_subs:
        if s.redundancy_group:
            group_counts[s.redundancy_group] = group_counts.get(s.redundancy_group, 0) + 1
    redundant_count = sum(cnt for grp, cnt in group_counts.items() if cnt > 1)

    # Category distribution
    cat_spend = {}
    for s in active_subs:
        cat = s.category or "Other"
        equiv = s.latest_amount / 12.0 if s.cadence == "annual" else s.latest_amount
        cat_spend[cat] = cat_spend.get(cat, 0.0) + equiv
    categories = [{"category": c, "monthly_spend": round(amt, 2)} for c, amt in cat_spend.items()]

    potential_subs = [s for s in active_subs if s.detection_type == "potential"]
    confirmed_subs = [s for s in active_subs if s.detection_type == "confirmed"]

    recs = db.query(Recommendation).filter(Recommendation.business_id == biz.id).all()
    potential_savings = sum(r.potential_monthly_saving for r in recs)
    if not potential_savings and (zombies or at_risk):
        potential_savings = sum(s.latest_amount for s in zombies) + sum(s.latest_amount * 0.2 for s in at_risk)

    return {
        "total_active_count": len(active_subs),
        "active_subscriptions": len(active_subs),
        "total_monthly_spend": round(monthly_spend, 2),
        "total_annual_spend": round(annual_spend, 2),
        "total_annual_run_rate": round(annual_spend, 2),
        "zombie_count": len(zombies),
        "zombie_subscriptions": len(zombies),
        "at_risk_count": len(at_risk),
        "at_risk_subscriptions": len(at_risk),
        "redundant_tool_count": redundant_count,
        "redundant_tools_detected": redundant_count,
        "potential_monthly_savings": round(potential_savings, 2),
        "category_distribution": cat_spend,
        "potential_count": len(potential_subs),
        "confirmed_count": len(confirmed_subs),
        "subscriptions": subs
    }

@router.get("/analysis", response_model=SubscriptionAnalysisResponse)
def get_subscription_expense_analysis(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()

    return SubscriptionExpenseAnalyzer.analyze(subscriptions=subs, transactions=txns, currency="USD")


@router.patch("/{subscription_id}", response_model=SubscriptionResponse)
def update_subscription(
    subscription_id: int,
    payload: SubscriptionUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    sub = db.query(Subscription).filter(Subscription.id == subscription_id, Subscription.business_id == biz.id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")

    if payload.priority_tier is not None:
        sub.priority_tier = payload.priority_tier
    if payload.is_essential is not None:
        sub.is_essential = payload.is_essential
    if payload.status is not None:
        sub.status = payload.status

    db.commit()
    db.refresh(sub)
    return sub
