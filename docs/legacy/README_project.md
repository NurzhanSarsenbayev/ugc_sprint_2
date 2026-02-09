---

# 🎬 UGC Analytics — Спринт 9

### *Исследование хранилища и нагрузочное тестирование*

---
> Archived (RU). Outdated sprint-era notes kept for history.
> The current documentation is EN-only under `docs/`.
## 📘 Цель

В этом спринте завершается блок **UGC** (лайки, закладки, рецензии, рейтинги).
Необходимо сравнить **MongoDB** и **PostgreSQL** на объёме данных ≥ 10 млн записей,
провести нагрузочное тестирование и сделать вывод о выборе хранилища.
Также выполняется интеграция **ELK**, **Sentry** и **CI/CD (GitHub Actions)**.

---

## ⚙️ Архитектура и окружение

* **FastAPI + Motor + PyMongo + Psycopg 3.2** — сервис и утилиты.
* **MongoDB 7.0 (rs0)** — хранилище UGC-сущностей.
* **PostgreSQL 16** — база для сравнительного тестирования.
* **Docker Compose** — инфраструктура (infra/bench-compose.yml).
* **ELK Stack + Sentry** — наблюдаемость и логирование.
* **CI/CD — GitHub Actions** с линтерами, тестами и Telegram-уведомлениями.

---

## 📊 Результаты исследования

|  №  | Сценарий                                   | Mongo p50/p95 | Postgres p50/p95 | Вывод                             |
| :-: | ------------------------------------------ | ------------- | ---------------- | --------------------------------- |
|  1  | Upsert + Get + Agg (рейтинги / лайки)      | ≈ 29 / 40 мс  | ≈ 1.7 / 2.1 мс   | Postgres быстрее ≈20×             |
|  2  | Рецензии (top-20 + последние 5)            | ≈ 7 / 14 мс   | ≈ 6 / 8 мс       | Сравнимо                          |
|  3  | Document vs Relational (вложенные массивы) | ≈ 23 / 44 мс  | ≈ 2.5 / 3.3 мс   | Pg быстрее                        |
|  4  | Top-N по многим фильмам (аналитика)        | —             | —                | Pg оптимален для JOIN / агрегаций |

---

### 💡 Выводы

1. **PostgreSQL** — стабилен, предсказуем и быстрее в аналитике.
2. **MongoDB** — гибче, с атомарными `$inc` и `$push`, проще масштабировать.
3. Оптимальная архитектура:

   * UGC-данные (лайки, рецензии, закладки) → **MongoDB**
   * Аналитика и отчёты → **PostgreSQL / ClickHouse / Elasticsearch**

---

## 🧪 Как запустить бенчмарки

### 1️Запуск инфраструктуры

```bash
make bench-setup
```

Поднимает Mongo (rs0), Postgres и контейнер `ugc-bench`.

---

### 2️⃣ Сидинг данных

```bash
make bench-seed-ratings    # 1 млн рейтингов
make bench-seed-reviews    # 100 тыс рецензий
```

---

### 3️⃣ Запуск сценариев

```bash
make bench-ratings       # Upsert / Get / Agg (рейтинги)
make bench-reviews-top   # Top-20 + Tail-5 (рецензии)
make bench-doc-vs-rel    # Документная vs реляционная модель
```

Для кастомного запуска можно использовать:

```bash
make bench-run CMD='OPS=5000 CONCURRENCY=10 python scripts/bench/runs/ratings.py'
```

---

## ⚙️ Makefile — основные команды

| Команда                                            | Назначение                                      |
| -------------------------------------------------- | ----------------------------------------------- |
| `make dev`                                         | Запуск UGC API + Mongo (rs0) + Redis + Postgres |
| `make test`                                        | Запуск pytest                                   |
| `make lint`                                        | Линтер flake8 (wemake) + HTML-отчёт             |
| `make mypy`                                        | Проверка mypy + HTML-отчёт                      |
| `make fmt`                                         | Форматирование ruff                             |
| `make elk-up` / `make elk-down` / `make elk-clean` | Управление ELK стеком                           |
| `make bench-*`                                     | Управление бенчмарками (setup, seed, run)       |

---

## 📈 ELK Stack

```bash
make elk-up
```

После запуска:

* **Kibana** — [http://localhost:5601](http://localhost:5601)
* **Elasticsearch** — [http://localhost:9200](http://localhost:9200)

Filebeat → Logstash → Elasticsearch → Kibana (`logs-engagement-*`).

Очистка:

```bash
make elk-clean
```

---

## 🪲 Sentry

Добавьте в `.env`:

```bash
SENTRY_DSN=<dsn>
SENTRY_ENV=local
```

Проверка:

```bash
curl http://localhost:8080/__sentry-test
```

---

## 🤖 CI/CD (GitHub Actions)

Файл — `.github/workflows/ci.yml`

* Матрица Python 3.10 / 3.11 / 3.12
* Линтеры: `wemake-python-styleguide`, `mypy`, `ruff`
* Тесты: `pytest`
* HTML-отчёты: `reports/mypy`, `reports/flake8`
* Telegram-уведомления (Secrets: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_TO`)

Пример уведомления:

```
✅ CI PASSED — ugc_sprint_2@main
Python 3.11
Commit: abcdef1
Actor: NurzhanSarsenbayev
```

---

## 🧰 Структура проекта

```
ugc_api/                # FastAPI UGC-сервис
scripts/bench/          # Бенчмарки и сидеры для Mongo / PG
infra/                  # Docker Compose (infra, elk, bench)
tests/                  # Pytest (~93 % покрытия)
.github/workflows/      # CI-пайплайн
docs/                   # Документация проекта
```

---

## 🧠 Заключение

| Хранилище      | Преимущества                                   | Недостатки                                                     | Применение                    |
| -------------- | ---------------------------------------------- | -------------------------------------------------------------- | ----------------------------- |
| **MongoDB**    | Гибкая схема, atomic-операции, масштабирование | Переменная производительность, нет межколлекционных транзакций | лайки, рецензии, закладки     |
| **PostgreSQL** | Стабильность, индексы, SQL, агрегации          | Жёсткая схема, сложнее масштабировать                          | аналитика, отчёты, статистика |

> 💡 **Выбор:**
> MongoDB — основное хранилище UGC.
> Postgres — аналитический слой и админ-интерфейсы.

---
