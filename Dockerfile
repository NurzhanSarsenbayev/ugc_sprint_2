ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    TZ=UTC

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements/ ./requirements/
RUN pip install --upgrade pip && pip install -r requirements/base.txt

COPY ugc_api ./ugc_api
COPY scripts ./scripts
COPY tests ./tests
COPY pytest.ini ./pytest.ini

EXPOSE 8080

CMD ["python", "-m", "uvicorn", "ugc_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
