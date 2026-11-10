"""

Live Application Launch Verification Script.
Connects via HTTP to the running FastAPI server on http://127.0.0.1:8000
and checks all API endpoints supporting the 9 frontend pages.
"""
import httpx
import datetime
import sys
import pytest

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_live_launch():
    print("=" * 75)
    print("PAYPAL SUBWISE AI - LIVE APPLICATION VERIFICATION (http://127.0.0.1:8000)")
    print("=" * 75)

    try:
        with httpx.Client(timeout=2.0) as check_client:
            resp = check_client.get(f"{BASE_URL}/health")
            if resp.status_code != 200:
                pytest.skip("FastAPI live server returned non-200")
    except Exception:
        pytest.skip("FastAPI live server is not running on http://127.0.0.1:8000")

    with httpx.Client(timeout=20.0) as client:
        # 1. Health check
        resp = client.get(f"{BASE_URL}/health")
        assert resp.status_code == 200, f"Health failed: {resp.status_code}"
        health_data = resp.json()
        print(f"[1] Health Check: Status={health_data.get('status')}, Database={health_data.get('database')}")
        assert health_data.get("status") == "healthy"
        assert health_data.get("database") == "connected"

        # 2. Registration
        email = f"launch_test_{int(datetime.datetime.utcnow().timestamp())}@subwise.io"
        password = "LiveLaunchPassword2026!"
        reg_payload = {
            "email": email,
            "password": password,
            "full_name": "Executive Tester",
            "company_name": "CloudScale Systems",
            "industry": "FinTech / SaaS"
        }
        reg_resp = client.post(f"{BASE_URL}/auth/register", json=reg_payload)
        assert reg_resp.status_code in [200, 201], f"Register failed: {reg_resp.text}"
        token = reg_resp.json()["access_token"]
        print(f"[2] User Registration (Landing / Register Page API): Created user {email}, token received.")

        # 3. Login
        login_resp = client.post(
            f"{BASE_URL}/auth/login",
            data={"username": email, "password": password}
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        login_token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {login_token}"}
        print("[3] Authentication & JWT Verification (Login Page API): Verified login and Bearer token.")

        # 4. Profile
        me_resp = client.get(f"{BASE_URL}/auth/me", headers=headers)
        assert me_resp.status_code == 200
        biz_resp = client.get(f"{BASE_URL}/business/profile", headers=headers)
        assert biz_resp.status_code == 200
        biz_data = biz_resp.json()
        print(f"[4] Dashboard Business Profile API: {biz_data['company_name']}, Reserves=${biz_data['current_cash_reserves']}")

        # 5. PayPal Synchronization
        sync_resp = client.post(f"{BASE_URL}/transactions/sync?force_demo=true", headers=headers)
        assert sync_resp.status_code == 200
        sync_data = sync_resp.json()
        print(f"[5] PayPal Synchronization Pipeline: Synced {sync_data['transactions_synced']} txs, identified {sync_data['new_subscriptions_identified']} subscriptions.")

        # 6. Subscriptions page API
        subs_resp = client.get(f"{BASE_URL}/subscriptions/", headers=headers)
        assert subs_resp.status_code == 200
        subs_data = subs_resp.json()
        sub_list = subs_data.get("subscriptions", [])
        print(f"[6] Subscriptions Page API: Retrieved {len(sub_list)} active subscriptions (Monthly Spend: ${subs_data.get('total_monthly_spend')})")
        assert len(sub_list) > 0

        # 7. Transactions page API
        txs_resp = client.get(f"{BASE_URL}/transactions/", headers=headers)
        assert txs_resp.status_code == 200
        txs_list = txs_resp.json()
        print(f"[7] Transactions Page API: Retrieved {len(txs_list)} ledger entries.")
        assert len(txs_list) > 0

        # 8. Simulator page API
        sim_payload = {
            "revenue_shock_pct": -30.0,
            "paused_subscription_ids": [sub_list[0]["id"]],
            "scenario_name": "Live Launch -30% Shock Test"
        }
        sim_resp = client.post(f"{BASE_URL}/simulation/run", json=sim_payload, headers=headers)
        assert sim_resp.status_code == 200
        sim_data = sim_resp.json()
        print(f"[8] Cash-Flow Simulator Page API: Run simulation with runway={sim_data.get('projected_runway_months')} months")

        # 9. Recommendations page API
        recs_resp = client.get(f"{BASE_URL}/recommendations/", headers=headers)
        assert recs_resp.status_code == 200
        recs_list = recs_resp.json()
        print(f"[9] Recommendations Page API: Retrieved {len(recs_list)} actionable recommendations.")

        # 10. AI Briefing API
        ai_resp = client.get(f"{BASE_URL}/recommendations/ai-briefing", headers=headers)
        assert ai_resp.status_code == 200
        ai_data = ai_resp.json()
        briefing_text = ai_data.get("ai_briefing") or ai_data.get("briefing", "")
        print(f"[10] AI Advisor & CFO Briefing: Generated briefing ({len(briefing_text)} characters, source={ai_data.get('source')})")

        # 11. PayPal Sandbox Connect & Disconnect API
        conn_resp = client.post(
            f"{BASE_URL}/business/paypal-connect",
            json={"paypal_mode": "demo"},
            headers=headers
        )
        assert conn_resp.status_code == 200
        disc_resp = client.post(f"{BASE_URL}/business/paypal-disconnect", headers=headers)
        assert disc_resp.status_code == 200
        print("[11] PayPal Sandbox Connect & Disconnect Modal API: Tested connection toggle and graceful disconnect.")

    print("=" * 75)
    print("ALL 11 LIVE SERVER ENDPOINT TESTS PASSED ON http://127.0.0.1:8000")
    print("=" * 75)

if __name__ == "__main__":
    try:
        test_live_launch()
    except Exception as e:
        print(f"FAILED: {e}")
        sys.exit(1)
