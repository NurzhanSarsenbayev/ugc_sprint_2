export STATE ?= local

# ---------- Vars ----------
COMPOSE        := infra/docker-compose.yml
BENCH_COMPOSE  := infra/bench-compose.yml
API            := api
PORT           := 8080
TIMESTAMP      := $(shell date +%Y%m%d_%H%M%S)

# Тестовый DSN для pytest
MONGO_TEST_DSN := mongodb://mongo:27017/engagement_test?replicaSet=rs0

# Бенч DSN и параметры (можно переопределять: make bench-ratings OPS=50000)
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
        bench-build bench-up bench-down bench-ps bench-run \
        bench-setup bench-seed-ratings bench-seed-reviews \
        bench-ratings bench-reviews-top bench-topn bench-doc-vs-rel \
        bench-seed-all bench-run-all bench-all bench-run-scenario \
        bench-pg-compat-views smoke-bench

# ---------- Help ----------
help:
	@echo "Targets:"
	@echo "  dev               Build + Up (основной старт)"
	@echo "  up                Поднять весь стек"
	@echo "  build             Пересобрать только API-образ"
	@echo "  restart           Пересобрать и перезапустить только API"
	@echo "  down              Остановить стек (без удаления томов)"
	@echo "  clean             Остановить стек и удалить тома"
	@echo "  ps                Показать контейнеры"
	@echo "  logs              Логи API (follow)"
	@echo "  shell             Bash внутри API-контейнера"
	@echo "  test              Прогнать pytest (+создание индексов), fail-under=90"
	@echo "  lint              flake8 -> reports/flake8 (HTML)"
	@echo "  mypy              mypy -> reports/mypy (HTML)"
	@echo "  indexes           Создать индексы в Mongo"
	@echo "  dedup-bookmarks   Удалить дубликаты закладок"
	@echo "  mongo-indexes     Показать индексы коллекций"
	@echo "  sentry-test       Проверить /__sentry-test (ожидаем 204)"
	@echo "  bench-build       Собрать образ runner'а бенчей со всеми зависимостями"
	@echo "  bench-up          Поднять стенд бенчей (mongo+postgres)"
	@echo "  bench-down        Уронить стенд бенчей и удалить тома"
	@echo "  bench-ps          Показать контейнеры стенда бенчей"
	@echo "  bench-run         Выполнить bench-команду: make bench-run CMD='...'"
	@echo "  bench-setup       Поднять стенд бенчей и подготовить rs0"
	@echo "  bench-seed-ratings Засидить рейтинги в обе БД"
	@echo "  bench-seed-reviews Засидить рецензии (Mongo doc + PG norm)"
	@echo "  bench-ratings     Запустить сценарий бенча рейтингов"
	@echo "  bench-reviews-top Запустить сценарий top-20 + tail-5"
#	@echo "  bench-topn        Топ-N по многим фильмам"
	@echo "  bench-doc-vs-rel  Документ против реляции (Mongo vs PG)"
	@echo "  bench-seed-all    Засидить все наборы данных для бенчей"
	@echo "  bench-run-all     Запустить все сценарии бенчмарков"
	@echo "  bench-all         setup -> seed-all -> run-all -> report"
	@echo "  bench-run-scenario SCENARIO={ratings|reviews-top|topn|doc-vs-rel}"
	@echo "  bench-pg-compat-views Создать совместимые вьюхи reviews/review_votes в PG"
	@echo "  smoke-bench       Быстрый смоук стенда бенчей (pg+mongo PRIMARY)"

# ---------- Core lifecycle ----------
dev:
	@echo "🔧 Building & 🚀 Starting..."
	@docker compose -f $(COMPOSE) up -d --build && echo "✅ Ready on http://localhost:$(PORT)"

up:
	@echo "🚀 Starting containers..."
	@docker compose -f $(COMPOSE) up -d && echo "✅ All containers started"

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
.PHONY: elk-up elk-down elk-logs elk-restart

elk-up:  ## Запустить стек ELK (Elastic + Kibana + Logstash + Filebeat)
	@echo "🚀 Starting ELK stack..."
	docker compose -f infra/docker-compose.yml --profile elk up -d elasticsearch kibana logstash filebeat
	@echo "✅ ELK started: http://localhost:5601"

elk-down:  ## Остановить стек ELK и удалить контейнеры
	@echo "🧹 Stopping ELK stack..."
	docker compose -f infra/docker-compose.yml --profile elk down --remove-orphans
	@echo "✅ ELK stopped."

elk-logs:  ## Смотреть логи Logstash и Filebeat
	@echo "📜 Tailing ELK logs..."
	docker compose -f infra/docker-compose.yml logs -f logstash filebeat

elk-restart:  ## Перезапустить Logstash и Filebeat (при изменении конфигов)
	@echo "♻️ Restarting Logstash and Filebeat..."
	docker compose -f infra/docker-compose.yml restart logstash filebeat
	@echo "✅ ELK pipeline restarted."
# ---------- Quality / Tests ----------
lint:
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
	  export MONGO_DSN="$(MONGO_TEST_DSN)"; \
	  python scripts/create_indexes.py; \
	  pytest -v --disable-warnings \
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
	  echo "✅ Sentry test event sent (204)" || \
	  (echo "❌ Sentry test failed (service down or DSN not set?)" && exit 1)

# ---------- Bench: build & control ----------
bench-build:
	@docker compose -f $(BENCH_COMPOSE) build bench && echo "✅ bench image built"

bench-up:
	@docker compose -f $(BENCH_COMPOSE) up -d --remove-orphans mongo postgres && echo "✅ Bench stack up"

