"""Service layer for film statistics aggregation and updates."""

from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from ugc_api.services.repositories.film_stats_repo import FilmStatsRepo


class FilmStatsService:
    """Manages film statistics for likes, ratings, and reviews."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        """Initialize repository."""
        self.repo = FilmStatsRepo(db)

    # ----- READ -----

    async def get_stats(self, film_id: str) -> dict:
        """Get or create a statistics document for a film."""
        doc = await self.repo.get_by_film_id(film_id)
        if doc is None:
            doc = await self.repo.ensure_doc(film_id)
        return doc

    # ----- LIKES -----

    async def apply_like_delta(
        self,
        film_id: str,
        like_delta: int = 0,
        dislike_delta: int = 0,
    ) -> dict:
        """Apply increment to likes/dislikes counters."""
        inc: dict[str, int] = {}
        if like_delta:
            inc['likes'] = like_delta
        if dislike_delta:
            inc['dislikes'] = dislike_delta
        return await self.repo.apply_inc_and_set(film_id, inc=inc)

    # ----- RATINGS -----

    async def apply_rating_set(
        self,
        film_id: str,
        old_rating: Optional[int],
        new_rating: Optional[int],
    ) -> dict:
        """Apply rating delta and recompute average rating."""
        inc: dict[str, int] = {}

        if old_rating is None and new_rating is not None:
            inc['ratings_count'] = 1
            inc['ratings_sum'] = new_rating
        elif old_rating is not None and new_rating is not None:
            inc['ratings_sum'] = new_rating - old_rating
        elif old_rating is not None and new_rating is None:
            inc['ratings_count'] = -1
            inc['ratings_sum'] = -old_rating
        else:
            return await self.repo.ensure_doc(film_id)

        updated = await self.repo.apply_inc_and_set(film_id, inc=inc)
        ratings_count = max(updated['ratings_count'], 0)
        ratings_sum = updated['ratings_sum']
        avg_rating = float(ratings_sum / ratings_count) \
            if ratings_count > 0 else 0.0

        return await self.repo.apply_inc_and_set(
            film_id,
            set_={'avg_rating': avg_rating},
        )

    # ----- REVIEWS COUNT -----

    async def apply_review_created(self, film_id: str) -> dict:
        """Increment reviews_count when a review is created."""
        return await self.repo.apply_inc_and_set(
            film_id,
            inc={'reviews_count': 1},
        )

    async def apply_review_deleted(self, film_id: str) -> dict:
        """Decrement reviews_count when a review is deleted."""
        return await self.repo.apply_inc_and_set(
            film_id,
            inc={'reviews_count': -1},
        )

    # ----- REVIEW VOTES -----

    async def apply_review_vote_change(
        self,
        film_id: str,
        old_vote: Optional[int],
        new_vote: Optional[int],
    ) -> dict:
        """Update votes_up and votes_down counters for review vote changes."""
        inc: dict[str, int] = {}

        def add(d: dict[str, int], key: str, value: int) -> None:
            """Helper for accumulating deltas in a dict."""
            d[key] = d.get(key, 0) + value

        if old_vote == new_vote:
            return await self.repo.ensure_doc(film_id)

        if old_vote == 1:
            add(inc, 'votes_up', -1)
        if old_vote == -1:
            add(inc, 'votes_down', -1)
        if new_vote == 1:
            add(inc, 'votes_up', 1)
        if new_vote == -1:
            add(inc, 'votes_down', 1)

        return await self.repo.apply_inc_and_set(film_id, inc=inc)
