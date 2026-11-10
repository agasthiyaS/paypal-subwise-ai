from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.schemas.forecast import ForecastResponse
from app.services.auth_service import get_current_user
from app.services.forecast_engine import ForecastEngine
from app.services.business_service import (
    get_active_business,
    get_environment_subscriptions,
    get_environment_transactions,
)

router = APIRouter(prefix="/forecast", tags=["Cash Flow Forecast"])

@router.get("", response_model=ForecastResponse)
@router.get("/", response_model=ForecastResponse)
def get_cashflow_forecast(
    request: Request = None,
    months: int = Query(6, ge=1, le=24, description="Number of months to forecast"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    subs = get_environment_subscriptions(db=db, biz=biz, request=request)
    txns = get_environment_transactions(db=db, biz=biz, request=request)

    forecast_data = ForecastEngine.generate_forecast(
        business=biz,
        subscriptions=subs,
        transactions=txns,
        forecast_months=months
    )
    return forecast_data
