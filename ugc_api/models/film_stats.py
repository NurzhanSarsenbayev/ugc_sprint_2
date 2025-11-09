from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class FilmStats(BaseModel):
    film_id: str
    likes: int = 0
    dislikes: int = 0

    ratings_count: int = 0
    ratings_sum: int = 0
    avg_rating: float = 0.0

    reviews_count: int = 0
    votes_up: int = 0
    votes_down: int = 0

    updated_at: datetime
