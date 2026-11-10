"""
Stage 6: Financial Reports & Export Intelligence API Router
Provides authenticated endpoints for:
- Monthly Financial Report (with period selection)
- Subscription Expense Report
- Upcoming Renewal Report
- Six-Month Cash-Flow Forecast Report
- Comprehensive Executive Financial Report
- Professional PDF Export (ReportLab with NumberedCanvas)
- CSV Export with spreadsheet formula injection protection
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.auth_service import get_current_user
from app.services.report_engine import ReportEngine
from app.services.business_service import get_active_business
from app.schemas.report import (
    MonthlyFinancialReport,
    SubscriptionExpenseReport,
    UpcomingRenewalReport,
    CashFlowForecastReport,
    ComprehensiveFinancialReport,
)

router = APIRouter(prefix="/reports", tags=["Financial Reports & Export"])


def _get_user_business(current_user: User, db: Session, request: Optional[Request] = None) -> BusinessProfile:
    """Helper to verify and retrieve the authenticated user's active business profile."""
    return get_active_business(current_user=current_user, db=db, request=request)


@router.get("/monthly", response_model=MonthlyFinancialReport)
def get_monthly_financial_report(
    request: Request = None,
    period: str = Query("all", description="Period preset: all, last_30_days, last_90_days, last_180_days, ytd, custom"),
    start_date: Optional[str] = Query(None, description="Custom start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Custom end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the Monthly Financial Report containing operating revenue, non-sub outflows,
    confirmed SaaS commitments, potential trials, and net operating cash flows.
    """
    biz = _get_user_business(current_user, db, request=request)
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    return ReportEngine.generate_monthly_financial_report(
        business=biz,
        transactions=txns,
        subscriptions=subs,
        period_preset=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/subscriptions", response_model=SubscriptionExpenseReport)
def get_subscription_expense_report(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the Subscription Expense Report detailing software commitments,
    monthly equivalents, annual run-rates, price creep alerts, and category distributions.
    """
    biz = _get_user_business(current_user, db, request=request)
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    return ReportEngine.generate_subscription_expense_report(
        business=biz,
        subscriptions=subs,
        transactions=txns,
    )


@router.get("/renewals", response_model=UpcomingRenewalReport)
def get_upcoming_renewal_report(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the Upcoming Subscription Renewal Report powered by the calendar schedule,
    highlighting renewal clustering and concentration spikes.
    """
    biz = _get_user_business(current_user, db, request=request)
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    return ReportEngine.generate_upcoming_renewal_report(
        business=biz,
        subscriptions=subs,
        transactions=txns,
    )


@router.get("/forecast", response_model=CashFlowForecastReport)
def get_cash_flow_forecast_report(
    request: Request = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the Six-Month Cash-Flow Forecast Report with Optimistic, Baseline,
    and Conservative multi-scenario timelines and assumptions disclosures.
    """
    biz = _get_user_business(current_user, db, request=request)
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    return ReportEngine.generate_forecast_report(
        business=biz,
        subscriptions=subs,
        transactions=txns,
    )


@router.get("/comprehensive", response_model=ComprehensiveFinancialReport)
def get_comprehensive_financial_report(
    request: Request = None,
    period: str = Query("all", description="Period preset: all, last_30_days, last_90_days, last_180_days, ytd, custom"),
    start_date: Optional[str] = Query(None, description="Custom start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Custom end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the Comprehensive Executive Financial Report unifying monthly performance,
    subscription overhead, calendar renewals, forecast scenarios, and Financial Health Index.
    """
    biz = _get_user_business(current_user, db, request=request)
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    return ReportEngine.generate_comprehensive_report(
        business=biz,
        transactions=txns,
        subscriptions=subs,
        period_preset=period,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/export/csv")
def export_csv_report(
    request: Request = None,
    export_type: str = Query("transactions", description="Export type: transactions, subscriptions, renewals, forecast, monthly"),
    period: str = Query("all", description="Period preset: all, last_30_days, last_90_days, last_180_days, ytd, custom"),
    start_date: Optional[str] = Query(None, description="Custom start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Custom end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Exports clean, spreadsheet-ready CSV with OWASP formula injection protection
    applied to all cells.
    """
    biz = _get_user_business(current_user, db, request=request)
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    csv_content = ReportEngine.generate_csv(
        export_type=export_type,
        business=biz,
        subscriptions=subs,
        transactions=txns,
        period_preset=period,
        start_date=start_date,
        end_date=end_date,
    )

    filename = f"subwise_{export_type}_{biz.company_name.lower().replace(' ', '_')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/export/pdf")
def export_pdf_report(
    request: Request = None,
    report_type: str = Query("comprehensive", description="Report type: comprehensive, monthly, subscriptions, renewals, forecast"),
    period: str = Query("all", description="Period preset: all, last_30_days, last_90_days, last_180_days, ytd, custom"),
    start_date: Optional[str] = Query(None, description="Custom start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="Custom end date YYYY-MM-DD"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generates a publication-grade PDF financial report via ReportLab with branded
    styling, dynamic 'Page X of Y' numbering, and methodology disclosures.
    """
    biz = _get_user_business(current_user, db, request=request)
    txns = db.query(Transaction).filter(Transaction.business_id == biz.id).all()
    subs = db.query(Subscription).filter(Subscription.business_id == biz.id).all()

    pdf_bytes = ReportEngine.generate_pdf(
        report_type=report_type,
        business=biz,
        subscriptions=subs,
        transactions=txns,
        period_preset=period,
        start_date=start_date,
        end_date=end_date,
    )

    filename = f"subwise_{report_type}_report_{biz.company_name.lower().replace(' ', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )
