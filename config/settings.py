from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration for the entire platform.
    All values loaded from .env file.
    Changing a value in .env changes behaviour across the whole app.
    """

    # ── App ────────────────────────────────────────────────────────
    app_name: str = "Indian Market Risk Platform"
    app_version: str = "1.0.0"
    app_env: str = "development"
    app_port: int = 8000

    # ── Database ───────────────────────────────────────────────────
    database_url: str = "postgresql://postgres:password@localhost:5432/quantrisk"

    # ── Redis ──────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600  # 1 hour default cache

    # ── Auth ───────────────────────────────────────────────────────
    jwt_secret_key: str = "your-super-secret-key-change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # ── Demo Credentials ───────────────────────────────────────────
    admin_username: str = "admin"
    admin_password: str = "quantrisk123"

    # ── Risk Engine Config ─────────────────────────────────────────
    var_confidence: float = 0.95
    rolling_window_days: int = 63
    risk_free_rate: float = 0.065  # RBI repo rate

    # ── Market Thresholds ──────────────────────────────────────────
    circuit_breaker_limit: float = 0.10
    vix_high_fear_threshold: float = 25.0
    vix_extreme_fear_threshold: float = 30.0

    # ── Rate Limiting ──────────────────────────────────────────────
    rate_limit_per_minute: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance.
    lru_cache means .env is only read once — not on every request.
    """
    return Settings()


# Convenience instance — import this directly in other files
settings = get_settings()