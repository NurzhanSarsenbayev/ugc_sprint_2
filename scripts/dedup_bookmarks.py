from pymongo import MongoClient, DESCENDING
from ugc_api.core.config import settings


def main():
    db = MongoClient(settings.mongo_dsn)[settings.mongo_db]
    col = db["bookmarks"]

    # Находим ключи с >1 документом
    pipeline = [
        {"$group": {"_id": {"user_id": "$user_id",
                            "film_id": "$film_id"}, "count": {"$sum": 1}}},
        {"$match": {"count": {"$gt": 1}}}
    ]
    dups = list(col.aggregate(pipeline))
    print(f"Duplicate keys: {len(dups)}")

    # Для каждого ключа оставляем самый новый, остальные удаляем
    for d in dups:
        key = d["_id"]
        docs = list(col.find(key).sort("created_at", DESCENDING))
        keep_id = docs[0]["_id"]
        to_delete = [x["_id"] for x in docs[1:]]
        if to_delete:
            col.delete_many({"_id": {"$in": to_delete}})
            print(f"  kept={keep_id}, deleted={len(to_delete)} for {key}")

    print("Dedup done.")


if __name__ == "__main__":
    main()
