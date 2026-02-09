import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ugc_api.api.v1.bookmarks import router as bookmarks_router
from ugc_api.api.v1.debug import include_debug_routes
from ugc_api.api.v1.film_stats import router as film_stats_router
from ugc_api.api.v1.likes import router as likes_router
from ugc_api.api.v1.ratings import router as ratings_router
from ugc_api.api.v1.ready_check import router as ready_check_router
from ugc_api.api.v1.reviews import router as reviews_router
from ugc_api.api.v1 import debug
from ugc_api.core.config import settings
from ugc_api.core.logger import setup_json_logging, shutdown_logging
from ugc_api.core.middleware import RequestContextMiddleware
from ugc_api.core.sentry import init_sentry
from ugc_api.db.mongo import get_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1) Logging must be initialized before anything else
    setup_json_logging(service=settings.app_name)
    init_sentry(settings.sentry_dsn, environment=settings.env)

    # 2) Initialize Motor client (lazy, but we warm up the connection)
    client = await get_client()
    # Optional: ping for early connectivity check
    # await client.admin.command("ping")

    try:
        yield
    finally:
        # Gracefully stop logging and close DB client
        client.close()
        shutdown_logging()


app = FastAPI(title="Engagement Service", lifespan=lifespan)

# Trace context + JSON access logs
app.add_middleware(RequestContextMiddleware)

# Silence uvicorn access logs to avoid duplicates (we emit our own access logs)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

include_debug_routes(app)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(ratings_router)
app.include_router(bookmarks_router)
app.include_router(reviews_router)
app.include_router(likes_router)
app.include_router(film_stats_router)
app.include_router(ready_check_router)
app.include_router(debug.router)