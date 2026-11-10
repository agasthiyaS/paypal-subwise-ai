"""
Stage 5: Financial Intelligence API Router
GET /api/v1/financial-intelligence
Returns a comprehensive financial intelligence overview for the authenticated business.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.schemas.financial_intelligence import FinancialIntelligenceOverview
from app.services.auth_service import get_current_user
from app.services.financial_intelligence_engine import FinancialIntelligenceEngine
from app.services.business_service import get_active_business

router = APIRouter(prefix="/financial-intelligence", tags=["Financial Intelligence"])


@router.get("", response_model=FinancialIntelligenceOverview)
def get_financial_intelligence_overview(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns a complete financial intelligence overview for the authenticated user's
    active business profile (Real Sandbox or Isolated Demo).
    """
    biz = get_active_business(current_user=current_user, db=db, request=request)

    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()

    return FinancialIntelligenceEngine.generate_overview(
        business=biz,
        subscriptions=subs,
        transactions=txns,
    )
