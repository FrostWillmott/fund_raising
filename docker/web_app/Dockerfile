FROM python:3.13.2-slim

# Устанавливаем Poetry и необходимые инструменты
RUN pip install --upgrade pip virtualenv==20.26.6
RUN pip install poetry

WORKDIR /app
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
 && poetry install --without dev --no-interaction --no-ansi

COPY . /app
CMD ["poetry", "run", "gunicorn", "project_name.asgi:application", "--bind", "0.0.0.0:8000"]
