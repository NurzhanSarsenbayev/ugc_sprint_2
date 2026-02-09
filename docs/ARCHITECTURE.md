# Architecture

This document explains the internal design decisions of the UGC Service.

---

# 1. System Components

## 1.1 API Layer (FastAPI)

Responsible for:
- Request validation
- Dependency injection
- Service orchestration
- Error mapping
- Observability (logging, tracing)

The API layer contains no business logic.

---

## 1.2 MongoDB (Primary Storage)

MongoDB stores:

- ratings
- likes
- reviews
- review votes

It is optimized for write-heavy workloads.

Transactions are used for:
- Review deletion (cascade votes)
- Vote updates

---

## 1.3 FilmStats Aggregation Layer

FilmStatsService maintains derived metrics:

- likes
- dislikes
- ratings_count
- ratings_sum
- average rating
- reviews_count
- votes_up
- votes_down

Updates are synchronous.

This guarantees consistency between write operations and aggregated state.

---

## 1.4 Redis Cache (Optional)

Film stats are cached in Redis.

Key format:
````
filmstats:{film_id}
````

TTL is configurable.

Cache invalidation occurs when:
- rating changes
- like changes
- review created/deleted
- vote applied/removed

If Redis is unavailable, the system still works.

---

## 1.5 PostgreSQL (Benchmark Only)

PostgreSQL is included to compare:

- Write performance
- Aggregation performance

It is not part of the main request path.

See `docs/research/STORAGE_BENCHMARK.md`.

---

# 2. Write Path

Example: PUT rating

1. Update MongoDB document
2. Update FilmStats counters
3. Invalidate Redis cache
4. Return response

All operations are synchronous.

This ensures read-after-write consistency.

---

# 3. Read Path

GET /film-stats/{film_id}

1. Check Redis
2. If cached → return
3. If not → compute from MongoDB
4. Store in Redis
5. Return result

---

# 4. Consistency Model

The system guarantees:

- Immediate consistency for aggregates
- No eventual delay
- No background workers
- No async pipelines

Trade-off:
Higher write latency compared to eventual consistency systems.

This is an intentional design decision for simplicity and determinism.

---

# 5. Trade-offs

| Decision | Why |
|----------|------|
| Synchronous aggregation | Simpler correctness model |
| No async workers | Fewer failure modes |
| Redis optional | Graceful degradation |
| MongoDB for OLTP | Flexible document schema |
| No sharding | Out of scope |

---

# 6. Failure Model

If Redis fails:
- Cache is bypassed
- System continues

If Mongo fails:
- Request fails

No partial writes occur inside transactions.
