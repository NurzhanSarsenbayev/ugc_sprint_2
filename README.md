# UGC Service  
![CI](https://github.com/NurzhanSarsenbayev/ugc_sprint_2/actions/workflows/ci.yml/badge.svg)


Transactional + Aggregated Backend (MongoDB + Redis + FastAPI)

A backend service for collecting and aggregating user interactions
(likes, ratings, reviews) with explicit workload separation.

Designed as a clean architectural example of:
- write-heavy OLTP workload
- synchronous aggregation layer
- optional Redis caching
- reproducible Docker-based environment
- CI with 90%+ test coverage

---

## What This Project Demonstrates

This service models a common real-world problem:

Applications that collect user interactions must handle:

1. High-volume writes (ratings, likes, reviews)
2. Aggregated reads (average rating, engagement metrics)

Instead of mixing concerns, this project separates them:

- MongoDB → write-optimized UGC storage
- FilmStats aggregation layer → derived counters
- Redis → optional cache for read optimization
- FastAPI → public API
- Docker Compose → reproducible environment
- GitHub Actions → quality gate

The focus is architectural clarity, not domain complexity.

---
## Project Status

- CI passing (Python 3.10 / 3.11 / 3.12)
- 90%+ test coverage
- Transactional MongoDB layer
- Aggregated FilmStats layer
- Redis caching with TTL
- Reproducible Docker environment

---
## Architecture (High-Level)

Write Path:
Client → API → MongoDB → FilmStats update → Redis invalidation

Read Path:
API → Redis (if cached) → fallback to MongoDB → cache result

See `docs/ARCHITECTURE.md` for detailed explanation.

---

## Quickstart

```bash
cp infra/.env.sample infra/.env
make up
make ready
````

Swagger:
[http://localhost:8080/docs](http://localhost:8080/docs)

Health:
[http://localhost:8080/health](http://localhost:8080/health)
[http://localhost:8080/ready](http://localhost:8080/ready)

---

## Quick Demo (2–5 minutes)

```bash
make demo
```

This runs:

* rating
* like
* bookmark
* review
* review vote
* film stats aggregation

Details: `docs/DEMO.md`

---

## Run Tests

```bash
make test
```

CI enforces:

Integration tests run via Docker Compose and are executed on Python 3.10/3.11/3.12 in CI matrix.

* Ruff
* Mypy (non-blocking)
* 90%+ coverage

---

## Project Structure

```
ugc_api/        FastAPI application
infra/          Docker configuration
scripts/        Benchmark utilities
tests/          Test suite
docs/           Documentation
```
---

## Observability (optional)

- Structured JSON logs (stdout) with per-request `trace_id`
- Optional local ELK stack demo (Kibana search by `trace_id`)

See: `docs/OBSERVABILITY.md`

Commands:
```bash
make elk-up
make elk-logs
```
---

## Documentation

* Architecture → `docs/ARCHITECTURE.md`
* Operations → `docs/OPERATIONS.md`
* Demo → `docs/DEMO.md`
* Benchmark research → `docs/research/STORAGE_BENCHMARK.md`
