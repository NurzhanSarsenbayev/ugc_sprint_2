# UGC Service (Transactional + Analytical Backend)

A backend service for collecting and aggregating user-generated content
with an explicit separation between write-heavy transactional workloads
and read-heavy analytical workloads.

Example use case: online cinema platform (likes, ratings, reviews).
The architecture is domain-agnostic and can be reused in any interaction-driven system.

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

This service is designed around workload separation:

- **MongoDB** – write-optimized storage for user interactions
- **FilmStats aggregation layer** – maintains counters and derived metrics
- **Redis** – optional performance optimization layer
- **PostgreSQL** – reference storage used for benchmarking
- **FastAPI** – public HTTP API
- **Docker Compose** – fully reproducible environment
- **CI (GitHub Actions)** – automated quality gate (90%+ coverage)

---

## Data Flow

### Write Path
Client -> API -> MongoDB

### Read / Aggregation Path
MongoDB -> FilmStats aggregation -> API response

### Storage Benchmark
MongoDB vs PostgreSQL comparison  
See `docs/research/STORAGE_BENCHMARK.md` for a practical storage comparison.

---

## Quickstart

```bash
cp infra/.env.sample infra/.env
make up
````

Health check:

http://localhost:8080/health  
http://localhost:8080/ready

Swagger:
[http://localhost:8080/docs](http://localhost:8080/docs)

Run tests:

```bash
make test
```
## Quick demo (2–5 minutes)

```bash
cp infra/.env.sample infra/.env
make up
make ready
make demo
```

See docs/DEMO.md for details.

---

## Project Structure

```
ugc_api/        FastAPI application
infra/          Docker configuration
scripts/        Benchmark and index utilities
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