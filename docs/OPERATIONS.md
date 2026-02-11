
# Operations Guide

This document explains how to run and operate the service locally.

The project contains two independent stacks:

1. Core Runtime (UGC API)
2. Research / Benchmark Stack (MongoDB vs PostgreSQL)

They are intentionally separated.

---

# 1. Core Runtime Stack

This is the actual UGC service.

## Services

- engagement_api (FastAPI)
- engagement_mongo (primary database)
- engagement_redis (FilmStats cache)

Optional:
- ELK stack (observability demo)

PostgreSQL is NOT part of the core runtime.

---

## Start Core Stack

```bash
make up
```

Verify readiness:

```bash
make ready
```

Run demo scenario:

```bash
make demo
```

Stop services:

```bash
make down
```

View logs:

```bash
make logs-api
make logs-mongo
make logs-redis
```

---

# 2. Observability (Optional)

ELK stack is available for demonstration purposes.

Start ELK:

```bash
make elk-up
```

Stop ELK:

```bash
make elk-down
```

Note:
ELK may behave differently depending on Docker Desktop vs Linux.
It is considered a demo environment, not production-ready logging.

See: docs/OBSERVABILITY.md

---

# 3. Research / Benchmark Stack

This stack is used for storage performance comparison (MongoDB vs PostgreSQL).
It runs independently of the core API service.

Databases included:

* MongoDB
* PostgreSQL

---

## Core Benchmark Flow

Start environment:

```bash
make bench-up
```

Seed datasets (ratings + reviews):

```bash
make bench-seed-all
```

Run core benchmark scenarios:

```bash
make bench-run-all
```

Generate aggregated report:

```bash
make bench-report
```

Stop benchmark stack:

```bash
make bench-down
```

---

## Run a Single Scenario

```bash
make bench-run-scenario SCENARIO=ratings
```

Available scenarios:

* ratings
* reviews-top
* topn
* doc-vs-rel

---

## Optional / Extended Benchmark Flows

Run extended benchmark suite:

```bash
make bench-optional
```

Run optional scenarios only (fast defaults):

```bash
make bench-run-optional
```

Run optional scenarios with heavier defaults:

```bash
make bench-run-optional-full
```

Run full suite (core + optional):

```bash
make bench-run-full
```

---

This stack exists to demonstrate storage research capability,
not to support the runtime of the API service.

See: docs/research/STORAGE_BENCHMARK.md
