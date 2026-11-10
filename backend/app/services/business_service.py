"""
Stage 8.5: Business Profile Service & Active Profile Resolver
Provides unified tenant resolution supporting both Real Sandbox profiles
and isolated Demonstration profiles (DemoTech Solutions).
"""
import logging
from typing import Optional, List, Set
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session, Query
from sqlalchemy import or_, not_

from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription

logger = logging.getLogger("subwise_ai.services.business")


def get_active_business(
    current_user: User,
    db: Session,
    request: Optional[Request] = None,
) -> BusinessProfile:
    """
    Resolves the currently active BusinessProfile for the authenticated user.

    Priority:
    1. Explicit request header: 'X-SubWise-Demo-Mode: true' or query param '?demo=true' / '?demo_mode=true'
    2. Explicit request header: 'X-SubWise-Demo-Mode: false' forces real sandbox profile
    3. User's saved active_business_id (persisted in DB)
    4. Default standard profile (is_demo == False)
    5. Fallback to any profile belonging to current_user
    """
    is_demo_requested: Optional[bool] = None

    if request:
        demo_hdr = request.headers.get("X-SubWise-Demo-Mode", "").lower().strip()
        if demo_hdr in ("true", "1", "yes"):
            is_demo_requested = True
        elif demo_hdr in ("false", "0", "no"):
            is_demo_requested = False

        if is_demo_requested is None:
            demo_param = (
                request.query_params.get("demo_mode")
                or request.query_params.get("demo")
            )
            if demo_param is not None:
                if str(demo_param).lower().strip() in ("true", "1", "yes"):
                    is_demo_requested = True
                elif str(demo_param).lower().strip() in ("false", "0", "no"):
                    is_demo_requested = False

    # Case 1: Header/query explicitly requested Demo mode
    if is_demo_requested is True:
        demo_biz = (
            db.query(BusinessProfile)
            .filter(
                BusinessProfile.user_id == current_user.id,
                BusinessProfile.is_demo == True,
            )
            .first()
        )
        if demo_biz:
            return demo_biz

    # Case 2: Header/query explicitly requested Sandbox/Standard mode
    if is_demo_requested is False:
        std_biz = (
            db.query(BusinessProfile)
            .filter(
                BusinessProfile.user_id == current_user.id,
                BusinessProfile.is_demo == False,
            )
            .first()
        )
        if std_biz:
            return std_biz

    # Case 3: Check user.active_business_id
    if current_user.active_business_id:
        active_biz = (
            db.query(BusinessProfile)
            .filter(
                BusinessProfile.id == current_user.active_business_id,
                BusinessProfile.user_id == current_user.id,
            )
            .first()
        )
        if active_biz:
            return active_biz

    # Case 4: Default to standard (non-demo) profile
    std_biz = (
        db.query(BusinessProfile)
        .filter(
            BusinessProfile.user_id == current_user.id,
            BusinessProfile.is_demo == False,
        )
        .first()
    )
    if std_biz:
        return std_biz

    # Case 5: Fallback to any existing profile
    biz = (
        db.query(BusinessProfile)
        .filter(BusinessProfile.user_id == current_user.id)
        .first()
    )
    if not biz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found. Please complete profile setup.",
        )
    return biz


def get_all_user_businesses(user: User, db: Session) -> List[BusinessProfile]:
    """Returns all businesses owned by user (standard and demo)."""
    return (
        db.query(BusinessProfile)
        .filter(BusinessProfile.user_id == user.id)
        .order_by(BusinessProfile.is_demo.asc(), BusinessProfile.id.asc())
        .all()
    )


def switch_active_business(
    user: User,
    db: Session,
    mode: str,  # 'demo' or 'sandbox' / 'standard'
) -> BusinessProfile:
    """
    Switches user.active_business_id between the standard Sandbox business
    and the isolated DemoTech Solutions business.
    """
    mode = mode.lower().strip()
    is_demo = (mode == "demo")

    target_biz = (
        db.query(BusinessProfile)
        .filter(
            BusinessProfile.user_id == user.id,
            BusinessProfile.is_demo == is_demo,
        )
        .first()
    )

    if not target_biz and is_demo:
        # Auto-create demo business if switching to demo for the first time
        from app.services.demo_data_generator import DemoDataGenerator
        target_biz = DemoDataGenerator.ensure_demo_business(user_id=user.id, db=db)

    if not target_biz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find a business profile for mode '{mode}'.",
        )

    user.active_business_id = target_biz.id
    db.commit()
    db.refresh(user)
    db.refresh(target_biz)
    return target_biz


