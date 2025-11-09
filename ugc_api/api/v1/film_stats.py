from uuid import UUID
from http import HTTPStatus
from fastapi import APIRouter, Depends
from ugc_api.dependencies import get_film_stats_service
from ugc_api.models.film_stats import FilmStats
from ugc_api.services.film_stats_service import FilmStatsService

router = APIRouter(prefix="/api/v1/film-stats", tags=["film-stats"])


@router.get("/{film_id}", response_model=FilmStats, status_code=HTTPStatus.OK)
async def get_film_stats(
    film_id: UUID,
    svc: FilmStatsService = Depends(get_film_stats_service),
) -> FilmStats:
    doc = await svc.get_stats(str(film_id))
    return FilmStats(**doc)
