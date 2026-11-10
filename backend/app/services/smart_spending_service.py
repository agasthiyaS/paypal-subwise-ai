import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.business import BusinessProfile
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.schemas.consumer_intelligence import (
    SpendingAnalysisResult,
    CategoryMoMChange,
    TopMerchantItem
)
from app.services.categorization_service import EXPENSE_CATEGORIES

class SmartSpendingService:
    @classmethod
    def analyze_spending(
        cls,
        business: BusinessProfile,
        db: Session,
        month: Optional[int] = None,
        year: Optional[int] = None
    ) -> SpendingAnalysisResult:
        now = datetime.datetime.utcnow()
        cur_m = month or now.month
        cur_y = year or now.year

        # Target month dates
        start_curr = datetime.datetime(cur_y, cur_m, 1)
        if cur_m == 12:
            end_curr = datetime.datetime(cur_y + 1, 1, 1)
        else:
            end_curr = datetime.datetime(cur_y, cur_m + 1, 1)

        # Prior month dates
        if cur_m == 1:
            start_prior = datetime.datetime(cur_y - 1, 12, 1)
            end_prior = datetime.datetime(cur_y, 1, 1)
        else:
            start_prior = datetime.datetime(cur_y, cur_m - 1, 1)
            end_prior = datetime.datetime(cur_y, cur_m, 1)

        # Retrieve current month expenses
        curr_expenses = (
            db.query(Expense)
            .filter(
                Expense.business_id == business.id,
                Expense.expense_date >= start_curr,
                Expense.expense_date < end_curr,
            )
            .all()
        )

        # If zero expenses in expenses table, check if transactions exist
        if not curr_expenses:
            txs = (
                db.query(Transaction)
                .filter(
                    Transaction.business_id == business.id,
                    Transaction.transaction_date >= start_curr,
                    Transaction.transaction_date < end_curr,
                )
                .all()
            )
        else:
            txs = []

        # Retrieve prior month expenses
        prior_expenses = (
            db.query(Expense)
            .filter(
                Expense.business_id == business.id,
                Expense.expense_date >= start_prior,
                Expense.expense_date < end_prior,
            )
            .all()
        )

        # Calculate income & expenses for current month
        total_income = sum(e.amount for e in curr_expenses if e.expense_type == "income")
        if total_income == 0.0 and business.monthly_baseline_revenue:
            total_income = float(business.monthly_baseline_revenue)

        actual_expenses = [e for e in curr_expenses if e.expense_type == "expense"]
        total_expenses = sum(e.amount for e in actual_expenses)

        # If fallback from raw transactions
        if not actual_expenses and txs:
            for t in txs:
                amt = abs(float(t.gross_amount or 0.0))
                if (t.gross_amount or 0.0) < 0:
                    total_expenses += amt
                elif (t.gross_amount or 0.0) > 0 and total_income == 0:
                    total_income += amt

        net_savings = max(0.0, total_income - total_expenses)
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0.0

        # Recurring vs Discretionary
        recurring_spend = sum(e.amount for e in actual_expenses if e.is_recurring)
        discretionary_spend = total_expenses - recurring_spend

        # Category maps for current and prior
        cat_curr = {cat: 0.0 for cat in EXPENSE_CATEGORIES}
        for e in actual_expenses:
            c = e.category if e.category in cat_curr else "Other"
            cat_curr[c] += e.amount

        cat_prior = {cat: 0.0 for cat in EXPENSE_CATEGORIES}
        for e in prior_expenses:
            if e.expense_type == "expense":
                c = e.category if e.category in cat_prior else "Other"
                cat_prior[c] += e.amount

        # Top Categories
        top_cats = []
        for cat, amt in sorted(cat_curr.items(), key=lambda x: x[1], reverse=True):
            if amt > 0:
                pct = (amt / total_expenses * 100) if total_expenses > 0 else 0.0
                top_cats.append({
                    "category": cat,
                    "amount": round(amt, 2),
                    "percentage": round(pct, 1)
                })

        # Month-over-Month changes & Spikes
        mom_changes: List[CategoryMoMChange] = []
        unusual_spikes: List[str] = []

        for cat in EXPENSE_CATEGORIES:
            c_amt = cat_curr[cat]
            p_amt = cat_prior[cat]
            if c_amt > 0 or p_amt > 0:
                diff = c_amt - p_amt
                pct = ((diff / p_amt) * 100) if p_amt > 0 else (100.0 if c_amt > 0 else 0.0)
                is_spike = diff > 40.0 and pct >= 20.0
                if is_spike:
                    unusual_spikes.append(
                        f"{cat} spending surged by {round(pct)}% (+${round(diff, 2)}) compared to last month."
                    )
                mom_changes.append(
                    CategoryMoMChange(
                        category=cat,
                        current_month_amount=round(c_amt, 2),
                        prior_month_amount=round(p_amt, 2),
                        dollar_change=round(diff, 2),
                        percent_change=round(pct, 1),
                        is_spike=is_spike
                    )
                )

        # Frequent Merchants
        merchant_map = {}
        for e in actual_expenses:
            m = e.merchant or e.description[:25]
            if m not in merchant_map:
                merchant_map[m] = {"amount": 0.0, "count": 0, "category": e.category}
            merchant_map[m]["amount"] += e.amount
            merchant_map[m]["count"] += 1

        frequent_merchants = [
            TopMerchantItem(
                merchant=m,
                amount=round(data["amount"], 2),
                count=data["count"],
                category=data["category"]
            )
            for m, data in sorted(merchant_map.items(), key=lambda x: x[1]["amount"], reverse=True)[:5]
        ]

        has_data = len(actual_expenses) > 0 or len(txs) > 0

        return SpendingAnalysisResult(
            month=cur_m,
            year=cur_y,
            total_income=round(total_income, 2),
            total_expenses=round(total_expenses, 2),
            net_savings=round(net_savings, 2),
            savings_rate_percent=round(savings_rate, 1),
            recurring_expenses_total=round(recurring_spend, 2),
            discretionary_expenses_total=round(discretionary_spend, 2),
            top_categories=top_cats,
            mom_changes=mom_changes,
            frequent_merchants=frequent_merchants,
            unusual_spikes=unusual_spikes,
            has_sufficient_data=has_data,
            notes=None if has_data else "No expenses recorded this month yet. Add expenses or sync PayPal to analyze trends."
        )

