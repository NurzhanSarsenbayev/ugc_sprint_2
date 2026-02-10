# Architecture Overview

The project consists of two independent parts:

1. UGC Service Runtime
2. Storage Research Environment

They serve different purposes.

---

# 1. UGC Service Runtime

## Components

Client → FastAPI → MongoDB
                     ↘ Redis (FilmStats cache)

### FastAPI

Handles:

- Likes
- Ratings
- Reviews
- Bookmarks
- FilmStats aggregation

### MongoDB

Primary storage for user engagement data.

### Redis

Used as read-through cache for FilmStats.

Flow:

1. Client requests FilmStats
2. Service checks Redis
3. If cache miss → aggregate from MongoDB
4. Store result in Redis (TTL)
5. Return response

Redis failures do NOT break the service.
It falls back to MongoDB.

---

# 2. Observability

Optional ELK stack:

API logs → Filebeat → Logstash → Elasticsearch → Kibana

Logs are structured JSON and include:

- trace_id
- service
- environment
- timestamp
- level
- message

Trace ID is generated per request via middleware.

ELK is demo-oriented and not required for core functionality.

---

# 3. Storage Research Environment

This environment exists to compare:

- MongoDB
- PostgreSQL

The benchmark measures:

- Insert performance
- Aggregation queries
- Top-N queries
- Filtering patterns

PostgreSQL is not used by the API service.

It exists solely to demonstrate storage evaluation capability
and understanding of trade-offs.

---

# Design Decisions

## Why MongoDB for UGC?

- Document flexibility
- Natural modeling for user interactions
- Good fit for engagement events

## Why Redis?

- FilmStats is aggregation-heavy
- Caching significantly reduces read load
- Demonstrates production-oriented thinking

## Why Separate Benchmark Stack?

- Prevents research from affecting runtime
- Demonstrates analytical capability
- Keeps production path clean

---

## Type Safety

The runtime layer (`ugc_api/`) is fully type-checked with strict mypy settings.

Design decision:
- Repositories return explicit dict structures (no implicit Any)
- Service layer uses typed deltas for vote transitions
- Aggregations always return deterministic structures (no Optional leaks)

This ensures predictable behavior across the API layer.
