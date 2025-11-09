from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from ugc_api.db.mongo import get_mongo_db
from ugc_api.services.ratings_service import RatingsService
from ugc_api.services.bookmarks_service import BookmarksService
from ugc_api.services.reviews_service import ReviewsService
from ugc_api.services.likes_service import LikesService
from ugc_api.services.film_stats_service import FilmStatsService


def user_id_header(x_user_id: str = Header(..., alias="X-User-Id")) -> str:
    try:
        return str(UUID(x_user_id))  # валидируем и нормализуем
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid X-User-Id")


async def get_db() -> AsyncIOMotorDatabase:
    # единая точка доступа к БД через твой singleton
    return await get_mongo_db()


async def get_film_stats_service(db=Depends(get_db)) -> FilmStatsService:
    return FilmStatsService(db)


async def get_ratings_service(
        db=Depends(get_db),
        stats: FilmStatsService = Depends(get_film_stats_service),
) -> RatingsService:
    return RatingsService(db, stats)


async def get_bookmarks_service(db=Depends(get_db)) -> BookmarksService:
    return BookmarksService(db)


async def get_reviews_service(
        db=Depends(get_db),
        stats: FilmStatsService = Depends(get_film_stats_service),
) -> ReviewsService:
    return ReviewsService(db, stats)


async def get_likes_service(
        db=Depends(get_db),
        stats: FilmStatsService = Depends(get_film_stats_service),
) -> LikesService:
    # теперь лайки знают про статы
    return LikesService(db, stats)
