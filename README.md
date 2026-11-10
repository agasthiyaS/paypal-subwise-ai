# PayPal SubWise AI

> **Intelligent Subscription Management & Cash-Flow Scenario Simulator for Small Businesses.**
> Built for competitive fintech hackathons with high-precision forecasting, PayPal payment stream intelligence, and automated SaaS waste mitigation.

---

## 1. Problem Statement
Small businesses with fluctuating income often struggle to balance recurring software subscriptions with forward cash-flow realities. While standard PayPal statements show historical outflows, they fail to explain how upcoming subscription renewals and contract creep will intersect with seasonal revenue dips or cash burns.

## 2. Proposed Solution
**PayPal SubWise AI** bridges this gap:
1. Ingests and normalizes raw PayPal payment descriptors (handling live production rails, developer sandboxes, and verified demonstration datasets).
2. Algorithmic cadence and price creep detection (inter-arrival variance, price hikes, license sprawl).
3. Deterministic cash-flow scenario stress simulator (models revenue shocks, pauses discretionary subscriptions, and calculates the exact depletion horizon).
4. Generates quantified financial action plans (`CANCEL`, `CONSOLIDATE`, `DOWNGRADE`, `SWITCH TO ANNUAL`) and supplier renegotiation scripts.
5. Synthesizes executive CFO intelligence summaries using contextual AI.

---

## 3. Technology Stack

- **Frontend**:
  - React.js 18+ (SPA architecture)
  - Recharts (Area charts for cash runway, donut charts for spend distribution)
  - Lucide React (Fintech iconography)
  - Modern Glassmorphism FinTech CSS System (Slate/Navy theme, responsive desktop/mobile)
- **Backend**:
  - Python 3.10+
  - FastAPI (REST API with OpenAPI/Swagger docs at `/docs`)
  - PostgreSQL & SQLAlchemy 2.0 (with connection pooling: `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=3600`)
  - Alembic (Database schema migrations)
  - Pydantic v2 (Strict data validation)
  - Native Bcrypt & PyJWT (Secure authentication)
- **Data & Forecasting**:
  - NumPy & Pandas (Data normalization, inter-arrival time cadence analysis, variance tracking)
  - Deterministic cash-flow projection algorithms
- **Integrations**:
  - PayPal REST API (OAuth 2.0, Transactions, Reporting)
  - Three strictly isolated ingestion modes: `LIVE`, `SANDBOX`, and `DEMO`
  - Contextual AI layer (Gemini / LLM API with resilient deterministic financial fallbacks)

---

## 4. Core Modules & Calculation Methodology

### Module 1: Business Registration & Account Connection
- JWT-based authentication with business context collection (baseline monthly revenue, liquid cash reserves, target runway safety margin, risk tolerance).
- PayPal credential management with live credential verification.

### Module 2: PayPal Payment Data Acquisition
- **Live Mode**: Direct REST API integration via PayPal OAuth 2.0 (`/v1/reporting/transactions`).
- **Sandbox Mode**: Safe test transactions via PayPal developer accounts.
- **Verified Demonstration Dataset**: 100% deterministic, transparent demo data covering 14 SaaS vendors with revenue spikes and dips.

### Module 3: Vendor Normalization Engine
- Transforms noisy card descriptors (e.g. `AMZN *AWS CLOUD 102938`, `SLACK TECH INC MO PYMT`, `GOOGLE *WORKSPACE GSUITE`) into canonical merchant entities (`AWS`, `Slack`, `Google Workspace`) with designated business tiers and redundancy groups.

### Module 4: Subscription Identification Engine
- **Cadence Detection**: Analyzes time deltas between consecutive transactions ($7\pm2$ days = Weekly, $30\pm4$ days = Monthly, $90\pm7$ days = Quarterly, $365\pm15$ days = Annual).
- **Creeping Cost Detection**: Flags subscriptions where cost escalated $>15\%$ over recent billing cycles.
- **Criticality Tiers**:
  - `Tier 1`: Mission-Critical Core Ops (AWS, Google Workspace, GitHub)
  - `Tier 2`: Important Operational Tools (Slack, Notion, Figma)
  - `Tier 3`: Discretionary / Convenience (Zoom, Asana, Dropbox, Mailchimp)

### Module 5: Cash-Flow Scenario Simulator
- Forward 12-to-24 month deterministic cash-flow projections:
  $$\text{Net Cash Flow} = \text{Simulated Revenue} - (\text{Operating Costs} + \text{Active Subscriptions})$$
- Computes exact depletion month, runway extension delta, and capital preserved.
- Interactive sliders for revenue shocks ($-50\%$ to $+50\%$) and selective subscription pausing.

### Module 6: Recommendation Engine & AI Advisor
- **Consolidation**: Detects duplicate tools in the same workflow (e.g. Zoom vs Google Meet, Asana vs Notion, Dropbox vs Google Drive).
- **Vendor Negotiation Scripts**: Pre-drafted retention desk negotiation letters for cost reduction.
- **AI CFO Briefing**: Executive briefing explaining cash health and strategic directives.

---

## 5. Quickstart & Installation

### Option A: 1-Click Launch (Recommended)
From the root directory:
```bash
python run_app.py
```
This automatically seeds the demo business dataset, launches the backend on `http://127.0.0.1:8000`, and opens the application in your browser.

### Option B: Decoupled Development Mode

#### 1. Backend:
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Run database migrations
alembic upgrade head

# Seed verified demonstration data
python seed.py

# Launch FastAPI development server
uvicorn app.main:app --reload --port 8000
```
Swagger UI available at: `http://127.0.0.1:8000/docs`

#### 2. Frontend:
```bash
cd frontend
npm install
npm run dev
```
Vite dev server running at: `http://localhost:3000`

---

## 6. Pre-Configured Demo Credentials
For instant demonstration:
- **Email**: `demo@subwise.io`
- **Password**: `DemoPass2026!`
- Or simply click **"Explore Verified Live Demo (1-Click)"** on the login screen.

---

## 7. Verification & Tests
Run all unit and integration test suites:
```bash
$env:PYTHONPATH="backend"
backend\venv\Scripts\python.exe -m pytest -p no:anyio backend\tests\
```
- `test_engines.py`: Tests vendor normalizer, cadence detector, cash-flow simulator, and redundancy mapping.
- `test_api.py`: Tests full end-to-end user registration, PayPal sync, subscription intelligence, simulation, and recommendations.

---

## 8. License
Developed for the FinTech Hackathon. Open-source under MIT License.

