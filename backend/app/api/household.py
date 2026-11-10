import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.household_member import HouseholdMember
from app.models.expense import Expense
from app.models.budget import Budget
from app.schemas.household import (
    HouseholdMemberCreate,
    HouseholdMemberUpdate,
    HouseholdMemberResponse,
    HouseholdFinancialSummary,
    MemberExpenseSummary,
)
from app.services.auth_service import get_current_user
from app.services.business_service import get_active_business

router = APIRouter(prefix="/household", tags=["Household Finance"])

@router.get("/members", response_model=List[HouseholdMemberResponse])
def get_household_members(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    members = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.business_id == biz.id, HouseholdMember.is_active == True)
        .order_by(HouseholdMember.id.asc())
        .all()
    )
    return members

@router.post("/members", response_model=HouseholdMemberResponse, status_code=status.HTTP_201_CREATED)
def create_household_member(
    payload: HouseholdMemberCreate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    member = HouseholdMember(
        business_id=biz.id,
        name=payload.name.strip(),
        role=payload.role or "Member",
        avatar_color=payload.avatar_color or "#0070ba",
        is_active=payload.is_active if payload.is_active is not None else True,
        monthly_income_share=payload.monthly_income_share or 0.0,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@router.put("/members/{member_id}", response_model=HouseholdMemberResponse)
def update_household_member(
    member_id: int,
    payload: HouseholdMemberUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    member = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.id == member_id, HouseholdMember.business_id == biz.id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Household member not found.")

    if payload.name is not None:
        member.name = payload.name.strip()
    if payload.role is not None:
        member.role = payload.role
    if payload.avatar_color is not None:
        member.avatar_color = payload.avatar_color
    if payload.is_active is not None:
        member.is_active = payload.is_active
    if payload.monthly_income_share is not None:
        member.monthly_income_share = payload.monthly_income_share

    db.commit()
    db.refresh(member)
    return member

@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_household_member(
    member_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    member = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.id == member_id, HouseholdMember.business_id == biz.id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Household member not found.")

    # Soft deactivate or remove
    db.delete(member)
    db.commit()
    return None

@router.get("/summary", response_model=HouseholdFinancialSummary)
def get_household_financial_summary(
    request: Request = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    now = datetime.datetime.utcnow()
    target_month = month or now.month
    target_year = year or now.year

    # 1. Retrieve members
    members = (
        db.query(HouseholdMember)
        .filter(HouseholdMember.business_id == biz.id, HouseholdMember.is_active == True)
        .all()
    )
    member_map = {m.id: m for m in members}

    # 2. Query household expenses
    query = db.query(Expense).filter(
        Expense.business_id == biz.id,
        Expense.expense_type == "expense"
    )
    
    # Filter by month/year if applicable
    # We can filter based on expense_date
    start_date = datetime.datetime(target_year, target_month, 1)
    if target_month == 12:
        end_date = datetime.datetime(target_year + 1, 1, 1)
    else:
        end_date = datetime.datetime(target_year, target_month + 1, 1)

    expenses = query.filter(Expense.expense_date >= start_date, Expense.expense_date < end_date).all()

    total_spent = sum(e.amount for e in expenses)
    grocery_spent = sum(e.amount for e in expenses if e.category == "Food & Groceries")
    utility_spent = sum(e.amount for e in expenses if e.category == "Electricity & Utilities")
    shared_spent = sum(e.amount for e in expenses if e.is_shared)
    personal_spent = sum(e.amount for e in expenses if not e.is_shared)

    # 3. Member-wise breakdown
    member_spending = {m.id: {"total": 0.0, "count": 0} for m in members}
    unassigned_total = 0.0
    unassigned_count = 0

    for e in expenses:
        if e.household_member_id and e.household_member_id in member_spending:
            member_spending[e.household_member_id]["total"] += e.amount
            member_spending[e.household_member_id]["count"] += 1
        else:
            unassigned_total += e.amount
            unassigned_count += 1

    member_summaries: List[MemberExpenseSummary] = []
    for m in members:
        spent = member_spending[m.id]["total"]
        pct = (spent / total_spent * 100) if total_spent > 0 else 0.0
        member_summaries.append(
            MemberExpenseSummary(
                member_id=m.id,
                member_name=m.name,
                role=m.role,
                avatar_color=m.avatar_color,
                total_spent=round(spent, 2),
                percentage_of_household=round(pct, 1),
                transaction_count=member_spending[m.id]["count"],
            )
        )

    if unassigned_count > 0:
        pct = (unassigned_total / total_spent * 100) if total_spent > 0 else 0.0
        member_summaries.append(
            MemberExpenseSummary(
                member_id=None,
                member_name="Shared Household Pool",
                role="Shared / Unassigned",
                avatar_color="#64748b",
                total_spent=round(unassigned_total, 2),
                percentage_of_household=round(pct, 1),
                transaction_count=unassigned_count,
            )
        )

    # 4. Budget determination
    budget_row = (
        db.query(Budget)
        .filter(Budget.business_id == biz.id, Budget.category == "Overall")
        .first()
    )
    budget_val = budget_row.monthly_limit if budget_row else (biz.monthly_baseline_revenue or 3500.0)
    remaining_budget = budget_val - total_spent
    util_pct = (total_spent / budget_val * 100) if budget_val > 0 else 0.0

    return HouseholdFinancialSummary(
        total_household_budget=round(budget_val, 2),
        total_household_spent=round(total_spent, 2),
        remaining_budget=round(remaining_budget, 2),
        budget_utilization_percent=round(util_pct, 1),
        grocery_spent=round(grocery_spent, 2),
        utility_spent=round(utility_spent, 2),
        shared_spent=round(shared_spent, 2),
        personal_spent=round(personal_spent, 2),
        active_member_count=len(members),
        members=member_summaries,
    )

