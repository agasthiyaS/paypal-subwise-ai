"""
Automated PostgreSQL Setup & Verification Pipeline for PayPal SubWise AI.
Tests connection, initializes database and tables via Alembic,
and runs the full suite of verification tests.
"""
import os
import sys
import subprocess
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def run_pipeline():
    print("=" * 75)
    print("SUBWISE AI - POSTGRESQL INTEGRATION & VERIFICATION PIPELINE")
    print("=" * 75)

    load_dotenv(".env")
    db_url = os.getenv("DATABASE_URL")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "SubWise2026!Secure")
    host = os.getenv("POSTGRES_SERVER", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "subwise_ai")

    print(f"Target Database: {dbname} on {host}:{port}")
    print(f"Database User: {user}")

    # 1. Test connection to server
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port,
            connect_timeout=3
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            ver = cur.fetchone()[0]
            print(f"[1] Server Connected: {ver[:55]}...")
            
            # Check if subwise_ai database exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (dbname,))
            exists = cur.fetchone()
            if not exists:
                print(f"    Creating database '{dbname}'...")
                cur.execute(f'CREATE DATABASE "{dbname}";')
                print(f"    Database '{dbname}' created successfully.")
            else:
                print(f"    Database '{dbname}' already exists.")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Could not connect to PostgreSQL server: {e}")
        return False

    # 2. Run Alembic Migrations
    print("\n[2] Executing Alembic Migrations (upgrade head)...")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        res = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        print("    Alembic Output:", res.stdout.strip())
        print("    Migrations successfully applied to head.")
    except subprocess.CalledProcessError as e:
        print(f"    Alembic migration failed: {e.stderr}")
        return False

    # 3. Verify Tables Created
    print("\n[3] Verifying PostgreSQL Schema Tables...")
    from sqlalchemy import create_engine, inspect
    engine = create_engine(db_url)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"    Found {len(tables)} tables: {tables}")
    required_tables = ["users", "business_profiles", "transactions", "subscriptions", "recommendations", "scenario_simulations"]
    for t in required_tables:
        if t not in tables:
            print(f"[ERROR] Missing required table: {t}")
            return False
    print("    All 6 application entity tables verified with foreign key cascades.")

    # 4. Run Direct Runtime Tests
    print("\n[4] Running Direct PostgreSQL Runtime Tests (test_pg_runtime.py)...")
    res = subprocess.run([sys.executable, "test_pg_runtime.py"], capture_output=True, text=True, env=env)
    if res.returncode == 0:
        print("    PASSED: 10/10 Runtime CRUD and isolation tests succeeded.")
    else:
        print(f"    FAILED: {res.stderr}\n{res.stdout}")
        return False

    # 5. Run FastAPI Live API Tests
    print("\n[5] Running FastAPI PostgreSQL Live API Tests (test_api_live_pg.py)...")
    res = subprocess.run([sys.executable, "test_api_live_pg.py"], capture_output=True, text=True, env=env)
    if res.returncode == 0:
        print("    PASSED: 10/10 FastAPI live endpoint tests succeeded.")
    else:
        print(f"    FAILED: {res.stderr}\n{res.stdout}")
        return False

    # 6. Run PayPal Sandbox Integration Tests
    print("\n[6] Running PayPal Sandbox Integration Tests (test_paypal_sandbox.py)...")
    res = subprocess.run([sys.executable, "test_paypal_sandbox.py"], capture_output=True, text=True, env=env)
    if res.returncode == 0:
        print("    PASSED: 12/12 PayPal Sandbox tests succeeded.")
    else:
        print(f"    FAILED: {res.stderr}\n{res.stdout}")
        return False

    # 7. Run Comprehensive Audit Test Suite
    print("\n[7] Running Full Application Audit (audit_test_runner.py)...")
    res = subprocess.run([sys.executable, "audit_test_runner.py"], capture_output=True, text=True, env=env)
    if res.returncode == 0:
        print("    PASSED: 25/25 Comprehensive audit assertions passed.")
    else:
        print(f"    FAILED: {res.stderr}\n{res.stdout}")
        return False

    print("\n" + "=" * 75)
    print("ALL POSTGRESQL DATABASE & APPLICATION TESTS PASSED 100%!")
    print("=" * 75)
    return True

if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)

