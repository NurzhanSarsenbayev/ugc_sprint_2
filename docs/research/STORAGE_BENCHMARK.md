# Storage Benchmark Research (MongoDB vs PostgreSQL)

This document presents a reproducible benchmark used to evaluate storage options
for the UGC (Engagement) service workload.

The goal is not to declare a "winner", but to understand trade-offs under a realistic workload:
- write-heavy operations (ratings)
- read-heavy access (FilmStats-like queries)
- top-N queries (reviews with votes)
- aggregation per film_id

All tests were executed locally using Docker Compose.

---
Benchmark is fully reproducible via:
```bash
make bench-all
make bench-run-optional
make bench-report
```
Raw logs are stored in:
reports/bench/

Latest generated summary:
reports/bench/results.md
---

## Environment

- MongoDB 7.0 (ReplicaSet, single node)
- PostgreSQL 16
- Python 3.11 benchmark runner
- Docker Desktop (local environment)
- Dataset: 1,000,000 ratings
- OPS per scenario: 20,000
- Concurrency: 20

Run commands:

```bash
make bench-all
make bench-report
````

Optional (long-running scenarios):

```bash
make bench-run-optional
make bench-report
```
Report is generated at:
reports/bench/results.md

---

## Dataset Seeding Performance (results may vary based on hardware)

Sample excerpt from a single local run (2026-02-09, Windows 11, Ryzen 5 5600, 32GB RAM, Docker Desktop).
For the latest numbers generated from raw logs, see: reports/bench/results.md.

Ratings dataset size: **1,000,000**

| Storage    | Time   | Throughput        |
| ---------- | ------ | ----------------- |
| MongoDB    | ~32.5 s | ~30,800 docs/sec  |
| PostgreSQL | ~6.7 s  | ~149,200 rows/sec |

Observation:

* PostgreSQL bulk insert is significantly faster in this setup.
* MongoDB write throughput is lower but still within acceptable UGC ingestion range.

---

## Workload 1 — Ratings (Upsert + Get + Aggregation)

OPS=20,000
CONCURRENCY=20

### MongoDB

* upsert p95: **~19.03 ms**
* get p95: **~16.15 ms**
* aggregation p95: **~18.50 ms**
* total p95: **~46.62 ms**

### PostgreSQL

* upsert p95: **~0.80 ms**
* get p95: **~0.21 ms**
* aggregation p95: **~0.20 ms**
* total p95: **~1.16 ms**

### Observation

In this local setup:

* PostgreSQL significantly outperforms MongoDB in raw latency.
* MongoDB latency remains stable but higher due to document model overhead and driver/network cost.

Important: this benchmark runs inside a single-node Docker environment.
Distributed deployment characteristics may differ.

---

## Workload 2 — Reviews (Top-20 + Last-5 Votes)

OPS=20,000
CONCURRENCY=20

### MongoDB

* query p95: **~21.58 ms**

### PostgreSQL

* query p95: **~16.28 ms**

### Observation

For structured, relational-style queries:

* PostgreSQL shows lower latency.
* MongoDB remains within acceptable response range for UGC read workloads.

---

## Interpretation & Architectural Implications

This benchmark demonstrates:

1. PostgreSQL provides extremely low latency for indexed relational queries.
2. MongoDB shows higher per-operation latency but maintains predictable performance.
3. For pure performance under this workload, PostgreSQL is faster.

However, storage decision is not based on raw latency alone.

UGC systems typically require:

* flexible schema evolution
* denormalized read models
* simpler horizontal scaling
* high write tolerance
* decoupling from strict relational constraints

MongoDB remains suitable when:

* document-based modeling simplifies API logic
* joins can be avoided by design
* read models are embedded
* write scaling is prioritized

PostgreSQL remains suitable when:

* strong relational integrity is required
* complex joins dominate workload
* predictable low-latency queries are critical

---

## Limitations

* Single-node local Docker environment
* No network latency simulation
* No horizontal scaling
* No replication lag simulation
* No production-level tuning

This benchmark should be interpreted as a baseline comparison,
not as a definitive production performance study.

---

## Conclusion

The benchmark confirms that:

* PostgreSQL outperforms MongoDB in raw local latency.
* MongoDB remains viable for UGC workloads with acceptable performance.
* Storage selection should consider data model flexibility and scaling strategy,
  not only microbenchmark latency.

Final storage decision should be aligned with product requirements,
data evolution strategy and operational model.

This benchmark is one input into the storage decision.
The final choice should align with product requirements and operational constraints.
