"""
Stage 8.5: Reproducible Demonstration Data Generator
Generates realistic, isolated 6-month financial records for DemoTech Solutions.

Design & Security Principles:
1. Complete Isolation: All records have business_id == demo_biz.id and data_source == 'demo_fixture'.
2. Zero PayPal Representation: paypal_transaction_id is None; is_simulated is True. Never synced to PayPal.
3. Realistic Fluctuations: 6 months of client revenues ($7.1k - $12.5k), 7 SaaS subscriptions,
   1 annual renewal (Figma Org due in 6-month horizon), and non-subscription operating expenses.
4. Reproducibility: Deterministic amounts and dates ensure identical demonstrations every time.
5. Absolute Safety: Reset deletes ONLY demo_fixture records for the demo business profile.
"""
import datetime
import calendar
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.services.recommendation_engine import RecommendationEngine


class DemoDataGenerator:

    @classmethod
    def ensure_demo_business(cls, user_or_id: Any = None, db: Session = None, user_id: Any = None) -> BusinessProfile:
        """
        Creates or retrieves the isolated DemoTech Solutions business profile for user_id.
        """
        target = user_id if user_id is not None else user_or_id
        uid = target.user_id if isinstance(target, BusinessProfile) else (target.id if hasattr(target, "id") else int(target))
        demo_biz = (
            db.query(BusinessProfile)
            .filter(
                BusinessProfile.user_id == uid,
                BusinessProfile.is_demo == True,
            )
            .first()
        )

        if not demo_biz:
            demo_biz = BusinessProfile(
                user_id=uid,
                company_name="DemoTech Solutions",
                industry="Software Services & Web Development",
                monthly_baseline_revenue=9800.0,
                current_cash_reserves=18500.0,
                target_runway_months=6,
                risk_tolerance="moderate",
                currency="USD",
                paypal_connected=True,
                paypal_mode="demo",
                is_demo=True,
                profile_type="DEMO",
            )
            db.add(demo_biz)
            db.commit()
            db.refresh(demo_biz)

        return demo_biz

    @classmethod
    def generate_demo_dataset(cls, user_or_biz: Any = None, db: Session = None, user_id: Any = None) -> Dict[str, Any]:
        """
        Generates or re-synchronizes the full 6-month demo dataset for DemoTech Solutions.
        """
        target = user_id if user_id is not None else user_or_biz
        if isinstance(target, BusinessProfile):
            demo_biz = target
        else:
            demo_biz = cls.ensure_demo_business(user_or_id=target, db=db)

        # Clear existing demo records first for clean reproducibility
        cls.clear_demo_records(demo_biz=demo_biz, db=db)

        # 1. Generate Transactions
        txs = cls._build_transactions(demo_biz=demo_biz)
        db.add_all(txs)
        db.commit()

        # 2. Generate Subscriptions
        subs = cls._build_subscriptions(demo_biz=demo_biz)
        db.add_all(subs)
        db.commit()

        # 3. Generate Recommendations
        fresh_txs = db.query(Transaction).filter(Transaction.business_id == demo_biz.id).all()
        fresh_subs = db.query(Subscription).filter(Subscription.business_id == demo_biz.id).all()
        recs = RecommendationEngine.generate_recommendations(
            business=demo_biz,
            subscriptions=fresh_subs,
            transactions=fresh_txs,
        )
        if recs:
            db.add_all(recs)
            db.commit()

        return {
            "business_id": demo_biz.id,
            "company_name": demo_biz.company_name,
            "is_demo": True,
            "profile_type": demo_biz.profile_type,
            "transaction_count": len(txs),
            "subscription_count": len(subs),
            "recommendation_count": len(recs) if recs else 0,
            "starting_cash": demo_biz.current_cash_reserves,
            "currency": demo_biz.currency,
        }

    @classmethod
    def clear_demo_records(cls, demo_biz: BusinessProfile, db: Session) -> Dict[str, int]:
        """
        Strictly deletes ONLY records belonging to demo_biz.id with data_source='demo_fixture'.
        NEVER touches real sandbox records or other business profiles.
        """
        assert demo_biz.is_demo is True, "Security Check Failed: Attempted to delete records from non-demo business!"

        # Delete recommendations
        del_recs = db.query(Recommendation).filter(Recommendation.business_id == demo_biz.id).delete()
        # Delete subscriptions
        del_subs = db.query(Subscription).filter(Subscription.business_id == demo_biz.id).delete()
        # Delete transactions
        deleted_count = (
            db.query(Transaction)
            .filter(
                Transaction.business_id == demo_biz.id,
                Transaction.data_source == "demo_fixture",
            )
            .delete()
        )
        db.commit()
        return {
            "cleared_transactions": deleted_count,
            "cleared_subscriptions": del_subs,
            "cleared_recommendations": del_recs,
        }

    @classmethod
    def _build_transactions(cls, demo_biz: BusinessProfile) -> List[Transaction]:
        """
        Builds ~75 realistic historical transactions spanning May 2026 to November 2026.
        """
        tx_list: List[Transaction] = []

        def add_tx(dt: datetime.datetime, raw: str, vendor: str, cat: str, gross: float, fee: float = 0.0):
            amt = round(gross, 2)
            net = round(amt - fee, 2) if fee else amt
            tx_list.append(
                Transaction(
                    business_id=demo_biz.id,
                    paypal_transaction_id=None,  # Do NOT fabricate PayPal transaction IDs
                    transaction_date=dt,
                    raw_description=raw,
                    normalized_vendor=vendor,
                    category=cat,
                    gross_amount=amt,
                    fee_amount=fee,
                    net_amount=net,
                    currency="USD",
                    status="COMPLETED",
                    data_source="demo_fixture",
                    is_simulated=True,
                )
            )

        # ---------------------------------------------------------------------
        # 1. MONTHLY REVENUE (Customer Invoices / Retainers / Projects)
        # ---------------------------------------------------------------------
        # May 2026 ($8,400)
        add_tx(datetime.datetime(2026, 5, 4, 10, 15), "Acme Corp - SaaS Client Monthly Retainer", "Acme Corp", "Customer Sale", 3200.00, 93.10)
        add_tx(datetime.datetime(2026, 5, 14, 14, 30), "Nexus Systems - Backend API Development", "Nexus Systems", "Customer Sale", 2500.00, 72.80)
        add_tx(datetime.datetime(2026, 5, 26, 16, 0), "Vertex Labs - Web App Milestone 1", "Vertex Labs", "Customer Sale", 2700.00, 78.60)

        # Jun 2026 ($11,200 - High month)
        add_tx(datetime.datetime(2026, 6, 3, 9, 45), "Acme Corp - SaaS Client Monthly Retainer", "Acme Corp", "Customer Sale", 3200.00, 93.10)
        add_tx(datetime.datetime(2026, 6, 12, 11, 20), "Nexus Systems - Backend API Development", "Nexus Systems", "Customer Sale", 2500.00, 72.80)
        add_tx(datetime.datetime(2026, 6, 20, 15, 0), "Alpha Retail - Custom Integration Project", "Alpha Retail", "Customer Sale", 2800.00, 81.50)
        add_tx(datetime.datetime(2026, 6, 28, 17, 10), "Vertex Labs - Web App Milestone 2", "Vertex Labs", "Customer Sale", 2700.00, 78.60)

        # Jul 2026 ($7,100 - Lower summer month)
        add_tx(datetime.datetime(2026, 7, 6, 10, 0), "Acme Corp - SaaS Client Monthly Retainer", "Acme Corp", "Customer Sale", 3200.00, 93.10)
        add_tx(datetime.datetime(2026, 7, 15, 13, 40), "Nexus Systems - Backend API Development", "Nexus Systems", "Customer Sale", 2500.00, 72.80)
        add_tx(datetime.datetime(2026, 7, 25, 16, 15), "QuickConsult - Security Architecture Review", "QuickConsult", "Customer Sale", 1400.00, 40.90)

        # Aug 2026 ($9,800)
        add_tx(datetime.datetime(2026, 8, 5, 11, 0), "Acme Corp - SaaS Client Monthly Retainer", "Acme Corp", "Customer Sale", 3200.00, 93.10)
        add_tx(datetime.datetime(2026, 8, 14, 14, 10), "Nexus Systems - Backend API Development", "Nexus Systems", "Customer Sale", 2500.00, 72.80)
        add_tx(datetime.datetime(2026, 8, 21, 10, 30), "Beta Tech - Cloud Migration Sprint", "Beta Tech", "Customer Sale", 1400.00, 40.90)
        add_tx(datetime.datetime(2026, 8, 29, 16, 45), "Vertex Labs - Final Deployment Milestone", "Vertex Labs", "Customer Sale", 2700.00, 78.60)

        # Sep 2026 ($12,500 - Peak fall rebound)
        add_tx(datetime.datetime(2026, 9, 4, 9, 30), "Acme Corp - SaaS Client Monthly Retainer", "Acme Corp", "Customer Sale", 3200.00, 93.10)
        add_tx(datetime.datetime(2026, 9, 11, 12, 15), "Nexus Systems - Backend API Development", "Nexus Systems", "Customer Sale", 2500.00, 72.80)
        add_tx(datetime.datetime(2026, 9, 18, 15, 0), "Vertex Labs - Monthly Maintenance & SLA", "Vertex Labs", "Customer Sale", 2700.00, 78.60)
        add_tx(datetime.datetime(2026, 9, 27, 16, 30), "Enterprise Audit - Security Compliance Project", "Enterprise Audit", "Customer Sale", 4100.00, 119.20)

        # Oct 2026 ($10,600)
        add_tx(datetime.datetime(2026, 10, 5, 10, 20), "Acme Corp - SaaS Client Monthly Retainer", "Acme Corp", "Customer Sale", 3200.00, 93.10)
        add_tx(datetime.datetime(2026, 10, 13, 14, 40), "Nexus Systems - Backend API Development", "Nexus Systems", "Customer Sale", 2500.00, 72.80)
        add_tx(datetime.datetime(2026, 10, 22, 11, 15), "Vertex Labs - Monthly Maintenance & SLA", "Vertex Labs", "Customer Sale", 2700.00, 78.60)
        add_tx(datetime.datetime(2026, 10, 30, 16, 0), "Acme Corp - Q4 Performance Optimization Add-on", "Acme Corp", "Customer Sale", 2200.00, 64.10)

        # Nov 2026 (Month-to-date)
        add_tx(datetime.datetime(2026, 11, 4, 10, 0), "Acme Corp - SaaS Client Monthly Retainer", "Acme Corp", "Customer Sale", 3200.00, 93.10)
        add_tx(datetime.datetime(2026, 11, 6, 14, 0), "Nexus Systems - Backend API Development", "Nexus Systems", "Customer Sale", 2500.00, 72.80)

        # ---------------------------------------------------------------------
        # 2. SOFTWARE SUBSCRIPTIONS (Recurring monthly disbursements)
        # ---------------------------------------------------------------------
        months = [
            (2026, 5), (2026, 6), (2026, 7), (2026, 8), (2026, 9), (2026, 10), (2026, 11)
        ]
        for y, m in months:
            # AWS (1st)
            if (y, m) <= (2026, 11):
                add_tx(datetime.datetime(y, m, 1, 3, 0), "Amazon Web Services - AWS Cloud Services", "AWS", "Cloud & Infrastructure", -245.50)
            # GitHub (5th)
            if (y, m) <= (2026, 11):
                add_tx(datetime.datetime(y, m, 5, 8, 30), "GitHub Inc - Team Organization Plan", "GitHub", "Developer Tools", -42.00)
            # Slack (12th)
            if (y, m) < (2026, 11):
                add_tx(datetime.datetime(y, m, 12, 9, 0), "Slack Technologies - Pro Monthly Subscription", "Slack", "Communication", -75.00)
            # OpenAI (15th)
            if (y, m) < (2026, 11):
                add_tx(datetime.datetime(y, m, 15, 11, 0), "OpenAI, LLC - API Usage & ChatGPT Team", "OpenAI", "AI Services", -85.00)
            # Adobe (18th)
            if (y, m) < (2026, 11):
                add_tx(datetime.datetime(y, m, 18, 14, 20), "Adobe Systems - Creative Cloud All Apps", "Adobe", "Design", -59.99)
            # Zoom (22nd)
            if (y, m) < (2026, 11):
                add_tx(datetime.datetime(y, m, 22, 10, 0), "Zoom Video Communications - Pro Plan", "Zoom", "Communication", -19.99)
            # Google Workspace (28th)
            if (y, m) < (2026, 11):
                add_tx(datetime.datetime(y, m, 28, 7, 0), "Google LLC - Google Workspace Enterprise", "Google Workspace", "Productivity", -36.00)

        # Annual Subscription Paid in Past (Figma Organization Annual - renewed Dec 15, 2025)
        # Note: Billed historically Dec 15, 2025; next renewal is Dec 15, 2026 (right in calendar horizon!)
        add_tx(datetime.datetime(2025, 12, 15, 10, 0), "Figma Inc - Organization Annual Plan (12 Seats)", "Figma", "Design", -540.00)

        # ---------------------------------------------------------------------
        # 3. NON-SUBSCRIPTION OPERATING EXPENSES
        # ---------------------------------------------------------------------
        for y, m in [(2026, 5), (2026, 6), (2026, 7), (2026, 8), (2026, 9), (2026, 10)]:
            # Google Ads Marketing
            ad_amt = -620.00 if m in (6, 9) else (-480.00 if m == 7 else -550.00)
            add_tx(datetime.datetime(y, m, 10, 12, 0), f"Google Ads - Performance Growth Campaign ({calendar.month_abbr[m]})", "Google Ads", "Marketing & Advertising", ad_amt)
            # Fastly CDN / Hosting Edge
            add_tx(datetime.datetime(y, m, 16, 4, 0), "Fastly CDN - Edge Infrastructure Delivery", "Fastly", "Cloud & Infrastructure", -120.00)
            # Equipment Lease
            add_tx(datetime.datetime(y, m, 20, 8, 0), "Apple Financial Services - Developer Workstation Lease", "Apple", "Office & Equipment", -280.00)
            # Legal & Accounting
            add_tx(datetime.datetime(y, m, 25, 15, 0), "Stripe Atlas & Pilot - Corporate Accounting Retainer", "Pilot Accounting", "Legal & Professional", -350.00)

        # Contractor Design Sprints in July and September
        add_tx(datetime.datetime(2026, 7, 18, 16, 0), "Upwork Global - Senior UI/UX Specialist Sprint", "Upwork", "Contractor & Freelance", -800.00)
        add_tx(datetime.datetime(2026, 9, 20, 16, 0), "Upwork Global - Security Pen-Testing Contractor", "Upwork", "Contractor & Freelance", -800.00)

        return tx_list

    @classmethod
    def _build_subscriptions(cls, demo_biz: BusinessProfile) -> List[Subscription]:
        """
        Creates the detected Subscription records for DemoTech Solutions.
        Includes 7 monthly subscriptions + 1 annual renewal (Figma Org due Dec 15, 2026).
        """
        subs = [
            # 1. AWS (Cloud & Infrastructure, $245.50/mo, fixed)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="AWS",
                category="Cloud & Infrastructure",
                cadence="monthly",
                average_amount=245.50,
                latest_amount=245.50,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 5, 1, 3, 0),
                last_billed_date=datetime.datetime(2026, 11, 1, 3, 0),
                next_billing_date=datetime.datetime(2026, 12, 1, 3, 0),
                price_change_pct=0.0,
                confidence_score=0.98,
                priority_tier=1,  # Mission Critical
                status="active",
                detection_type="confirmed",
                detection_reason="7 consecutive monthly disbursements detected from Amazon Web Services.",
                billing_type="fixed",
                utilization_score=0.92,
                is_essential=True,
            ),
            # 2. GitHub (Developer Tools, $42.00/mo, fixed)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="GitHub",
                category="Developer Tools",
                cadence="monthly",
                average_amount=42.00,
                latest_amount=42.00,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 5, 5, 8, 30),
                last_billed_date=datetime.datetime(2026, 11, 5, 8, 30),
                next_billing_date=datetime.datetime(2026, 12, 5, 8, 30),
                price_change_pct=0.0,
                confidence_score=0.99,
                priority_tier=1,
                status="active",
                detection_type="confirmed",
                detection_reason="7 monthly cycles detected for GitHub Team Organization.",
                billing_type="fixed",
                utilization_score=0.95,
                is_essential=True,
            ),
            # 3. Slack (Communication, $75.00/mo, fixed)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="Slack",
                category="Communication",
                cadence="monthly",
                average_amount=75.00,
                latest_amount=75.00,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 5, 12, 9, 0),
                last_billed_date=datetime.datetime(2026, 10, 12, 9, 0),
                next_billing_date=datetime.datetime(2026, 11, 12, 9, 0),  # Upcoming in 4 days!
                price_change_pct=0.0,
                confidence_score=0.97,
                priority_tier=2,
                status="active",
                detection_type="confirmed",
                detection_reason="6 monthly cycles detected for Slack Technologies Pro.",
                billing_type="fixed",
                utilization_score=0.88,
                is_essential=True,
            ),
            # 4. OpenAI (AI Services, $85.00/mo, fixed)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="OpenAI",
                category="AI Services",
                cadence="monthly",
                average_amount=85.00,
                latest_amount=85.00,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 5, 15, 11, 0),
                last_billed_date=datetime.datetime(2026, 10, 15, 11, 0),
                next_billing_date=datetime.datetime(2026, 11, 15, 11, 0),  # Upcoming in 7 days!
                price_change_pct=0.0,
                confidence_score=0.96,
                priority_tier=2,
                status="active",
                detection_type="confirmed",
                detection_reason="6 monthly API and Team disbursements detected for OpenAI LLC.",
                billing_type="fixed",
                utilization_score=0.94,
                is_essential=True,
            ),
            # 5. Adobe (Design, $59.99/mo, fixed)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="Adobe",
                category="Design",
                cadence="monthly",
                average_amount=59.99,
                latest_amount=59.99,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 5, 18, 14, 20),
                last_billed_date=datetime.datetime(2026, 10, 18, 14, 20),
                next_billing_date=datetime.datetime(2026, 11, 18, 14, 20),  # Upcoming in 10 days!
                price_change_pct=0.0,
                confidence_score=0.97,
                priority_tier=2,
                status="active",
                detection_type="confirmed",
                detection_reason="6 monthly cycles detected for Adobe Creative Cloud.",
                billing_type="fixed",
                utilization_score=0.75,
                is_essential=False,
            ),
            # 6. Zoom (Communication, $19.99/mo, fixed)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="Zoom",
                category="Communication",
                cadence="monthly",
                average_amount=19.99,
                latest_amount=19.99,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 5, 22, 10, 0),
                last_billed_date=datetime.datetime(2026, 10, 22, 10, 0),
                next_billing_date=datetime.datetime(2026, 11, 22, 10, 0),
                price_change_pct=0.0,
                confidence_score=0.95,
                priority_tier=3,
                status="active",
                detection_type="confirmed",
                detection_reason="6 monthly disbursements for Zoom Video Pro.",
                billing_type="fixed",
                utilization_score=0.70,
                is_essential=False,
            ),
            # 7. Google Workspace (Productivity, $36.00/mo, fixed)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="Google Workspace",
                category="Productivity",
                cadence="monthly",
                average_amount=36.00,
                latest_amount=36.00,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 5, 28, 7, 0),
                last_billed_date=datetime.datetime(2026, 10, 28, 7, 0),
                next_billing_date=datetime.datetime(2026, 11, 28, 7, 0),
                price_change_pct=0.0,
                confidence_score=0.98,
                priority_tier=1,
                status="active",
                detection_type="confirmed",
                detection_reason="6 monthly cycles detected for Google Workspace Enterprise.",
                billing_type="fixed",
                utilization_score=0.96,
                is_essential=True,
            ),
            # 8. ANNUAL SUBSCRIPTION: Figma (Design, $540.00/year, fixed)
            # Due December 15, 2026! Triggers renewal concentration spike in Month 2!
            Subscription(
                business_id=demo_biz.id,
                vendor_name="Figma",
                category="Design",
                cadence="annual",
                average_amount=540.00,
                latest_amount=540.00,
                currency="USD",
                first_billed_date=datetime.datetime(2025, 12, 15, 10, 0),
                last_billed_date=datetime.datetime(2025, 12, 15, 10, 0),
                next_billing_date=datetime.datetime(2026, 12, 15, 10, 0),  # Upcoming in December 2026!
                price_change_pct=0.0,
                confidence_score=0.95,
                priority_tier=2,
                status="active",
                detection_type="confirmed",
                detection_reason="Annual enterprise contract detected for Figma Organization.",
                billing_type="fixed",
                utilization_score=0.85,
                is_essential=True,
            ),
            # 9. POTENTIAL SUBSCRIPTION: Linear (Productivity, $32.00/mo, potential trial)
            Subscription(
                business_id=demo_biz.id,
                vendor_name="Linear",
                category="Productivity",
                cadence="monthly",
                average_amount=32.00,
                latest_amount=32.00,
                currency="USD",
                first_billed_date=datetime.datetime(2026, 10, 25, 12, 0),
                last_billed_date=datetime.datetime(2026, 10, 25, 12, 0),
                next_billing_date=datetime.datetime(2026, 11, 25, 12, 0),
                price_change_pct=0.0,
                confidence_score=0.65,
                priority_tier=3,
                status="active",
                detection_type="potential",
                detection_reason="Single initial billing detected for Linear Software. Potential unconfirmed trial.",
                billing_type="fixed",
                utilization_score=0.50,
                is_essential=False,
            ),
        ]
        return subs

    # Legacy compatibility method for sandbox sync simulation
    @staticmethod
    def generate_demo_transactions(months_back: int = 6) -> List[Dict[str, Any]]:
        """Legacy helper returning raw dictionaries for sandbox simulation preview."""
        import random
        now = datetime.datetime.utcnow()
        transactions: List[Dict[str, Any]] = []

        subscriptions_spec = [
            ("AMZN *AWS CLOUD 109283-US", 245.50, 1, "Cloud Infrastructure"),
            ("GOOGLE *WORKSPACE GSUITE ENTERPRISE", 36.0, 28, "Productivity & Email"),
            ("SLACK TECH INC MO PYMT", 75.0, 12, "Team Collaboration"),
            ("GITHUB ENTERPRISE ORG", 42.0, 5, "Developer Tools"),
            ("OPENAI *API BILLING USAGE", 85.0, 15, "AI & Machine Learning"),
            ("ZOOM.US MO SUB", 19.99, 22, "Video Conferencing"),
            ("ADOBE SYSTEMS CREATIVE CLOUD", 59.99, 18, "Design"),
        ]

        for m in range(months_back, -1, -1):
            ref_month = now - datetime.timedelta(days=m * 30.4)
            year = ref_month.year
            month = ref_month.month

            # Inbound sales
            sales = [3200.0, 2500.0, 2700.0]
            if m % 2 == 1:
                sales.append(2800.0)
            for idx, s_amt in enumerate(sales):
                day = min(4 + idx * 7, 28)
                tx_date = datetime.datetime(year, month, day, 14, 0, 0)
                if tx_date <= now:
                    fee = round(s_amt * 0.029 + 0.30, 2)
                    transactions.append({
                        "paypal_transaction_id": f"DEMO_REV_{year}{month:02d}_{day:02d}_{idx}",
                        "transaction_date": tx_date,
                        "raw_description": f"Customer Invoice Payment #{1000 + idx}",
                        "gross_amount": float(s_amt),
                        "fee_amount": fee,
                        "net_amount": round(float(s_amt) - fee, 2),
                        "currency": "USD",
                        "status": "COMPLETED",
                        "data_source": "demo"
                    })

            for desc, base_amt, dom, cat in subscriptions_spec:
                day = min(dom, 28)
                tx_date = datetime.datetime(year, month, day, 10, 0, 0)
                if tx_date <= now:
                    transactions.append({
                        "paypal_transaction_id": f"DEMO_SUB_{year}{month:02d}_{day:02d}_{abs(hash(desc)) % 1000}",
                        "transaction_date": tx_date,
                        "raw_description": desc,
                        "gross_amount": -float(base_amt),
                        "fee_amount": 0.0,
                        "net_amount": -float(base_amt),
                        "currency": "USD",
                        "status": "COMPLETED",
                        "data_source": "demo"
                    })

        transactions.sort(key=lambda x: x["transaction_date"])
        return transactions
