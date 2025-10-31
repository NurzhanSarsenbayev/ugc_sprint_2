from fastapi import FastAPI, Request
import time
from ugc_api.core.config import settings
from ugc_api.core.logger import setup_json_logging
from ugc_api.core.sentry import setup_sentry
from ugc_api.api.v1.ratings import router as ratings_router

app = FastAPI(title="Engagement API")

setup_json_logging(service=settings.app_name)
setup_sentry(dsn=settings.sentry_dsn, environment=settings.env)

@app.middleware("http")
async def add_logging(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    dur_ms = (time.perf_counter() - start) * 1000
    # простой access-log
    import logging
    logging.info(
        "request",
        extra={"method": request.method, "path": request.url.path, "status": response.status_code, "latency_ms": round(dur_ms, 2)},
    )
    return response

@app.get("/health")
def health():
    return {"status":"ok"}

app.include_router(ratings_router)