def get_business_environment(
    biz: BusinessProfile,
    request: Optional[Request] = None,
) -> str:
    """
    Determines whether the active evaluation environment is 'demo', 'sandbox', or 'live'.
    """
    if request:
        demo_hdr = request.headers.get("X-SubWise-Demo-Mode", "").lower().strip()
        if demo_hdr in ("true", "1", "yes"):
            return "demo"
        demo_param = (
            request.query_params.get("demo_mode")
            or request.query_params.get("demo")
        )
        if demo_param is not None and str(demo_param).lower().strip() in ("true", "1", "yes"):
            return "demo"

    if getattr(biz, "is_demo", False):
        return "demo"

    mode = (getattr(biz, "paypal_mode", "") or "sandbox").lower().strip()
    if mode in ("live", "demo"):
        return mode
    return "sandbox"


def get_environment_transactions_query(
    db: Session,
    biz: BusinessProfile,
    request: Optional[Request] = None,
    env: Optional[str] = None,
) -> Query:
    """
    Returns an SQLAlchemy Query for Transactions strictly filtered to the active environment:
    - 'demo': ONLY demo transactions (data_source in ('demo', 'demo_fixture'), is_simulated=True, or DEMO_% ID)
    - 'sandbox': ONLY genuine Sandbox transactions (data_source == 'sandbox', is_simulated=False, not DEMO_%)
    - 'live': ONLY genuine Live transactions (data_source == 'live', is_simulated=False, not DEMO_%)
    """
    environment = env or get_business_environment(biz, request)
    base_query = db.query(Transaction).filter(Transaction.business_id == biz.id)

    if environment == "demo":
        return base_query.filter(
            or_(
                Transaction.data_source.in_(["demo", "demo_fixture"]),
                Transaction.is_simulated == True,
                Transaction.paypal_transaction_id.like("DEMO_%"),
            )
        )
    elif environment == "live":
        return base_query.filter(
            Transaction.data_source == "live",
            Transaction.is_simulated == False,
            or_(
                Transaction.paypal_transaction_id == None,
                not_(Transaction.paypal_transaction_id.like("DEMO_%")),
            ),
        )
    else:  # sandbox
        return base_query.filter(
            Transaction.data_source == "sandbox",
            Transaction.is_simulated == False,
            or_(
                Transaction.paypal_transaction_id == None,
                not_(Transaction.paypal_transaction_id.like("DEMO_%")),
            ),
        )


def get_environment_transactions(
    db: Session,
    biz: BusinessProfile,
    request: Optional[Request] = None,
    env: Optional[str] = None,
) -> List[Transaction]:
    """Returns all transactions for biz in the active environment."""
    return get_environment_transactions_query(db, biz, request, env).all()


def get_environment_subscriptions(
    db: Session,
    biz: BusinessProfile,
    request: Optional[Request] = None,
    env: Optional[str] = None,
) -> List[Subscription]:
    """
    Returns Subscription records strictly belonging to the active environment.
    - If demo: returns demo subscriptions.
    - If sandbox/live: returns ONLY subscriptions that have supporting outbound expense
      transactions in the genuine environment.
    Guarantees demo subscriptions are never presented in sandbox/live mode,
    while safely preserving all subscription records in the database.
    """
    environment = env or get_business_environment(biz, request)
    all_subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    if getattr(biz, "is_demo", False) or environment == "demo":
        if getattr(biz, "is_demo", False):
            return all_subs
        demo_vendors = {
            v.lower().strip()
            for (v,) in db.query(Transaction.normalized_vendor)
            .filter(
                Transaction.business_id == biz.id,
                or_(
                    Transaction.data_source.in_(["demo", "demo_fixture"]),
                    Transaction.is_simulated == True,
                    Transaction.paypal_transaction_id.like("DEMO_%"),
                ),
                Transaction.gross_amount < 0,
            )
            .distinct()
            .all()
            if v
        }
        return [s for s in all_subs if (s.vendor_name or "").lower().strip() in demo_vendors]

    # Sandbox or Live:
    genuine_vendors = {
        v.lower().strip()
        for (v,) in db.query(Transaction.normalized_vendor)
        .filter(
            Transaction.business_id == biz.id,
            Transaction.data_source == environment,
            Transaction.is_simulated == False,
            or_(
                Transaction.paypal_transaction_id == None,
                not_(Transaction.paypal_transaction_id.like("DEMO_%")),
            ),
            Transaction.gross_amount < 0,
        )
        .distinct()
        .all()
        if v
    }

    return [s for s in all_subs if (s.vendor_name or "").lower().strip() in genuine_vendors]


