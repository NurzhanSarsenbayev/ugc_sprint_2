from datetime import datetime
from pymongo import ReturnDocument
from ugc_api.db.mongo import col

LIKE_THRESHOLD = 6
DISLIKE_THRESHOLD = 4

def upsert_rating(user_id: str, film_id: str, value: int):
    ratings = col("ratings")
    stats = col("film_stats")

    # найти старое значение
    old = ratings.find_one({"user_id": user_id, "film_id": film_id}, {"value": 1})

    # upsert оценки
    ratings.update_one(
        {"user_id": user_id, "film_id": film_id},
        {"$set": {"value": value, "updated_at": datetime.utcnow()}},
        upsert=True,
    )

    # инкрементальные корректировки статистики
    inc = {"ratings_sum": value, "ratings_cnt": 1}
    if value >= LIKE_THRESHOLD:
        inc["likes_count"] = 1
    if value <= DISLIKE_THRESHOLD:
        inc["dislikes_count"] = 1

    # если меняли оценку — откатить влияние старой
    if old is not None:
        old_val = old["value"]
        inc["ratings_sum"] -= old_val
        inc["ratings_cnt"] -= 1
        if old_val >= LIKE_THRESHOLD:
            inc["likes_count"] = inc.get("likes_count", 0) - 1
        if old_val <= DISLIKE_THRESHOLD:
            inc["dislikes_count"] = inc.get("dislikes_count", 0) - 1

    doc = stats.find_one_and_update(
        {"_id": film_id},
        {
            "$inc": inc,
            "$set": {"updated_at": datetime.utcnow()},
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    # безопасный пересчёт avg
    sum_ = doc.get("ratings_sum", 0)
    cnt_ = doc.get("ratings_cnt", 0)
    avg = float(sum_) / cnt_ if cnt_ > 0 else 0.0
    stats.update_one({"_id": film_id}, {"$set": {"avg_rating": avg}})
    return stats.find_one({"_id": film_id}, {"_id": 1, "likes_count": 1, "dislikes_count": 1, "avg_rating": 1})
