from uuid import UUID
from http import HTTPStatus
from fastapi import APIRouter, Depends, Query, Response

from ugc_api.dependencies import get_ratings_service, user_id_header
from ugc_api.services.ratings_service import RatingsService
from ugc_api.models.ratings import RatingGetResponse, RatingPutResponse

router = APIRouter(prefix="/api/v1/ratings", tags=["ratings"])


@router.put(
    "/{film_id}",
    response_model=RatingPutResponse,
    status_code=HTTPStatus.OK)
async def set_rating(
    film_id: UUID,
    score: int = Query(..., ge=1, le=10),
    user_id: str = Depends(user_id_header),
    svc: RatingsService = Depends(get_ratings_service),
):
    return await svc.put_rating(
        user_id=user_id,
        film_id=str(film_id),
        score=score)


@router.get(
    "/{film_id}",
    response_model=RatingGetResponse,
    status_code=HTTPStatus.OK)
async def get_rating(
    film_id: UUID,
    user_id: str = Depends(user_id_header),
    svc: RatingsService = Depends(get_ratings_service),
) -> RatingGetResponse:
    score = await svc.get_user_rating(user_id=user_id, film_id=str(film_id))
    return RatingGetResponse(
        film_id=str(film_id),
        user_id=user_id,
        score=score)


@router.delete("/{film_id}", status_code=HTTPStatus.NO_CONTENT)
async def delete_rating(
    film_id: UUID,
    user_id: str = Depends(user_id_header),
    svc: RatingsService = Depends(get_ratings_service),
) -> Response:
    await svc.delete_rating(user_id=user_id, film_id=str(film_id))
    return Response(status_code=HTTPStatus.NO_CONTENT)
