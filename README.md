# UGC Engagement Service

![CI](https://github.com/NurzhanSarsenbayev/ugc-engagement-service/actions/workflows/ci.yml/badge.svg)

A production-minded microservice responsible for managing user engagement data:

* Ratings
* Likes
* Reviews + votes
* Bookmarks
* Aggregated FilmStats

This project demonstrates how an engagement system can be implemented with:

* strict runtime typing
* reproducible Docker setup
* integration-first testing
* cache discipline (Redis + TTL)
* structured logging with trace_id
* clear separation between runtime and research environments

---

# Why This Service Exists

User engagement systems are write-heavy and aggregation-sensitive.

They require:

- predictable aggregation logic
- disciplined cache invalidation
- storage models aligned with access patterns
- observability from day one

This repository focuses on implementing these concerns
without over-engineering the solution.

---

# 60-Second Local Run

Start core runtime:

```bash
make up
make ready
make demo
```

Stop:

```bash
make down
```

Core runtime includes:

* FastAPI
* MongoDB (primary storage)
* Redis (FilmStats cache)

PostgreSQL is NOT part of the runtime stack.

---

# Implemented

Core Features:

* Ratings (PUT)
* Likes (+1 / -1)
* Reviews + voting
* Bookmarks
* Aggregated FilmStats

Engineering Discipline:

* Redis cache with TTL and graceful fallback
* Structured JSON logging
* trace_id propagation
* Integration tests (executed inside Docker)
* Test coverage ≥ 90%
* Strict mypy for runtime code
* ruff (lint + format)
* pre-commit hooks
* CI matrix (Python 3.10 / 3.11 / 3.12)

---

# Optional Components

These are intentionally separated from the runtime service:

Observability demo (ELK):

```bash
make elk-up
```

Storage research stack (MongoDB vs PostgreSQL):

```bash
make bench-up
make bench-seed-all
make bench-run-all
make bench-report
```

The benchmark environment exists exclusively for storage comparison research.
It does not participate in the API runtime.

See: docs/research/STORAGE_BENCHMARK.md

---

# Architecture Overview

The system is intentionally structured into two independent stacks:

```
Core Runtime (docker-compose)
────────────────────────────────────────────────────

Client (curl / Postman / frontend)
                |
               HTTP
                v
        UGC API (FastAPI)
            |           \
            |            \  FilmStats cache (TTL + fallback)
            v             v
        MongoDB         Redis
        (primary)       (cache)

Optional Observability (ELK profile)
────────────────────────────────────────────────────

UGC API logs (JSON + trace_id)
        |
        v
    Filebeat → Logstash → Elasticsearch → Kibana


Research / Benchmark Stack (separate compose)
────────────────────────────────────────────────────

Bench Runner (Python)
        |\
        | \
        |  \-> MongoDB (document model)
        |  \-> PostgreSQL (relational model)
        |
        └──> reports/bench/results.md
```

Key design decisions:

* PostgreSQL is used exclusively for research and benchmarking.
* The benchmark stack is isolated from the runtime API.
* Observability (ELK) is optional and does not affect core logic.
* Redis is used only for FilmStats caching with explicit TTL discipline.

See: `docs/ARCHITECTURE.md`

---

# Quality & Development Workflow

Local setup:

```bash
make deps-dev
make test
```

Before committing:

```bash
pre-commit run --all-files
```

Quality gates:

* strict typing for runtime code
* integration-first testing strategy
* reproducible container-based execution
* enforced coverage threshold

---

# Documentation

* Architecture → docs/ARCHITECTURE.md
* Operations → docs/OPERATIONS.md
* Testing → docs/TESTS.md
* Observability → docs/OBSERVABILITY.md
* Storage Benchmark → docs/research/STORAGE_BENCHMARK.md

---

# What This Repository Demonstrates

* Clean microservice boundaries
* Explicit runtime vs research separation
* Reproducible local environments
* Operational clarity
* Storage trade-off experimentation
