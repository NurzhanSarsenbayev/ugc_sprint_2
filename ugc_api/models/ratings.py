from pydantic import BaseModel, Field, conint

class RatingIn(BaseModel):
    film_id: str
    value: conint(ge=0, le=10)

class FilmStatsOut(BaseModel):
    film_id: str
    likes_count: int = 0
    dislikes_count: int = 0
    avg_rating: float = 0.0
