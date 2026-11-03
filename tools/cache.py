
import json
import logging
import os
from functools import lru_cache

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 300


@lru_cache(maxsize=1)
def get_redis_client():
    """Create one reusable Redis client."""

    client = redis.Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )

    client.ping()
    return client


def cache_get(key: str):
    """Return cached data, or None on a miss/error."""

    try:
        raw = get_redis_client().get(key)

        if raw is None:
            logger.info("CACHE MISS: %s", key)
            return None

        logger.info("CACHE HIT: %s", key)
        return json.loads(raw)

    except (RedisError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("Cache read failed for %s: %s", key, exc)
        return None


def cache_set(key: str, value, ttl_seconds: int = DEFAULT_TTL_SECONDS):
    """Cache JSON-compatible data without changing numeric types."""

    if ttl_seconds <= 0:
        raise ValueError("ttl_seconds must be greater than zero")

    serialized = json.dumps(value, allow_nan=False)

    try:
        get_redis_client().set(key, serialized, ex=ttl_seconds)
        logger.info("CACHE SET: %s (TTL=%ss)", key, ttl_seconds)
        return True

    except RedisError as exc:
        logger.warning("Cache write failed for %s: %s", key, exc)
        return False


def get_or_fetch(
    key: str,
    fetch_function,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
):
    """
    Check cache first.
    On a miss, fetch once, then attempt to cache the result.
    """

    cached_value = cache_get(key)

    if cached_value is not None:
        return cached_value

    fresh_value = fetch_function()

    # Validate that the result can be safely represented as JSON.
    # This rejects NaN and infinity rather than caching invalid numbers.
    json.dumps(fresh_value, allow_nan=False)

    cache_set(key, fresh_value, ttl_seconds)

    return fresh_value
