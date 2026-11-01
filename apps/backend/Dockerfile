FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY apps/backend/pyproject.toml apps/backend/uv.lock ./apps/backend/
COPY apps/backend ./apps/backend
RUN uv sync --project apps/backend --frozen --no-dev
COPY static ./static
COPY data ./data

ENV PYTHONPATH=/app/apps/backend

EXPOSE 8000

CMD ["uv", "run", "--project", "apps/backend", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
