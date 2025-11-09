from http import HTTPStatus
from fastapi import APIRouter
from ugc_api.core.config import settings

router = APIRouter(tags=["debug"])


@router.get("/__sentry-test", status_code=HTTPStatus.NO_CONTENT)
async def sentry_test():
    import sentry_sdk
    sentry_sdk.capture_message("✅ Sentry test ping from engagement_service")
    return None


def include_debug_routes(app):
    # Подключаем эндпоинт только если явно разрешён
    if str(settings.sentry_test_enabled).lower() in {"1", "true", "yes"}:
        app.include_router(router)
