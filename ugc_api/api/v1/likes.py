from uuid import UUID
from http import HTTPStatus
from fastapi import APIRouter, Depends, Response
from ugc_api.dependencies import get_likes_service, user_id_header
from ugc_api.models.likes import LikeSetRequest, LikeStateResponse
from ugc_api.services.likes_service import LikesService

router = APIRouter(prefix="/api/v1/likes", tags=["likes"])


@router.get(
    "/{film_id}",
    response_model=LikeStateResponse,
    status_code=HTTPStatus.OK)
async def get_like_state(
    film_id: UUID,
    user_id: str = Depends(user_id_header),
    svc: LikesService = Depends(get_likes_service),
) -> LikeStateResponse:
    val = await svc.get_state(str(film_id), user_id)
    return LikeStateResponse(film_id=str(film_id), user_id=user_id, value=val)


@router.put("/{film_id}", status_code=HTTPStatus.NO_CONTENT)
async def put_like(
    film_id: UUID,
    body: LikeSetRequest,
    user_id: str = Depends(user_id_header),
    svc: LikesService = Depends(get_likes_service),
) -> Response:
    await svc.set_like(str(film_id), user_id, body.value)
    return Response(status_code=HTTPStatus.NO_CONTENT)


@router.delete("/{film_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_like(
    film_id: UUID,
    user_id: str = Depends(user_id_header),
    svc: LikesService = Depends(get_likes_service),
) -> Response:
    await svc.remove_like(str(film_id), user_id)
    return Response(status_code=HTTPStatus.NO_CONTENT)
