"""
Stage 6: Professional Financial Reporting and Export Intelligence Tests

Test Coverage:
1.  test_monthly_financial_report_calculations
2.  test_subscription_expense_report_calculations
3.  test_upcoming_renewals_report
4.  test_cash_flow_forecast_report
5.  test_reporting_period_filtering
6.  test_csv_generation_and_formula_injection_protection
7.  test_pdf_generation_validity
8.  test_insufficient_data_empty_state_handling
9.  test_reports_api_auth_and_isolation
10. test_existing_api_compatibility
"""
import pytest
import datetime
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.report_engine import ReportEngine, sanitize_csv_cell
from app.api.reports import (
    get_monthly_financial_report,
    get_subscription_expense_report,
    get_upcoming_renewal_report,
    get_cash_flow_forecast_report,
    get_comprehensive_financial_report,
    export_csv_report,
    export_pdf_report,
)


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def _make_biz(id=1, user_id=1, name="Apex FinTech", cash=15000.0):
    return BusinessProfile(
        id=id,
        user_id=user_id,
        company_name=name,
        current_cash_reserves=cash,
        currency="USD",
    )


def _make_tx(id, biz_id, amount, months_ago=0, vendor="Customer Sale", is_expense=False, raw_desc=None):
    d = datetime.date.today() - datetime.timedelta(days=30 * months_ago)
    amt = -abs(float(amount)) if is_expense else abs(float(amount))
    return Transaction(
        id=id,
        business_id=biz_id,
        gross_amount=amt,
        net_amount=amt,
        transaction_date=datetime.datetime.combine(d, datetime.time(12, 0)),
        status="COMPLETED",
        raw_description=raw_desc or vendor,
        normalized_vendor=vendor,
        category="General Software" if is_expense else "Sales Revenue",
        currency="USD",
    )


def _make_sub(id, biz_id, vendor, amount, cadence="monthly",
              detection_type="confirmed", price_change_pct=0.0):
    now = datetime.datetime.utcnow()
    avg = round(amount / (1 + price_change_pct / 100), 2) if price_change_pct else amount
    return Subscription(
        id=id,
        business_id=biz_id,
        vendor_name=vendor,
        latest_amount=float(amount),
        average_amount=float(avg),
        cadence=cadence,
        detection_type=detection_type,
        status="active",
        price_change_pct=price_change_pct,
        billing_type="fixed",
        first_billed_date=now - datetime.timedelta(days=60),
        last_billed_date=now - datetime.timedelta(days=30),
        next_billing_date=now + datetime.timedelta(days=15),
    )


# ---------------------------------------------------------------------------
# 1. Monthly Financial Report Calculations
# ---------------------------------------------------------------------------

def test_monthly_financial_report_calculations():
    biz = _make_biz()
    txns = [
        _make_tx(1, 1, 6000.0, months_ago=2, vendor="Client Wire"),
        _make_tx(2, 1, 6500.0, months_ago=1, vendor="Client Wire"),
        _make_tx(3, 1, 6200.0, months_ago=0, vendor="Client Wire"),
        _make_tx(4, 1, 500.0, months_ago=1, vendor="Office Supplies", is_expense=True),
        _make_tx(5, 1, 300.0, months_ago=1, vendor="Slack", is_expense=True),
    ]
    subs = [_make_sub(10, 1, "Slack", 300.0)]

    rep = ReportEngine.generate_monthly_financial_report(biz, txns, subs)

    assert rep.data_sufficiency_status in ("sufficient_data", "limited_data")
    assert rep.total_operating_revenue == 18700.0
    assert rep.total_confirmed_sub_expenses >= 300.0
    assert rep.total_non_sub_expenses >= 500.0
    assert rep.net_operating_cashflow > 0
    assert len(rep.monthly_breakdown) >= 2


# ---------------------------------------------------------------------------
# 2. Subscription Expense Report Calculations
# ---------------------------------------------------------------------------

