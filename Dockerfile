FROM python:3.13.13-slim AS builder

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
     build-essential default-libmysqlclient-dev gcc \
 && pip install --no-cache-dir pip==24.0 poetry==2.1.1

WORKDIR /app

COPY pyproject.toml poetry.lock README.md LICENSE /app/

RUN poetry config virtualenvs.create true \
 && poetry config virtualenvs.in-project true \
 && poetry install --no-interaction --no-ansi --no-root --only main


FROM python:3.13.13-slim AS runtime

RUN apt-get update \
 && apt-get install -y --no-install-recommends default-libmysqlclient-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"

COPY . /app/

ENV PYTHONUNBUFFERED=1
ENV DJANGO_ENV=development
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["gunicorn", "fund_raising.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
