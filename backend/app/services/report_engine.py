"""
Stage 6: Report Engine & Export Intelligence Service
Generates structured Monthly Financial Reports, Subscription Expense Reports,
Upcoming Renewal Reports, 6-Month Cash-Flow Forecast Reports, and Comprehensive
Intelligence Reports.

Provides:
1. Date range filtering over completed operating ledger records.
2. CSV exports with spreadsheet formula injection protection (OWASP CSV Injection).
3. Professional PDF report compilation via ReportLab with branded styling,
   page numbers ("Page X of Y"), and methodology disclosures.
4. Strict separation of historical actuals from forward projections.
5. Protection against data fabrication for insufficient data accounts.
"""
import io
import csv
import datetime
import calendar
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

from app.models.business import BusinessProfile
from app.models.subscription import Subscription
from app.models.transaction import Transaction
from app.services.forecast_engine import ForecastEngine
from app.services.subscription_analyzer import SubscriptionExpenseAnalyzer
from app.services.financial_intelligence_engine import FinancialIntelligenceEngine
from app.services.normalizer import TransactionNormalizer
from app.schemas.report import (
    ReportPeriodFilter,
    MonthlyReportMonthItem,
    MonthlyFinancialReport,
    SubscriptionExpenseReportItem,
    SubscriptionExpenseReport,
    UpcomingRenewalReportItem,
    UpcomingRenewalReport,
    ForecastScenarioMonthItem,
    ForecastScenarioSummary,
    CashFlowForecastReport,
    ComprehensiveFinancialReport,
)


# ---------------------------------------------------------------------------
# Numbered Canvas for "Page X of Y" and professional header/footer
# ---------------------------------------------------------------------------

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass ReportLab canvas that dynamically writes running header, rule,
    and footer with true total page count ('Page X of Y').
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        # Top running header (pages 2+)
        if self._pageNumber > 1:
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#003087"))
            self.drawString(36, 755, "PayPal SubWise AI")
            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748b"))
            self.drawString(130, 755, "— Financial Intelligence & Subscription Cash-Flow Report")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(36, 747, 576, 747)

        # Bottom footer (all pages)
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(36, 42, 576, 42)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(36, 30, "CONFIDENTIAL · PayPal SubWise AI · Figures derived from completed PayPal ledger records.")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(576, 30, page_str)
        self.restoreState()


# ---------------------------------------------------------------------------
# CSV Formula Injection Protection
# ---------------------------------------------------------------------------

def sanitize_csv_cell(value: Any) -> Any:
    """
    Protects spreadsheet users from CSV / Formula Injection (DDE attacks).
    If a textual cell starts with '=', '+', '-', '@', '\\t', or '\\r',
    and is not a valid standard numeric float/integer, prepend a single quote (').
    """
    if value is None:
        return ""
    if isinstance(value, (int, float, Decimal)):
        return value

    s = str(value)
    if not s:
        return ""

    # Check if string starts with formula trigger characters
    if s[0] in ("=", "+", "-", "@", "\t", "\r"):
        # Test if it is purely numeric (e.g. "-49.99", "+100")
        try:
            float(s)
            return s  # Safe numeric string
        except ValueError:
            # Dangerous formula or command payload — prefix with single quote
            return f"'{s}"

    return s


# ---------------------------------------------------------------------------
# Report Engine Service
# ---------------------------------------------------------------------------

