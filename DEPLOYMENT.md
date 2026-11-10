# PayPal SubWise AI — Production Deployment & Operations Guide

## 1. System Architecture Overview
PayPal SubWise AI is an enterprise-grade financial intelligence and automated subscription optimization platform. It features strict multi-tenant data isolation supporting three operational tiers:
- **Individual:** Personal income, recurring streaming/subscriptions, and expense optimization.
- **Household:** Multi-member expense pooling, shared grocery/utility management, and fairness audits.
- **Business:** Comprehensive SMB treasury intelligence, PayPal REST API sync, webhook lifecycle processing, multi-currency conversions, and cash-flow scenario forecasting.

```
       [Client Browser (React SPA)]
                    │
                    ▼ (HTTPS / WSS)
         [Reverse Proxy (Nginx)]
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
 [Vite Static Dist]   [FastAPI ASGI (Uvicorn)]
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
         [PostgreSQL 16] [PayPal API]   [Gemini AI]
```

---

## 2. Prerequisites & Minimum Requirements
- **Operating System:** Linux (Ubuntu 22.04 LTS / Debian 12 recommended) or Windows Server 2022
- **Python:** Python 3.10 or 3.11 with `pip` and `virtualenv`
- **Node.js:** Node.js v18.x or v20.x with `npm`
- **Database:** PostgreSQL 16 with standard UTF-8 collation
- **Memory & Storage:** 2 CPU cores, 4GB RAM minimum (8GB recommended for production reporting), 20GB SSD

---

## 3. Environment Variables Specification

Create or configure `.env` in the `backend/` directory:

```env
# ─── CORE ENVIRONMENT ────────────────────────────────────────────────────────
ENVIRONMENT=production
PROJECT_NAME="PayPal SubWise AI"
VERSION="2.0.0"
API_V1_STR="/api/v1"

# ─── DATABASE CONFIGURATION ──────────────────────────────────────────────────
DATABASE_URL=postgresql://subwise_user:STRONG_SECURE_PASSWORD@localhost:5432/subwise_ai_db

# ─── AUTHENTICATION & SECURITY ───────────────────────────────────────────────
SECRET_KEY=GENERATE_A_64_CHAR_HEX_SECRET_FOR_PRODUCTION
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ─── PAYPAL INTEGRATION ──────────────────────────────────────────────────────
PAYPAL_ENVIRONMENT=sandbox          # 'sandbox' or 'live'
PAYPAL_CLIENT_ID=your_paypal_client_id_here
PAYPAL_CLIENT_SECRET=your_paypal_client_secret_here
PAYPAL_WEBHOOK_ID=your_paypal_webhook_id_here

# ─── AI ASSISTANT CONFIGURATION ──────────────────────────────────────────────
GEMINI_API_KEY=your_gemini_api_key_here
```

Create or configure `.env` in the `frontend/` directory (if different from default relative `/api/v1`):

```env
VITE_API_URL=/api/v1
```

---

## 4. Database Setup & Migrations

```bash
# 1. Connect to PostgreSQL and create database and user
sudo -u postgres psql
CREATE DATABASE subwise_ai_db;
CREATE USER subwise_user WITH ENCRYPTED PASSWORD 'STRONG_SECURE_PASSWORD';
GRANT ALL PRIVILEGES ON DATABASE subwise_ai_db TO subwise_user;
\q

# 2. Run Alembic Migrations to apply full schema (up to Phase 6)
cd backend
source venv/bin/activate   # On Windows: .\venv\Scripts\activate
alembic upgrade head
```

Verified Alembic head revision: `b40_platform_expansion`.

---

## 5. Admin Bootstrap Procedure

To grant administrator access to an initial user:

```bash
cd backend
python -c "
from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
admin = db.query(User).filter_by(email='admin@yourdomain.com').first()
if admin:
    admin.is_admin = True
    db.commit()
    print('Admin privileges enabled for:', admin.email)
else:
    print('User not found. Register via frontend or API first.')
db.close()
"
```

Once designated as an admin, accessing `/admin` in the frontend reveals the **Platform Operations & Metrics** portal.

---

## 6. Building and Running the Application

### A. Production Frontend Build
```bash
cd frontend
npm ci
npm run build
```
The compiled production bundle will reside in `frontend/dist/`.

### B. Production Backend Server (Systemd / Uvicorn)
Create a systemd unit `/etc/systemd/system/subwise-api.service`:

```ini
[Unit]
Description=PayPal SubWise AI API Server
After=network.target postgresql.service

[Service]
User=subwise
Group=subwise
WorkingDirectory=/opt/subwise/backend
EnvironmentFile=/opt/subwise/backend/.env
ExecStart=/opt/subwise/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4 --proxy-headers

Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable subwise-api
sudo systemctl start subwise-api
```

---

## 7. Reverse Proxy Configuration (Nginx)

Create `/etc/nginx/sites-available/subwise`:

```nginx
server {
    listen 80;
    server_name subwise.yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name subwise.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/subwise.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/subwise.yourdomain.com/privkey.pem;

    # Security Headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Backend API & Webhooks
    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000/api/v1/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # Frontend Single Page Application
    location / {
        root /opt/subwise/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 8. PayPal Webhook Configuration

1. Log in to the [PayPal Developer Dashboard](https://developer.paypal.com/).
2. Navigate to your REST App in **Sandbox** or **Live**.
3. Under **Webhooks**, click **Add Webhook**.
4. Set Webhook URL to: `https://subwise.yourdomain.com/api/v1/paypal/webhooks`
5. Subscribe to the following recommended events:
   - `Payment capture completed` (`PAYMENT.CAPTURE.COMPLETED`)
   - `Payment capture refunded` (`PAYMENT.CAPTURE.REFUNDED`)
   - `Payment capture reversed` (`PAYMENT.CAPTURE.REVERSED`)
   - `Billing subscription created / activated` (`BILLING.SUBSCRIPTION.ACTIVATED`)
   - `Billing subscription cancelled` (`BILLING.SUBSCRIPTION.CANCELLED`)
   - `Billing subscription suspended` (`BILLING.SUBSCRIPTION.SUSPENDED`)
   - `Customer dispute created / resolved` (`CUSTOMER.DISPUTE.*`)
6. Copy the generated **Webhook ID** and set it in your `.env` as `PAYPAL_WEBHOOK_ID`.

---

## 9. Security Hardening Checklist
- [x] **OWASP Formula Injection Defense:** CSV exports enforce prepending `'` to `=`, `+`, `-`, and `@` cells.
- [x] **Cryptographic Webhook Verification:** Real signatures validated against PayPal's `/v1/notifications/verify-webhook-signature`.
- [x] **Idempotency Assurance:** Webhook events deduplicated by `paypal_event_id`; identical payloads processed only once.
- [x] **Tenant Isolation:** All financial queries enforce `business_id` scoping; demo vs live environments strictly separated.
- [x] **Safe AI Assistant:** Deterministic financial fallback active when `GEMINI_API_KEY` is omitted; no credentials leaked in logs.

