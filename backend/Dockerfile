# Stage 1: Builder — install Python dependencies
FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY pyproject.toml .

# Create a minimal package so pip can resolve the project deps
RUN mkdir -p app && touch app/__init__.py \
    && pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /install/bin /usr/local/bin

WORKDIR /app

# Copy application code and config
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY pyproject.toml ./

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
