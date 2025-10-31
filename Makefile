.PHONY: up down logs lint mypy test bench seed

up:
	docker compose -f infra/docker-compose.yml up -d

down:
	docker compose -f infra/docker-compose.yml down -v

logs:
	docker compose -f infra/docker-compose.yml logs -f api

lint:
	flake8 src --format=html --htmldir=reports/flake8

mypy:
	mypy src --html-report reports/mypy

test:
	pytest -v --disable-warnings

seed:
	docker compose exec api python scripts/seed.py

bench:
	docker compose exec api python scripts/bench_read.py
