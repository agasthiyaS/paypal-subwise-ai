import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationResponse,
    RecommendationUpdate,
    PurchaseSimulationRequest,
    PurchaseSimulationResponse
)
from app.services.auth_service import get_current_user
from app.services.recommendation_engine import RecommendationEngine
from app.services.business_service import get_active_business

logger = logging.getLogger("subwise_ai.api.recommendations")

router = APIRouter(prefix="/recommendations", tags=["Recommendations & AI"])

@router.get("/", response_model=List[RecommendationResponse])
def get_recommendations(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    existing = db.query(Recommendation).filter(Recommendation.business_id == biz.id).order_by(Recommendation.potential_annual_saving.desc()).all()
    if not existing:
        subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()
        if subs:
            txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
            recs = RecommendationEngine.generate_recommendations(biz, subs, txns)
            for r in recs:
                db.add(r)
            db.commit()
            existing = db.query(Recommendation).filter(Recommendation.business_id == biz.id).order_by(Recommendation.potential_annual_saving.desc()).all()

    return existing

@router.post("/generate", response_model=List[RecommendationResponse])
def generate_recommendations(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()

    recs = RecommendationEngine.generate_recommendations(biz, subs, txns)
    db.query(Recommendation).filter(Recommendation.business_id == biz.id).delete()
    for r in recs:
        db.add(r)
    db.commit()

    return db.query(Recommendation).filter(Recommendation.business_id == biz.id).order_by(Recommendation.potential_annual_saving.desc()).all()

@router.post("/simulate-purchase", response_model=PurchaseSimulationResponse)
def simulate_purchase(
    payload: PurchaseSimulationRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Evaluates affordability and liquidity impact for a proposed subscription purchase.
    Uses calendar-aware forward cash flow and verified baseline data.
    """
    biz = get_active_business(current_user=current_user, db=db, request=request)

    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()

    return RecommendationEngine.simulate_purchase(biz, subs, txns, payload)

@router.patch("/{rec_id}", response_model=RecommendationResponse)
def update_recommendation(
    rec_id: int,
    payload: RecommendationUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    rec = db.query(Recommendation).filter(Recommendation.id == rec_id, Recommendation.business_id == biz.id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")

    rec.status = payload.status
    db.commit()
    db.refresh(rec)
    return rec

@router.get("/ai-briefing")
def get_ai_briefing(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    subs = db.query(Subscription).filter(Subscription.business_id == biz.id, Subscription.status != "cancelled").all()
    recs = db.query(Recommendation).filter(Recommendation.business_id == biz.id, Recommendation.status == "pending").all()

    total_monthly = sum(s.latest_amount for s in subs)
    savings = sum(r.potential_monthly_saving for r in recs)
    
    # Runway calculation
    net_burn = max(1.0, total_monthly + (biz.monthly_baseline_revenue * 0.45) - biz.monthly_baseline_revenue)
    current_runway = round(biz.current_cash_reserves / net_burn, 1)
    extended_runway = round(biz.current_cash_reserves / max(1.0, net_burn - savings), 1)

    bullets = [
        f"Tracking {len(subs)} active software subscriptions totaling ${total_monthly:,.2f}/month.",
        f"Identified {len(recs)} optimization opportunities that could recover ${savings:,.2f}/month (${savings*12:,.2f}/year).",
        f"Applying these recommendations could extend your cash runway from {current_runway} to {extended_runway} months (+{round(extended_runway - current_runway, 1)} months buffer)."
    ]

    return {
        "status": "ready",
        "company_name": biz.company_name,
        "executive_summary": " ".join(bullets),
        "executive_briefing": " ".join(bullets),
        "key_takeaways": bullets,
        "potential_monthly_savings": savings,
        "potential_annual_savings": savings * 12.0,
        "current_runway_months": current_runway,
        "runway_months": current_runway,
        "projected_runway_months": extended_runway
    }
