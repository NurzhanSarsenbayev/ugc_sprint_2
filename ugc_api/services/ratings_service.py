"""Service layer for ratings CRUD and film stats integration."""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from ugc_api.models.ratings import FilmStatsResponse, RatingPutResponse
from ugc_api.services.film_stats_service import FilmStatsService
from .repositories.ratings_repo import RatingsRepo


class RatingsService:
    """Business logic for ratings with optional film stats updates."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        stats: FilmStatsService | None = None,
    ) -> None:
        """Init with DB adapter and optional stats service."""
        self.repo = RatingsRepo(db)
        self.stats = stats  # may be None

    # ---------- CREATE / UPDATE ----------

    async def put_rating(
        self,
        user_id: str,
        film_id: str,
        score: int,
    ) -> RatingPutResponse:
        """Upsert rating and update film stats if configured."""
        old_doc = await self.repo.find_user_film(
            user_id=user_id,
            film_id=film_id,
        )
        old_score: Optional[int] = (
            int(old_doc['score']) if old_doc and 'score' in old_doc else None
        )

        doc = await self.repo.upsert(
            user_id=user_id,
            film_id=film_id,
            score=score,
        )

        if self.stats is not None:
            await self.stats.apply_rating_set(
                film_id=film_id,
                old_rating=old_score,
                new_rating=int(score),
            )

        return RatingPutResponse(
            film_id=film_id,
            score=int(doc['score']),
        )

    # ---------- READ ----------

    async def get_user_rating(
        self,
        user_id: str,
        film_id: str,
    ) -> Optional[int]:
        """Return user score for a film (or None)."""
        doc = await self.repo.find_user_film(
            user_id=user_id,
            film_id=film_id,
        )
        return int(doc['score']) if doc and 'score' in doc else None

    # ---------- DELETE ----------

    async def delete_rating(
        self,
        user_id: str,
        film_id: str,
    ) -> None:
        """Delete rating and update film stats if needed."""
        old_doc = await self.repo.find_user_film(
            user_id=user_id,
            film_id=film_id,
        )
        old_score: Optional[int] = (
            int(old_doc['score']) if old_doc and 'score' in old_doc else None
        )

        await self.repo.delete(
            user_id=user_id,
            film_id=film_id,
        )

        if old_score is not None and self.stats is not None:
            await self.stats.apply_rating_set(
                film_id=film_id,
                old_rating=old_score,
                new_rating=None,
            )

    # ---------- STATS ----------

    async def film_stats(self, film_id: str) -> FilmStatsResponse:
        """Get film stats (prefer cached stats service,
         fallback to on-the-fly)."""
        if self.stats is not None:
            doc = await self.stats.get_stats(film_id)
            return FilmStatsResponse(**doc)

        agg = await self.repo.film_aggregate(film_id=film_id)
        return FilmStatsResponse(**agg)
