import logging
import sys
from logging.handlers import QueueHandler, QueueListener
from queue import Queue

from pythonjsonlogger import jsonlogger

from ugc_api.core.config import settings
from ugc_api.core.trace import get_trace_id


class TraceContextFilter(logging.Filter):
    """Inject trace/service/env fields into every log record."""

    def __init__(self, service: str | None = None) -> None:
        super().__init__()
        self._service = service

    def filter(self, record: logging.LogRecord) -> bool:
        # Ensure context fields exist before the record is emitted.
        record.trace_id = getattr(record, "trace_id", None) or get_trace_id() or "-"
        record.service = getattr(record, "service", None) or self._service or settings.app_name
        record.env = getattr(record, "env", None) or settings.env
        return True


_listener: QueueListener | None = None


def setup_json_logging(service: str = "engagement_service") -> None:
    """Configure JSON logging with a queue-based handler (non-blocking)."""
    global _listener

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(pathname)s %(lineno)d %(trace_id)s %(service)s %(env)s"
    )

    context_filter = TraceContextFilter(service=service)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    stream_handler.addFilter(context_filter)

    q: Queue = Queue(-1)
    queue_handler = QueueHandler(q)
    queue_handler.addFilter(context_filter)

    _listener = QueueListener(q, stream_handler, respect_handler_level=True)
    _listener.start()

    root.handlers = [queue_handler]
    root.addFilter(context_filter)

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logging.getLogger(__name__).info("logger_initialized")


def shutdown_logging() -> None:
    """Stop the log listener on application shutdown."""
    global _listener
    if _listener:
        _listener.stop()
        _listener = None
