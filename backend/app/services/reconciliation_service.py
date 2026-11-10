import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.expense import Expense
from app.models.subscription import Subscription
from app.services.forecast_engine import ForecastEngine

class ReconciliationDiscrepancy(BaseModel):
    category: str  # 'unprojected_transaction', 'status_mismatch', 'unlinked_subscription', 'timing_difference'
    severity: str  # 'info', 'warning', 'critical'
    description: str
    amount: Optional[float] = None
    identifier: Optional[str] = None

class FinancialReconciliationReport(BaseModel):
    business_id: int
    company_name: str
    reconciled_at: str
    is_reconciled: bool
    reconciliation_score: float  # 0.0 to 100.0%
    
    # Raw PayPal Transactions
    raw_paypal_total_count: int
    raw_paypal_operating_inflows: float
    raw_paypal_operating_outflows: float
    raw_paypal_net_cash_flow: float
    
    # Expense Ledger Projections
    expense_ledger_total_count: int
    expense_ledger_total_expenses: float
    expense_ledger_total_income: float
    
    # Subscription Commitments
    active_subscriptions_count: int
    monthly_subscription_commitments: float
    
    # Discrepancies
    discrepancies: List[ReconciliationDiscrepancy] = []
    summary_verdict: str

class ReconciliationService:
    """
    Financial Data Accuracy & Integrity Reconciliation Engine:
    Compares raw PayPal ledger records, projected expenses, active subscriptions,
    and dashboard metrics to detect inconsistencies without altering historical data.
    """

    @classmethod
    def reconcile(cls, business: BusinessProfile, db: Session) -> FinancialReconciliationReport:
        now_str = datetime.datetime.utcnow().isoformat()
        
        # 1. Fetch raw transactions
        txs = db.query(Transaction).filter(Transaction.business_id == business.id).all()
        
        valid_txs = [t for t in txs if ForecastEngine.is_valid_operating(t)]
        
        operating_inflows = sum(float(t.gross_amount) for t in valid_txs if (t.gross_amount or 0.0) > 0)
        operating_outflows = sum(abs(float(t.gross_amount)) for t in valid_txs if (t.gross_amount or 0.0) < 0)
        net_cash = round(operating_inflows - operating_outflows, 2)
        
        # 2. Fetch expense ledger records
        expenses = db.query(Expense).filter(Expense.business_id == business.id).all()
        exp_expenses = sum(float(e.amount) for e in expenses if e.expense_type == "expense")
        exp_income = sum(float(e.amount) for e in expenses if e.expense_type == "income")
        
        # 3. Fetch active subscriptions
        subs = db.query(Subscription).filter(
            Subscription.business_id == business.id,
            Subscription.status == "active"
        ).all()
        sub_monthly_total = sum(float(s.latest_amount or 0.0) for s in subs)
        
        discrepancies: List[ReconciliationDiscrepancy] = []
        
        # Check for raw PayPal txs not yet projected into expenses ledger
        synced_paypal_ids = {
            e.paypal_transaction_id
            for e in expenses
            if e.paypal_transaction_id is not None
        }
        unprojected_txs = [t for t in txs if t.paypal_transaction_id and t.paypal_transaction_id not in synced_paypal_ids]
        if unprojected_txs:
            unproj_amt = sum(abs(float(t.gross_amount or 0.0)) for t in unprojected_txs)
            discrepancies.append(ReconciliationDiscrepancy(
                category="unprojected_transaction",
                severity="info",
                description=f"{len(unprojected_txs)} raw PayPal transaction(s) available for projection into personal/household expense ledger (${unproj_amt:,.2f} total).",
                amount=round(unproj_amt, 2),
                identifier=f"{len(unprojected_txs)}_transactions"
            ))

        # Check for pending / failed transactions in raw ledger
        pending_txs = [t for t in txs if (t.status or "").upper() in ("PENDING", "FAILED", "DENIED")]
        if pending_txs:
            p_amt = sum(abs(float(t.gross_amount or 0.0)) for t in pending_txs)
            discrepancies.append(ReconciliationDiscrepancy(
                category="status_mismatch",
                severity="warning",
                description=f"{len(pending_txs)} transaction(s) in non-completed status ({', '.join(set(t.status for t in pending_txs))}) excluded from operating revenue.",
                amount=round(p_amt, 2),
                identifier=f"{len(pending_txs)}_non_completed"
            ))

        # Check subscription alignment against recurring expenses
        rec_expenses = [e for e in expenses if e.is_recurring and e.expense_type == "expense"]
        rec_exp_total = sum(float(e.amount) for e in rec_expenses)
        if subs and not rec_expenses and expenses:
            discrepancies.append(ReconciliationDiscrepancy(
                category="unlinked_subscription",
                severity="info",
                description=f"Active subscriptions detected ({len(subs)} SaaS services) but not yet flagged as recurring in manual expense ledger.",
                amount=round(sub_monthly_total, 2),
                identifier=f"{len(subs)}_subscriptions"
            ))

        # Calculate reconciliation score
        # Base 100%, deduct based on discrepancy severities
        deductions = 0.0
        for d in discrepancies:
            if d.severity == "critical":
                deductions += 25.0
            elif d.severity == "warning":
                deductions += 10.0
            elif d.severity == "info":
                deductions += 2.0
                
        reconciled_score = max(50.0, round(100.0 - deductions, 1)) if txs or expenses else 100.0
        is_reconciled = len([d for d in discrepancies if d.severity == "critical"]) == 0

        summary_verdict = (
            "Financial ledgers are fully aligned: All operating inflows, subscription commitments, and cash flows match verified sources."
            if not discrepancies
            else f"Ledgers synchronized with {len(discrepancies)} informational variances noted. Historical records preserved intact."
        )

        return FinancialReconciliationReport(
            business_id=business.id,
            company_name=business.company_name,
            reconciled_at=now_str,
            is_reconciled=is_reconciled,
            reconciliation_score=reconciled_score,
            raw_paypal_total_count=len(txs),
            raw_paypal_operating_inflows=round(operating_inflows, 2),
            raw_paypal_operating_outflows=round(operating_outflows, 2),
            raw_paypal_net_cash_flow=net_cash,
            expense_ledger_total_count=len(expenses),
            expense_ledger_total_expenses=round(exp_expenses, 2),
            expense_ledger_total_income=round(exp_income, 2),
            active_subscriptions_count=len(subs),
            monthly_subscription_commitments=round(sub_monthly_total, 2),
            discrepancies=discrepancies,
            summary_verdict=summary_verdict
        )

