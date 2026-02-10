from collections.abc import Awaitable, Callable
from functools import wraps
from http import HTTPStatus
from typing import Any, TypeVar

from fastapi import HTTPException


def handle_runtime_errors(
    mapping: dict[str, HTTPStatus],
) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
    """
    Convert RuntimeError messages into HTTPException
    based on a provided mapping.

    Example:
        {"review_not_found": HTTPStatus.NOT_FOUND}
    """

    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await fn(*args, **kwargs)
            except RuntimeError as e:
                msg = str(e)
                for key, status in mapping.items():
                    if key in msg:
                        raise HTTPException(status_code=status, detail=key)
                # unknown error -> 500
                raise HTTPException(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    detail="internal_error",
                )

        return wrapper

    return decorator


T = TypeVar("T")


def not_found_if_none(value: T | None, detail: str = "review_not_found") -> T:
    """Raise 404 if value is None."""
    if value is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=detail,
        )
    return value
