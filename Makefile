export STATE ?= local

# ---------- Vars ----------
COMPOSE        := infra/docker-compose.yml
BENCH_COMPOSE  := infra/bench-compose.yml
API            := api
PORT           := 8080
TIMESTAMP      := $(shell date +%Y%m%d_%H%M%S)
PY=python
BASE_URL?=http://localhost:8080
USER_HEADER?=X-User-Id

# Test DSN for pytest
MONGO_TEST_DSN := mongodb://mongo:27017/engagement_test?replicaSet=rs0

# Bench DSN and params (override: make bench-ratings OPS=50000)
MONGO_BENCH_DSN ?= mongodb://mongo:27017/engagement_bench?replicaSet=rs0
PG_BENCH_DSN    ?= postgresql://bench:bench@postgres:5432/bench
OPS        ?= 20000
CONCURRENCY?= 20
TOPN       ?= 20
K_LAST     ?= 20
FILM_ID    ?= 36573970-4f97-4ab8-b3d8-0d6d5bba64fc

REPORTS_DIR := reports/bench

.DEFAULT_GOAL := help

# ---------- Phony ----------
.PHONY: help dev up build restart down clean ps logs shell \
        test lint mypy indexes dedup-bookmarks mongo-indexes \
        sentry-test \
        elk-up elk-down elk-logs elk-restart \
        bench-build bench-up bench-down bench-ps bench-run \
        bench-setup bench-seed-ratings bench-seed-reviews \
        bench-ratings bench-reviews-top bench-topn bench-doc-vs-rel \
        bench-seed-all bench-run-all bench-all bench-run-scenario \
        bench-pg-compat-views smoke-bench \
        bench-ratings-save bench-reviews-top-save bench-topn-save bench-doc-vs-rel-save bench-report

# ---------- Help ----------
help:
	@echo "Targets:"
	@echo "  dev                 Build images and start the main stack"
	@echo "  up                  Start the main stack"
	@echo "  build               Rebuild API image only"
	@echo "  restart             Rebuild and restart API container only"
	@echo "  down                Stop the main stack (keep volumes)"
	@echo "  clean               Stop the stack and remove volumes (main + bench)"
	@echo "  ps                  List containers"
	@echo "  logs                Follow API logs"
	@echo "  shell               Open bash inside API container"
	@echo ""
	@echo "Quality:"
	@echo "  test                Run pytest (creates indexes; coverage fail-under=90)"
	@echo "  lint                Run flake8 for ugc_api"
	@echo "  mypy                Run mypy and write HTML report to reports/mypy"
	@echo ""
	@echo "Mongo helpers:"
	@echo "  indexes             Create Mongo indexes"
	@echo "  dedup-bookmarks     Remove duplicate bookmarks"
	@echo "  mongo-indexes       Show Mongo collection indexes"
	@echo ""
	@echo "Observability:"
	@echo "  elk-up              Start ELK stack (Elastic + Kibana + Logstash + Filebeat)"
	@echo "  elk-down            Stop ELK stack and remove containers"
	@echo "  elk-logs            Follow Logstash + Filebeat logs"
	@echo "  elk-restart         Restart Logstash + Filebeat"
	@echo "  sentry-test         Call /__sentry-test (expects 204)"
	@echo ""
	@echo "Bench:"
	@echo "  bench-build         Build bench runner image"
	@echo "  bench-up            Start bench stack (mongo+postgres)"
	@echo "  bench-down          Stop bench stack and remove volumes"
	@echo "  bench-ps            List bench containers"
	@echo "  bench-run           Run a command inside bench container: make bench-run CMD='...'"
	@echo "  bench-setup         Build + up + wait + init rs0"
	@echo "  bench-seed-ratings  Seed ratings into both DBs"
	@echo "  bench-seed-reviews  Seed reviews (Mongo doc + PG normalized)"
	@echo "  bench-ratings       Run ratings benchmark"
	@echo "  bench-reviews-top   Run reviews benchmark (top-20 + tail-5)"
	@echo "  bench-topn          Run top-N per many films benchmark"
	@echo "  bench-doc-vs-rel    Run document vs relational benchmark (Mongo vs PG)"
	@echo "  bench-seed-all      Seed all datasets"
	@echo "  bench-run-all       Run all scenarios and save logs"
	@echo "  bench-report        Aggregate logs into reports/bench/results.md"
	@echo "  bench-all           setup -> seed-all -> run-all -> report"
	@echo "  bench-run-scenario  Run one scenario: SCENARIO={ratings|reviews-top|topn|doc-vs-rel}"
	@echo "  bench-pg-compat-views Create compatibility views (reviews, review_votes) in PG"
	@echo "  smoke-bench         Quick smoke check for bench stack (pg+mongo PRIMARY)"

