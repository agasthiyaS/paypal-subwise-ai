import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

logger = logging.getLogger("subwise_ai.database")

# Detect database dialect from connection URL
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite configuration (for isolated in-memory or file test suites)
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True
    )
else:
    # Enterprise PostgreSQL connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,       # Health check probe before issuing query
        pool_recycle=3600,        # Reconnect periodically to prevent stale drops
        pool_timeout=30           # Max wait time for pool connection checkout
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency yielding a scoped database session with guaranteed cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
