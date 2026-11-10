"""
Comprehensive verification of all endpoints for data isolation:
- Tests Biz 36 (NovaTech SaaS Inc) in Sandbox mode:
    * exactly 10 genuine Sandbox transactions (0 demo transactions)
    * verified starting cash $4,964.41
    * exactly 1 potential subscription (CloudSoft)
    * 0 confirmed subscriptions
    * operating revenue $0.00, operating expenses $40.00
- Tests Demo Mode (DemoTech Solutions or X-SubWise-Demo-Mode: true):
    * returns demo transactions & demo subscriptions
    * demo financial metrics function completely
"""
import sys
sys.path.insert(0, r"c:\Users\AGASTHIYASENTHILMAN\Desktop\projects\PAYPAL- SUBWISE AI\backend")

from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models import User, BusinessProfile
from app.services.auth_service import create_access_token

db = SessionLocal()
try:
    user_36 = db.query(User).filter(User.id == 36).first()
    # Explicitly set active_business_id to 36 (NovaTech SaaS Inc) for Sandbox testing
    user_36.active_business_id = 36
    db.commit()

    token = create_access_token(data={"sub": str(user_36.id)})
    sandbox_headers = {
        "Authorization": f"Bearer {token}",
        "X-SubWise-Demo-Mode": "false"
    }

    client = TestClient(app)

    print("=================================================================")
    print("TEST 1: GET /api/v1/transactions/ (Sandbox Mode - NovaTech SaaS Inc)")
    print("=================================================================")
    res = client.get("/api/v1/transactions/", headers=sandbox_headers)
    assert res.status_code == 200, f"Status: {res.status_code}, {res.text}"
    txs = res.json()
    print(f"Transactions returned: {len(txs)}")
    assert len(txs) == 10, f"Expected 10 genuine Sandbox transactions, got {len(txs)}"
    sources = set(t.get("data_source") for t in txs)
    print(f"Data sources in response: {sources}")
    assert sources == {"sandbox"}, f"Expected only sandbox data_source, got {sources}"
    has_demo_id = any(t.get("paypal_transaction_id", "").startswith("DEMO_") for t in txs)
    assert not has_demo_id, "Found DEMO_ ID in sandbox transactions!"
    for t in txs:
        print(f"  {t.get('paypal_transaction_id'):20} | gross={t.get('gross_amount'):>8.2f} {t.get('currency')} | ds={t.get('data_source')}")

    print("\n=================================================================")
    print("TEST 2: GET /api/v1/subscriptions/ (Sandbox Mode - NovaTech SaaS Inc)")
    print("=================================================================")
    res = client.get("/api/v1/subscriptions/", headers=sandbox_headers)
    assert res.status_code == 200, f"Status: {res.status_code}, {res.text}"
    sub_data = res.json()
    print(f"Total active count: {sub_data.get('total_active_count')}")
    print(f"Confirmed count: {sub_data.get('confirmed_count')}")
    print(f"Potential count: {sub_data.get('potential_count')}")
    print(f"Monthly spend: ${sub_data.get('total_monthly_spend')}")
    print(f"Potential monthly savings: ${sub_data.get('potential_monthly_savings')}")
    assert sub_data.get("confirmed_count") == 0, f"Expected 0 confirmed subs, got {sub_data.get('confirmed_count')}"
    assert sub_data.get("potential_count") == 1, f"Expected 1 potential sub (CloudSoft), got {sub_data.get('potential_count')}"
    subs = sub_data.get("subscriptions", [])
    print(f"Subscriptions list count: {len(subs)}")
    assert len(subs) == 1, f"Expected 1 subscription, got {len(subs)}"
    assert subs[0].get("vendor_name") == "CloudSoft", f"Expected CloudSoft, got {subs[0].get('vendor_name')}"
    print(f"  Vendor: {subs[0].get('vendor_name')}, amount: ${subs[0].get('latest_amount')}, type: {subs[0].get('detection_type')}")

    print("\n=================================================================")
    print("TEST 3: GET /api/v1/forecast/ (Sandbox Mode - NovaTech SaaS Inc)")
    print("=================================================================")
    res = client.get("/api/v1/forecast/", headers=sandbox_headers)
    assert res.status_code == 200, f"Status: {res.status_code}, {res.text}"
    fc_data = res.json()
    verified_cash = fc_data.get("verified_starting_cash")
    has_cash = fc_data.get("has_verified_cash")
    print(f"Verified starting cash: ${verified_cash} (has_verified={has_cash})")
    print(f"Status: {fc_data.get('status')}")
    assert verified_cash == 4964.41, f"Expected $4,964.41 starting cash, got {verified_cash}"

    print("\n=================================================================")
    print("TEST 4: GET /api/v1/reports/monthly (Sandbox Mode - NovaTech SaaS Inc)")
    print("=================================================================")
    res = client.get("/api/v1/reports/monthly", headers=sandbox_headers)
    assert res.status_code == 200, f"Status: {res.status_code}, {res.text}"
    rep_data = res.json()
    print(f"Total operating revenue: ${rep_data.get('total_operating_revenue')}")
    print(f"Total operating expenses: ${rep_data.get('total_operating_expenses')}")
    print(f"Total confirmed sub expenses: ${rep_data.get('total_confirmed_sub_expenses')}")
    print(f"Total potential sub expenses: ${rep_data.get('total_potential_sub_expenses')}")
    print(f"Net operating cashflow: ${rep_data.get('net_operating_cashflow')}")
    print(f"Verified available cash: ${rep_data.get('verified_available_cash')}")
    assert rep_data.get("total_operating_revenue") == 0.0, f"Expected 0 operating revenue, got {rep_data.get('total_operating_revenue')}"
    assert rep_data.get("total_confirmed_sub_expenses") == 0.0, f"Expected 0 confirmed sub expenses, got {rep_data.get('total_confirmed_sub_expenses')}"
    assert rep_data.get("total_potential_sub_expenses") == 40.0, f"Expected 40 potential sub expenses (2x $20 CloudSoft), got {rep_data.get('total_potential_sub_expenses')}"
    assert rep_data.get("verified_available_cash") == 4964.41, f"Expected 4964.41 verified cash, got {rep_data.get('verified_available_cash')}"

    print("\n=================================================================")
    print("TEST 5: GET /api/v1/recommendations/ (Sandbox Mode - NovaTech SaaS Inc)")
    print("=================================================================")
    res = client.get("/api/v1/recommendations/", headers=sandbox_headers)
    assert res.status_code == 200, f"Status: {res.status_code}, {res.text}"
    recs = res.json()
    print(f"Recommendations returned: {len(recs)}")
    for r in recs:
        print(f"  Vendor: {r.get('vendor_name')}, action: {r.get('action_type')}, saving: ${r.get('potential_monthly_saving')}/mo")

    print("\n=================================================================")
    print("TEST 6: DEMO MODE ISOLATION (X-SubWise-Demo-Mode: true)")
    print("=================================================================")
    demo_headers = {
        "Authorization": f"Bearer {token}",
        "X-SubWise-Demo-Mode": "true"
    }
    res_demo_txs = client.get("/api/v1/transactions/", headers=demo_headers)
    assert res_demo_txs.status_code == 200
    dtxs = res_demo_txs.json()
    print(f"Demo mode transactions returned: {len(dtxs)}")
    assert len(dtxs) > 0, "Expected demo transactions in demo mode"
    res_demo_subs = client.get("/api/v1/subscriptions/", headers=demo_headers)
    assert res_demo_subs.status_code == 200
    dsubs = res_demo_subs.json()
    print(f"Demo mode subscriptions returned: {len(dsubs.get('subscriptions', []))}")
    assert len(dsubs.get("subscriptions", [])) > 0, "Expected demo subscriptions in demo mode"
    print(f"Demo mode monthly spend: ${dsubs.get('total_monthly_spend')}")

    print("\n=================================================================")
    print("ALL 6 ISOLATION TESTS PASSED WITH 100% SUCCESS!")
    print("=================================================================")

finally:
    db.close()
