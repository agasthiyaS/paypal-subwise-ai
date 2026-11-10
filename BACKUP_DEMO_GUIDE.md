# PayPal SubWise AI — Backup Demonstration & Failover Guide

This guide provides step-by-step failover procedures to guarantee a seamless live demonstration under any unexpected technical circumstance during hackathon presentations or judge evaluations.

---

## 1. Quick Emergency Recovery Dashboard

| Failure Mode | Immediate Symptoms | Failover Action | Recovery Time |
| :--- | :--- | :--- | :--- |
| **PayPal Sandbox Down** | Sync hangs or returns 500/503 | Click **"Demo Mode"** in the top navigation bar. | **2 seconds** |
| **Internet Offline** | External APIs unreachable | All deterministic engines run locally on PostgreSQL/SQLite; Gemini falls back to rule engine. | **Instant (Zero Downtime)** |
| **Backend Halts** | Frontend shows "Cannot reach backend" | Run Emergency Restart Command in PowerShell. | **5 seconds** |
| **Frontend Halts** | Browser displays `ERR_CONNECTION_REFUSED` | Restart Vite dev server or serve production build. | **5 seconds** |
| **Gemini API Throttled (429)** | AI Assistant response delayed | Engine automatically activates Deterministic Synthesis with verified cards. | **Instant (Zero Downtime)** |

---

## 2. Scenario 1: PayPal Developer Sandbox API is Offline or Slow

### Why this happens
PayPal Developer Sandbox occasionally experiences maintenance windows, elevated latency, or intermittent 500/502 errors during high-volume hackathon periods.

### Failover Procedure
1. In the top navigation bar, click the purple **"Demo Mode"** button (or click **"Switch to Demo"** in the PayPal Stream banner).
2. The application will instantly switch the active tenant context to **DemoTech Solutions**.
3. Point out to judges:
   > *"Notice our dual-mode resilience architecture: while our application supports live PayPal Developer Sandbox OAuth 2.0 integration, we provide a hermetically isolated 6-month demonstration profile (DemoTech Solutions) that allows evaluators to inspect realistic historical trends, multi-scenario simulations, and calendar concentration warnings regardless of external sandbox uptime."*
4. All 6 months of data, 9 subscriptions (including the Figma annual renewal), and the 100-point Financial Health Index (78/100) will render immediately.

---

## 3. Scenario 2: External AI Provider (Google Gemini) is Unavailable or Rate-Limited

### Why this happens
Google Gemini API may return HTTP 429 quota exhaustion, invalid API keys, or experience network timeouts.

### Failover Procedure
1. Navigate to **AI Assistant** (`/assistant`).
2. Ask any question:
   - *"What renewals are due in the next 30 days?"*
   - *"Can I afford Datadog for $350/month?"*
   - *"Summarize my software expenses."*
3. The backend automatically catches the exception in `AIAdvisor.chat_query()` and invokes `AIAdvisor._deterministic_query_response()`.
4. Point out to judges:
   > *"Notice the reliability of our Deterministic-First architecture: SubWise AI never relies solely on an external LLM for financial accuracy. When an external model is unavailable or rate-limited, our internal rule synthesis engine delivers verified Markdown summaries with full interactive evidence cards citing exact database records."*

---

## 4. Scenario 3: Complete Internet Outage (100% Offline Mode)

### Why this happens
Conference Wi-Fi disconnects or venue internet drops during presentation.

### Verification of Offline Capability
SubWise AI has zero runtime cloud dependencies for core operations:
- Backend: Runs on `http://127.0.0.1:8000` (FastAPI + local PostgreSQL).
- Frontend: Runs on `http://127.0.0.1:3000` (Vite SPA).
- PDF Generator: ReportLab renders vector PDFs locally using pure Python.
- CSV Generator: Python standard `csv` module with OWASP formula sanitization.
- Assistant: Deterministic Fallback engine operates 100% offline.

### Demonstration in Offline Mode
1. Stay connected to `http://localhost:3000`.
2. Navigate through:
   - Dashboard (`/`)
   - Subscriptions (`/subscriptions`)
   - Cash-Flow Forecast (`/forecast`)
   - Purchase Simulator (`/simulator`)
   - Reports (`/reports` - click Export PDF and show the generated document)
   - AI Assistant (`/assistant`)
3. Every single calculation, visualization, and PDF generation works flawlessly without internet access.

---

## 5. Scenario 4: Backend Server Halts or Needs Quick Restart

If the FastAPI backend process was closed or needs to be restarted:

### PowerShell Command (from Project Root)
```powershell
cd "backend"
$env:PYTHONPATH = "."
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Health Check Verification
Open a new browser tab or run:
```powershell
curl http://127.0.0.1:8000/docs
```
You should see the FastAPI interactive Swagger documentation.

---

## 6. Scenario 5: Frontend Server Halts or Needs Quick Restart

If the Vite frontend development server stops:

### PowerShell Command (from Project Root)
```powershell
cd "frontend"
npm run dev -- --host 127.0.0.1 --port 3000
```

### Alternate: Serve Production Static Build
If Vite dev server has issues, serve the pre-compiled production build:
```powershell
cd "frontend"
npx serve -s dist -l 3000
```

---

## 7. Scenario 6: Resetting Demo Data to Canonical State

If you or a previous evaluator modified or deleted demo records and you want a pristine 6-month baseline:

### Option A: In the UI
Click the white **"Reset Demo Data"** button in the purple DEMO MODE top banner.

### Option B: Via Python CLI
```powershell
cd "backend"
.\venv\Scripts\python.exe -c "
from app.database import SessionLocal
from app.models.user import User
from app.services.demo_data_generator import DemoDataGenerator
db = SessionLocal()
user = db.query(User).filter(User.id == 40).first() or db.query(User).first()
DemoDataGenerator.generate_demo_dataset(user_id=user.id, db=db)
db.close()
print('DemoTech Solutions canonical dataset restored successfully!')
"
```

---

## 8. Summary Checklist Before Pitching to Judges

- [ ] Backend running on `http://127.0.0.1:8000` (FastAPI)
- [ ] Frontend running on `http://127.0.0.1:3000` (React)
- [ ] Logged in as `summavidee@gmail.com`
- [ ] Active profile is set to **DemoTech Solutions** (purple DEMO MODE badge visible)
- [ ] Browser zoom set to 100% or 110% for crisp display on projector
- [ ] Pre-downloaded sample PDF report available in `Downloads` folder as extra backup
- [ ] `FIVE_MINUTE_DEMO_SCRIPT.md` open on speaker notes screen

