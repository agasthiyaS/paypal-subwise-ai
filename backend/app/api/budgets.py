import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.budget import Budget
from app.models.expense import Expense
from app.schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from app.services.auth_service import get_current_user
from app.services.business_service import get_active_business

router = APIRouter(prefix="/budgets", tags=["Budgets"])

@router.get("", response_model=List[BudgetResponse])
def get_budgets(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    now = datetime.datetime.utcnow()
    start_of_month = datetime.datetime(now.year, now.month, 1)
    if now.month == 12:
        end_of_month = datetime.datetime(now.year + 1, 1, 1)
    else:
        end_of_month = datetime.datetime(now.year, now.month + 1, 1)

    budgets = db.query(Budget).filter(Budget.business_id == biz.id).all()

    # Pre-calculate current month expenses by category
    expenses = (
        db.query(Expense)
        .filter(
            Expense.business_id == biz.id,
            Expense.expense_type == "expense",
            Expense.expense_date >= start_of_month,
            Expense.expense_date < end_of_month,
        )
        .all()
    )

    total_spent_overall = sum(e.amount for e in expenses)
    cat_spent = {}
    for e in expenses:
        cat_spent[e.category] = cat_spent.get(e.category, 0.0) + e.amount

    responses = []
    for b in budgets:
        spent = total_spent_overall if b.category == "Overall" else cat_spent.get(b.category, 0.0)
        rem = b.monthly_limit - spent
        pct = (spent / b.monthly_limit * 100) if b.monthly_limit > 0 else 0.0
        responses.append(
            BudgetResponse(
                id=b.id,
                business_id=b.business_id,
                category=b.category,
                monthly_limit=b.monthly_limit,
                currency=b.currency,
                period_month=b.period_month,
                period_year=b.period_year,
                current_spent=round(spent, 2),
                utilization_percent=round(pct, 1),
                remaining_amount=round(rem, 2),
                is_over_budget=spent > b.monthly_limit,
                created_at=b.created_at,
                updated_at=b.updated_at,
            )
        )
    return responses

@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def set_budget(
    payload: BudgetCreate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    category = payload.category or "Overall"

    # Upsert budget for category & period
    existing = (
        db.query(Budget)
        .filter(
            Budget.business_id == biz.id,
            Budget.category == category,
            Budget.period_month == payload.period_month,
            Budget.period_year == payload.period_year,
        )
        .first()
    )

    if existing:
        existing.monthly_limit = payload.monthly_limit
        existing.currency = payload.currency or "USD"
        db.commit()
        db.refresh(existing)
        b = existing
    else:
        b = Budget(
            business_id=biz.id,
            category=category,
            monthly_limit=payload.monthly_limit,
            currency=payload.currency or "USD",
            period_month=payload.period_month,
            period_year=payload.period_year,
        )
        db.add(b)
        db.commit()
        db.refresh(b)

    # Compute current utilization
    now = datetime.datetime.utcnow()
    start_of_month = datetime.datetime(now.year, now.month, 1)
    if now.month == 12:
        end_of_month = datetime.datetime(now.year + 1, 1, 1)
    else:
        end_of_month = datetime.datetime(now.year, now.month + 1, 1)

    query = db.query(Expense).filter(
        Expense.business_id == biz.id,
        Expense.expense_type == "expense",
        Expense.expense_date >= start_of_month,
        Expense.expense_date < end_of_month,
    )
    if b.category != "Overall":
        query = query.filter(Expense.category == b.category)
    spent = sum(e.amount for e in query.all())
    rem = b.monthly_limit - spent
    pct = (spent / b.monthly_limit * 100) if b.monthly_limit > 0 else 0.0

    return BudgetResponse(
        id=b.id,
        business_id=b.business_id,
        category=b.category,
        monthly_limit=b.monthly_limit,
        currency=b.currency,
        period_month=b.period_month,
        period_year=b.period_year,
        current_spent=round(spent, 2),
        utilization_percent=round(pct, 1),
        remaining_amount=round(rem, 2),
        is_over_budget=spent > b.monthly_limit,
        created_at=b.created_at,
        updated_at=b.updated_at,
    )

@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    b = db.query(Budget).filter(Budget.id == budget_id, Budget.business_id == biz.id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Budget not found.")
    db.delete(b)
    db.commit()
    return None

