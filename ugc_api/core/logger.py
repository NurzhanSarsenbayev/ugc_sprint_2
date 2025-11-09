import logging
import sys
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from pythonjsonlogger import jsonlogger
from ugc_api.core.trace import get_trace_id
from ugc_api.core.config import settings


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # гарантированно проставляем поля ДО записи в поток
        record.trace_id = (getattr(record, "trace_id", None)
                           or get_trace_id() or "-")
        record.service = getattr(record, "service", None) or settings.app_name
        record.env = getattr(record, "env", None) or settings.env
        return True


_listener: QueueListener | None = None


def setup_json_logging(service: str = "engagement_service") -> None:
    global _listener

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # добавили trace_id/service/env в формат
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s"
        " %(message)s %(pathname)s %(lineno)d "
        "%(trace_id)s %(service)s %(env)s"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    # ← фильтр на конечный обработчик (на всякий случай)
    stream_handler.addFilter(TraceContextFilter())

    q: Queue = Queue(-1)
    queue_handler = QueueHandler(q)
    # ← фильтр на очередь, чтобы обогатить record ДО помещения в очередь
    queue_handler.addFilter(TraceContextFilter())

    _listener = QueueListener(q, stream_handler, respect_handler_level=True)
    _listener.start()

    root.handlers = [queue_handler]
    # ← и на сам root (если где-то есть прямые хендлеры)
    root.addFilter(TraceContextFilter())

    for name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logging.getLogger(__name__).info(
        "logger_initialized",
        extra={"service": service})


def shutdown_logging() -> None:
    """Аккуратно остановить listener при выключении приложения."""
    global _listener
    if _listener:
        _listener.stop()
        _listener = None
