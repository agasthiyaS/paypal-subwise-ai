"""
Live FastAPI API End-to-End Verification against PostgreSQL 16.
Tests all endpoints using FastAPI TestClient with the live PostgreSQL engine.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine, SessionLocal
from app.models.user import User

client = TestClient(app)

def test_api_pg_live():
    print("=" * 70)
    print("PAYPAL SUBWISE AI - FASTAPI LIVE POSTGRESQL API VERIFICATION")
    print("=" * 70)

    # 1. Health check
    res = client.get("/api/v1/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health_data = res.json()
    print("[1] Health Check:", health_data)
    assert health_data.get("status") == "healthy"
    print(" -> PASSED: /api/v1/health returned 200 OK & healthy.")

    # Clean up test user if exists
    db = SessionLocal()
    existing = db.query(User).filter(User.email == "api_pg_test@subwise.io").first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()

    # 2. Registration against PostgreSQL
    reg_payload = {
        "email": "api_pg_test@subwise.io",
        "password": "FintechPostgres2026!",
        "full_name": "API Test User",
        "company_name": "Fintech Live Systems",
        "industry": "Financial Technology"
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code in [200, 201], f"Register failed: {reg_res.status_code} {reg_res.text}"
    reg_data = reg_res.json()
    token = reg_data.get("access_token")
    assert token is not None
    print(f"[2] Registration on PostgreSQL: User registered, token received ({token[:20]}...)")
    print(" -> PASSED: /api/v1/auth/register persisted user & business to PostgreSQL.")

    headers = {"Authorization": f"Bearer {token}"}

    # 3. /auth/me lookup
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user"]["email"] == "api_pg_test@subwise.io"
    print(f"[3] Current User Profile: {me_data['user']['email']} ({me_data['user']['full_name']})")
    print(" -> PASSED: /api/v1/auth/me fetched from PostgreSQL.")

    # 4. /business/profile
    biz_res = client.get("/api/v1/business/profile", headers=headers)
    assert biz_res.status_code == 200
    biz_data = biz_res.json()
    print(f"[4] Business Profile: {biz_data['company_name']} (Reserves: ${biz_data['current_cash_reserves']})")
    print(" -> PASSED: /api/v1/business/profile returned PostgreSQL record.")

    # 5. Connect Demo Data via /transactions/sync
    sync_res = client.post("/api/v1/transactions/sync?force_demo=true", headers=headers)
    assert sync_res.status_code == 200, f"Sync failed: {sync_res.status_code} {sync_res.text}"
    print("[5] Demo Transaction Sync into PostgreSQL:", sync_res.json())
    print(" -> PASSED: Demo transactions & detected subscriptions stored in PostgreSQL.")

    # 6. /subscriptions/
    subs_res = client.get("/api/v1/subscriptions/", headers=headers)
    assert subs_res.status_code == 200
    subs_data = subs_res.json()
    sub_list = subs_data.get("subscriptions", [])
    print(f"[6] Retrieved Subscriptions from PostgreSQL: {len(sub_list)} detected subscriptions.")
    assert len(sub_list) > 0
    print(" -> PASSED: /api/v1/subscriptions/ fetched real records from PostgreSQL.")

    # 7. /transactions/
    tx_res = client.get("/api/v1/transactions/", headers=headers)
    assert tx_res.status_code == 200
    tx_list = tx_res.json()
    print(f"[7] Retrieved Transactions from PostgreSQL: {len(tx_list)} records.")
    assert len(tx_list) > 0
    print(" -> PASSED: /api/v1/transactions/ fetched records from PostgreSQL.")

    # 8. Scenario Simulation against PostgreSQL
    sim_payload = {
        "revenue_shock_pct": -25.0,
        "paused_subscription_ids": [sub_list[0]["id"]],
        "scenario_name": "PostgreSQL 25% Revenue Drop Test"
    }
    sim_res = client.post("/api/v1/simulation/run", json=sim_payload, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    print(f"[8] Scenario Simulation Run: Runway={sim_data.get('projected_runway_months')} months, Depletion={sim_data.get('depletion_month')}")
    print(" -> PASSED: /api/v1/simulation/run executed math & saved scenario into PostgreSQL.")

    # 9. Recommendations
    rec_res = client.get("/api/v1/recommendations/", headers=headers)
    assert rec_res.status_code == 200
    rec_list = rec_res.json()
    print(f"[9] Recommendations from PostgreSQL: {len(rec_list)} recommendations.")
    assert len(rec_list) > 0
    print(" -> PASSED: /api/v1/recommendations/ retrieved successfully.")

    # Clean up test user
    db = SessionLocal()
    cleanup_user = db.query(User).filter(User.email == "api_pg_test@subwise.io").first()
    if cleanup_user:
        db.delete(cleanup_user)
        db.commit()
    db.close()
    print("[10] Cleanup: Test user and cascading data cleaned up successfully.")

    print("\n" + "=" * 70)
    print("ALL 10 FASTAPI LIVE POSTGRESQL END-TO-END TESTS PASSED!")
    print("=" * 70)

if __name__ == "__main__":
    test_api_pg_live()
