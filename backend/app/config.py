import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "PayPal SubWise AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "subwise_ai_hackathon_super_secret_jwt_key_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
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

    def model_post_init(self, __context):
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
