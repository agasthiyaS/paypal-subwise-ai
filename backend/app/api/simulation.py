from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.schemas.simulation import SimulationRequest, SimulationResult
from app.services.auth_service import get_current_user
from app.services.cashflow_simulator import CashFlowSimulator
from app.services.business_service import get_active_business

router = APIRouter(prefix="/simulation", tags=["Cash Flow Simulation"])

@router.post("/run", response_model=SimulationResult)
def run_simulation(
    payload: SimulationRequest,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    result = CashFlowSimulator.run_simulation(
        business=biz,
        subscriptions=subs,
        revenue_shock_pct=payload.revenue_shock_pct,
        paused_subscription_ids=payload.paused_subscription_ids,
        pause_tier_3=payload.pause_tier_3_discretionary,
        additional_monthly_burn=payload.additional_monthly_burn,
        projection_months=12
    )
    return result
