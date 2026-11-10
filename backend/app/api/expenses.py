import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.models.budget import Budget
from app.models.household_member import HouseholdMember
from app.models.transaction import Transaction
from app.schemas.expense import (
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
    MonthlyExpenseSummary,
    CategorySpendingItem,
)
from app.services.auth_service import get_current_user
from app.services.business_service import get_active_business
from app.services.categorization_service import CategorizationService, EXPENSE_CATEGORIES

router = APIRouter(prefix="/expenses", tags=["Personal & Household Expenses"])

@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    request: Request = None,
    category: Optional[str] = None,
    expense_type: Optional[str] = None,
    household_member_id: Optional[int] = None,
    is_shared: Optional[bool] = None,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    query = db.query(Expense).filter(Expense.business_id == biz.id)

    if category:
        query = query.filter(Expense.category == category)
    if expense_type:
        query = query.filter(Expense.expense_type == expense_type)
    if household_member_id is not None:
        query = query.filter(Expense.household_member_id == household_member_id)
    if is_shared is not None:
        query = query.filter(Expense.is_shared == is_shared)
    if start_date:
        query = query.filter(Expense.expense_date >= datetime.datetime.combine(start_date, datetime.time.min))
    if end_date:
        query = query.filter(Expense.expense_date <= datetime.datetime.combine(end_date, datetime.time.max))

    items = query.order_by(Expense.expense_date.desc()).offset(offset).limit(limit).all()

    # Enrich with member_name if available
    member_ids = {e.household_member_id for e in items if e.household_member_id}
    members = db.query(HouseholdMember).filter(HouseholdMember.id.in_(member_ids)).all() if member_ids else []
    member_map = {m.id: m.name for m in members}

    responses = []
    for e in items:
        resp = ExpenseResponse.from_orm(e)
        if e.household_member_id in member_map:
            resp.member_name = member_map[e.household_member_id]
        responses.append(resp)
    return responses

