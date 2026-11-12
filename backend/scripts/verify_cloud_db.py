"""
Cloud Database Verification Utility
Safely inspects the connected PostgreSQL database (e.g., Neon Cloud)
to verify schema completion, Alembic migration head, and table structure.
Masks credentials and never outputs secrets or connection passwords.
"""
import os
import sys
import re
from urllib.parse import urlparse

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from sqlalchemy import create_engine, inspect, text


REQUIRED_TABLES = [
    "users",
    "business_profiles",
    "transactions",
    "subscriptions",
    "expenses",
    "budgets",
    "household_members",
    "vendors",
    "vendor_plans",
    "recommendations",
    "scenario_simulations",
    "conversations",
    "chat_messages",
    "webhook_events",
    "alembic_version",
]


def mask_db_url(url: str) -> str:
    """Masks database password in connection string for safe console output."""
    if not url:
        return "<EMPTY>"
    return re.sub(r":([^:@]+)@", r":***@", url)


def verify_database():
    raw_url = settings.DATABASE_URL
    masked_url = mask_db_url(raw_url)
    print("=" * 60)
    print("  SUBWISE AI — CLOUD DATABASE VERIFICATION")
    print("=" * 60)
    print(f"Target Database: {masked_url}")

    if "localhost" in raw_url or "127.0.0.1" in raw_url:
        print("[WARNING] Connection URL points to LOCALHOST.")
        print("          Set DATABASE_URL to your Neon connection string to verify the cloud database.")

    try:
        engine = create_engine(raw_url, pool_pre_ping=True)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
    except Exception as e:
        print(f"\n[FAIL] Could not connect to database: {e}")
        sys.exit(1)

    print(f"\n[SUCCESS] Successfully connected to database engine.")
    print(f"Total Tables Detected: {len(tables)}")

    missing = [t for t in REQUIRED_TABLES if t not in tables]
    if missing:
        print(f"\n[INCOMPLETE] Missing {len(missing)} required tables: {', '.join(missing)}")
        print("Run `alembic upgrade head` against this database to apply all migrations.")
        sys.exit(1)
    else:
        print(f"\n[VERIFIED] All {len(REQUIRED_TABLES)} required database tables exist:")
        for t in sorted(REQUIRED_TABLES):
            col_count = len(inspector.get_columns(t))
            print(f"  ✓ {t:<24} ({col_count} columns)")

    # Check Alembic migration head
    with engine.connect() as conn:
        try:
            res = conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1")).scalar()
            print(f"\nAlembic Current Version: {res}")
            if res == "b50_conversations":
                print("✓ Database is up to date with HEAD migration (b50_conversations).")
            else:
                print(f"[NOTE] Current version is '{res}'. Expected head is 'b50_conversations'.")
        except Exception as e:
            print(f"[WARNING] Could not read alembic_version table: {e}")

    print("\n" + "=" * 60)
    print("  DATABASE VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    verify_database()
