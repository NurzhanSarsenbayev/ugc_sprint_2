import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from ugc_api.core.trace import set_trace_id

alog = logging.getLogger("access")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        set_trace_id(str(uuid.uuid4()))
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            dur_ms = int((time.perf_counter() - start) * 1000)
            alog.info(
                "access",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "query": str(request.url.query)
                    if request.url.query else "",
                    "status": status if "status" in locals() else 500,
                    "latency_ms": dur_ms,
                    "client_ip": request.client.host
                    if request.client else None,
                },
            )
