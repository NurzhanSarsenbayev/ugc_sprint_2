# Architecture

This repository contains a UGC (User Generated Content) backend service.

Domain examples: online cinema, marketplaces, media apps.
The architecture is designed to be domain-agnostic.

Components:
- UGC API (FastAPI)
- MongoDB (primary storage for UGC)
- Redis (cache / auxiliary layer)
- Postgres (benchmark/reference storage for research)
- Optional observability tooling (Sentry/ELK if enabled)

See also:
- OPERATIONS.md
- DEMO.md
- TESTS.md
- research/STORAGE_BENCHMARK.md
