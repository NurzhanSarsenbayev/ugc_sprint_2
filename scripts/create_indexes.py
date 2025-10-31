from pymongo import ASCENDING, DESCENDING
from ugc_api.db.mongo import col

def main():
    col("ratings").create_index([("user_id", ASCENDING), ("film_id", ASCENDING)], unique=True)
    col("ratings").create_index([("user_id", ASCENDING)])
    col("ratings").create_index([("film_id", ASCENDING)])

    col("reviews").create_index([("film_id", ASCENDING), ("created_at", DESCENDING)])
    col("reviews").create_index([("film_id", ASCENDING), ("votes.up", DESCENDING)])

    col("review_votes").create_index([("review_id", ASCENDING), ("user_id", ASCENDING)], unique=True)

    col("bookmarks").create_index([("user_id", ASCENDING), ("film_id", ASCENDING)], unique=True)
    col("bookmarks").create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

    print("Indexes created.")

if __name__ == "__main__":
    main()
