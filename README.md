# UGC Service

A backend service for collecting user-generated content (likes, ratings, reviews, bookmarks)
with a clear separation between transactional and analytical workloads.

Example domain: online cinema platform.  
The architecture is domain-agnostic and can be reused for marketplaces,
media platforms, or any product with user interactions.

---

## Problem

Modern applications collect large volumes of user interactions:
- reactions (likes / dislikes)
- ratings
- reviews
- bookmarks

These writes must be fast and reliable, while aggregated analytics
(e.g., average rating, engagement metrics) require efficient read patterns.

This project explores a practical design separating:

- **OLTP workload** (high-volume writes)
- **Analytical workload** (aggregated reads)

---

## Architecture Overview

- **FastAPI** — public API layer
- **MongoDB** — primary storage for UGC (write-optimized)
- **Redis** — auxiliary layer (caching / optimization)
- **PostgreSQL** — reference storage for benchmarking and comparison
- **Docker Compose** — local reproducible environment

The service focuses on data modeling, aggregation logic,
and operational stability rather than domain-specific features.

---

## Data Flow

### Write Path
Client → API → MongoDB

### Aggregation / Stats
MongoDB → service-level aggregation → Film Stats collection

### Benchmark Layer
MongoDB vs PostgreSQL comparison (see `docs/research/`)

---

## Quickstart

```bash
cp .env.sample .env
make up
```
API:
http://localhost:8080/docs

Run tests:

```bash
make test
```
### Project Structure
ugc_api/        # FastAPI application
infra/          # Docker and environment configuration
scripts/        # Index management and benchmarks
tests/          # Test suite
docs/           # Project documentation

### Documentation
- Architecture: docs/ARCHITECTURE.md

- Operations: docs/OPERATIONS.md

- Demo: docs/DEMO.md

- Tests: docs/TESTS.md

- Storage benchmark: docs/research/STORAGE_BENCHMARK.md

---