# ---------- Core lifecycle ----------
dev:
	@echo "Building images and starting containers..."
	@docker compose -f $(COMPOSE) up -d --build && echo "Ready: http://localhost:$(PORT)"

up:
	@echo "Starting containers..."
	@docker compose -f $(COMPOSE) up -d && echo "All containers started"

build:
	@docker compose -f $(COMPOSE) build $(API)

restart:
	@docker compose -f $(COMPOSE) up -d --build $(API)

down:
	@docker compose -f $(COMPOSE) down

clean:
	@docker compose -f $(COMPOSE) down -v
	@docker compose -f $(BENCH_COMPOSE) down -v || true

ps:
	@docker compose -f $(COMPOSE) ps

logs:
	@docker compose -f $(COMPOSE) logs -f $(API)

shell:
	@docker compose -f $(COMPOSE) exec $(API) bash

# ---------- ELK stack management ----------
elk-up:  ## Start ELK stack (Elastic + Kibana + Logstash + Filebeat)
	@echo "Starting ELK stack..."
	docker compose -f infra/docker-compose.yml --profile elk up -d elasticsearch kibana logstash filebeat
	@echo "ELK started: http://localhost:5601"

elk-down:  ## Stop ELK stack and remove containers
	@echo "Stopping ELK stack..."
	docker compose -f infra/docker-compose.yml --profile elk down --remove-orphans
	@echo "ELK stopped."

elk-logs:  ## Follow Logstash and Filebeat logs
	@echo "Tailing ELK logs..."
	docker compose -f infra/docker-compose.yml logs -f logstash filebeat

elk-restart:  ## Restart Logstash and Filebeat (after config changes)
	@echo "Restarting Logstash and Filebeat..."
	docker compose -f infra/docker-compose.yml restart logstash filebeat
	@echo "ELK pipeline restarted."

# ---------- Quality / Tests ----------

lint:
	python -m ruff check .

lint-fix:
	python -m ruff check . --fix

format:
	python -m ruff format .

check: lint test

fmt: lint-fix format

lint-docker:
	@docker compose -f $(COMPOSE) exec -T $(API) bash -lc '\
	  flake8 ugc_api \
	'

mypy:
	@docker compose -f $(COMPOSE) exec -T $(API) bash -lc '\
	  mypy ugc_api --html-report reports/mypy \
	'

test:
	@$(MAKE) -s up >/dev/null
	@docker compose -f $(COMPOSE) exec -T $(API) bash -lc '\
	  python -m pip install -q -r requirements/dev.txt; \
	  export MONGO_DSN="$(MONGO_TEST_DSN)"; \
	  python scripts/create_indexes.py; \
	  python -m pytest -v --disable-warnings \
	    --cov=ugc_api --cov-report=term-missing \
	    --cov-config=.coveragerc --cov-fail-under=90 \
	'

# ---------- Mongo service scripts ----------
indexes:
	@docker compose -f $(COMPOSE) exec -T $(API) python scripts/create_indexes.py

dedup-bookmarks:
	@docker compose -f $(COMPOSE) exec -T $(API) python scripts/dedup_bookmarks.py

mongo-indexes:
	@docker compose -f $(COMPOSE) exec -T $(API) python scripts/show_indexes.py

# ---------- Sentry ----------
sentry-test:
	@curl -fsS http://localhost:$(PORT)/__sentry-test -o /dev/null && \
	  echo "Sentry test event sent (204)" || \
	  (echo "Sentry test failed (service down or DSN not set?)" && exit 1)

