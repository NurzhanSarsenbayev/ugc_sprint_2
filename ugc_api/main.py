import logging

from fastapi import FastAPI

from contextlib import asynccontextmanager
from ugc_api.db.mongo import get_client

from ugc_api.core.logger import setup_json_logging, shutdown_logging
from ugc_api.core.sentry import init_sentry
from ugc_api.core.config import settings
from ugc_api.core.middleware import RequestContextMiddleware

from ugc_api.api.v1.ratings import router as ratings_router
from ugc_api.api.v1.bookmarks import router as bookmarks_router
from ugc_api.api.v1.reviews import router as reviews_router
from ugc_api.api.v1.likes import router as likes_router
from ugc_api.api.v1.film_stats import router as film_stats_router
from ugc_api.api.v1.debug import include_debug_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) логи до всего
    setup_json_logging(service=settings.app_name)
    init_sentry(settings.sentry_dsn, environment=settings.env)

    # 2) инициализируем Motor-клиент (лениво, но прогреем коннект)
    client = await get_client()
    # опционально: ping для ранней проверки доступности
    # await client.admin.command("ping")

    try:
        yield
    finally:
        # корректно останавливаем лог-листенер
        client.close()
        shutdown_logging()


app = FastAPI(title="Engagement Service", lifespan=lifespan)

# наш trace_id + access JSON
app.add_middleware(RequestContextMiddleware)

# приглушим штатный uvicorn-access, чтобы не было дублей
logging.getLogger("uvicorn.access").setLevel("WARNING")

include_debug_routes(app)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(ratings_router)
app.include_router(bookmarks_router)
app.include_router(reviews_router)
app.include_router(likes_router)
app.include_router(film_stats_router)
