from contextvars import ContextVar

_trace_id: ContextVar[str] = ContextVar("trace_id", default="-")


def get_trace_id() -> str:
    return _trace_id.get()


def set_trace_id(value: str) -> None:
    _trace_id.set(value)
