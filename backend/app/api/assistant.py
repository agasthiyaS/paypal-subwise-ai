"""
Stage 7 & 8.5: Intelligent Financial Assistant API Router
Provides authenticated endpoints for:
- POST /api/v1/assistant/query: Evidence-grounded natural language Q&A.
- GET /api/v1/assistant/suggestions: Starter prompts tailored to data sufficiency status.
Supports both Real Sandbox and Isolated Demo profiles.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.schemas.assistant import (
    AssistantQueryRequest,
    AssistantQueryResponse,
    AssistantSuggestionsResponse,
)
from app.services.auth_service import get_current_user
from app.services.financial_assistant_engine import FinancialAssistantEngine
from app.services.business_service import (
    get_active_business,
    get_environment_subscriptions,
    get_environment_transactions,
)

router = APIRouter(prefix="/assistant", tags=["Financial Assistant"])


@router.post("/query", response_model=AssistantQueryResponse)
def query_financial_assistant(
    request: AssistantQueryRequest,
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submits a natural language query to the intelligent financial assistant.
    The response is grounded exclusively in the active business's ledger
    records, subscription commitments, and forecast models.

    Tenant Isolation: Queries are strictly filtered by current_user.id and active business.
    """
    biz = get_active_business(current_user=current_user, db=db, request=http_request)

    subscriptions = get_environment_subscriptions(db=db, biz=biz, request=http_request)
    transactions = get_environment_transactions(db=db, biz=biz, request=http_request)

    return FinancialAssistantEngine.process_query(
        business=biz,
        subscriptions=subscriptions,
        transactions=transactions,
        request=request,
    )


@router.get("/suggestions", response_model=AssistantSuggestionsResponse)
def get_assistant_suggestions(
    http_request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns starter conversation prompts dynamically tailored to whether the business
    has sufficient or insufficient operating data.
    """
    biz = get_active_business(current_user=current_user, db=db, request=http_request)

    subscriptions = get_environment_subscriptions(db=db, biz=biz, request=http_request)
    transactions = get_environment_transactions(db=db, biz=biz, request=http_request)

    return FinancialAssistantEngine.get_starter_suggestions(
        business=biz,
        subscriptions=subscriptions,
        transactions=transactions,
    )
