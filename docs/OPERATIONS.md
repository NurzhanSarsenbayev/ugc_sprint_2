# Operations

This document explains how to run and inspect the service.

---

# 1. Local Run

```bash
cp infra/.env.sample infra/.env
make up
make ready
````

---

# 2. Docker Services

* engagement_api
* engagement_mongo
* engagement_pg
* engagement_redis

---

# 3. Reset Environment

```bash
make down
make down-v
```

---

# 4. Inspect Redis

```bash
make redis-inspect
make redis-ttl
```

---

# 5. Run Tests

```bash
make test
```

---

# 6. Health & Readiness

Health:

* Service process running

Ready:

* Mongo reachable
* Redis reachable
