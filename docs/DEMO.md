# UGC Service — Demo

This demo walks through the main UGC flows end-to-end and verifies:

- Ratings
- Likes
- Bookmarks
- Reviews + voting
- FilmStats aggregation
- Redis caching with TTL

The goal is to show that:
- Aggregates are updated correctly
- Cache is invalidated on writes
- The service is fully reproducible locally

---

## Prerequisites

- Docker
- Docker Compose
- Make

---

## 1. Start the stack

```bash
cp infra/.env.sample infra/.env
make up
````

Wait until containers become healthy.

Check readiness:

```bash
make ready
```

Expected:

```json
{"status":"ready"}
```

---

## 2. Run full UGC flow

```bash
make demo
```

This command performs:

1. Generate random `user_id` and `film_id`
2. PUT rating (score=8)
3. PUT like (+1)
4. GET FilmStats (verify likes & rating)
5. PUT bookmark
6. POST review
7. Vote review "up"
8. GET FilmStats again

Expected result:

* Rating returns `{film_id, score}`
* Like returns `204 No Content`
* FilmStats after like:

  * `likes: 1`
  * `ratings_count: 1`
* Review created: `Review: <review_id>`
* Vote returns: `{"ok": true, "applied": true}`
* Final FilmStats:

  * `reviews_count: 1`
  * `votes_up: 1`

If this completes successfully, core flows work correctly.

---

## 3. Verify Redis caching

After running `make demo`, verify cache keys:

```bash
make redis-inspect
```

You should see keys like:

```
filmstats:<film_id>
```

Check TTL:

```bash
make redis-ttl
```

Expected: positive integer (seconds remaining)

After TTL expires, the key disappears automatically.

This confirms:

* Read-through cache
* TTL applied
* Cache invalidation on writes

---

## 4. Stop the stack

```bash
make down
```

---

## What This Demonstrates

* MongoDB as source of truth
* Aggregated FilmStats
* Redis cache layer with TTL
* Explicit cache invalidation on writes
* Reproducible environment
* Clean Makefile workflow

The demo is fully self-contained and reproducible.
