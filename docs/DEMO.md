# Demo

This demo validates the full request -> storage -> aggregation pipeline.

---

## 1. Start the stack

```bash
cp .env.sample .env
make up
```
API will be available at:

http://localhost:8080/docs

## 2. Create a rating
```bash
curl -X PUT "http://localhost:8080/api/v1/ratings/22222222-2222-2222-2222-222222222222?score=8" \
  -H "X-User-Id: 11111111-1111-1111-1111-111111111111"
```

## 3. Retrieve user rating
```bash
curl -X GET "http://localhost:8080/api/v1/ratings/22222222-2222-2222-2222-222222222222" \
  -H "X-User-Id: 11111111-1111-1111-1111-111111111111"
```

## 4. Verify aggregated film statistics
```bash
curl http://localhost:8080/api/v1/film-stats/22222222-2222-2222-2222-222222222222
```
You should see updated counters and avg_rating.

## 5. Run automated tests
```bash
make test
```
Expected result: all tests passing with 90%+ coverage.