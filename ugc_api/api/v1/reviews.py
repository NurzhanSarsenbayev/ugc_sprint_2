from uuid import UUID
from http import HTTPStatus
from fastapi import APIRouter, Depends, Path, Query, HTTPException

from ugc_api.dependencies import user_id_header, get_reviews_service
from ugc_api.services.reviews_service import ReviewsService
from ugc_api.models.reviews import (
    ReviewCreateRequest, ReviewCreateResponse,
    ReviewItem, ReviewListResponse,
    ReviewUpdateRequest, ReviewUpdateResponse,
    ReviewVoteRequest, ReviewVoteResponse,
)
from ugc_api.api.http_utils import handle_runtime_errors, not_found_if_none

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])

ERRMAP = {
    "review_not_found": HTTPStatus.NOT_FOUND,
    "review_not_found_or_not_author": HTTPStatus.NOT_FOUND,
}


@router.post("", response_model=ReviewCreateResponse,
             status_code=HTTPStatus.CREATED)
@handle_runtime_errors(ERRMAP)
async def create_review(
    body: ReviewCreateRequest,
    user_id: str = Depends(user_id_header),
    svc: ReviewsService = Depends(get_reviews_service),
):
    return await svc.create_review(user_id=user_id,
                                   data=body)


@router.get("/{review_id}", response_model=ReviewItem,
            status_code=HTTPStatus.OK)
@handle_runtime_errors(ERRMAP)
async def get_review(
    review_id: str = Path(..., description="Mongo ObjectId"),
    svc: ReviewsService = Depends(get_reviews_service),
):
    return not_found_if_none(await svc.get_review(review_id))


@router.get("/films/{film_id}",
            response_model=ReviewListResponse,
            status_code=HTTPStatus.OK)
@handle_runtime_errors(ERRMAP)
async def list_reviews_by_film(
    film_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    sort: str = Query("new", pattern="^(new|top)$"),
    svc: ReviewsService = Depends(get_reviews_service),
):
    return await svc.list_by_film(film_id=str(film_id),
                                  limit=limit,
                                  offset=offset,
                                  sort=sort)


@router.patch("/{review_id}",
              response_model=ReviewUpdateResponse,
              status_code=HTTPStatus.OK)
@handle_runtime_errors(ERRMAP)
async def update_review_text(
    review_id: str,
    body: ReviewUpdateRequest,
    user_id: str = Depends(user_id_header),
    svc: ReviewsService = Depends(get_reviews_service),
):
    ok = await svc.update_text(user_id=user_id,
                               review_id=review_id,
                               text=body.text)
    if not ok:
        # автор не совпал или не найдена рецензия
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="review_not_found_or_not_author")
    return ReviewUpdateResponse(ok=True)


@router.delete("/{review_id}",
               status_code=HTTPStatus.NO_CONTENT)
@handle_runtime_errors(ERRMAP)
async def delete_review(
    review_id: str,
    user_id: str = Depends(user_id_header),
    svc: ReviewsService = Depends(get_reviews_service),
):
    deleted = await svc.delete_review(user_id=user_id,
                                      review_id=review_id)
    if not deleted:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="review_not_found_or_not_author")
    return None


@router.post("/{review_id}/vote",
             response_model=ReviewVoteResponse,
             status_code=HTTPStatus.OK)
@handle_runtime_errors(ERRMAP)
async def vote_review(
    review_id: str,
    body: ReviewVoteRequest,
    user_id: str = Depends(user_id_header),
    svc: ReviewsService = Depends(get_reviews_service),
):
    return await svc.vote(user_id=user_id,
                          review_id=review_id,
                          value=body.value)


@router.delete("/{review_id}/vote",
               response_model=ReviewVoteResponse,
               status_code=HTTPStatus.OK)
@handle_runtime_errors(ERRMAP)
async def unvote_review(
    review_id: str,
    user_id: str = Depends(user_id_header),
    svc: ReviewsService = Depends(get_reviews_service),
):
    return await svc.unvote(user_id=user_id,
                            review_id=review_id)
