"""Service layer for managing user likes/dislikes on films."""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from ugc_api.services.film_stats_service import FilmStatsService
from ugc_api.services.repositories.likes_repo import LikesRepo


class LikesService:
    """Manage user's reaction state for a film: value ∈ {+1, -1} or None."""

    def __init__(
            self,
            db: AsyncIOMotorDatabase,
            stats: FilmStatsService) -> None:
        """Initialize service with database and film stats dependency."""
        self.repo = LikesRepo(db)
        self.stats = stats

    async def get_state(self, film_id: str, user_id: str) -> Optional[int]:
        """Return current reaction value (+1, -1, or None)."""
        return await self.repo.get(film_id, user_id)

    async def set_like(self, film_id: str, user_id: str, value: int):
        """Set like/dislike state and update film stats if changed."""
        assert value in (-1, 1)
        old = await self.repo.set(film_id, user_id, value)

        if old == value:
            # idempotent case: no aggregate changes needed
            return old, value

        like_delta = 0
        dislike_delta = 0

        if old == 1:
            like_delta -= 1
        if old == -1:
            dislike_delta -= 1
        if value == 1:
            like_delta += 1
        if value == -1:
            dislike_delta += 1

        await self.stats.apply_like_delta(
            film_id,
            like_delta=like_delta,
            dislike_delta=dislike_delta,
        )
        return old, value

    async def remove_like(self, film_id: str, user_id: str):
        """Remove user's reaction and update film stats accordingly."""
        old = await self.repo.delete(film_id, user_id)
        if old == 1:
            await self.stats.apply_like_delta(film_id, like_delta=-1)
        elif old == -1:
            await self.stats.apply_like_delta(film_id, dislike_delta=-1)
        return old
