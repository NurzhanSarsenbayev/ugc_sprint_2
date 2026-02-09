# Storage Benchmark: MongoDB vs PostgreSQL

This document describes a practical comparison between MongoDB and PostgreSQL
for a write-heavy User Generated Content (UGC) workload.

The goal is not to declare a universal winner,
but to understand trade-offs in real-world backend scenarios.

---

## Motivation

User interaction systems (likes, ratings, reviews, bookmarks)
typically require:

- High-volume writes
- Low-latency updates
- Aggregation queries (e.g. average rating, counters)
- Horizontal scalability potential

This benchmark evaluates how MongoDB and PostgreSQL behave
under these constraints.

---

## Workload Description

The benchmark simulates a UGC system with:

- Random user interactions
- Repeated writes per user
- Aggregation queries per content item
- Concurrent access patterns

Entities involved:

- Likes
- Ratings
- Reviews
- Film statistics (aggregated counters)

---

## Methodology

- Local Docker-based environment
- Indexed collections / tables
- Synthetic dataset generation
- Batched write operations
- Read-heavy aggregation queries

Benchmark tooling is available under:

```

scripts/bench/

```

The environment can be reproduced using:

```

make bench

```

---

## Observations

### Write Performance

MongoDB demonstrated:

- Lower write latency under high concurrency
- Flexible schema advantages for UGC workloads

PostgreSQL demonstrated:

- Strong consistency guarantees
- Predictable transactional behavior

---

### Aggregation Queries

PostgreSQL:

- Efficient with proper indexing
- Stable query planner performance

MongoDB:

- Fast aggregation pipelines
- Good performance for document-based grouping

---

## Trade-offs

### MongoDB Strengths
- Flexible schema
- High write throughput
- Natural fit for document-style UGC

### PostgreSQL Strengths
- Mature transactional model
- Strong relational guarantees
- Better for complex relational joins

---

## Conclusion

For write-heavy UGC workloads with flexible schema needs,
MongoDB is a practical and efficient primary storage choice.

PostgreSQL remains a strong alternative when strict relational
constraints and transactional integrity are primary concerns.

The final architecture in this project uses MongoDB
as the primary storage engine,
with PostgreSQL included for benchmarking and comparison purposes.
```