bench-down:
	@docker compose -f $(BENCH_COMPOSE) down -v --remove-orphans || true
	@echo "🧹 Bench stack down & volumes removed"

bench-ps:
	@docker compose -f $(BENCH_COMPOSE) ps

bench-run:
	@test -n "$(CMD)" || (echo "Usage: make bench-run CMD='<command inside bench>'" && exit 2)
	@docker compose -f $(BENCH_COMPOSE) run --rm --remove-orphans bench bash -lc '$(CMD)'

# ---- Bench helpers ----
bench-mongo-init:
	@docker exec bench_mongo mongosh --quiet /scripts/bench/mongo-rs-init.js && \
	  echo "✅ rs0 PRIMARY ready" || (echo "❌ rs-init failed" && exit 1)

bench-wait:
	@printf "⏳ waiting for postgres & mongo "
	@for i in $$(seq 1 60); do \
	  PG=$$(docker exec bench_postgres pg_isready -U bench -d bench >/dev/null 2>&1 && echo ok || echo no); \
	  MG=$$(docker exec bench_mongo bash -lc 'mongosh --quiet --eval "db.runCommand({ping:1}).ok" 2>/dev/null | grep -q 1 && echo ok || echo no'); \
	  case $$((i%4)) in 1) printf "." ;; 2) printf "." ;; 3) printf "." ;; 0) printf "." ;; esac; \
	  if [ "$$PG" = "ok" ] && [ "$$MG" = "ok" ]; then echo "\n✅ postgres & mongo up"; exit 0; fi; \
	  sleep 1; \
	done; \
	echo "\n❌ services not ready" && exit 1

bench-build:
	@docker compose -f $(BENCH_COMPOSE) build bench

bench-setup:
	@docker compose -f $(BENCH_COMPOSE) build bench        # <— соберём bench-образ
	@docker compose -f $(BENCH_COMPOSE) up -d --remove-orphans mongo postgres
	@$(MAKE) bench-wait
	@$(MAKE) bench-mongo-init
	@echo "✅ Bench stack ready"

# ---- Bench common runner (без pip install на каждый запуск) ----
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
	@echo "✅ reviews seeded (Mongo: bench_reviews & reviews_doc; PG: reviews & bench_reviews). View bench_review_votes ready."

# ---- Bench runs ----
bench-ratings:
	$(call RUN_BENCH, OPS=$(OPS) CONCURRENCY=$(CONCURRENCY) \
	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/runs/ratings.py)

bench-reviews-top:
	$(call RUN_BENCH, OPS=$(OPS) CONCURRENCY=$(CONCURRENCY) FILM_ID="$(FILM_ID)" \
	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
	  python scripts/bench/runs/reviews_top_tail.py)

#bench-topn:
#	$(call RUN_BENCH, OPS=$(OPS) CONCURRENCY=$(CONCURRENCY) TOPN=$(TOPN) \
#	  MONGO_DSN="$(MONGO_BENCH_DSN)" PG_DSN="$(PG_BENCH_DSN)" \
#	  python scripts/bench/runs/topn_many_films.py)

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
	echo "✅ Wrote $(REPORTS_DIR)/results.md"

# ---- Bench convenience pipelines ----
bench-seed-all:
	@$(MAKE) -s bench-seed-ratings
	@$(MAKE) -s bench-seed-reviews
	@echo "✅ seeded ratings+reviews"

bench-run-all:
	@mkdir -p $(REPORTS_DIR)
	@$(MAKE) -s bench-ratings       | tee $(REPORTS_DIR)/ratings_$(TIMESTAMP).log
	@$(MAKE) -s bench-reviews-top   | tee $(REPORTS_DIR)/reviews_top_tail_$(TIMESTAMP).log
	@$(MAKE) -s bench-topn          | tee $(REPORTS_DIR)/topn_many_films_$(TIMESTAMP).log
	@$(MAKE) -s bench-doc-vs-rel    | tee $(REPORTS_DIR)/doc_vs_rel_$(TIMESTAMP).log
	@echo "✅ all scenarios done"

bench-all:
	@$(MAKE) bench-setup
	@$(MAKE) bench-seed-all
	@$(MAKE) bench-run-all
	@$(MAKE) bench-report
	@echo "🎯 Bench pipeline finished"

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
	if [ -z "$$t" ]; then echo "❌ unknown SCENARIO=$(SCENARIO)"; exit 2; fi; \
	log="$(REPORTS_DIR)/$${SCENARIO}_$(TIMESTAMP).log"; \
	echo "▶ run $$t -> $$log"; \
	$(MAKE) -s $$t | tee "$$log"
	@echo "✅ saved log to $(REPORTS_DIR)/$(SCENARIO)_$(TIMESTAMP).log"

# ---- PG совместимость для run-скриптов (если SQL ждёт reviews/review_votes) ----
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
	" && echo "✅ created compatibility views (reviews, review_votes)"

# ---- Quick smoke for bench stack ----
smoke-bench:
	@docker exec bench_postgres pg_isready -U bench -d bench >/dev/null 2>&1 || (echo "❌ pg down" && exit 1)
	@docker exec bench_mongo bash -lc 'mongosh --quiet --eval "db.hello().isWritablePrimary?1:0"' | grep -q '^1$$' || (echo "❌ mongo not PRIMARY" && exit 1)
	@docker exec bench_postgres psql -U bench -d bench -c "SELECT 1" >/dev/null 2>&1 || (echo "❌ pg query" && exit 1)
	@docker exec bench_mongo mongosh --quiet --eval "db.runCommand({ping:1}).ok" | grep -q '^1$$' || (echo "❌ mongo ping" && exit 1)
	@echo "✅ smoke-bench ok"
