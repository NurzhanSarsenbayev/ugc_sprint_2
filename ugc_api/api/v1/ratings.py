from fastapi import APIRouter, Depends, Header
from ugc_api.models.ratings import RatingIn, FilmStatsOut
from ugc_api.services.ratings_service import upsert_rating
from ugc_api.db.mongo import col

router = APIRouter(prefix="/ratings", tags=["ratings"])

# заглушка аутентификации: берём user_id из заголовка
def get_user_id(x_user_id: str | None = Header(default=None)):
    return x_user_id or "demo-user"

@router.put("", response_model=FilmStatsOut)
def put_rating(payload: RatingIn, user_id: str = Depends(get_user_id)):
    doc = upsert_rating(user_id=user_id, film_id=payload.film_id, value=payload.value)
    return FilmStatsOut(film_id=payload.film_id, **{k: doc.get(k, 0) for k in ("likes_count","dislikes_count","avg_rating")})

@router.get("/films/{film_id}/stats", response_model=FilmStatsOut)
def get_film_stats(film_id: str):
    s = col("film_stats").find_one({"_id": film_id}) or {}
    return FilmStatsOut(film_id=film_id, likes_count=s.get("likes_count",0), dislikes_count=s.get("dislikes_count",0), avg_rating=s.get("avg_rating",0.0))
