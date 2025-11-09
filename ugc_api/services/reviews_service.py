"""Reviews service: CRUD + voting with optional film stats updates."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List, Optional

from pymongo.errors import PyMongoError

from ugc_api.models.reviews import (
    ReviewCreateRequest,
    ReviewCreateResponse,
    ReviewItem,
    ReviewListResponse,
    ReviewVoteResponse,
    VoteValue,
)
from ugc_api.services.film_stats_service import FilmStatsService
from ugc_api.services.repositories.review_votes_repo import ReviewVotesRepo
from ugc_api.services.repositories.reviews_repo import ReviewsRepo

# Reused string literals to satisfy WPS226:
VOTES_KEY = 'votes'
UP = 'up'
DOWN = 'down'


class ReviewsService:  # noqa: WPS214 (methods count)
    """Business-logic for reviews (CRUD + voting).

    Optionally updates film stats if the `stats` dependency is provided.
    """

    def __init__(self, db, stats: Optional[FilmStatsService] = None) -> None:
        """Initialize service with db adapter
         and optional film stats service."""
        self.repo = ReviewsRepo(db)
        self.votes_repo = ReviewVotesRepo(db)
        self.stats = stats

    # ---------- helpers ----------

    @asynccontextmanager
    async def _txn(self):
        """Open mongo session + transaction and yield session."""
        async with await self.repo.client.start_session() as session:
            async with session.start_transaction():
                yield session

    @staticmethod
    def _vote_delta(
            old: Optional[str],
            new: Optional[str]
    ) -> tuple[Optional[int], Optional[int]]:
        """Map old/new vote ('up'/'down'/None)
         into numeric deltas (old, new)."""
        def map_vote(val: Optional[str]) -> Optional[int]:
            if val == UP:
                return 1
            if val == DOWN:
                return -1
            return None

        return (map_vote(old), map_vote(new))

    # ---------- CREATE ----------

    async def create_review(
            self,
            user_id: str,
            data: ReviewCreateRequest) -> ReviewCreateResponse:
        """Create new review and update film stats (optional)."""
        try:
            review_id = await self.repo.insert(
                film_id=data.film_id,
                user_id=user_id,
                text=data.text,
            )
            if self.stats:
                await self.stats.apply_review_created(data.film_id)
            return ReviewCreateResponse(review_id=review_id)
        except PyMongoError as error:
            raise RuntimeError(
                f'mongo_review_create_error: {error}'
            ) from error

    # ---------- GET ONE ----------

    async def get_review(self, review_id: str) -> Optional[ReviewItem]:
        """Get single review by id."""
        try:
            doc = await self.repo.get_by_id(review_id)
            if not doc:
                return None
            return ReviewItem(
                review_id=str(doc['_id']),
                film_id=doc['film_id'],
                user_id=doc['user_id'],
                text=doc['text'],
                up=int(doc.get(VOTES_KEY, {}).get(UP, 0)),
                down=int(doc.get(VOTES_KEY, {}).get(DOWN, 0)),
                created_at=doc['created_at'],
            )
        except PyMongoError as error:
            raise RuntimeError(f'mongo_review_get_error: {error}') from error

    # ---------- LIST ----------

    async def list_by_film(
        self,
        film_id: str,
        limit: int = 20,
        offset: int = 0,
        sort: str = 'new',
    ) -> ReviewListResponse:
        """List reviews for a film with pagination and sorting."""
        try:
            docs = await self.repo.list_by_film(
                film_id,
                limit,
                offset,
                sort=sort,
            )
            items: List[ReviewItem] = [
                ReviewItem(
                    review_id=str(doc['_id']),
                    film_id=doc['film_id'],
                    user_id=doc['user_id'],
                    text=doc['text'],
                    up=int(doc.get(VOTES_KEY, {}).get(UP, 0)),
                    down=int(doc.get(VOTES_KEY, {}).get(DOWN, 0)),
                    created_at=doc['created_at'],
                )
                for doc in docs
            ]
            total = await self.repo.count_by_film(film_id)
            return ReviewListResponse(items=items, total=total)
        except PyMongoError as error:
            raise RuntimeError(f'mongo_review_list_error: {error}') from error

    # ---------- UPDATE (EDIT) ----------

    async def update_text(
            self,
            user_id: str,
            review_id: str,
            text: str) -> bool:
        """Edit review text by author."""
        try:
            return await self.repo.update_text(user_id, review_id, text)
        except PyMongoError as error:
            raise RuntimeError(
                f'mongo_review_update_error: {error}'
            ) from error

    # ---------- DELETE ----------

    async def delete_review(self, user_id: str, review_id: str) -> bool:
        """Delete review with cascade votes removal and stats update."""
        try:
            async with self._txn() as session:
                # 1) delete all votes of the review
                await self.votes_repo.delete_many_by_review(
                    review_id, session=session)
                # 2) delete review and get its film_id
                deleted = await self.repo.delete_and_return(
                    user_id,
                    review_id,
                    session=session,
                )
                if not deleted:
                    return False

                film_id = deleted['film_id']
                # 3) update aggregates
                if self.stats:
                    await self.stats.apply_review_deleted(film_id)
                return True
        except PyMongoError as error:
            raise RuntimeError(
                f'mongo_review_delete_error: {error}'
            ) from error

    # ---------- VOTE (UP/DOWN) ----------

    async def vote(
            self,
            user_id: str,
            review_id: str,
            value: VoteValue) -> ReviewVoteResponse:
        """Apply vote (up/down) for a review;
         updates counters and film stats."""
        try:
            async with self._txn() as session:
                old_vote = await self.votes_repo.get_user_vote(
                    review_id,
                    user_id,
                    session=session,
                )
                new_vote = value.value  # 'up' | 'down'

                if old_vote == new_vote:
                    return ReviewVoteResponse(ok=True, applied=False)

                # 1) update counters on review
                updated = await self.repo.apply_vote_delta(
                    review_id,
                    old_vote=old_vote,
                    new_vote=new_vote,
                    session=session,
                )
                if not updated:
                    raise RuntimeError('review_not_found')

                # 2) upsert user vote
                await self.votes_repo.upsert_vote(
                    review_id,
                    user_id,
                    new_vote,
                    session=session,
                )

                # 3) update film stats
                if self.stats:
                    film_id = await self.repo.get_film_id(
                        review_id,
                        session=session,
                    )
                    old_delta, new_delta = self._vote_delta(old_vote, new_vote)
                    if film_id:
                        await self.stats.apply_review_vote_change(
                            film_id,
                            old_delta,
                            new_delta,
                        )

                return ReviewVoteResponse(ok=True, applied=True)
        except PyMongoError as error:
            raise RuntimeError(f'mongo_review_vote_error: {error}') from error

    # ---------- UNVOTE ----------

    async def unvote(
            self, user_id: str, review_id: str) -> ReviewVoteResponse:
        """Remove user's vote from a review;
         updates counters and film stats."""
        try:
            async with self._txn() as session:
                old_vote = await self.votes_repo.get_user_vote(
                    review_id,
                    user_id,
                    session=session,
                )
                if not old_vote:
                    return ReviewVoteResponse(ok=True, applied=False)

                # 1) decrement counters on review
                updated = await self.repo.apply_vote_delta(
                    review_id,
                    old_vote=old_vote,
                    new_vote=None,
                    session=session,
                )
                if not updated:
                    raise RuntimeError('review_not_found')

                # 2) delete user vote
                await self.votes_repo.delete_vote(
                    review_id,
                    user_id,
                    session=session,
                )

                # 3) update film stats
                if self.stats:
                    film_id = await self.repo.get_film_id(
                        review_id,
                        session=session,
                    )
                    old_delta, _ = self._vote_delta(old_vote, None)
                    if film_id:
                        await self.stats.apply_review_vote_change(
                            film_id,
                            old_delta,
                            None,
                        )

                return ReviewVoteResponse(ok=True, applied=True)
        except PyMongoError as error:
            raise RuntimeError(
                f'mongo_review_unvote_error: {error}'
            ) from error