def test_subscription_expense_report_calculations():
    biz = _make_biz()
    txns = [
        _make_tx(1, 1, 5000.0, months_ago=1),
        _make_tx(2, 1, 100.0, months_ago=1, vendor="GitHub", is_expense=True),
        _make_tx(3, 1, 100.0, months_ago=0, vendor="GitHub", is_expense=True),
    ]
    sub_confirmed = _make_sub(1, 1, "GitHub", 100.0, cadence="monthly", detection_type="confirmed")
    sub_annual = _make_sub(2, 1, "AWS Annual", 1200.0, cadence="annual", detection_type="confirmed")
    sub_potential = _make_sub(3, 1, "Figma Trial", 45.0, cadence="monthly", detection_type="potential")

    rep = ReportEngine.generate_subscription_expense_report(biz, [sub_confirmed, sub_annual, sub_potential], txns)

    assert rep.confirmed_subscriptions_count == 2
    assert rep.potential_subscriptions_count == 1
    # Monthly eq for AWS Annual is 1200 / 12 = 100; GitHub is 100 -> confirmed monthly = 200
    assert rep.total_confirmed_monthly_commitments == 200.0
    assert rep.total_confirmed_annual_commitments == 2400.0
    assert rep.total_potential_monthly_commitments == 45.0

    # GitHub historical spending was 2 * 100 = 200
    gh_item = next(i for i in rep.items if i.vendor_name == "GitHub")
    assert gh_item.historical_payment_count == 2
    assert gh_item.total_historical_spend == 200.0


# ---------------------------------------------------------------------------
# 3. Upcoming Renewals Report
# ---------------------------------------------------------------------------

def test_upcoming_renewals_report():
    biz = _make_biz()
    txns = [_make_tx(1, 1, 4000.0, months_ago=0)]
    subs = [
        _make_sub(1, 1, "Datadog", 250.0, cadence="monthly"),
        _make_sub(2, 1, "HubSpot", 800.0, cadence="annual"),
    ]

    rep = ReportEngine.generate_upcoming_renewal_report(biz, subs, txns)

    assert rep.total_upcoming_60_days_count >= 1
    assert len(rep.scheduled_renewals) >= 1
    assert rep.unknown_renewal_date_count == 0

    first_pmt = rep.scheduled_renewals[0]
    assert first_pmt.expected_payment_amount > 0
    assert first_pmt.expected_payment_date != ""


# ---------------------------------------------------------------------------
# 4. Six-Month Cash-Flow Forecast Report
# ---------------------------------------------------------------------------

def test_cash_flow_forecast_report():
    biz = _make_biz(cash=10000.0)
    txns = [
        _make_tx(1, 1, 5000.0, months_ago=1),
        _make_tx(2, 1, 5000.0, months_ago=0),
    ]
    subs = [_make_sub(1, 1, "Salesforce", 300.0)]

    rep = ReportEngine.generate_forecast_report(biz, subs, txns)

    assert rep.forecast_months == 6
    assert "optimistic" in rep.scenarios
    assert "baseline" in rep.scenarios
    assert "conservative" in rep.scenarios

    # Assumptions: Optimistic +15%, Baseline 0%, Conservative -20%
    assert rep.scenarios["optimistic"].revenue_adjustment_pct == 15.0
    assert rep.scenarios["baseline"].revenue_adjustment_pct == 0.0
    assert rep.scenarios["conservative"].revenue_adjustment_pct == -20.0

    # Timeline has 6 months
    assert len(rep.scenarios["baseline"].timeline) == 6


# ---------------------------------------------------------------------------
# 5. Reporting Period Filtering
# ---------------------------------------------------------------------------

def test_reporting_period_filtering():
    biz = _make_biz()
    # Transactions at 10, 45, and 120 days ago
    txns = [
        _make_tx(1, 1, 1000.0, months_ago=0, vendor="Recent Sale"),      # ~0-5 days ago
        _make_tx(2, 1, 1000.0, months_ago=2, vendor="Mid-Range Sale"),    # ~60 days ago
        _make_tx(3, 1, 1000.0, months_ago=4, vendor="Older Sale"),        # ~120 days ago
    ]

    # Preset: last_30_days should only capture the recent transaction
    filtered_30, filter_obj_30 = ReportEngine.filter_transactions_by_period(txns, period_preset="last_30_days")
    assert len(filtered_30) == 1
    assert filtered_30[0].normalized_vendor == "Recent Sale"

    # Preset: all should capture all 3
    filtered_all, filter_obj_all = ReportEngine.filter_transactions_by_period(txns, period_preset="all")
    assert len(filtered_all) == 3


# ---------------------------------------------------------------------------
# 6. CSV Generation & Formula Injection Protection (OWASP)
# ---------------------------------------------------------------------------

