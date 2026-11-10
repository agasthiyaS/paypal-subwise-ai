from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from app.services.auth_service import get_password_hash, verify_password, create_access_token, get_current_user
from app.services.business_service import get_active_business

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name
    )
    db.add(user)
    db.flush() # Populate user.id

    # Create associated Business / Account Profile
    acct_type = payload.account_type or "business"
    company_name = payload.company_name
    if not company_name:
        if acct_type == "individual":
            company_name = f"{payload.full_name or 'Personal'}'s Finances"
        elif acct_type == "household":
            company_name = f"{payload.full_name or 'Family'} Household"
        else:
            company_name = "My Business"

    biz = BusinessProfile(
        user_id=user.id,
        company_name=company_name,
        account_type=acct_type,
        industry=payload.industry or ("Personal Finances" if acct_type == "individual" else "Household Budget" if acct_type == "household" else "SaaS / Technology"),
        monthly_baseline_revenue=payload.monthly_baseline_revenue or 0.0,
        current_cash_reserves=payload.current_cash_reserves or 0.0,
        paypal_mode="sandbox",
        paypal_connected=True
    )
    db.add(biz)
    db.commit()
    db.refresh(user)
    db.refresh(biz)

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "business_id": biz.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "business_id": biz.id,
        "email": user.email,
        "company_name": biz.company_name,
        "account_type": biz.account_type or "business",
        "is_admin": bool(getattr(user, "is_admin", False))
    }

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    biz = db.query(BusinessProfile).filter(
        BusinessProfile.user_id == user.id,
        BusinessProfile.is_demo == False,
    ).first()
    if not biz:
        biz = db.query(BusinessProfile).filter(BusinessProfile.user_id == user.id).first()
    biz_id = biz.id if biz else 0
    biz_name = biz.company_name if biz else "Business"
    biz_mode = (
        biz.paypal_mode
        if (biz and biz.paypal_mode in ["live", "sandbox"])
        else getattr(settings, "PAYPAL_ENVIRONMENT", "sandbox")
    )
    biz_connected = bool(biz and biz.paypal_connected) or bool(settings.PAYPAL_CLIENT_ID and settings.PAYPAL_CLIENT_SECRET)

    biz_acct_type = biz.account_type if (biz and biz.account_type) else "business"

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "business_id": biz_id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "business_id": biz_id,
        "email": user.email,
        "company_name": biz_name,
        "account_type": biz_acct_type,
        "is_admin": bool(getattr(user, "is_admin", False)),
        "paypal_mode": biz_mode,
        "paypal_connected": biz_connected
    }

@router.get("/me")
def get_current_user_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Use get_active_business() so the correct profile is returned based on
    # active_business_id (or header if explicitly set), rather than a raw
    # .first() that may return the wrong profile when multiple exist.
    biz = get_active_business(current_user=current_user, db=db, request=request)
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "is_admin": bool(getattr(current_user, "is_admin", False)),
            "created_at": current_user.created_at
        },
        "business": biz
    }

