import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "PayPal SubWise AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
    
    # Security
    DEFAULT_DEV_SECRET: str = "subwise_ai_hackathon_super_secret_jwt_key_2026"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "subwise_ai_hackathon_super_secret_jwt_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    # CORS Configuration: Comma-separated list of allowed origins
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # Database Lifecycle Configuration
    AUTO_CREATE_TABLES: bool = True

    # PostgreSQL Configuration
    POSTGRES_USER: Optional[str] = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: Optional[str] = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_SERVER: Optional[str] = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: Optional[str] = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB: Optional[str] = os.getenv("POSTGRES_DB", "subwise_ai")
    
    # Target Database URL: Reads directly from DATABASE_URL if set,
    # or assembles from POSTGRES_* parameters.
    DATABASE_URL: Optional[str] = None
    
    # PayPal Configuration
    PAYPAL_MODE: str = "sandbox"           # 'sandbox' or 'live'
    PAYPAL_ENVIRONMENT: str = "sandbox"    # alias kept for compatibility
    PAYPAL_BASE_URL: str = "https://api-m.sandbox.paypal.com"
    PAYPAL_CLIENT_ID: Optional[str] = ""
    PAYPAL_CLIENT_SECRET: Optional[str] = ""
    PAYPAL_WEBHOOK_ID: Optional[str] = ""
    
    # AI / LLM Configuration
    GEMINI_API_KEY: Optional[str] = ""
    LLM_API_KEY: Optional[str] = ""

    class Config:
        env_file = ".env"
        extra = "allow"

    @property
    def cors_origins_list(self) -> list:
        default_dev = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
        raw = (self.CORS_ORIGINS or "").strip()
        if not raw:
            return default_dev

        configured = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]
        # In non-production environments, ensure localhost origins are also accepted
        if self.ENVIRONMENT not in ("production", "prod"):
            for dev_origin in default_dev:
                if dev_origin not in configured:
                    configured.append(dev_origin)
        return configured

    def model_post_init(self, __context):
        # Enforce production security constraints
        if self.ENVIRONMENT in ("production", "prod"):
            secret = (self.SECRET_KEY or "").strip()
            if not secret or secret == self.DEFAULT_DEV_SECRET:
                raise ValueError(
                    "Production Configuration Error: A dedicated, cryptographically strong SECRET_KEY "
                    "must be provided in production via environment variables. The default development "
                    "secret key cannot be used in production."
                )
            if len(secret) < 32:
                raise ValueError(
                    "Production Configuration Error: The production SECRET_KEY must be at least 32 characters long."
                )

        # Database auto-create tables: default to False in production (managed by Alembic), True in dev/test
        auto_create_env = os.getenv("AUTO_CREATE_TABLES")
        if auto_create_env is not None:
            self.AUTO_CREATE_TABLES = auto_create_env.lower() in ("true", "1", "yes")
        else:
            self.AUTO_CREATE_TABLES = self.ENVIRONMENT not in ("production", "prod")

        env_db_url = os.getenv("DATABASE_URL")
        if env_db_url:
            self.DATABASE_URL = env_db_url
        elif not self.DATABASE_URL:
            user = self.POSTGRES_USER or "postgres"
            password = self.POSTGRES_PASSWORD or "postgres"
            server = self.POSTGRES_SERVER or "localhost"
            port = self.POSTGRES_PORT or "5432"
            db = self.POSTGRES_DB or "subwise_ai"
            self.DATABASE_URL = f"postgresql://{user}:{password}@{server}:{port}/{db}"

        # Standardize postgres:// to postgresql:// (e.g. from Cloud PaaS providers)
        if self.DATABASE_URL and self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)

settings = Settings()
