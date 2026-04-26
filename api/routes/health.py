from fastapi import APIRouter
from api.models import check_db_connection
from api.cache import check_cache_connection
from config.settings import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
def health_check():
    """
    Basic health check — always public, never protected.
    Cloud platforms (Render, Railway) ping this to verify app is alive.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get("/db")
def database_health():
    """Check PostgreSQL connectivity."""
    connected = check_db_connection()
    return {
        "status": "healthy" if connected else "unhealthy",
        "database": "postgresql",
        "connected": connected,
    }


@router.get("/cache")
def cache_health():
    """Check Redis connectivity."""
    connected = check_cache_connection()
    return {
        "status": "healthy" if connected else "unhealthy",
        "cache": "redis",
        "connected": connected,
    }


@router.get("/full")
def full_health():
    """
    Complete system health — checks all services at once.
    Used by monitoring tools and deployment pipelines.
    """
    db_ok = check_db_connection()
    cache_ok = check_cache_connection()

    overall = "healthy" if db_ok and cache_ok else "degraded"

    return {
        "status": overall,
        "app": settings.app_name,
        "version": settings.app_version,
        "services": {
            "api": True,
            "database": db_ok,
            "cache": cache_ok,
        }
    }