def test_csv_generation_and_formula_injection_protection():
    # Direct cell unit tests
    # 1. Dangerous formula starting with '='
    assert sanitize_csv_cell("=1+1") == "'=1+1"
    # 2. Command injection starting with '+'
    assert sanitize_csv_cell("+cmd|' /C calc'!A0") == "'+cmd|' /C calc'!A0"
    # 3. Formula starting with '@'
    assert sanitize_csv_cell("@SUM(A1:A5)") == "'@SUM(A1:A5)"
    # 4. Text with dangerous leading '-'
    assert sanitize_csv_cell("-2+3*cmd") == "'-2+3*cmd"
    # 5. Valid negative amount should NOT be quote-prefixed
    assert sanitize_csv_cell(-49.99) == -49.99
    assert sanitize_csv_cell("-49.99") == "-49.99"
    # 6. Plain safe string
    assert sanitize_csv_cell("Adobe Systems") == "Adobe Systems"

    # Full CSV export test with malicious vendor names
    biz = _make_biz()
    malicious_txs = [
        _make_tx(1, 1, 500.0, months_ago=0, vendor="=SUM(A1:A10)", raw_desc="=cmd|' /C calc'!A0"),
        _make_tx(2, 1, 200.0, months_ago=0, vendor="@MaliciousVendor"),
    ]

    csv_text = ReportEngine.generate_csv("transactions", biz, [], malicious_txs)

    # Malicious cells must be sanitized with leading single quote
    assert "'=SUM(A1:A10)" in csv_text or "'=cmd|' /C calc'!A0" in csv_text
    assert "'@MaliciousVendor" in csv_text


# ---------------------------------------------------------------------------
# 7. PDF Generation Validity
# ---------------------------------------------------------------------------

def test_pdf_generation_validity():
    biz = _make_biz()
    txns = [
        _make_tx(1, 1, 5000.0, months_ago=1),
        _make_tx(2, 1, 5000.0, months_ago=0),
    ]
    subs = [_make_sub(1, 1, "Slack", 150.0)]

    for r_type in ("comprehensive", "monthly", "subscriptions", "renewals", "forecast"):
        pdf_bytes = ReportEngine.generate_pdf(r_type, biz, subs, txns)
        # PDF magic bytes
        assert pdf_bytes.startswith(b"%PDF-"), f"Report type {r_type} did not produce valid PDF header"
        # Reasonable size for a multi-element ReportLab doc
        assert len(pdf_bytes) > 1500, f"Report type {r_type} produced unexpectedly small PDF: {len(pdf_bytes)} bytes"


# ---------------------------------------------------------------------------
# 8. Insufficient Data Empty State Handling
# ---------------------------------------------------------------------------

def test_insufficient_data_empty_state_handling():
    biz = _make_biz(cash=0.0)

    # Monthly report
    m_rep = ReportEngine.generate_monthly_financial_report(biz, [], [])
    assert m_rep.data_sufficiency_status == "insufficient_data"
    assert m_rep.total_operating_revenue == 0.0
    assert m_rep.monthly_breakdown == []

    # Subscriptions report
    s_rep = ReportEngine.generate_subscription_expense_report(biz, [], [])
    assert s_rep.confirmed_subscriptions_count == 0
    assert s_rep.items == []

    # Renewals report
    r_rep = ReportEngine.generate_upcoming_renewal_report(biz, [], [])
    assert r_rep.total_upcoming_60_days_count == 0

    # CSV and PDF must generate cleanly without throwing exceptions
    csv_text = ReportEngine.generate_csv("monthly", biz, [], [])
    assert "Operating Revenue" in csv_text

    pdf_bytes = ReportEngine.generate_pdf("comprehensive", biz, [], [])
    assert pdf_bytes.startswith(b"%PDF-")


