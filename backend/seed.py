from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.models.recommendation import Recommendation
from app.services.auth_service import get_password_hash
from app.services.demo_data_generator import DemoDataGenerator
from app.services.normalizer import TransactionNormalizer
from app.services.subscription_detector import SubscriptionDetector
from app.services.recommendation_engine import RecommendationEngine
import datetime

def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if demo user already exists
    demo_email = "demo@subwise.io"
    user = db.query(User).filter(User.email == demo_email).first()

    if not user:
        print("Creating demo user...")
        user = User(
            email=demo_email,
            hashed_password=get_password_hash("DemoPass2026!"),
            full_name="Alex Mercer"
        )
        db.add(user)
        db.flush()

        biz = BusinessProfile(
            user_id=user.id,
            company_name="NovaTech SaaS Inc",
            industry="Software & AI Services",
            monthly_baseline_revenue=24500.0,
            current_cash_reserves=58000.0,
            target_runway_months=6,
            risk_tolerance="moderate",
            paypal_connected=True,
            paypal_mode="demo",
            last_synced_at=datetime.datetime.utcnow()
        )
        db.add(biz)
        db.flush()
    else:
        biz = user.business
        # Clear existing transactions/subs for fresh seed
        db.query(Transaction).filter(Transaction.business_id == biz.id).delete()
        db.query(Subscription).filter(Subscription.business_id == biz.id).delete()
        db.query(Recommendation).filter(Recommendation.business_id == biz.id).delete()
        db.flush()

    print("Generating demo transactions...")
    raw_txs = DemoDataGenerator.generate_demo_transactions(months_back=6)
    created_txs = []
    for item in raw_txs:
        meta = TransactionNormalizer.normalize_vendor_and_category(item["raw_description"])
        tx = Transaction(
            business_id=biz.id,
            paypal_transaction_id=item.get("paypal_transaction_id"),
            transaction_date=item["transaction_date"],
            raw_description=item["raw_description"],
            normalized_vendor=meta["normalized_vendor"],
            category=meta["category"],
            gross_amount=item["gross_amount"],
            fee_amount=item.get("fee_amount", 0.0),
            net_amount=item["net_amount"],
            currency=item.get("currency", "USD"),
            status=item.get("status", "COMPLETED"),
            data_source="demo"
        )
        db.add(tx)
        created_txs.append(tx)
    db.flush()

    print("Running subscription detection...")
    subs = SubscriptionDetector.identify_subscriptions(created_txs, biz.id)
    for s in subs:
        db.add(s)
    db.flush()

    print("Generating financial recommendations...")
    recs = RecommendationEngine.generate_recommendations(biz, subs)
    for r in recs:
        db.add(r)

    db.commit()
    db.close()
    print("Seed complete! Demo user: demo@subwise.io / DemoPass2026!")

if __name__ == "__main__":
    seed_demo_data()

