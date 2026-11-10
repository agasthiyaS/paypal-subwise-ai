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
from app.schemas.consumer_intelligence import (
    UnifiedFinancialIntelligence,
    SpendingAnalysisResult,
    ExplainableHealthScore,
    MultiScenarioForecast,
    ActionableSavingsRecommendation
)
from app.services.auth_service import get_current_user
from app.services.financial_intelligence_engine import FinancialIntelligenceEngine
from app.services.smart_spending_service import SmartSpendingService
from app.services.financial_health_service import FinancialHealthService
from app.services.multi_scenario_forecast_service import MultiScenarioForecastService
from app.services.consumer_recommendation_engine import ConsumerRecommendationEngine
from app.services.business_service import (
    get_active_business,
    get_environment_subscriptions,
    get_environment_transactions,
)

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

    subs = get_environment_subscriptions(db=db, biz=biz, request=request)
    txns = get_environment_transactions(db=db, biz=biz, request=request)

    return FinancialIntelligenceEngine.generate_overview(
        business=biz,
        subscriptions=subs,
        transactions=txns,
    )


@router.get("/unified", response_model=UnifiedFinancialIntelligence)
def get_unified_financial_intelligence(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns unified financial intelligence for Personal, Household, and SMB users:
    - Smart Spending Analysis with MoM changes and spike alerts
    - Explainable 4-Factor Financial Health Score
    - 30/60/90 Day Multi-Scenario Forecast (Baseline, Conservative, Optimistic)
    - Actionable Savings Directives without false assumptions
    """
    biz = get_active_business(current_user=current_user, db=db, request=request)
    subs = get_environment_subscriptions(db=db, biz=biz, request=request)

    spending = SmartSpendingService.analyze_spending(business=biz, db=db)
    health = FinancialHealthService.calculate_health_score(business=biz, analysis=spending, db=db)
    forecast = MultiScenarioForecastService.generate_forecast(business=biz, analysis=spending)
    recs = ConsumerRecommendationEngine.generate_recommendations(business=biz, analysis=spending, subscriptions=subs, db=db)

    total_m_save = sum(r.monthly_savings for r in recs)
    total_a_save = sum(r.annual_savings for r in recs)

    return UnifiedFinancialIntelligence(
        account_type=biz.account_type or "individual",
        company_or_family_name=biz.company_name or "Personal Account",
        spending_analysis=spending,
        health_score=health,
        forecast=forecast,
        recommendations=recs,
        total_potential_monthly_savings=round(total_m_save, 2),
        total_potential_annual_savings=round(total_a_save, 2),
    )


@router.get("/spending-analysis", response_model=SpendingAnalysisResult)
def get_spending_analysis(
    month: int = None,
    year: int = None,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    return SmartSpendingService.analyze_spending(business=biz, db=db, month=month, year=year)


@router.get("/health-score", response_model=ExplainableHealthScore)
def get_financial_health_score(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    spending = SmartSpendingService.analyze_spending(business=biz, db=db)
    return FinancialHealthService.calculate_health_score(business=biz, analysis=spending, db=db)


@router.get("/forecast-scenarios", response_model=MultiScenarioForecast)
def get_multi_scenario_forecast(
    days: int = 90,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    spending = SmartSpendingService.analyze_spending(business=biz, db=db)
    return MultiScenarioForecastService.generate_forecast(business=biz, analysis=spending, days=days)
