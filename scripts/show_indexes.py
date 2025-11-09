from pymongo import MongoClient
from ugc_api.core.config import settings


def dump(col_name: str):
    db = MongoClient(settings.mongo_dsn)[settings.mongo_db]
    idx = list(db[col_name].list_indexes())
    print(f"\nIndexes in '{col_name}':")
    for i in idx:
        print(" -", i)


if __name__ == "__main__":
    dump("bookmarks")
    dump("ratings")
    dump("reviews")
    dump("review_votes")
    dump("likes")
    dump("film_stats")
