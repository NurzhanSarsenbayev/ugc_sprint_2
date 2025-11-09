from pydantic import BaseModel
from typing import Optional


class RatingPutResponse(BaseModel):
    film_id: str
    score: int


class RatingGetResponse(BaseModel):
    film_id: str
    user_id: str
    score: Optional[int]  # None если нет оценки


class FilmStatsResponse(BaseModel):
    film_id: str
    avg_rating: Optional[float]
    likes: int
    dislikes: int
    count: int