class ReportEngine:
    """
    Core engine for assembling financial reports, applying period filters,
    and rendering CSV / PDF export deliverables.
    """

    DISCLAIMER_TEXT = (
        "All historical figures are derived strictly from settled PayPal Sandbox ledger records. "
        "The displayed cash balance reflects net PayPal transaction flows in this dataset — not an "
        "independently verified PayPal Account Balance. Forward projections are mathematical scenario "
        "estimates and are not guaranteed financial outcomes. Potential subscription commitments are "
        "first-cycle vendor disbursements awaiting contractual confirmation."
    )

    @classmethod
    def filter_transactions_by_period(
        cls,
        transactions: List[Transaction],
        period_preset: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Tuple[List[Transaction], ReportPeriodFilter]:
        """
        Filters completed operating transactions based on period presets or custom date bounds.
        Presets: 'all', 'last_30_days', 'last_90_days', 'last_180_days', 'ytd', 'custom'.
        """
        valid_txs = [
            tx for tx in transactions
            if ForecastEngine.is_valid_operating(tx, all_txs=transactions) and tx.transaction_date
        ]

        if not valid_txs:
            filt = ReportPeriodFilter(
                period_preset=period_preset,
                start_date=start_date,
                end_date=end_date,
                available_history_start=None,
                available_history_end=None,
                total_operating_records_in_period=0,
            )
            return [], filt

        # Determine true ledger bounds from actual completed data
        all_dates = [tx.transaction_date for tx in valid_txs]
        avail_start = min(all_dates)
        avail_end = max(all_dates)

        target_start = avail_start
        target_end = avail_end

        preset_clean = (period_preset or "all").lower().strip()

        if preset_clean == "last_30_days":
            target_start = max(avail_start, avail_end - datetime.timedelta(days=30))
        elif preset_clean == "last_90_days":
            target_start = max(avail_start, avail_end - datetime.timedelta(days=90))
        elif preset_clean == "last_180_days":
            target_start = max(avail_start, avail_end - datetime.timedelta(days=180))
        elif preset_clean == "ytd":
            y_start = datetime.datetime(avail_end.year, 1, 1, 0, 0, 0)
            target_start = max(avail_start, y_start)
        elif preset_clean == "custom":
            if start_date:
                try:
                    target_start = datetime.datetime.fromisoformat(start_date)
                except Exception:
                    pass
            if end_date:
                try:
                    target_end = datetime.datetime.fromisoformat(end_date)
                except Exception:
                    pass

        filtered = [
            tx for tx in valid_txs
            if target_start <= tx.transaction_date <= target_end
        ]

        filt = ReportPeriodFilter(
            period_preset=preset_clean,
            start_date=target_start.strftime("%Y-%m-%d"),
            end_date=target_end.strftime("%Y-%m-%d"),
            available_history_start=avail_start.strftime("%Y-%m-%d"),
            available_history_end=avail_end.strftime("%Y-%m-%d"),
            total_operating_records_in_period=len(filtered),
        )

        return filtered, filt

    @classmethod
    def generate_monthly_financial_report(
        cls,
        business: BusinessProfile,
        transactions: List[Transaction],
        subscriptions: List[Subscription],
        period_preset: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> MonthlyFinancialReport:
        """
        Builds the Monthly Financial Report from completed ledger transactions.
        """
        filtered_txs, period_filter = cls.filter_transactions_by_period(
            transactions, period_preset, start_date, end_date
        )

        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Determine cash basis and status
        starting_cash, has_verified_cash = ForecastEngine.calculate_verified_cash_balance(business, transactions)
        total_settled_net = sum(
            float(tx.net_amount if tx.net_amount is not None else tx.gross_amount)
            for tx in transactions if (tx.status or "").upper() == "COMPLETED"
        )

        if has_verified_cash and starting_cash is not None:
            cash_prov = f"Net sum of settled PayPal ledger transactions (${starting_cash:,.2f})."
        elif business.current_cash_reserves and business.current_cash_reserves > 0:
            cash_prov = "Business Profile declared liquid reserves."
        else:
            cash_prov = "No verified liquid cash basis recorded."

        paypal_balance_note = (
            "IMPORTANT: The displayed cash figure is derived from net PayPal transaction flows in this dataset. "
            "It is NOT equivalent to your verified PayPal Account Balance. Verify actual reserves in PayPal."
        )

        if not filtered_txs:
            return MonthlyFinancialReport(
                business_id=business.id,
                company_name=business.company_name,
                generated_at=now_str,
                reporting_period="No completed operating records in selected period",
                period_filter=period_filter,
                data_sufficiency_status="insufficient_data",
                total_operating_revenue=0.0,
                total_non_sub_expenses=0.0,
                total_confirmed_sub_expenses=0.0,
                total_potential_sub_expenses=0.0,
                total_operating_expenses=0.0,
                net_operating_cashflow=0.0,
                average_monthly_revenue=0.0,
                average_monthly_expenses=0.0,
                verified_available_cash=starting_cash if has_verified_cash else None,
                cash_provenance=cash_prov,
                paypal_balance_note=paypal_balance_note,
                monthly_breakdown=[],
                disclaimer=cls.DISCLAIMER_TEXT,
            )

        # Categorize subscriptions by vendor name
        confirmed_subs = [s for s in subscriptions if getattr(s, "detection_type", "confirmed") == "confirmed" and s.status != "cancelled"]
        potential_subs = [s for s in subscriptions if getattr(s, "detection_type", "confirmed") == "potential" and s.status != "cancelled"]
        confirmed_vendors = {(s.vendor_name or "").lower().strip() for s in confirmed_subs}
        potential_vendors = {(s.vendor_name or "").lower().strip() for s in potential_subs}

        # Monthly buckets
        month_buckets: Dict[str, Dict[str, Any]] = {}

        for tx in filtered_txs:
            d = tx.transaction_date
            key = f"{d.year}-{d.month:02d}"
            label = f"{calendar.month_abbr[d.month]} {d.year}"
            if key not in month_buckets:
                month_buckets[key] = {
                    "key": key,
                    "label": label,
                    "revenue": 0.0,
                    "non_sub": 0.0,
                    "confirmed_sub": 0.0,
                    "potential_sub": 0.0,
                    "tx_count": 0,
                }

            amt = float(tx.gross_amount)
            month_buckets[key]["tx_count"] += 1

            if amt > 0:
                month_buckets[key]["revenue"] += amt
            else:
                outflow = abs(amt)
                v_name = (tx.normalized_vendor or "").lower().strip()
                norm_meta = TransactionNormalizer.normalize_vendor_and_category(tx.raw_description)
                norm_v = (norm_meta.get("normalized_vendor") or "").lower().strip()

                if v_name in confirmed_vendors or norm_v in confirmed_vendors:
                    month_buckets[key]["confirmed_sub"] += outflow
                elif v_name in potential_vendors or norm_v in potential_vendors:
                    month_buckets[key]["potential_sub"] += outflow
                else:
                    month_buckets[key]["non_sub"] += outflow

        sorted_keys = sorted(month_buckets.keys())
        monthly_items: List[MonthlyReportMonthItem] = []

        total_rev = 0.0
        total_non_sub = 0.0
        total_c_sub = 0.0
        total_p_sub = 0.0

        for k in sorted_keys:
            b = month_buckets[k]
            tot_exp = round(b["non_sub"] + b["confirmed_sub"], 2)
            net_cf = round(b["revenue"] - tot_exp, 2)
            total_rev += b["revenue"]
            total_non_sub += b["non_sub"]
            total_c_sub += b["confirmed_sub"]
            total_p_sub += b["potential_sub"]

            monthly_items.append(MonthlyReportMonthItem(
                month_key=b["key"],
                month_label=b["label"],
                operating_revenue=round(b["revenue"], 2),
                non_sub_expenses=round(b["non_sub"], 2),
                confirmed_subscription_expenses=round(b["confirmed_sub"], 2),
                potential_subscription_expenses=round(b["potential_sub"], 2),
                total_operating_expenses=tot_exp,
                net_operating_cashflow=net_cf,
                operating_transaction_count=b["tx_count"],
                period_type="ACTUAL",
            ))

        months_cnt = max(len(monthly_items), 1)
        tot_exp_all = round(total_non_sub + total_c_sub, 2)
        net_all = round(total_rev - tot_exp_all, 2)

        rep_period = f"{period_filter.start_date} to {period_filter.end_date}" if period_filter.start_date else "All Available History"
        data_status = "sufficient_data" if len(monthly_items) >= 2 and total_rev > 0 else "limited_data"

        return MonthlyFinancialReport(
            business_id=business.id,
            company_name=business.company_name,
            generated_at=now_str,
            reporting_period=rep_period,
            period_filter=period_filter,
            data_sufficiency_status=data_status,
            total_operating_revenue=round(total_rev, 2),
            total_non_sub_expenses=round(total_non_sub, 2),
            total_confirmed_sub_expenses=round(total_c_sub, 2),
            total_potential_sub_expenses=round(total_p_sub, 2),
            total_operating_expenses=tot_exp_all,
            net_operating_cashflow=net_all,
            average_monthly_revenue=round(total_rev / months_cnt, 2),
            average_monthly_expenses=round(tot_exp_all / months_cnt, 2),
            verified_available_cash=starting_cash if has_verified_cash else None,
            cash_provenance=cash_prov,
            paypal_balance_note=paypal_balance_note,
            monthly_breakdown=monthly_items,
            disclaimer=cls.DISCLAIMER_TEXT,
        )

    @classmethod
    def generate_subscription_expense_report(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
    ) -> SubscriptionExpenseReport:
        """
        Builds the Subscription Expense Report detailing all confirmed and potential software overhead.
        """
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Map historical payments per vendor from completed transactions
        vendor_history: Dict[str, Dict[str, Any]] = {}
        for tx in transactions:
            if (tx.status or "").upper() == "COMPLETED" and tx.gross_amount and float(tx.gross_amount) < 0:
                v = (tx.normalized_vendor or "").lower().strip()
                if v not in vendor_history:
                    vendor_history[v] = {"count": 0, "total": 0.0}
                vendor_history[v]["count"] += 1
                vendor_history[v]["total"] += abs(float(tx.gross_amount))

        items: List[SubscriptionExpenseReportItem] = []
        confirmed_m_tot = 0.0
        confirmed_a_tot = 0.0
        potential_m_tot = 0.0
        potential_a_tot = 0.0
        confirmed_count = 0
        potential_count = 0

        category_sums: Dict[str, float] = {}

        for sub in subscriptions:
            if sub.status == "cancelled":
                continue

            cadence = getattr(sub, "cadence", "monthly") or "monthly"
            m_eq, a_eq = SubscriptionExpenseAnalyzer.calculate_cadence_equivalents(
                float(sub.latest_amount or 0.0), cadence
            )

            det_type = getattr(sub, "detection_type", "confirmed") or "confirmed"
            v_key = (sub.vendor_name or "").lower().strip()
            hist = vendor_history.get(v_key, {"count": 0, "total": 0.0})

            pct = float(sub.price_change_pct or 0.0)
            has_creep = pct >= 15.0 and det_type == "confirmed"
            creep_note = f"+{pct:.1f}% escalation detected vs baseline" if has_creep else None

            next_dt_str = None
            if getattr(sub, "next_billing_date", None):
                dt = sub.next_billing_date
                if isinstance(dt, (datetime.datetime, datetime.date)):
                    next_dt_str = dt.strftime("%Y-%m-%d")
                else:
                    next_dt_str = str(dt)

            cat = sub.category or "General Software"

            if det_type == "confirmed":
                confirmed_count += 1
                confirmed_m_tot += m_eq
                confirmed_a_tot += a_eq
                category_sums[cat] = category_sums.get(cat, 0.0) + m_eq
            else:
                potential_count += 1
                potential_m_tot += m_eq
                potential_a_tot += a_eq

            items.append(SubscriptionExpenseReportItem(
                id=sub.id,
                vendor_name=sub.vendor_name or "Unknown Vendor",
                category=cat,
                billing_frequency=cadence,
                latest_amount=round(float(sub.latest_amount or 0.0), 2),
                average_amount=round(float(sub.average_amount or sub.latest_amount or 0.0), 2),
                monthly_equivalent=round(m_eq, 2),
                annual_run_rate=round(a_eq, 2),
                detection_type=det_type,
                priority_tier=getattr(sub, "priority_tier", 2) or 2,
                status=sub.status or "active",
                price_change_pct=round(pct, 1),
                has_price_creep=has_creep,
                price_change_note=creep_note,
                next_billing_date=next_dt_str,
                historical_payment_count=hist["count"],
                total_historical_spend=round(hist["total"], 2),
            ))

        # Sort confirmed first, then by monthly equivalent descending
        items.sort(key=lambda x: (0 if x.detection_type == "confirmed" else 1, -x.monthly_equivalent))

        cat_breakdown = [
            {"category": k, "monthly_total": round(v, 2), "annual_total": round(v * 12, 2)}
            for k, v in sorted(category_sums.items(), key=lambda x: -x[1])
        ]

        return SubscriptionExpenseReport(
            business_id=business.id,
            company_name=business.company_name,
            generated_at=now_str,
            confirmed_subscriptions_count=confirmed_count,
            potential_subscriptions_count=potential_count,
            total_confirmed_monthly_commitments=round(confirmed_m_tot, 2),
            total_confirmed_annual_commitments=round(confirmed_a_tot, 2),
            total_potential_monthly_commitments=round(potential_m_tot, 2),
            total_potential_annual_commitments=round(potential_a_tot, 2),
            items=items,
            category_breakdown=cat_breakdown,
            disclaimer=cls.DISCLAIMER_TEXT,
        )

    @classmethod
    def generate_upcoming_renewal_report(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
    ) -> UpcomingRenewalReport:
        """
        Builds the Upcoming Renewal Report using the Stage 3 calendar schedule.
        """
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Reuse ForecastEngine calendar schedule directly
        payment_cal, monthly_scheduled, unknown_cnt, month_targets, concentration_warns = (
            ForecastEngine.schedule_subscription_payments(
                subscriptions=subscriptions,
                eval_date=datetime.datetime.utcnow(),
                forecast_months=6,
            )
        )

        renewals: List[UpcomingRenewalReportItem] = []
        tot_60d_amt = 0.0
        tot_60d_cnt = 0

        for p in payment_cal:
            amt = float(p.get("expected_payment_amount") or 0.0)
            m_idx = int(p.get("month_index") or 1)
            det_type = p.get("detection_type", "confirmed")

            if m_idx <= 2:
                tot_60d_cnt += 1
                if det_type == "confirmed":
                    tot_60d_amt += amt

            renewals.append(UpcomingRenewalReportItem(
                vendor_name=p.get("vendor_name", "Vendor"),
                expected_payment_date=str(p.get("expected_payment_date", "")),
                expected_payment_amount=round(amt, 2),
                currency=p.get("currency", "USD"),
                billing_frequency=p.get("billing_frequency", "monthly"),
                detection_type=det_type,
                is_date_confirmed=p.get("is_confirmed_date", True),
                month_index=m_idx,
                month_name=p.get("month_name", ""),
                is_high_concentration=p.get("is_high_concentration", False),
            ))

        return UpcomingRenewalReport(
            business_id=business.id,
            company_name=business.company_name,
            generated_at=now_str,
            total_upcoming_60_days_count=tot_60d_cnt,
            total_upcoming_60_days_amount=round(tot_60d_amt, 2),
            unknown_renewal_date_count=unknown_cnt,
            monthly_concentration_warnings=concentration_warns,
            monthly_totals=monthly_scheduled,
            scheduled_renewals=renewals,
            disclaimer=cls.DISCLAIMER_TEXT,
        )

    @classmethod
    def generate_forecast_report(
        cls,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
    ) -> CashFlowForecastReport:
        """
        Builds the 6-Month Cash-Flow Forecast Report with Optimistic, Baseline, and Conservative scenarios.
        """
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        forecast = ForecastEngine.generate_forecast(
            business=business,
            subscriptions=subscriptions,
            transactions=transactions,
            forecast_months=6,
        )

        status = forecast.get("status", "insufficient_data")
        scenarios_raw = forecast.get("scenarios") or {}
        scenarios_out: Dict[str, ForecastScenarioSummary] = {}

        for s_key in ("optimistic", "baseline", "conservative"):
            raw_s = forecast.get(s_key) or (forecast.get("scenarios") or {}).get(s_key) or {}
            months_list = raw_s.get("months") or []

            timeline_items: List[ForecastScenarioMonthItem] = []
            lowest_bal: Optional[float] = None

            for m in months_list:
                bal = m.get("projected_closing_cash_balance")
                if bal is not None:
                    if lowest_bal is None or bal < lowest_bal:
                        lowest_bal = bal

                timeline_items.append(ForecastScenarioMonthItem(
                    month_index=m.get("month", 1),
                    month_name=m.get("month_name", ""),
                    projected_revenue=round(float(m.get("projected_operating_revenue") or 0.0), 2),
                    projected_non_sub_expenses=round(float(m.get("projected_non_sub_expenses") or 0.0), 2),
                    projected_confirmed_sub_expenses=round(float(m.get("projected_confirmed_subscription_expenses") or 0.0), 2),
                    potential_sub_expenses=round(float(m.get("potential_subscription_expenses") or 0.0), 2),
                    projected_net_cashflow=round(float(m.get("projected_net_cashflow") or 0.0), 2),
                    projected_closing_balance=round(float(bal), 2) if bal is not None else None,
                    is_cash_depleted=bool(m.get("is_cash_depleted", False)),
                ))

            assump = raw_s.get("assumptions") or {}
            scenarios_out[s_key] = ForecastScenarioSummary(
                scenario_name=s_key,
                display_label=raw_s.get("display_label", s_key.title()),
                revenue_adjustment_pct=float(assump.get("revenue_adjustment_pct", 0.0)),
                monthly_projected_revenue=round(float(raw_s.get("monthly_revenue") or 0.0), 2),
                monthly_projected_expenses=round(float(raw_s.get("monthly_non_sub_expenses") or 0.0), 2),
                monthly_confirmed_sub_expenses=round(float(raw_s.get("monthly_confirmed_sub_expenses") or 0.0), 2),
                monthly_projected_net_cashflow=round(float(raw_s.get("monthly_net_cashflow") or 0.0), 2),
                lowest_projected_closing_balance=round(lowest_bal, 2) if lowest_bal is not None else None,
                runway_status=raw_s.get("runway_note", "Indeterminate") if raw_s.get("runway_available") else "Indeterminate",
                runway_months=raw_s.get("runway_months"),
                runway_note=raw_s.get("runway_note", ""),
                timeline=timeline_items,
            )

        return CashFlowForecastReport(
            business_id=business.id,
            company_name=business.company_name,
            generated_at=now_str,
            data_sufficiency_status=status,
            forecast_months=6,
            scenarios=scenarios_out,
            assumptions_disclosure=(
                "Scenario projections apply configurable top-line revenue adjustments (+15% Optimistic, 0% Baseline, -20% Conservative). "
                "Confirmed contractual subscription obligations and historical non-subscription operating expenses are held constant across all scenarios. "
                "These calculations are deterministic sensitivity models, not speculative AI predictions."
            ),
            methodology_note=forecast.get("scenario_methodology_note", ""),
        )

    @classmethod
    def generate_comprehensive_report(
        cls,
        business: BusinessProfile,
        transactions: List[Transaction],
        subscriptions: List[Subscription],
        period_preset: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> ComprehensiveFinancialReport:
        """
        Assembles the all-inclusive Executive Financial Intelligence Report.
        """
        now_str = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        monthly = cls.generate_monthly_financial_report(
            business, transactions, subscriptions, period_preset, start_date, end_date
        )
        sub_rep = cls.generate_subscription_expense_report(business, subscriptions, transactions)
        ren_rep = cls.generate_upcoming_renewal_report(business, subscriptions, transactions)
        fc_rep = cls.generate_forecast_report(business, subscriptions, transactions)

        # Overview from Stage 5 engine for health index and briefing
        overview = FinancialIntelligenceEngine.generate_overview(business, subscriptions, transactions)

        return ComprehensiveFinancialReport(
            business_id=business.id,
            company_name=business.company_name,
            generated_at=now_str,
            reporting_period=monthly.reporting_period,
            monthly_report=monthly,
            subscription_report=sub_rep,
            renewal_report=ren_rep,
            forecast_report=fc_rep,
            health_score=overview.financial_health_index.score,
            health_status=overview.financial_health_index.status_label,
            health_scoring_methodology=overview.financial_health_index.scoring_methodology,
            risk_triggers=[r.model_dump() for r in overview.risk_intelligence],
            executive_briefing_markdown=overview.monthly_briefing.full_briefing_markdown,
            overall_transparency_disclosure=cls.DISCLAIMER_TEXT,
        )

    # -----------------------------------------------------------------------
    # CSV Generator
    # -----------------------------------------------------------------------

    @classmethod
    def generate_csv(
        cls,
        export_type: str,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
        period_preset: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """
        Generates CSV text with formula injection protection across all cells.
        Supported export types: 'transactions', 'subscriptions', 'renewals', 'forecast', 'monthly'.
        """
        out = io.StringIO()
        writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)

        exp_clean = (export_type or "transactions").lower().strip()

        if exp_clean == "transactions":
            filtered, _ = cls.filter_transactions_by_period(transactions, period_preset, start_date, end_date)
            writer.writerow([
                "Transaction Date", "Transaction ID", "Vendor / Description",
                "Category", "Gross Amount", "Fee Amount", "Net Amount",
                "Currency", "Status", "Operating Classification"
            ])
            for tx in filtered:
                is_op = ForecastEngine.is_valid_operating(tx)
                writer.writerow([
                    sanitize_csv_cell(tx.transaction_date.strftime("%Y-%m-%d %H:%M") if tx.transaction_date else ""),
                    sanitize_csv_cell(tx.paypal_transaction_id or str(tx.id)),
                    sanitize_csv_cell(tx.normalized_vendor or tx.raw_description or "General"),
                    sanitize_csv_cell(tx.category or "General Software"),
                    sanitize_csv_cell(tx.gross_amount),
                    sanitize_csv_cell(tx.fee_amount or 0.0),
                    sanitize_csv_cell(tx.net_amount if tx.net_amount is not None else tx.gross_amount),
                    sanitize_csv_cell(tx.currency or "USD"),
                    sanitize_csv_cell(tx.status or "COMPLETED"),
                    sanitize_csv_cell("Operating" if is_op else "Non-Operating / Adjustment"),
                ])

        elif exp_clean == "subscriptions":
            rep = cls.generate_subscription_expense_report(business, subscriptions, transactions)
            writer.writerow([
                "Vendor Name", "Category", "Billing Cadence", "Latest Amount",
                "Monthly Equivalent", "Annual Run Rate", "Classification",
                "Price Creep %", "Priority Tier", "Status", "Next Billing Date",
                "Historical Payment Count", "Total Historical Spend"
            ])
            for s in rep.items:
                writer.writerow([
                    sanitize_csv_cell(s.vendor_name),
                    sanitize_csv_cell(s.category),
                    sanitize_csv_cell(s.billing_frequency),
                    sanitize_csv_cell(s.latest_amount),
                    sanitize_csv_cell(s.monthly_equivalent),
                    sanitize_csv_cell(s.annual_run_rate),
                    sanitize_csv_cell(s.detection_type),
                    sanitize_csv_cell(s.price_change_pct),
                    sanitize_csv_cell(s.priority_tier),
                    sanitize_csv_cell(s.status),
                    sanitize_csv_cell(s.next_billing_date or "Unknown"),
                    sanitize_csv_cell(s.historical_payment_count),
                    sanitize_csv_cell(s.total_historical_spend),
                ])

        elif exp_clean == "renewals":
            ren = cls.generate_upcoming_renewal_report(business, subscriptions, transactions)
            writer.writerow([
                "Vendor Name", "Expected Renewal Date", "Expected Amount",
                "Currency", "Billing Frequency", "Classification",
                "Date Confirmed", "Month Index", "Month Name", "Concentration Warning"
            ])
            for r in ren.scheduled_renewals:
                writer.writerow([
                    sanitize_csv_cell(r.vendor_name),
                    sanitize_csv_cell(r.expected_payment_date),
                    sanitize_csv_cell(r.expected_payment_amount),
                    sanitize_csv_cell(r.currency),
                    sanitize_csv_cell(r.billing_frequency),
                    sanitize_csv_cell(r.detection_type),
                    sanitize_csv_cell("Yes" if r.is_date_confirmed else "Estimated"),
                    sanitize_csv_cell(r.month_index),
                    sanitize_csv_cell(r.month_name),
                    sanitize_csv_cell("High Concentration Spike" if r.is_high_concentration else "Normal"),
                ])

        elif exp_clean == "forecast":
            fc = cls.generate_forecast_report(business, subscriptions, transactions)
            writer.writerow([
                "Scenario", "Month", "Month Name", "Projected Revenue",
                "Projected Non-Sub Expenses", "Projected Confirmed Sub Expenses",
                "Potential Sub Expenses", "Projected Net Cashflow",
                "Projected Closing Balance", "Cash Depleted"
            ])
            for s_name, s_data in fc.scenarios.items():
                for m in s_data.timeline:
                    writer.writerow([
                        sanitize_csv_cell(s_data.display_label),
                        sanitize_csv_cell(m.month_index),
                        sanitize_csv_cell(m.month_name),
                        sanitize_csv_cell(m.projected_revenue),
                        sanitize_csv_cell(m.projected_non_sub_expenses),
                        sanitize_csv_cell(m.projected_confirmed_sub_expenses),
                        sanitize_csv_cell(m.potential_sub_expenses),
                        sanitize_csv_cell(m.projected_net_cashflow),
                        sanitize_csv_cell(m.projected_closing_balance if m.projected_closing_balance is not None else "N/A"),
                        sanitize_csv_cell("Depleted" if m.is_cash_depleted else "Solvent"),
                    ])

        elif exp_clean == "monthly":
            m_rep = cls.generate_monthly_financial_report(business, transactions, subscriptions, period_preset, start_date, end_date)
            writer.writerow([
                "Month", "Month Key", "Operating Revenue", "Non-Subscription Expenses",
                "Confirmed Subscription Expenses", "Potential Subscription Expenses",
                "Total Operating Expenses", "Net Operating Cashflow", "Transaction Count", "Period Classification"
            ])
            for m in m_rep.monthly_breakdown:
                writer.writerow([
                    sanitize_csv_cell(m.month_label),
                    sanitize_csv_cell(m.month_key),
                    sanitize_csv_cell(m.operating_revenue),
                    sanitize_csv_cell(m.non_sub_expenses),
                    sanitize_csv_cell(m.confirmed_subscription_expenses),
                    sanitize_csv_cell(m.potential_subscription_expenses),
                    sanitize_csv_cell(m.total_operating_expenses),
                    sanitize_csv_cell(m.net_operating_cashflow),
                    sanitize_csv_cell(m.operating_transaction_count),
                    sanitize_csv_cell(m.period_type),
                ])

        return out.getvalue()

    # -----------------------------------------------------------------------
    # PDF Generator
    # -----------------------------------------------------------------------

    @classmethod
    def generate_pdf(
        cls,
        report_type: str,
        business: BusinessProfile,
        subscriptions: List[Subscription],
        transactions: List[Transaction],
        period_preset: str = "all",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> bytes:
        """
        Compiles a publication-quality PDF report using ReportLab.
        """
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=45,
            bottomMargin=45,
        )

        styles = getSampleStyleSheet()

        # Custom Palette & Typography
        c_primary = colors.HexColor("#003087")  # PayPal Deep Blue
        c_accent = colors.HexColor("#009cde")   # PayPal Cyan
        c_dark = colors.HexColor("#0f172a")     # Slate 900
        c_muted = colors.HexColor("#64748b")    # Slate 500
        c_light = colors.HexColor("#f8fafc")    # Slate 50
        c_border = colors.HexColor("#e2e8f0")   # Slate 200
        c_green = colors.HexColor("#059669")
        c_red = colors.HexColor("#dc2626")

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            textColor=c_primary,
            alignment=0,
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=c_muted,
            alignment=0,
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=c_primary,
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["Normal"],
            fontSize=8.5,
            leading=12,
            textColor=c_dark,
        )
        cell_bold = ParagraphStyle(
            "CellBold",
            parent=body_style,
            fontName="Helvetica-Bold",
        )
        cell_right = ParagraphStyle(
            "CellRight",
            parent=body_style,
            alignment=2,
        )
        cell_right_bold = ParagraphStyle(
            "CellRightBold",
            parent=body_style,
            alignment=2,
            fontName="Helvetica-Bold",
        )
        badge_style = ParagraphStyle(
            "Badge",
            parent=body_style,
            fontSize=7,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#1d4ed8"),
            alignment=1,
        )

        story = []

        rep_clean = (report_type or "comprehensive").lower().strip()

        # Titles & Headers
        titles_map = {
            "comprehensive": ("Executive Financial Intelligence Report", "Comprehensive CFO Report & Scenario Projections"),
            "monthly": ("Monthly Financial Report", "Operating Revenue, Disbursements & Cash Movements"),
            "subscriptions": ("Subscription Expense Report", "Contractual SaaS Commitments & Run Rate Analysis"),
            "renewals": ("Upcoming Subscription Renewal Report", "Calendar-Aware Renewal Schedule & Liquidity Spikes"),
            "forecast": ("6-Month Cash-Flow Forecast Report", "Multi-Scenario Projections & Liquidity Sensitivity"),
        }
        main_title, sub_title = titles_map.get(rep_clean, titles_map["comprehensive"])

        # 1. Header Banner
        now_dt = datetime.datetime.utcnow().strftime("%B %d, %Y")
        story.append(Paragraph(f"<b>{main_title}</b>", title_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Business:</b> {business.company_name} · <b>Generated:</b> {now_dt} · <b>Platform:</b> PayPal SubWise AI", subtitle_style))
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1.5, color=c_accent, spaceBefore=2, spaceAfter=12))

        # 2. Executive Health Summary Box (for comprehensive & monthly)
        if rep_clean in ("comprehensive", "monthly"):
            overview = FinancialIntelligenceEngine.generate_overview(business, subscriptions, transactions)
            hi = overview.financial_health_index
            ha = overview.historical_actuals

            score_str = str(hi.score) if hi.score is not None else "UNSCORED"
            status_str = hi.status_label

            summary_data = [
                [
                    Paragraph(f"<b>Financial Health Status</b><br/><font size=14 color='{c_primary.hexval()}'><b>{score_str}</b></font> · <font size=9>{status_str}</font>", body_style),
                    Paragraph(f"<b>Verified Monthly Revenue:</b> ${ha.historical_monthly_operating_revenue:,.2f}<br/><b>Monthly Software Commitments:</b> ${overview.forward_commitments.confirmed_monthly_subscription_commitments:,.2f}", body_style),
                    Paragraph(f"<b>Est. Liquid Cash:</b> ${ha.verified_available_cash:,.2f}<br/><b>Runway Status:</b> {overview.projected_estimates.runway_status}", body_style) if ha.verified_available_cash is not None else Paragraph(f"<b>Est. Liquid Cash:</b> Unverified<br/><b>Runway:</b> {overview.projected_estimates.runway_status}", body_style),
                ]
            ]
            summary_table = Table(summary_data, colWidths=[2.2 * inch, 2.7 * inch, 2.6 * inch])
            summary_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), c_light),
                ("BOX", (0, 0), (-1, -1), 1, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(summary_table)
            story.append(Spacer(1, 12))

        # 3. Monthly Financial Table
        if rep_clean in ("comprehensive", "monthly"):
            m_rep = cls.generate_monthly_financial_report(business, transactions, subscriptions, period_preset, start_date, end_date)
            story.append(Paragraph(f"<b>1. Historical Monthly Performance (Period: {m_rep.reporting_period})</b>", h2_style))

            if not m_rep.monthly_breakdown:
                story.append(Paragraph("<i>No completed operating transactions available in this period.</i>", body_style))
            else:
                m_table_data = [
                    [
                        Paragraph("<b>Month</b>", cell_bold),
                        Paragraph("<b>Operating Revenue</b>", cell_right_bold),
                        Paragraph("<b>Software Subs</b>", cell_right_bold),
                        Paragraph("<b>Non-Sub Outflows</b>", cell_right_bold),
                        Paragraph("<b>Total Expenses</b>", cell_right_bold),
                        Paragraph("<b>Net Cash Flow</b>", cell_right_bold),
                        Paragraph("<b>Status</b>", badge_style),
                    ]
                ]
                for mb in m_rep.monthly_breakdown:
                    net_color = c_green if mb.net_operating_cashflow >= 0 else c_red
                    m_table_data.append([
                        Paragraph(mb.month_label, body_style),
                        Paragraph(f"${mb.operating_revenue:,.2f}", cell_right),
                        Paragraph(f"${mb.confirmed_subscription_expenses:,.2f}", cell_right),
                        Paragraph(f"${mb.non_sub_expenses:,.2f}", cell_right),
                        Paragraph(f"${mb.total_operating_expenses:,.2f}", cell_right),
                        Paragraph(f"<font color='{net_color.hexval()}'><b>${mb.net_operating_cashflow:,.2f}</b></font>", cell_right),
                        Paragraph("ACTUAL", badge_style),
                    ])

                # Total Row
                net_tot_color = c_green if m_rep.net_operating_cashflow >= 0 else c_red
                m_table_data.append([
                    Paragraph("<b>Total Period</b>", cell_bold),
                    Paragraph(f"<b>${m_rep.total_operating_revenue:,.2f}</b>", cell_right_bold),
                    Paragraph(f"<b>${m_rep.total_confirmed_sub_expenses:,.2f}</b>", cell_right_bold),
                    Paragraph(f"<b>${m_rep.total_non_sub_expenses:,.2f}</b>", cell_right_bold),
                    Paragraph(f"<b>${m_rep.total_operating_expenses:,.2f}</b>", cell_right_bold),
                    Paragraph(f"<font color='{net_tot_color.hexval()}'><b>${m_rep.net_operating_cashflow:,.2f}</b></font>", cell_right_bold),
                    Paragraph("—", badge_style),
                ])

                m_table = Table(m_table_data, colWidths=[1.1 * inch, 1.15 * inch, 1.05 * inch, 1.15 * inch, 1.1 * inch, 1.15 * inch, 0.8 * inch])
                m_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, c_light]),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(m_table)

            story.append(Spacer(1, 14))

        # 4. Subscription Expense Breakdown Table
        if rep_clean in ("comprehensive", "subscriptions"):
            s_rep = cls.generate_subscription_expense_report(business, subscriptions, transactions)
            sec_num = "2" if rep_clean == "comprehensive" else "1"
            story.append(Paragraph(f"<b>{sec_num}. Contractual Subscription Commitments (${s_rep.total_confirmed_monthly_commitments:,.2f}/mo · ${s_rep.total_confirmed_annual_commitments:,.2f}/yr)</b>", h2_style))

            if not s_rep.items:
                story.append(Paragraph("<i>No active subscriptions detected in ledger records.</i>", body_style))
            else:
                s_table_data = [
                    [
                        Paragraph("<b>Vendor</b>", cell_bold),
                        Paragraph("<b>Category</b>", cell_bold),
                        Paragraph("<b>Cadence</b>", cell_bold),
                        Paragraph("<b>Monthly Eq.</b>", cell_right_bold),
                        Paragraph("<b>Annual Run Rate</b>", cell_right_bold),
                        Paragraph("<b>Type</b>", cell_bold),
                        Paragraph("<b>Price Creep</b>", cell_right_bold),
                    ]
                ]
                for s in s_rep.items[:15]:  # Top 15 subscriptions
                    creep_str = f"+{s.price_change_pct:.1f}%" if s.has_price_creep else "Normal"
                    c_color = c_red if s.has_price_creep else c_muted
                    s_table_data.append([
                        Paragraph(s.vendor_name[:20], body_style),
                        Paragraph(s.category[:16], body_style),
                        Paragraph(s.billing_frequency.capitalize(), body_style),
                        Paragraph(f"${s.monthly_equivalent:,.2f}", cell_right),
                        Paragraph(f"${s.annual_run_rate:,.2f}", cell_right),
                        Paragraph(s.detection_type.capitalize(), body_style),
                        Paragraph(f"<font color='{c_color.hexval()}'>{creep_str}</font>", cell_right),
                    ])

                s_table = Table(s_table_data, colWidths=[1.5 * inch, 1.3 * inch, 0.9 * inch, 1.0 * inch, 1.1 * inch, 0.9 * inch, 0.8 * inch])
                s_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(s_table)

            story.append(Spacer(1, 14))

        # 5. Upcoming Renewals Table
        if rep_clean in ("comprehensive", "renewals"):
            r_rep = cls.generate_upcoming_renewal_report(business, subscriptions, transactions)
            sec_num = "3" if rep_clean == "comprehensive" else "1"
            story.append(Paragraph(f"<b>{sec_num}. Upcoming Subscription Renewals (Next 60 Days: {r_rep.total_upcoming_60_days_count} due, ${r_rep.total_upcoming_60_days_amount:,.2f})</b>", h2_style))

            if not r_rep.scheduled_renewals:
                story.append(Paragraph("<i>No upcoming renewals scheduled in the calendar horizon.</i>", body_style))
            else:
                r_table_data = [
                    [
                        Paragraph("<b>Expected Date</b>", cell_bold),
                        Paragraph("<b>Vendor</b>", cell_bold),
                        Paragraph("<b>Cadence</b>", cell_bold),
                        Paragraph("<b>Amount</b>", cell_right_bold),
                        Paragraph("<b>Type</b>", cell_bold),
                        Paragraph("<b>Concentration</b>", cell_bold),
                    ]
                ]
                for pmt in r_rep.scheduled_renewals[:12]:
                    conc_label = "Spike Risk" if pmt.is_high_concentration else "Normal"
                    conc_color = c_red if pmt.is_high_concentration else c_muted
                    r_table_data.append([
                        Paragraph(pmt.expected_payment_date, body_style),
                        Paragraph(pmt.vendor_name[:22], body_style),
                        Paragraph(pmt.billing_frequency.capitalize(), body_style),
                        Paragraph(f"${pmt.expected_payment_amount:,.2f}", cell_right),
                        Paragraph(pmt.detection_type.capitalize(), body_style),
                        Paragraph(f"<font color='{conc_color.hexval()}'>{conc_label}</font>", body_style),
                    ])

                r_table = Table(r_table_data, colWidths=[1.2 * inch, 1.8 * inch, 1.0 * inch, 1.1 * inch, 1.1 * inch, 1.3 * inch])
                r_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(r_table)

            story.append(Spacer(1, 14))

        # 6. Six-Month Forecast Multi-Scenario Table
        if rep_clean in ("comprehensive", "forecast"):
            fc_rep = cls.generate_forecast_report(business, subscriptions, transactions)
            sec_num = "4" if rep_clean == "comprehensive" else "1"
            story.append(Paragraph(f"<b>{sec_num}. Six-Month Forward Cash-Flow Projections (Multi-Scenario)</b>", h2_style))

            b_scenario = fc_rep.scenarios.get("baseline")
            if not b_scenario or not b_scenario.timeline:
                story.append(Paragraph("<i>Insufficient historical operating records to generate 6-month projections.</i>", body_style))
            else:
                fc_table_data = [
                    [
                        Paragraph("<b>Month</b>", cell_bold),
                        Paragraph("<b>Optimistic (+15%)</b>", cell_right_bold),
                        Paragraph("<b>Baseline (0%)</b>", cell_right_bold),
                        Paragraph("<b>Conservative (-20%)</b>", cell_right_bold),
                        Paragraph("<b>Confirmed SaaS</b>", cell_right_bold),
                        Paragraph("<b>Closing Cash (Base)</b>", cell_right_bold),
                    ]
                ]
                o_timeline = fc_rep.scenarios.get("optimistic", b_scenario).timeline
                c_timeline = fc_rep.scenarios.get("conservative", b_scenario).timeline

                for i, b_m in enumerate(b_scenario.timeline):
                    o_m = o_timeline[i] if i < len(o_timeline) else b_m
                    c_m = c_timeline[i] if i < len(c_timeline) else b_m
                    bal_str = f"${b_m.projected_closing_balance:,.2f}" if b_m.projected_closing_balance is not None else "N/A"

                    fc_table_data.append([
                        Paragraph(b_m.month_name, body_style),
                        Paragraph(f"${o_m.projected_revenue:,.2f}", cell_right),
                        Paragraph(f"${b_m.projected_revenue:,.2f}", cell_right),
                        Paragraph(f"${c_m.projected_revenue:,.2f}", cell_right),
                        Paragraph(f"${b_m.projected_confirmed_sub_expenses:,.2f}", cell_right),
                        Paragraph(bal_str, cell_right),
                    ])

                fc_table = Table(fc_table_data, colWidths=[1.2 * inch, 1.3 * inch, 1.2 * inch, 1.3 * inch, 1.25 * inch, 1.25 * inch])
                fc_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.5, c_border),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, c_border),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light]),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                story.append(fc_table)

            story.append(Spacer(1, 14))

        # 7. Regulatory & Methodology Disclosures (Always at the end)
        story.append(KeepTogether([
            HRFlowable(width="100%", thickness=0.5, color=c_border, spaceBefore=8, spaceAfter=8),
            Paragraph("<b>Regulatory & Methodology Disclosures</b>", ParagraphStyle("DiscTitle", parent=body_style, fontName="Helvetica-Bold", fontSize=8)),
            Spacer(1, 3),
            Paragraph(cls.DISCLAIMER_TEXT, ParagraphStyle("DiscBody", parent=body_style, fontSize=7, leading=10, textColor=c_muted)),
        ]))

        doc.build(story, canvasmaker=NumberedCanvas)
        return buf.getvalue()
