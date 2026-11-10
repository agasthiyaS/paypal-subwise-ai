import datetime
from typing import Dict, Any, List
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.expense import Expense
from app.models.household_member import HouseholdMember
from app.models.subscription import Subscription
from app.models.budget import Budget

class SyntheticFinanceFixtures:
    """
    Isolated Synthetic Testing Framework for PayPal SubWise AI:
    - Provides standardized, high-integrity test fixtures across Individual, Household, and SMB accounts.
    - Simulates multi-currency transactions, refunds, reversals, price increases, and webhook events.
    - Guaranteed zero database pollution; used exclusively in isolated test runners and memory databases.
    """

    @staticmethod
    def create_individual_scenario(user_id: int = 801, business_id: int = 801) -> Dict[str, Any]:
        """Synthetic individual account with personal income, groceries, rent, and streaming."""
        now = datetime.datetime.utcnow()
        biz = BusinessProfile(
            id=business_id,
            user_id=user_id,
            company_name="Alex River Personal Finances",
            account_type="individual",
            current_cash_reserves=4500.0,
            monthly_baseline_revenue=4200.0,
            paypal_mode="sandbox"
        )
        expenses = [
            Expense(
                business_id=business_id,
                user_id=user_id,
                amount=4200.0,
                expense_type="income",
                category="Other",
                description="Monthly Tech Employment Salary",
                merchant="Employer Direct Deposit",
                expense_date=now - datetime.timedelta(days=5),
                data_source="synthetic_test"
            ),
            Expense(
                business_id=business_id,
                user_id=user_id,
                amount=1400.0,
                expense_type="expense",
                category="Housing & Rent",
                description="Apartment Monthly Rent",
                merchant="Property Management",
                expense_date=now - datetime.timedelta(days=4),
                data_source="synthetic_test"
            ),
            Expense(
                business_id=business_id,
                user_id=user_id,
                amount=380.0,
                expense_type="expense",
                category="Food & Groceries",
                description="Organic Market Groceries",
                merchant="Whole Foods",
                expense_date=now - datetime.timedelta(days=3),
                data_source="synthetic_test"
            ),
            Expense(
                business_id=business_id,
                user_id=user_id,
                amount=22.99,
                expense_type="expense",
                category="Subscriptions",
                description="Netflix Premium 4K",
                merchant="Netflix",
                is_recurring=True,
                expense_date=now - datetime.timedelta(days=2),
                data_source="synthetic_test"
            ),
        ]
        budgets = [
            Budget(
                business_id=business_id,
                category="Overall",
                monthly_limit=3000.0,
                period_month=now.month,
                period_year=now.year
            ),
            Budget(
                business_id=business_id,
                category="Food & Groceries",
                monthly_limit=500.0,
                period_month=now.month,
                period_year=now.year
            ),
        ]
        return {"business": biz, "expenses": expenses, "budgets": budgets}

    @staticmethod
    def create_household_scenario(user_id: int = 802, business_id: int = 802) -> Dict[str, Any]:
        """Synthetic household account with 3 members, shared utility/grocery bills, and pooled subscriptions."""
        now = datetime.datetime.utcnow()
        biz = BusinessProfile(
            id=business_id,
            user_id=user_id,
            company_name="Oakwood Family Household",
            account_type="household",
            current_cash_reserves=8500.0,
            monthly_baseline_revenue=7500.0,
            paypal_mode="sandbox"
        )
        members = [
            HouseholdMember(id=81, business_id=business_id, name="Sarah Oakwood", role="Head of Household", monthly_income_share=4500.0),
            HouseholdMember(id=82, business_id=business_id, name="David Oakwood", role="Partner", monthly_income_share=3000.0),
            HouseholdMember(id=83, business_id=business_id, name="Emma Oakwood", role="Dependent", monthly_income_share=0.0),
        ]
        expenses = [
            Expense(
                business_id=business_id,
                user_id=user_id,
                amount=650.0,
                expense_type="expense",
                category="Food & Groceries",
                description="Costco Bulk Family Staples",
                merchant="Costco Wholesale",
                is_shared=True,
                household_member_id=81,
                expense_date=now - datetime.timedelta(days=7),
                data_source="synthetic_test"
            ),
            Expense(
                business_id=business_id,
                user_id=user_id,
                amount=245.0,
                expense_type="expense",
                category="Electricity & Utilities",
                description="City Power & Electric Bill",
                merchant="Metropolitan Electric",
                is_shared=True,
                household_member_id=82,
                expense_date=now - datetime.timedelta(days=6),
                data_source="synthetic_test"
            ),
        ]
        return {"business": biz, "members": members, "expenses": expenses}

    @staticmethod
    def create_business_multicurrency_scenario(user_id: int = 803, business_id: int = 803) -> Dict[str, Any]:
        """Synthetic SMB with SaaS subscriptions in USD, EUR, and GBP, plus refunds and reversals."""
        now = datetime.datetime.utcnow()
        biz = BusinessProfile(
            id=business_id,
            user_id=user_id,
            company_name="CloudMatrix Software Labs",
            account_type="business",
            current_cash_reserves=28000.0,
            monthly_baseline_revenue=15000.0,
            paypal_mode="sandbox"
        )
        txs = [
            # Inbound revenue
            Transaction(
                business_id=business_id,
                paypal_transaction_id="TX_REV_001",
                transaction_date=now - datetime.timedelta(days=12),
                raw_description="Enterprise Software SaaS License",
                normalized_vendor="Acme Corp Client",
                gross_amount=5000.0,
                fee_amount=145.0,
                net_amount=4855.0,
                currency="USD",
                status="COMPLETED",
                data_source="sandbox"
            ),
            # Inbound EUR revenue
            Transaction(
                business_id=business_id,
                paypal_transaction_id="TX_REV_002_EUR",
                transaction_date=now - datetime.timedelta(days=10),
                raw_description="European Client License",
                normalized_vendor="EuroTech GmbH",
                gross_amount=2000.0,
                fee_amount=60.0,
                net_amount=1940.0,
                currency="EUR",
                status="COMPLETED",
                data_source="sandbox"
            ),
            # Outbound SaaS with price creep: AWS
            Transaction(
                business_id=business_id,
                paypal_transaction_id="TX_SUB_AWS_1",
                transaction_date=now - datetime.timedelta(days=60),
                raw_description="Amazon Web Services Cloud Infrastructure",
                normalized_vendor="Amazon Web Services",
                gross_amount=-400.0,
                fee_amount=0.0,
                net_amount=-400.0,
                currency="USD",
                status="COMPLETED",
                data_source="sandbox"
            ),
            Transaction(
                business_id=business_id,
                paypal_transaction_id="TX_SUB_AWS_2",
                transaction_date=now - datetime.timedelta(days=30),
                raw_description="Amazon Web Services Cloud Infrastructure",
                normalized_vendor="Amazon Web Services",
                gross_amount=-450.0,
                fee_amount=0.0,
                net_amount=-450.0,
                currency="USD",
                status="COMPLETED",
                data_source="sandbox"
            ),
            # Refunded transaction
            Transaction(
                business_id=business_id,
                paypal_transaction_id="TX_REF_001",
                transaction_date=now - datetime.timedelta(days=5),
                raw_description="Returned Hardware Equipment",
                normalized_vendor="Dell Direct",
                gross_amount=-350.0,
                fee_amount=0.0,
                net_amount=-350.0,
                currency="USD",
                status="REFUNDED",
                data_source="sandbox"
            ),
            # Pending transaction
            Transaction(
                business_id=business_id,
                paypal_transaction_id="TX_PEND_001",
                transaction_date=now - datetime.timedelta(days=1),
                raw_description="Pending Wire Transfer Check",
                normalized_vendor="Pending Consulting Invoice",
                gross_amount=1200.0,
                fee_amount=0.0,
                net_amount=1200.0,
                currency="USD",
                status="PENDING",
                data_source="sandbox"
            ),
        ]
        return {"business": biz, "transactions": txs}

    @staticmethod
    def sample_webhook_payload(event_type: str = "PAYMENT.CAPTURE.COMPLETED", event_id: str = "WH-SAMPLE-001") -> Dict[str, Any]:
        """Generates a realistic PayPal Webhook event payload for testing."""
        return {
            "id": event_id,
            "event_version": "1.0",
            "create_time": datetime.datetime.utcnow().isoformat() + "Z",
            "resource_type": "capture",
            "event_type": event_type,
            "summary": f"PayPal event {event_type}",
            "resource": {
                "id": f"CAP-{event_id}",
                "status": "COMPLETED" if "COMPLETED" in event_type else "REFUNDED",
                "amount": {
                    "value": "150.00",
                    "currency_code": "USD"
                },
                "seller_receivable_breakdown": {
                    "gross_amount": {"value": "150.00", "currency_code": "USD"},
                    "paypal_fee": {"value": "4.65", "currency_code": "USD"},
                    "net_amount": {"value": "145.35", "currency_code": "USD"}
                },
                "custom_id": "803"
            }
        }