@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)

    # Automatic categorization if category is omitted, "Auto", or "Other"
    category = payload.category
    cat_method = "manual"
    if not category or category in ("Auto", "Other", ""):
        auto_cat, reason, conf = CategorizationService.categorize(payload.description, payload.merchant)
        if conf >= 0.5:
            category = auto_cat
            cat_method = "rules_engine"
        else:
            category = "Other"

    expense = Expense(
        business_id=biz.id,
        user_id=current_user.id,
        amount=abs(payload.amount),
        currency=payload.currency or biz.currency or "USD",
        expense_type=payload.expense_type or "expense",
        category=category,
        description=payload.description.strip(),
        merchant=payload.merchant.strip() if payload.merchant else None,
        expense_date=payload.expense_date or datetime.datetime.utcnow(),
        is_recurring=payload.is_recurring or False,
        payment_method=payload.payment_method or "Manual Entry",
        household_member_id=payload.household_member_id,
        is_shared=payload.is_shared if payload.is_shared is not None else True,
        data_source="manual",
        categorization_method=cat_method,
        notes=payload.notes,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    resp = ExpenseResponse.from_orm(expense)
    if expense.household_member_id:
        m = db.query(HouseholdMember).filter(HouseholdMember.id == expense.household_member_id).first()
        if m:
            resp.member_name = m.name
    return resp

@router.put("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    payload: ExpenseUpdate,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.business_id == biz.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense entry not found.")

    if payload.amount is not None:
        expense.amount = abs(payload.amount)
    if payload.expense_type is not None:
        expense.expense_type = payload.expense_type
    if payload.category is not None:
        expense.category = payload.category
        expense.categorization_method = "user_corrected"
    if payload.description is not None:
        expense.description = payload.description.strip()
    if payload.merchant is not None:
        expense.merchant = payload.merchant.strip()
    if payload.expense_date is not None:
        expense.expense_date = payload.expense_date
    if payload.is_recurring is not None:
        expense.is_recurring = payload.is_recurring
    if payload.payment_method is not None:
        expense.payment_method = payload.payment_method
    if payload.household_member_id is not None:
        expense.household_member_id = payload.household_member_id
    if payload.is_shared is not None:
        expense.is_shared = payload.is_shared
    if payload.notes is not None:
        expense.notes = payload.notes

    db.commit()
    db.refresh(expense)

    resp = ExpenseResponse.from_orm(expense)
    if expense.household_member_id:
        m = db.query(HouseholdMember).filter(HouseholdMember.id == expense.household_member_id).first()
        if m:
            resp.member_name = m.name
    return resp

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    biz = get_active_business(current_user=current_user, db=db, request=request)
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.business_id == biz.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense entry not found.")

    # Protect non-manual records if applicable
    if expense.data_source not in ("manual", "paypal_sync", "demo"):
        raise HTTPException(status_code=400, detail="Cannot delete this synchronized transaction.")

    db.delete(expense)
    db.commit()
    return None

@router.get("/summary", response_model=MonthlyExpenseSummary)
def get_monthly_expense_summary(
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

    start_date = datetime.datetime(target_year, target_month, 1)
    if target_month == 12:
        end_date = datetime.datetime(target_year + 1, 1, 1)
    else:
        end_date = datetime.datetime(target_year, target_month + 1, 1)

    # Retrieve all expenses & income for target month
    all_records = (
        db.query(Expense)
        .filter(
            Expense.business_id == biz.id,
            Expense.expense_date >= start_date,
            Expense.expense_date < end_date,
        )
        .all()
    )

    total_income = sum(e.amount for e in all_records if e.expense_type == "income")
    # If no manual income is recorded, use baseline revenue from business profile
    if total_income == 0.0 and biz.monthly_baseline_revenue:
        total_income = float(biz.monthly_baseline_revenue)

    expenses = [e for e in all_records if e.expense_type == "expense"]
    total_expenses = sum(e.amount for e in expenses)

    net_savings = max(0.0, total_income - total_expenses)
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0

    # Category breakdown
    cat_map = {}
    for cat in EXPENSE_CATEGORIES:
        cat_map[cat] = {"amount": 0.0, "count": 0}

    for e in expenses:
        c = e.category if e.category in cat_map else "Other"
        cat_map[c]["amount"] += e.amount
        cat_map[c]["count"] += 1

    category_items: List[CategorySpendingItem] = []
    for cat, data in sorted(cat_map.items(), key=lambda x: x[1]["amount"], reverse=True):
        if data["amount"] > 0:
            pct = (data["amount"] / total_expenses * 100) if total_expenses > 0 else 0.0
            category_items.append(
                CategorySpendingItem(
                    category=cat,
                    amount=round(data["amount"], 2),
                    percentage=round(pct, 1),
                    count=data["count"],
                )
            )

    grocery_total = cat_map["Food & Groceries"]["amount"]
    utility_total = cat_map["Electricity & Utilities"]["amount"]
    subs_total = cat_map["Subscriptions"]["amount"]
    discretionary_total = max(0.0, total_expenses - (grocery_total + utility_total + subs_total))

    # Overall Budget
    budget_row = (
        db.query(Budget)
        .filter(Budget.business_id == biz.id, Budget.category == "Overall")
        .first()
    )
    overall_budget = budget_row.monthly_limit if budget_row else (biz.monthly_baseline_revenue or 3500.0)
    budget_rem = overall_budget - total_expenses
    budget_pct = (total_expenses / overall_budget * 100) if overall_budget > 0 else 0.0

    # Recent 6-month trend
    trend = []
    for i in range(5, -1, -1):
        m = target_month - i
        y = target_year
        while m <= 0:
            m += 12
            y -= 1
        m_start = datetime.datetime(y, m, 1)
        m_end = datetime.datetime(y + 1, 1, 1) if m == 12 else datetime.datetime(y, m + 1, 1)

        m_records = (
            db.query(Expense)
            .filter(
                Expense.business_id == biz.id,
                Expense.expense_date >= m_start,
                Expense.expense_date < m_end,
            )
            .all()
        )
        m_inc = sum(e.amount for e in m_records if e.expense_type == "income")
        if m_inc == 0.0 and biz.monthly_baseline_revenue:
            m_inc = float(biz.monthly_baseline_revenue)
        m_exp = sum(e.amount for e in m_records if e.expense_type == "expense")
        trend.append({
            "month": m_start.strftime("%b %Y"),
            "income": round(m_inc, 2),
            "expenses": round(m_exp, 2),
            "net": round(m_inc - m_exp, 2),
        })

    return MonthlyExpenseSummary(
        total_income=round(total_income, 2),
        total_expenses=round(total_expenses, 2),
        net_savings=round(net_savings, 2),
        savings_rate=round(savings_rate, 1),
        overall_budget=round(overall_budget, 2),
        budget_remaining=round(budget_rem, 2),
        budget_utilization_percent=round(budget_pct, 1),
        category_breakdown=category_items,
        grocery_total=round(grocery_total, 2),
        utility_total=round(utility_total, 2),
        discretionary_total=round(discretionary_total, 2),
        active_subscriptions_total=round(subs_total, 2),
        recent_trend=trend,
    )

@router.post("/sync-paypal", response_model=dict)
def sync_paypal_into_expenses(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Safely projects verified PayPal transactions into the expenses ledger without
    mutating original raw PayPal transaction records.
    Idempotent: Skips any PayPal transaction that was already imported.
    """
    biz = get_active_business(current_user=current_user, db=db, request=request)

    # 1. Fetch PayPal transactions for this business
    txs = (
        db.query(Transaction)
        .filter(Transaction.business_id == biz.id)
        .all()
    )

    # 2. Existing imported PayPal transaction IDs in expenses
    existing_paypal_ids = {
        e.paypal_transaction_id
        for e in db.query(Expense.paypal_transaction_id)
        .filter(Expense.business_id == biz.id, Expense.paypal_transaction_id.isnot(None))
        .all()
    }

    imported_count = 0
    for tx in txs:
        # Generate or use identifier
        tx_id = tx.paypal_transaction_id or f"TX_{tx.id}"
        if tx_id in existing_paypal_ids:
            continue

        # Classify as income or expense
        gross = float(tx.gross_amount or 0.0)
        is_income = gross > 0
        amount = abs(gross)

        # Categorize
        cat, reason, _ = CategorizationService.categorize(tx.raw_description, tx.normalized_vendor)

        expense = Expense(
            business_id=biz.id,
            user_id=current_user.id,
            amount=amount,
            currency=tx.currency or "USD",
            expense_type="income" if is_income else "expense",
            category=cat if not is_income else "Other",
            description=tx.raw_description,
            merchant=tx.normalized_vendor,
            expense_date=tx.transaction_date,
            is_recurring=False,
            payment_method="PayPal",
            is_shared=True,
            data_source="paypal_sync",
            paypal_transaction_id=tx_id,
            categorization_method="rules_engine",
            notes=f"Synchronized from PayPal transaction {tx_id}",
        )
        db.add(expense)
        imported_count += 1

    if imported_count > 0:
        db.commit()

    return {
        "status": "success",
        "total_paypal_transactions": len(txs),
        "newly_projected_expenses": imported_count,
        "already_synced": len(existing_paypal_ids),
    }

