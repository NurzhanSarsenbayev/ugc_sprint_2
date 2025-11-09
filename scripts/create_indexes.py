from pymongo import MongoClient, ASCENDING, DESCENDING
from ugc_api.core.config import settings


def main():
    db = MongoClient(settings.mongo_dsn)[settings.mongo_db]

    print("Using DSN:", settings.mongo_dsn, "DB:", settings.mongo_db)
    # ratings
    db["ratings"].create_index(
        [("user_id", ASCENDING), ("film_id", ASCENDING)],
        unique=True, name="ratings_user_film"
    )
    db["ratings"].create_index([("user_id", ASCENDING)],
                               name="ratings_user_id")
    db["ratings"].create_index([("film_id", ASCENDING)],
                               name="ratings_film_id")

    # reviews: сортировки по фильму (new/top)
    db["reviews"].create_index(
        [("film_id", ASCENDING), ("created_at", DESCENDING)],
        name="reviews_film_created_desc"
    )
    db["reviews"].create_index(
        [("film_id", ASCENDING),
         ("votes.up", DESCENDING),
         ("created_at", DESCENDING)],
        name="reviews_film_votes_up_desc"
    )
    # если нужна сортировка по down — делаем тоже составной,
    # а одиночный можно не создавать:
    db["reviews"].create_index(
        [("film_id", ASCENDING),
         ("votes.down", DESCENDING),
         ("created_at", DESCENDING)],
        name="reviews_film_votes_down_desc"
    )

    # review_votes
    db["review_votes"].create_index(
        [("review_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True, name="review_user"
    )

    # likes (исправлено имя коллекции!)
    db["likes"].create_index(
        [("user_id", ASCENDING),
         ("film_id", ASCENDING)],
        unique=True,
        name="likes_user_film"
    )
    db["likes"].create_index([("film_id", ASCENDING)], name="likes_film_id")

    # bookmarks
    db["bookmarks"].create_index(
        [("user_id", ASCENDING), ("film_id", ASCENDING)],
        unique=True, name="bookmarks_user_film"
    )
    db["bookmarks"].create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)],
        name="bookmarks_user_created_desc"
    )

    # film_stats
    db["film_stats"].create_index(
        [("film_id", ASCENDING)], unique=True, name="film_stats_film_id"
    )

    print("Indexes ensured.")


if __name__ == "__main__":
    main()
