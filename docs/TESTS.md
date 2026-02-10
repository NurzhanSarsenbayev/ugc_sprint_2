# Testing Strategy

This project includes unit and integration tests that run against real infrastructure
(MongoDB, Redis, and the API container) using Docker Compose.

The goal is not only correctness, but also reproducibility and CI reliability.

---

## How to Run Tests

From project root:

```bash
make test
````

This command:

1. Builds the Docker image
2. Starts required services (MongoDB, Redis)
3. Runs pytest inside the API container
4. Collects coverage
5. Fails if coverage < 90%

Tests are executed inside Docker to ensure consistency with CI.

---

## CI Matrix

CI runs the full test suite on:

* Python 3.10
* Python 3.11
* Python 3.12

Each job:

* Builds containers
* Starts the stack
* Executes `make test`
* Runs lint (ruff)
* Runs type checking (mypy, non-blocking)

The matrix ensures compatibility across supported Python versions.

---

## Test Types

### 1) API / Integration Tests

These tests:

* Call real HTTP endpoints
* Interact with MongoDB
* Validate business logic (likes, ratings, reviews)
* Verify FilmStats aggregation
* Verify Redis caching behavior

They simulate real service usage.

---

### 2) Redis Cache Tests

Dedicated tests verify:

* Cache write on first FilmStats request
* Cache hit on subsequent request
* TTL-based invalidation behavior

Redis failures are handled gracefully (fallback to DB).

---

## Coverage Policy

The project enforces:

```
--cov-fail-under=90
```

This ensures that changes do not silently reduce test coverage.

Coverage is measured inside Docker and validated in CI.

---

## What Is NOT Covered

The following components are intentionally not unit-tested:

* ELK stack (demo-only observability)
* Benchmark stack (separate research environment)

Those parts are considered optional infrastructure,
not part of core service logic.

---

## Philosophy

Testing is focused on:

* Business correctness
* Integration stability
* Reproducibility
* CI reliability

The goal is to simulate real usage rather than mock-heavy unit isolation.

---

## Static Analysis

Runtime code (`ugc_api/`) is type-checked with strict `mypy`.

Excluded from strict typing:
- `tests/`
- `scripts/bench/`

This keeps the production runtime layer strictly typed,
while allowing flexibility in benchmarks and test utilities.

Run locally:

```bash
pre-commit run --all-files
```
