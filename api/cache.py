import redis
import json
from config.settings import settings
from api.logger import logger


def get_redis_client():
    """Create Redis client from settings."""
    return redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )


def check_cache_connection() -> bool:
    """Health check — verify Redis is reachable."""
    try:
        client = get_redis_client()
        client.ping()
        return True
    except Exception:
        return False


def cache_get(key: str) -> dict | None:
    """
    Retrieve cached value by key.
    Returns None if key doesn't exist or Redis is down.
    """
    try:
        client = get_redis_client()
        value = client.get(key)
        if value:
            logger.info("Cache hit", extra={"key": key})
            return json.loads(value)
        logger.info("Cache miss", extra={"key": key})
        return None
    except Exception as e:
        logger.warning("Cache get failed", extra={
            "key": key, "error": str(e)
        })
        return None


def cache_set(key: str, value: dict, ttl: int = None) -> bool:
    """
    Store value in cache with TTL.
    Fails silently — cache is optional, not critical.
    """
    try:
        client = get_redis_client()
        ttl = ttl or settings.cache_ttl_seconds
        client.setex(key, ttl, json.dumps(value, default=str))
        logger.info("Cache set", extra={"key": key, "ttl": ttl})
        return True
    except Exception as e:
        logger.warning("Cache set failed", extra={
            "key": key, "error": str(e)
        })
        return False


def cache_delete(key: str) -> bool:
    """Invalidate a cache entry."""
    try:
        client = get_redis_client()
        client.delete(key)
        return True
    except Exception:
        return False


def make_cache_key(*parts) -> str:
    """
    Build a consistent cache key from parts.
    Example: make_cache_key("risk", "RELIANCE.NS", "1y") 
    → "risk:RELIANCE.NS:1y"
    """
    return ":".join(str(p) for p in parts)