# ---------- Bench: build & control ----------
bench-build:
	@docker compose -f $(BENCH_COMPOSE) build bench && echo "bench image built"

bench-up:
	@docker compose -f $(BENCH_COMPOSE) up -d --remove-orphans mongo postgres && echo "Bench stack up"

bench-down:
	@docker compose -f $(BENCH_COMPOSE) down -v --remove-orphans || true
	@echo "Bench stack down; volumes removed"

bench-ps:
	@docker compose -f $(BENCH_COMPOSE) ps

bench-run:
	@test -n "$(CMD)" || (echo "Usage: make bench-run CMD='<command inside bench>'" && exit 2)
	@docker compose -f $(BENCH_COMPOSE) run --rm --remove-orphans bench bash -lc '$(CMD)'

# ---- Bench helpers ----
bench-mongo-init:
	@docker exec bench_mongo mongosh --quiet /scripts/bench/mongo-rs-init.js && \
	  echo "rs0 PRIMARY ready" || (echo "rs-init failed" && exit 1)

bench-wait:
	@printf "waiting for postgres & mongo "
	@for i in $$(seq 1 60); do \
	  PG=$$(docker exec bench_postgres pg_isready -U bench -d bench >/dev/null 2>&1 && echo ok || echo no); \
	  MG=$$(docker exec bench_mongo bash -lc 'mongosh --quiet --eval "db.runCommand({ping:1}).ok" 2>/dev/null | grep -q 1 && echo ok || echo no'); \
	  printf "."; \
	  if [ "$$PG" = "ok" ] && [ "$$MG" = "ok" ]; then echo "\npostgres & mongo up"; exit 0; fi; \
	  sleep 1; \
	done; \
	echo "\nservices not ready" && exit 1

bench-setup:
	@docker compose -f $(BENCH_COMPOSE) build bench
	@docker compose -f $(BENCH_COMPOSE) up -d --remove-orphans mongo postgres
	@$(MAKE) bench-wait
	@$(MAKE) bench-mongo-init
	@echo "Bench stack ready"

# ---- Bench common runner (avoid pip install on every run) ----
define RUN_BENCH
	@docker compose -f $(BENCH_COMPOSE) run --rm bench bash -lc '$(1)'
endef

# ---- Bench seed ----
bench-seed-ratings:
	$(call RUN_BENCH, MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/loaders/seed_mongo.py && \
	  python scripts/bench/loaders/seed_pg.py)

bench-seed-reviews:
	$(call RUN_BENCH, \
	  FILM_ID="$(FILM_ID)" \
	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/loaders/seed_reviews.py && \
	  python scripts/bench/loaders/seed_mongo_reviews_doc.py && \
	  python scripts/bench/loaders/seed_pg_reviews_norm.py \
	)
	@docker exec bench_postgres psql -U bench -d bench -c "CREATE OR REPLACE VIEW bench_review_votes AS SELECT * FROM review_votes;" >/dev/null
	@echo "reviews seeded (Mongo: bench_reviews & reviews_doc; PG: reviews & bench_reviews). View bench_review_votes ready."

# ---- Bench runs ----
bench-ratings:
	$(call RUN_BENCH, OPS=$(OPS) CONCURRENCY=$(CONCURRENCY) \
	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/runs/ratings.py)

bench-reviews-top:
	$(call RUN_BENCH, OPS=$(OPS) CONCURRENCY=$(CONCURRENCY) FILM_ID="$(FILM_ID)" \
	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/runs/reviews_top_tail.py)

bench-topn:
	$(call RUN_BENCH, OPS=$(OPS) CONCURRENCY=$(CONCURRENCY) TOPN=$(TOPN) \
	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/runs/topn_many_films.py)

bench-doc-vs-rel:
	$(call RUN_BENCH, OPS=$(OPS) CONCURRENCY=$(CONCURRENCY) TOPN=$(TOPN) K_LAST=$(K_LAST) \
	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/runs/doc_vs_rel.py)

