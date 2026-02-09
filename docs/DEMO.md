# Demo

This demo shows the main UGC flows end-to-end (ratings, likes, bookmarks, reviews) and verifies that
**FilmStats aggregates are updated**.

## Prerequisites

- Docker + Docker Compose
- Make

## Run

```bash
cp infra/.env.sample infra/.env
make up
make ready
make demo
make down
```

## What the demo does

`make demo` will:

1. Generate random `user_id` and `film_id`
2. Put a rating (`score=8`)
3. Put a like (`value=+1`)
4. Fetch FilmStats and show that likes/ratings changed
5. Add a bookmark
6. Create a review
7. Upvote the review
8. Fetch FilmStats again and show the updated aggregates

## Expected output (example)

You should see something similar to:

* `PUT rating=8` returns JSON with `film_id` and `score`
* `PUT like=+1` returns `HTTP/1.1 204 No Content` (success without body)
* FilmStats after like shows `likes: 1`, `ratings_count: 1`
* Review creation prints `Review: <review_id>`
* Vote returns `{"ok": true, "applied": true}`
* Final FilmStats shows `reviews_count: 1`, `votes_up: 1`

If `make ready` returns `{"status":"ready"}` and `make demo` completes, the project is working correctly.
