# UGC Service (Transactional + Analytical Backend)

A backend service for collecting and aggregating user-generated content
with an explicit separation between write-heavy transactional workloads
and read-heavy analytical workloads.

Example domain: online cinema platform.  
The design is domain-agnostic and applicable to any system
that processes user interactions (e-commerce, marketplaces, media apps).

---

## Why This Project Exists

Applications that collect user interactions (likes, ratings, reviews)
face two fundamentally different problems:

1. High-volume, low-latency writes
2. Efficient aggregated reads (e.g. average rating, engagement stats)

Using a single storage engine for both often leads to trade-offs.

This project explores a practical separation of concerns:

- **MongoDB** for write-optimized UGC storage (OLTP)
- **Service-level aggregation layer** for film statistics
- **PostgreSQL** as a benchmark/reference storage
- **Redis** as an auxiliary performance layer

The goal is not domain complexity,
but architectural clarity and operational stability.

---

## Architecture Overview

- FastAPI — public HTTP API
- MongoDB — primary source of truth for UGC
- Redis — auxiliary optimization layer
- PostgreSQL — storage benchmark comparison
- Docker Compose — reproducible local environment
- CI + test suite — quality gate (90%+ coverage)

---

## Data Flow

### Write Path
Client → API → MongoDB

### Read / Aggregation Path
MongoDB → FilmStats aggregation → API response

### Storage Benchmark
MongoDB vs PostgreSQL comparison  
See `docs/research/STORAGE_BENCHMARK.md` for a practical storage comparison.

---

## Quickstart

```bash
cp .env.sample .env
make up
````

Swagger:
[http://localhost:8080/docs](http://localhost:8080/docs)

Run tests:

```bash
make test
```

---

## Project Structure

```
ugc_api/        FastAPI application
infra/          Docker configuration
scripts/        Index and benchmark utilities
tests/          Test suite
docs/           Documentation
```

---

## Documentation

* Architecture: `docs/ARCHITECTURE.md`
* Operations: `docs/OPERATIONS.md`
* Demo: `docs/DEMO.md`
* Tests: `docs/TESTS.md`
* Research: `docs/research/STORAGE_BENCHMARK.md`

```