# ---- Bench: save logs ----
bench-ratings-save:
	@mkdir -p $(REPORTS_DIR)
	@$(MAKE) bench-ratings | tee $(REPORTS_DIR)/ratings.log

bench-reviews-top-save:
	@mkdir -p $(REPORTS_DIR)
	@$(MAKE) bench-reviews-top | tee $(REPORTS_DIR)/reviews_top_tail.log

bench-topn-save:
	@mkdir -p $(REPORTS_DIR)
	@$(MAKE) bench-topn | tee $(REPORTS_DIR)/topn_many_films.log

bench-doc-vs-rel-save:
	@mkdir -p $(REPORTS_DIR)
	@$(MAKE) bench-doc-vs-rel | tee $(REPORTS_DIR)/doc_vs_rel.log

# ---- Bench: aggregate markdown report ----
bench-report:
	@mkdir -p $(REPORTS_DIR)
	@echo "# Bench Results" > $(REPORTS_DIR)/results.md
	@echo "" >> $(REPORTS_DIR)/results.md
	@for f in ratings.log reviews_top_tail.log topn_many_films.log doc_vs_rel.log ; do \
	  if [ -f "$(REPORTS_DIR)/$$f" ]; then \
	    echo "## $${f}" >> $(REPORTS_DIR)/results.md; \
	    echo "" >> $(REPORTS_DIR)/results.md; \
	    echo "```text" >> $(REPORTS_DIR)/results.md; \
	    sed 's/\x1b\[[0-9;]*m//g' "$(REPORTS_DIR)/$$f" >> $(REPORTS_DIR)/results.md; \
	    echo "```" >> $(REPORTS_DIR)/results.md; \
	    echo "" >> $(REPORTS_DIR)/results.md; \
	  fi \
	done; \
	echo "Wrote $(REPORTS_DIR)/results.md"

# ---- Bench convenience pipelines ----
bench-seed-all:
	@$(MAKE) -s bench-seed-ratings
	@$(MAKE) -s bench-seed-reviews
	@echo "seeded ratings+reviews"

bench-run-all:
	@mkdir -p $(REPORTS_DIR)
	@$(MAKE) -s bench-ratings       | tee $(REPORTS_DIR)/ratings_$(TIMESTAMP).log
	@$(MAKE) -s bench-reviews-top   | tee $(REPORTS_DIR)/reviews_top_tail_$(TIMESTAMP).log
	@$(MAKE) -s bench-topn          | tee $(REPORTS_DIR)/topn_many_films_$(TIMESTAMP).log
	@$(MAKE) -s bench-doc-vs-rel    | tee $(REPORTS_DIR)/doc_vs_rel_$(TIMESTAMP).log
	@echo "all scenarios done"

bench-all:
	@$(MAKE) bench-setup
	@$(MAKE) bench-seed-all
	@$(MAKE) bench-run-all
	@$(MAKE) bench-report
	@echo "Bench pipeline finished"

# map for bench-run-scenario
define _SC2TARGET
ratings=bench-ratings
reviews-top=bench-reviews-top
topn=bench-topn
doc-vs-rel=bench-doc-vs-rel
endef
export _SC2TARGET
SCENARIO ?= ratings

bench-run-scenario:
	@mkdir -p $(REPORTS_DIR)
	@t=$$(echo "$$(_SC2TARGET)" | tr ' ' '\n' | grep '^$(SCENARIO)=' | cut -d= -f2); \
	if [ -z "$$t" ]; then echo "unknown SCENARIO=$(SCENARIO)"; exit 2; fi; \
	log="$(REPORTS_DIR)/$${SCENARIO}_$(TIMESTAMP).log"; \
	echo "run $$t -> $$log"; \
	$(MAKE) -s $$t | tee "$$log"
	@echo "saved log to $(REPORTS_DIR)/$(SCENARIO)_$(TIMESTAMP).log"

