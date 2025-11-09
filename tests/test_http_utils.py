from http import HTTPStatus
import pytest
from ugc_api.api.http_utils import handle_runtime_errors, not_found_if_none
from fastapi import HTTPException


def test_not_found_if_none_raises_404_with_detail():
    with pytest.raises(HTTPException) as e:
        not_found_if_none(None, detail="x")
    assert e.value.status_code == HTTPStatus.NOT_FOUND
    assert e.value.detail == "x"


async def test_handle_runtime_errors_maps_known_message():
    @handle_runtime_errors({"boom": HTTPStatus.BAD_REQUEST})
    async def fn():
        raise RuntimeError("boom")
    with pytest.raises(HTTPException) as e:
        await fn()
    assert e.value.status_code == HTTPStatus.BAD_REQUEST
    assert e.value.detail == "boom"


async def test_handle_runtime_errors_maps_unknown_to_500():
    @handle_runtime_errors({"known": HTTPStatus.BAD_REQUEST})
    async def fn():
        raise RuntimeError("something else")
    with pytest.raises(HTTPException) as e:
        await fn()
    assert e.value.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
    assert e.value.detail == "internal_error"


async def test_handle_runtime_errors_happy_path_returns_value():
    @handle_runtime_errors({"x": HTTPStatus.BAD_REQUEST})
    async def ok():
        return "ok"
    assert await ok() == "ok"
