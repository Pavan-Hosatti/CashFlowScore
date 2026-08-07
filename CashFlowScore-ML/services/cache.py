from __future__ import annotations

import json
import os
from time import monotonic

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    redis = None

redis_client = None
redis_url = os.getenv("REDIS_URL")
if redis is not None and redis_url:
    try:
        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
    except Exception:
        redis_client = None

CACHE_TTL = 300

_memory_cache = {}


def get_cache(key):
    print("Checking cache:", key)

    if redis_client is not None:
        value = redis_client.get(key)
        print("Cache value:", value)
        if value:
            return json.loads(value)

    entry = _memory_cache.get(key)
    if entry is None:
        return None

    expires_at, value = entry
    if expires_at < monotonic():
        _memory_cache.pop(key, None)
        return None

    # Ensure value is returned properly without printing un-encodable characters
    return value

    return value


def set_cache(key, value):
    print("Saving cache:", key)

    if redis_client is not None:
        redis_client.setex(key, CACHE_TTL, json.dumps(value))

    _memory_cache[key] = (monotonic() + CACHE_TTL, value)