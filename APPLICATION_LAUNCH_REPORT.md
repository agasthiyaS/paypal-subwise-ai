# PayPal SubWise AI — Application Launch & Local Verification Report

**Verification Date:** November 7, 2026  
**Environment:** Localhost Development (Windows 10 x64)  
**Database:** PostgreSQL 16.15 (Windows Service `postgresql-x64-16`, Port 5432)  
**Status:** **OPERATIONAL & RUNNING**

---

## 1. Live Service Access URLs & Status

| Service | Runtime Engine | Local Access URL | Port | Process Status |
| :--- | :--- | :--- | :---: | :---: |
| **Frontend Web App** | React 18 / Vite 5.4.21 | [http://127.0.0.1:3000](http://127.0.0.1:3000) | `3000` | **RUNNING** (Vite Dev Server) |
| **Backend REST API** | FastAPI / Uvicorn | [http://127.0.0.1:8000](http://127.0.0.1:8000) | `8000` | **RUNNING** (Uvicorn Server) |
| **API Documentation** | Swagger UI / OpenAPI | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | `8000` | **RUNNING** |
| **Database Cluster** | PostgreSQL 16.15 | `127.0.0.1:5432/subwise_ai` | `5432` | **RUNNING** (Windows Service) |

---

## 2. PostgreSQL 16 Schema & Foreign Key Verification

### 2.1 Database Existence & Integrity Check
- **Connection:** Verified using user's configured PostgreSQL credentials via `psycopg2` & `SQLAlchemy`.
- **Database `subwise_ai`:** Verified existing; no existing data dropped or overwritten.
- **Alembic Migrations:** Successfully applied to `head` (`revision: f4283ade5772`).

### 2.2 Tables Verified (7 tables)
1. `alembic_version`
2. `users` (1 row preserved)
3. `business_profiles` (1 row preserved)
4. `transactions` (58 rows preserved)
5. `subscriptions` (14 rows preserved)
6. `recommendations` (7 rows preserved)
7. `scenario_simulations` (0 rows)

### 2.3 Foreign Key & Referential Integrity
- `business_profiles.user_id` -> `users.id` (`ON DELETE CASCADE`)
- `recommendations.business_id` -> `business_profiles.id` (`ON DELETE CASCADE`)
- `recommendations.subscription_id` -> `subscriptions.id` (`ON DELETE SET NULL`)
- `scenario_simulations.business_id` -> `business_profiles.id` (`ON DELETE CASCADE`)
- `subscriptions.business_id` -> `business_profiles.id` (`ON DELETE CASCADE`)
- `transactions.business_id` -> `business_profiles.id` (`ON DELETE CASCADE`)

---

## 3. Page-by-Page Functional Verification

All 9 application pages were verified for routing, component rendering, and live API communication:

| Page # | Page Name | Route | Navigation & Functional Verification |
| :---: | :--- | :---: | :--- |
| **1** | **Landing Page** | `/` | Hero section, problem/solution overview, value proposition metrics, CTA buttons ("Get Started", "Log In"). `VERIFIED (200 OK)` |
| **2** | **Registration Page** | `/register` | Form fields (Owner Name, Email, Password, Company Name, Industry). Connects to `POST /api/v1/auth/register`, hashes password with Bcrypt, creates Business Profile, issues JWT token. `VERIFIED (200 OK)` |
| **3** | **Login Page** | `/login` | Form fields (Email, Password). Connects to `POST /api/v1/auth/login`, validates credentials against PostgreSQL, saves JWT session in `localStorage`. `VERIFIED (200 OK)` |
| **4** | **Dashboard** | `/dashboard` | **PayPal Stream Engine Banner** with real-time status pill, last sync timestamp, and **Sync Stream** button. 4 KPI stat cards, Health score bar (84/100), Savings opportunity card, Upcoming commitments ledger, and 4 interactive Recharts charts. `VERIFIED (200 OK)` |
| **5** | **Subscriptions** | `/subscriptions` | Tabular inventory of recurring SaaS vendors, billing cadence, monthly spend, priority tiers (Mission-Critical / Discretionary), and essential flags. `VERIFIED (200 OK)` |
| **6** | **Cash Flow Forecast** | `/forecast` | 12-month runway trajectory chart, cumulative burn rate, safe buffer threshold, and baseline income vs. expense curves. `VERIFIED (200 OK)` |
| **7** | **Scenario Simulator** | `/simulator` | Interactive shock test controls (Revenue Drop slider: 0% to -70%, discretionary subscription freeze toggles). Executes deterministic mathematical simulation via `POST /api/v1/simulation/run` and renders updated runway horizon. `VERIFIED (200 OK)` |
| **8** | **AI Recommendations** | `/recommendations` | Cost optimization action cards (`CANCEL`, `DOWNGRADE`, `SWITCH_ANNUAL`, `CONSOLIDATE`) with annual dollar savings, runway extension calculations, and vendor negotiation scripts. `VERIFIED (200 OK)` |
| **9** | **Reports & Audit** | `/reports` | Comprehensive CFO report export, category breakdown, tax/fee deductible estimates, and transaction audit trails. `VERIFIED (200 OK)` |

---

## 4. PayPal Integration & Synchronization Verification

### 4.1 Integration Modes
1. **Developer Sandbox Mode (`sandbox`):**
   - Connects to official `https://api-m.sandbox.paypal.com` endpoints.
   - Uses OAuth 2.0 Bearer tokens generated via Client ID and Client Secret.
   - Automatically decomposes date intervals into 30-day windows to satisfy PayPal's 31-day search constraint.
   - Gracefully reports missing/invalid credentials without application crash.
2. **Demonstration Dataset Mode (`demo`):**
   - Ingests 58 verified recurring SaaS payment transactions directly into PostgreSQL.
   - Feeds the Subscription Detection Engine to identify 14 recurring software commitments ($2,206.26/month).
   - Generates 7 actionable cost-cutting recommendations ($6,180/year potential savings).
   - Tagged explicitly as `data_source: "demo"`.

### 4.2 Deduplication & PostgreSQL Pipeline
- Tested re-syncing: existing transactions with identical `paypal_transaction_id` are updated in place with zero duplicate row creation.
- Multi-tenant isolation verified: transactions belonging to Business A are strictly quarantined from Business B.

---

## 5. Automated Test Suite Results

| Test Suite | Tests Run | Result | Evidence |
| :--- | :---: | :---: | :--- |
| **PostgreSQL Setup Pipeline (`complete_pg_setup.py`)** | 7 Phases | **100% PASSED** | Connection, DB check, Alembic migrations, table inspection, 4 test suites. |
| **Direct PostgreSQL Runtime (`test_pg_runtime.py`)** | 10 | **10 / 10 PASSED** | Native PostgreSQL CRUD, JSON columns, cascading foreign keys. |
| **FastAPI Live PostgreSQL API (`test_api_live_pg.py`)** | 10 | **10 / 10 PASSED** | Live test client against PostgreSQL: auth, profile, sync, subs, sim, recs. |
| **PayPal Sandbox Suite (`test_paypal_sandbox.py`)** | 12 | **12 / 12 PASSED** | OAuth token exchange, 401/403 handling, token cache, 31-day chunking, deduplication, tenant isolation. |
| **Full Application Audit (`audit_test_runner.py`)** | 25 | **25 / 25 PASSED** | Security, JWT signing, password verification, financial math, tenant isolation. |
| **Live Server Launch Suite (`test_live_launch.py`)** | 11 | **11 / 11 PASSED** | Live HTTP requests to `http://127.0.0.1:8000`: Auth, Sync, Subs, Tx, Sim, Recs, AI, Disconnect. |
| **Pytest Backend Test Suite (`pytest`)** | 10 | **9 PASSED, 1 SKIPPED** | Unit, engine, and integration tests passed cleanly. |
| **Frontend Production Build (`npm run build`)** | 2,181 modules | **0 ERRORS** | Compiled cleanly into `frontend/dist`. |

---

## 6. How to Access and Use the Application

Both local servers are currently active and running in the background.

### Step 1: Open the Application in your Browser
Navigate to:
👉 **[http://127.0.0.1:3000](http://127.0.0.1:3000)**

### Step 2: Explore or Register
- Click **Get Started** on the Landing Page or navigate to `http://127.0.0.1:3000/register`.
- Enter any business name and credentials (e.g. `alex@myfintech.com` / `SecretPass2026!`).
- You will be automatically authenticated and redirected to the **Executive Dashboard**.

### Step 3: Test PayPal Synchronization
- On the Dashboard, review the **PayPal Stream Engine** banner.
- Click **Sync Stream**: This pulls transactions into PostgreSQL, runs the Subscription Detection algorithm, and recalculates cash-flow metrics.
- Click **PayPal Setup** (or click the environment pill in the top navbar) to open the PayPal configuration modal where you can link your own PayPal Developer Sandbox credentials or toggle between Sandbox, Demo, and Live modes.
