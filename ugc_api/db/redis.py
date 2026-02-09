import json
import logging
from typing import Any
from datetime import datetime, date
from bson import ObjectId

from redis.asyncio import Redis

from ugc_api.core.config import settings

log = logging.getLogger(__name__)

_client: Redis | None = None

def _json_default(obj: object):
    if isinstance(obj, (datetime, date)):
        # ISO 8601, как в API
        s = obj.isoformat()
        return s.replace("+00:00", "Z")
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

def _client_instance() -> Redis:
    global _client
    if _client is None:
        _client = Redis.from_url(settings.redis_dsn, decode_responses=True)
    return _client


async def cache_get_json(key: str) -> dict[str, Any] | None:
    try:
        raw = await _client_instance().get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        log.exception("Redis GET failed (key=%s)", key)
        return None


async def cache_set_json(key: str, value: dict[str, Any], ttl: int) -> None:
    try:
        raw = json.dumps(value, ensure_ascii=False, default=_json_default)
        await _client_instance().set(key, raw, ex=ttl)
    except Exception:
        log.exception("Redis SET failed (key=%s)", key)


async def cache_del(key: str) -> None:
    try:
        await _client_instance().delete(key)
    except Exception:
        log.exception("Redis DEL failed (key=%s)", key)