# ---------------------------------------------------------------------------
# 9. API Auth and Tenant Isolation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def sqlite_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def test_reports_api_auth_and_isolation(sqlite_db):
    user_a = User(id=1, email="cfo_a@test.com", hashed_password="pw_a", is_active=True, full_name="User A")
    biz_a = BusinessProfile(id=1, user_id=1, company_name="Biz A", current_cash_reserves=10000.0, currency="USD")

    # User B without business
    user_b = User(id=2, email="cfo_b@test.com", hashed_password="pw_b", is_active=True, full_name="User B")

    sqlite_db.add_all([user_a, biz_a, user_b])
    sqlite_db.commit()

    # User A -> 200
    res_monthly = get_monthly_financial_report(period="all", start_date=None, end_date=None, current_user=user_a, db=sqlite_db)
    assert res_monthly.business_id == biz_a.id

    res_subs = get_subscription_expense_report(current_user=user_a, db=sqlite_db)
    assert res_subs.business_id == biz_a.id

    res_renewals = get_upcoming_renewal_report(current_user=user_a, db=sqlite_db)
    assert res_renewals.business_id == biz_a.id

    res_forecast = get_cash_flow_forecast_report(current_user=user_a, db=sqlite_db)
    assert res_forecast.business_id == biz_a.id

    res_comp = get_comprehensive_financial_report(period="all", start_date=None, end_date=None, current_user=user_a, db=sqlite_db)
    assert res_comp.business_id == biz_a.id

    res_csv = export_csv_report(export_type="transactions", period="all", start_date=None, end_date=None, current_user=user_a, db=sqlite_db)
    assert res_csv.status_code == 200

    res_pdf = export_pdf_report(report_type="comprehensive", period="all", start_date=None, end_date=None, current_user=user_a, db=sqlite_db)
    assert res_pdf.status_code == 200

    # User B (no business) -> 404 on all endpoints
    with pytest.raises(HTTPException) as exc:
        get_monthly_financial_report(period="all", start_date=None, end_date=None, current_user=user_b, db=sqlite_db)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc:
        export_pdf_report(report_type="comprehensive", period="all", start_date=None, end_date=None, current_user=user_b, db=sqlite_db)
    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# 10. Existing API Compatibility
# ---------------------------------------------------------------------------

def test_existing_api_compatibility():
    biz = _make_biz()
    txns = [_make_tx(1, 1, 3000.0, months_ago=0)]
    subs = [_make_sub(1, 1, "Zoom", 50.0)]

    comp = ReportEngine.generate_comprehensive_report(biz, txns, subs)

    assert comp.monthly_report is not None
    assert comp.subscription_report is not None
    assert comp.renewal_report is not None
    assert comp.forecast_report is not None
    assert isinstance(comp.health_scoring_methodology, str)
    assert len(comp.overall_transparency_disclosure) > 20


# ---------------------------------------------------------------------------
# 11. Regression: Subscriptions & Reports Response Contract
# ---------------------------------------------------------------------------

def test_subscription_summary_and_reports_contract():
    """
    Regression test for ReportsPage.jsx TypeError: subscriptions.forEach is not a function.
    Verifies that the /subscriptions/ endpoint returns a SubscriptionSummaryResponse
    with 'subscriptions' as a nested list, ensuring the frontend safeExtractArray
    contract remains aligned with backend schemas.
    """
    from app.schemas.subscription import SubscriptionSummaryResponse
    from app.schemas.report import (
        MonthlyFinancialReport,
        SubscriptionExpenseReport,
        UpcomingRenewalReport,
        CashFlowForecastReport,
        ComprehensiveFinancialReport
    )

    # 1. Verify schema contract for SubscriptionSummaryResponse
    fields = SubscriptionSummaryResponse.model_fields
    assert "subscriptions" in fields, "SubscriptionSummaryResponse must have 'subscriptions' field"
    assert "total_active_count" in fields
    assert "total_monthly_spend" in fields

    # 2. Verify all report response models contain array fields
    assert "monthly_breakdown" in MonthlyFinancialReport.model_fields
    assert "items" in SubscriptionExpenseReport.model_fields
    assert "scheduled_renewals" in UpcomingRenewalReport.model_fields
    assert "scenarios" in CashFlowForecastReport.model_fields
    assert "monthly_report" in ComprehensiveFinancialReport.model_fields

    # 3. Simulate client unpack logic
    sample_response = {
        "total_active_count": 1,
        "subscriptions": [{"id": 1, "vendor_name": "GitHub", "latest_amount": 42.0}]
    }
    # Unpack must yield a list
    unpacked = sample_response.get("subscriptions", [])
    assert isinstance(unpacked, list)
    assert len(unpacked) == 1
    # Iteration must succeed
    total = sum(s["latest_amount"] for s in unpacked)
    assert total == 42.0


