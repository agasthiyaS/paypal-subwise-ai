import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.vendor import Vendor, VendorPlan
from app.services.auth_service import get_current_admin_user, get_optional_current_user

router = APIRouter(prefix="/vendors", tags=["Vendor Management"])


class VendorPlanBase(BaseModel):
    plan_name: str
    price: float
    cadence: str = "monthly"
    currency: str = "USD"
    features: Optional[str] = None


class VendorPlanCreate(VendorPlanBase):
    pass


class VendorPlanResponse(VendorPlanBase):
    id: int
    vendor_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class VendorBase(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    website_url: Optional[str] = None
    rating: Optional[float] = 4.5
    is_recommended: Optional[bool] = True


class VendorCreate(VendorBase):
    plans: Optional[List[VendorPlanCreate]] = []


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    website_url: Optional[str] = None
    rating: Optional[float] = None
    is_recommended: Optional[bool] = None


class VendorResponse(VendorBase):
    id: int
    plans: List[VendorPlanResponse] = []
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[VendorResponse])
def list_vendors(
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Public / user catalog search of verified software and household service vendors.
    """
    query = db.query(Vendor).options(joinedload(Vendor.plans))
    if category:
        query = query.filter(Vendor.category.ilike(f"%{category}%"))
    if search:
        query = query.filter(
            Vendor.name.ilike(f"%{search}%") | Vendor.description.ilike(f"%{search}%")
        )
    return query.order_by(Vendor.rating.desc(), Vendor.name.asc()).all()


@router.get("/categories", response_model=List[str])
def list_vendor_categories(db: Session = Depends(get_db)):
    """
    Returns unique categories available in the vendor directory.
    """
    results = db.query(Vendor.category).distinct().all()
    categories = [r[0] for r in results if r[0]]
    if not categories:
        # Default core categories if table is empty
        return [
            "Cloud & Infrastructure",
            "Project Management & Collaboration",
            "Customer Support & CRM",
            "Design & Creative",
            "Communication & Video",
            "Developer Tools",
            "Utilities & Household"
        ]
    return sorted(categories)


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).options(joinedload(Vendor.plans)).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
def create_vendor(
    payload: VendorCreate,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin-only: register a new vendor and optional plans."""
    existing = db.query(Vendor).filter(Vendor.name.ilike(payload.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Vendor '{payload.name}' already exists")

    vendor = Vendor(
        name=payload.name,
        category=payload.category,
        description=payload.description,
        website_url=payload.website_url,
        rating=payload.rating if payload.rating is not None else 4.5,
        is_recommended=payload.is_recommended if payload.is_recommended is not None else True,
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    if payload.plans:
        for plan_in in payload.plans:
            plan = VendorPlan(
                vendor_id=vendor.id,
                plan_name=plan_in.plan_name,
                price=plan_in.price,
                cadence=plan_in.cadence,
                currency=plan_in.currency,
                features=plan_in.features,
            )
            db.add(plan)
        db.commit()
        db.refresh(vendor)

    return vendor


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    payload: VendorUpdate,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin-only: update vendor metadata."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    if payload.name is not None:
        vendor.name = payload.name
    if payload.category is not None:
        vendor.category = payload.category
    if payload.description is not None:
        vendor.description = payload.description
    if payload.website_url is not None:
        vendor.website_url = payload.website_url
    if payload.rating is not None:
        vendor.rating = payload.rating
    if payload.is_recommended is not None:
        vendor.is_recommended = payload.is_recommended

    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor(
    vendor_id: int,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin-only: remove vendor."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    db.delete(vendor)
    db.commit()
    return None


@router.post("/{vendor_id}/plans", response_model=VendorPlanResponse, status_code=status.HTTP_201_CREATED)
def create_vendor_plan(
    vendor_id: int,
    payload: VendorPlanCreate,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin-only: add a pricing plan to a vendor."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    plan = VendorPlan(
        vendor_id=vendor.id,
        plan_name=payload.plan_name,
        price=payload.price,
        cadence=payload.cadence,
        currency=payload.currency,
        features=payload.features,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/{vendor_id}/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor_plan(
    vendor_id: int,
    plan_id: int,
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Admin-only: delete a vendor pricing plan."""
    plan = db.query(VendorPlan).filter(VendorPlan.id == plan_id, VendorPlan.vendor_id == vendor_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(plan)
    db.commit()
    return None

