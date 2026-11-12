"""
Test suite for Deployment Readiness:
- Production JWT SECRET_KEY enforcement
- CORS origin parsing and configuration
- Database lifecycle (AUTO_CREATE_TABLES) controls
"""
import os
import pytest
from app.config import Settings


def test_production_jwt_secret_fails_on_default_dev_secret(monkeypatch):
    """Production mode must fail safely if the default development JWT secret is used."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "subwise_ai_hackathon_super_secret_jwt_key_2026")

    with pytest.raises(ValueError) as excinfo:
        Settings()
    assert "Production Configuration Error" in str(excinfo.value)
    assert "SECRET_KEY" in str(excinfo.value)
    # Ensure secret value is never leaked in the error message
    assert "subwise_ai_hackathon_super_secret_jwt_key_2026" not in str(excinfo.value)


def test_production_jwt_secret_fails_on_short_secret(monkeypatch):
    """Production mode must fail safely if the secret is shorter than 32 characters."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "short_secret_12345")

    with pytest.raises(ValueError) as excinfo:
        Settings()
    err_msg = str(excinfo.value)
    assert "Production Configuration Error" in err_msg
    assert "at least 32 characters" in err_msg
    # Ensure our validation message itself does not echo the secret
    first_error_msg = excinfo.value.errors()[0]["msg"] if hasattr(excinfo.value, "errors") else str(excinfo.value)
    assert "short_secret_12345" not in first_error_msg


def test_production_jwt_secret_succeeds_with_strong_secret(monkeypatch):
    """Production mode must succeed when a strong secret (>= 32 chars) is provided."""
    strong_key = "a_very_secure_and_cryptographically_strong_key_for_production_2026!"
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", strong_key)

    cfg = Settings()
    assert cfg.ENVIRONMENT == "production"
    assert cfg.SECRET_KEY == strong_key


def test_development_jwt_secret_succeeds_with_default(monkeypatch):
    """Development mode allows default development secret for ease of local testing."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    cfg = Settings()
    assert cfg.ENVIRONMENT == "development"
    assert cfg.SECRET_KEY == cfg.DEFAULT_DEV_SECRET


def test_cors_origins_default_dev(monkeypatch):
    """When CORS_ORIGINS is unset in development, standard localhost ports are allowed."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    cfg = Settings()
    origins = cfg.cors_origins_list
    assert "http://localhost:3000" in origins
    assert "http://127.0.0.1:3000" in origins
    assert "*" not in origins


def test_cors_origins_custom_configured(monkeypatch):
    """CORS_ORIGINS parses comma-separated cloud domains accurately and strips trailing slashes."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "a_very_secure_and_cryptographically_strong_key_for_production_2026!")
    monkeypatch.setenv("CORS_ORIGINS", "https://subwise.vercel.app/, https://subwise-demo.vercel.app")

    cfg = Settings()
    origins = cfg.cors_origins_list
    assert origins == ["https://subwise.vercel.app", "https://subwise-demo.vercel.app"]
    assert "*" not in origins


def test_auto_create_tables_defaults(monkeypatch):
    """AUTO_CREATE_TABLES defaults to True in development and False in production."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("AUTO_CREATE_TABLES", raising=False)
    cfg_dev = Settings()
    assert cfg_dev.AUTO_CREATE_TABLES is True

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "a_very_secure_and_cryptographically_strong_key_for_production_2026!")
    monkeypatch.delenv("AUTO_CREATE_TABLES", raising=False)
    cfg_prod = Settings()
    assert cfg_prod.AUTO_CREATE_TABLES is False


def test_auto_create_tables_explicit_override(monkeypatch):
    """AUTO_CREATE_TABLES respects explicit override regardless of environment."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "a_very_secure_and_cryptographically_strong_key_for_production_2026!")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "true")
    cfg = Settings()
    assert cfg.AUTO_CREATE_TABLES is True


def test_cors_origins_production_isolation(monkeypatch):
    """In production mode, only explicitly specified origins are permitted; no implicit dev origins."""
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("SECRET_KEY", "a_very_secure_and_cryptographically_strong_key_for_production_2026!")
    monkeypatch.setenv("CORS_ORIGINS", "https://subwise.vercel.app")

    cfg = Settings()
    origins = cfg.cors_origins_list
    assert origins == ["https://subwise.vercel.app"]
    assert "http://localhost:3000" not in origins
    assert "*" not in origins


def test_cors_origins_development_includes_both(monkeypatch):
    """In development mode, custom origins retain localhost origins for seamless local DX."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("CORS_ORIGINS", "https://staging.subwise.app")

    cfg = Settings()
    origins = cfg.cors_origins_list
    assert "https://staging.subwise.app" in origins
    assert "http://localhost:3000" in origins
    assert "*" not in origins
