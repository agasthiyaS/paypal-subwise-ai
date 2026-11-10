"""
Stage 8.5: Business Profile Service & Active Profile Resolver
Provides unified tenant resolution supporting both Real Sandbox profiles
and isolated Demonstration profiles (DemoTech Solutions).
"""
import logging
from typing import Optional, List
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.business import BusinessProfile

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

