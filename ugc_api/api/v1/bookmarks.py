from uuid import UUID
from http import HTTPStatus
from fastapi import APIRouter, Depends, Query

from ugc_api.dependencies import user_id_header, get_bookmarks_service
from ugc_api.services.bookmarks_service import BookmarksService
from ugc_api.models.bookmarks import (
    BookmarkPutResponse, BookmarkDeleteResponse, BookmarkListResponse
)

router = APIRouter(prefix="/api/v1/bookmarks", tags=["bookmarks"])


@router.put(
    "/{film_id}",
    response_model=BookmarkPutResponse,
    status_code=HTTPStatus.OK)
async def add_bookmark(
    film_id: UUID,
    user_id: str = Depends(user_id_header),
    svc: BookmarksService = Depends(get_bookmarks_service),
):
    return await svc.add_bookmark(user_id=user_id, film_id=str(film_id))


@router.delete(
    "/{film_id}",
    response_model=BookmarkDeleteResponse,
    status_code=HTTPStatus.OK)
async def remove_bookmark(
    film_id: UUID,
    user_id: str = Depends(user_id_header),
    svc: BookmarksService = Depends(get_bookmarks_service),
):
    return await svc.remove_bookmark(user_id=user_id, film_id=str(film_id))


@router.get(
    "",
    response_model=BookmarkListResponse,
    status_code=HTTPStatus.OK)
async def list_bookmarks(
    user_id: str = Depends(user_id_header),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    svc: BookmarksService = Depends(get_bookmarks_service),
):
    return await svc.list_bookmarks(
        user_id=user_id, limit=limit, offset=offset)
