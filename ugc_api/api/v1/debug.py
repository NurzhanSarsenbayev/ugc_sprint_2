from http import HTTPStatus
from typing import Any

from fastapi import APIRouter, FastAPI

from ugc_api.core.config import settings
from ugc_api.db.redis import cache_get_json

router = APIRouter(tags=["debug"])


@router.get("/__sentry-test", status_code=HTTPStatus.NO_CONTENT)
async def sentry_test() -> None:
    import sentry_sdk

    sentry_sdk.capture_message("Sentry test ping from engagement_service")
    return None


def include_debug_routes(app: FastAPI) -> None:
    # Enable the endpoint only when explicitly allowed
    if str(settings.sentry_test_enabled).lower() in {"1", "true", "yes"}:
        app.include_router(router)


@router.get("/debug/cache/filmstats/{film_id}")
async def debug_filmstats_cache(film_id: str) -> dict[str, Any]:
    key = f"filmstats:{film_id}"
    v = await cache_get_json(key)
    return {"key": key, "exists": v is not None}
