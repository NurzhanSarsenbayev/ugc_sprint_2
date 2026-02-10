# UGC Service
![CI](https://github.com/NurzhanSarsenbayev/ugc_sprint_2/actions/workflows/ci.yml/badge.svg)

Production-oriented user engagement service supporting:

- Likes
- Ratings
- Reviews
- Bookmarks
- Aggregated FilmStats

The project demonstrates integration-first testing, caching strategy,
observability, and storage research (MongoDB vs PostgreSQL).

---

# Quickstart (Core Runtime)

Start services:

```bash
make up
````

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

Core stack includes:

* FastAPI
* MongoDB
* Redis (FilmStats cache)

---

# Tests

Run full test suite (integration tests + coverage):

```bash
make test
```

* Executed inside Docker
* Coverage enforced (>= 90%)
* CI matrix: Python 3.10 / 3.11 / 3.12

---

# Observability (Optional)

ELK demo stack available:

```bash
make elk-up
```

Logs include structured JSON and `trace_id` for request tracing.

See: docs/OBSERVABILITY.md

---

# Storage Research (MongoDB vs PostgreSQL)

Separate benchmark stack:

```bash
make bench-up
make bench-seed
make bench-run
make bench-report
```

PostgreSQL is used exclusively for storage benchmarking.
It is NOT part of the API runtime.

See: docs/research/STORAGE_BENCHMARK.md

---

# Project Structure

Core runtime:

* FastAPI API
* MongoDB primary storage
* Redis cache

Research environment:

* MongoDB
* PostgreSQL

Optional:

* ELK stack (observability demo)

---
---

## Quality & Tooling

The project uses a strict development workflow:

- `ruff` for linting and formatting
- `mypy` (strict mode for runtime code)
- `pre-commit` hooks
- CI matrix: Python 3.10 / 3.11 / 3.12
- Test coverage ≥ 90%

Before committing:

```bash
pre-commit run --all-files
```

Local checks:
```bash
make fmt
make test
```

---

# Documentation

* Architecture → docs/ARCHITECTURE.md
* Operations → docs/OPERATIONS.md
* Testing → docs/TESTS.md
* Observability → docs/OBSERVABILITY.md
* Storage Benchmark → docs/research/STORAGE_BENCHMARK.md