# ---- PG compatibility for run-scripts (if SQL expects reviews/review_votes) ----
bench-pg-compat-views:
	@docker exec bench_postgres psql -U bench -d bench -v ON_ERROR_STOP=1 -c "\
	  DO $$ BEGIN \
	    BEGIN \
	      CREATE VIEW reviews AS SELECT * FROM bench_reviews; \
	    EXCEPTION WHEN duplicate_table THEN NULL; \
	    END; \
	    BEGIN \
	      CREATE VIEW review_votes AS SELECT * FROM bench_review_votes; \
	    EXCEPTION WHEN duplicate_table THEN NULL; \
	    END; \
	  END $$; \
	" && echo "created compatibility views (reviews, review_votes)"

# ---- Quick smoke for bench stack ----
smoke-bench:
	@docker exec bench_postgres pg_isready -U bench -d bench >/dev/null 2>&1 || (echo "pg down" && exit 1)
	@docker exec bench_mongo bash -lc 'mongosh --quiet --eval "db.hello().isWritablePrimary?1:0"' | grep -q '^1$$' || (echo "mongo not PRIMARY" && exit 1)
	@docker exec bench_postgres psql -U bench -d bench -c "SELECT 1" >/dev/null 2>&1 || (echo "pg query failed" && exit 1)
	@docker exec bench_mongo mongosh --quiet --eval "db.runCommand({ping:1}).ok" | grep -q '^1$$' || (echo "mongo ping failed" && exit 1)
	@echo "smoke-bench ok"

health:
	curl -s http://localhost:8080/health | jq .

ready:
	curl -s http://localhost:8080/ready | jq .

uuid:
	@$(PY) -c "import uuid; print(uuid.uuid4())"


demo:
	@USER_ID=$$($(PY) -c "import uuid; print(uuid.uuid4())"); \
	FILM_ID=$$($(PY) -c "import uuid; print(uuid.uuid4())"); \
	echo "User: $$USER_ID"; \
	echo "Film: $$FILM_ID"; \
	echo ""; \
	echo "1) PUT rating=8"; \
	curl -s -X PUT "$(BASE_URL)/api/v1/ratings/$$FILM_ID?score=8" \
	  -H "$(USER_HEADER): $$USER_ID"; \
	echo ""; \
	echo "2) PUT like=+1"; \
	curl -s -X PUT "$(BASE_URL)/api/v1/likes/$$FILM_ID" \
	  -H "Content-Type: application/json" \
	  -H "$(USER_HEADER): $$USER_ID" \
	  -d "{\"value\": 1}" -i | head -n 1; \
	echo "2.1) GET film stats after like"; \
    curl -s "$(BASE_URL)/api/v1/film-stats/$$FILM_ID"; \
    echo ""; \
	echo "3) PUT bookmark"; \
	curl -s -X PUT "$(BASE_URL)/api/v1/bookmarks/$$FILM_ID" \
	  -H "$(USER_HEADER): $$USER_ID"; \
	echo ""; \
	echo "4) POST review"; \
	REVIEW_ID=$$(curl -s -X POST "$(BASE_URL)/api/v1/reviews" \
	  -H "Content-Type: application/json" \
	  -H "$(USER_HEADER): $$USER_ID" \
	  -d "{\"film_id\":\"$$FILM_ID\",\"text\":\"Solid movie. Demo review.\"}" \
	  | $(PY) -c "import sys,json; print(json.load(sys.stdin)['review_id'])"); \
	echo "Review: $$REVIEW_ID"; \
	echo "5) Vote review up"; \
	curl -s -X POST "$(BASE_URL)/api/v1/reviews/$$REVIEW_ID/vote" \
	  -H "Content-Type: application/json" \
	  -H "$(USER_HEADER): $$USER_ID" \
	  -d "{\"value\": \"up\"}"; \
	echo ""; \
	echo "6) GET film stats (should reflect rating/like/review/vote)"; \
	curl -s "$(BASE_URL)/api/v1/film-stats/$$FILM_ID"; \
	echo ""

redis-inspect:
	@docker exec -it engagement_redis redis-cli KEYS "filmstats:*"

redis-ttl:
	@key=$$(docker exec engagement_redis redis-cli --scan --pattern "filmstats:*" | head -n 1); \
	if [ -z "$$key" ]; then echo "no filmstats:* keys"; exit 0; fi; \
	echo "$$key"; \
	docker exec engagement_redis redis-cli TTL "$$key"