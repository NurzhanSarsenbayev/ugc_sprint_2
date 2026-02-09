from functools import wraps
from http import HTTPStatus

from fastapi import HTTPException


def handle_runtime_errors(mapping: dict[str, HTTPStatus]):
    """
    Convert RuntimeError messages into HTTPException
    based on a provided mapping.

    Example:
        {"review_not_found": HTTPStatus.NOT_FOUND}
    """

    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
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


def not_found_if_none(value, detail: str = "review_not_found"):
    """Raise 404 if value is None."""
    if value is None:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=detail,
        )
    return value
