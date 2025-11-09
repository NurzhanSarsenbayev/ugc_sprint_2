FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    TZ=UTC

WORKDIR /app

# если колёса чисто питоновые — достаточно curl; иначе оставь gcc
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ugc_api ./ugc_api
COPY scripts ./scripts
COPY tests ./tests
COPY pytest.ini ./pytest.ini

EXPOSE 8080

# если код в ugc_api/main.py
CMD ["python", "-m", "uvicorn", "ugc_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
