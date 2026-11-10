import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
from app.api import auth, business, transactions, subscriptions, simulation, recommendations, paypal, forecast, financial_intelligence, reports, assistant, demo, expenses, household, budgets, savings_discovery

# Create DB tables
Base.metadata.create_all(bind=engine)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("subwise_ai")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PayPal SubWise AI: Intelligent Subscription Management & Cash-Flow Scenario Simulator for SMBs."
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(business.router, prefix=settings.API_V1_STR)
app.include_router(paypal.router, prefix=settings.API_V1_STR)
app.include_router(transactions.router, prefix=settings.API_V1_STR)
app.include_router(subscriptions.router, prefix=settings.API_V1_STR)
app.include_router(simulation.router, prefix=settings.API_V1_STR)
app.include_router(recommendations.router, prefix=settings.API_V1_STR)
app.include_router(forecast.router, prefix=settings.API_V1_STR)
app.include_router(financial_intelligence.router, prefix=settings.API_V1_STR)
app.include_router(reports.router, prefix=settings.API_V1_STR)
app.include_router(assistant.router, prefix=settings.API_V1_STR)
app.include_router(demo.router, prefix=settings.API_V1_STR)
app.include_router(expenses.router, prefix=settings.API_V1_STR)
app.include_router(household.router, prefix=settings.API_V1_STR)
app.include_router(budgets.router, prefix=settings.API_V1_STR)
app.include_router(savings_discovery.router, prefix=settings.API_V1_STR)

# Health Check Endpoint
@app.get(f"{settings.API_V1_STR}/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected"
    }

# Serve built frontend SPA if available
import os
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="static-assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str, request: Request):
        # API paths must NOT be intercepted by the SPA catch-all.
        # Returning None here caused FastAPI to serialize it as JSON null,
        # which made /api/v1/paypal/status and similar endpoints appear to
        # return null in the browser. Raise 404 instead so the real API
        # route error (e.g. 401 Unauthorized) is surfaced correctly.
        if (
            full_path.startswith("api/")
            or full_path == "api"
            or full_path in ("docs", "openapi.json", "redoc")
        ):
            raise HTTPException(
                status_code=404,
                detail=f"API route /{full_path} not found or requires authentication."
            )
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "app": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "status": "operational",
            "docs": "/docs",
            "health": f"{settings.API_V1_STR}/health"
        }
