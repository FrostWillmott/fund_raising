# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run tests with coverage (default — requires no external services)
pytest

# Run tests without coverage
pytest --no-cov

# Run a single test file or test function
pytest tests/test_api.py::TestCollects::test_create_collect

# Lint
ruff check .

# Type check
mypy .

# Run hooks manually across all files
poetry run pre-commit run --all-files
```

Docker-based commands (require a running stack):
```bash
# Start full dev stack (MySQL, Redis, Celery, MailHog)
docker compose up --build

# Seed data
docker compose exec web python manage.py generate_test_data --users 50 --collects 100 --payments 5000
```

## Settings layout

`fund_raising/` holds four settings files:
- `base.py` — shared config; reads env vars for DB, Redis, Celery, JWT
- `development.py` — extends base; adds MailHog email backend, `DEBUG=True`
- `production.py` — extends base; Gunicorn-ready, tighter security
- `test_settings.py` — extends development; swaps MySQL → SQLite (`db_test.sqlite3`), swaps Redis cache → `LocMemCache`

`pytest.ini` pins `DJANGO_SETTINGS_MODULE = fund_raising.test_settings`, so tests run without Docker.

## Architecture

The API layer (`api/v1/`) is thin: ViewSets + serializers only. Business logic lives in the domain apps.

**`collects/`**
- `models.py` — `Collect` model; image validated for extension and 2 MB size limit
- `signals.py` — `pre_save` triggers `process_cover_image` (resize to 1200×800, JPEG optimisation) on cover change
- `tasks.py` — Celery task: email to collect author on creation
- `utils.py` — image processing implementation

**`payments/`**
- `models.py` — `Payment.save()` increments `Collect.collected_amount` via `F()` expression on first completed save; DB index on `(collect, status)`
- `tasks.py` — Celery task: email to payer on donation

**`api/v1/collects/views.py`** — `CollectViewSet`:
- List/retrieve responses cached for 60 s; cache key pattern `*collects*` is invalidated on any write via `transaction.on_commit`
- `perform_destroy` raises `ValidationError` if the collect has payments
- `perform_create` fires the Celery email task inside `transaction.on_commit`

**`api/v1/payments/views.py`** — `PaymentViewSet`:
- POST only (no PATCH/PUT/DELETE); status is forced to `COMPLETED` at creation
- Also invalidates `*payments*` and `*collects*` cache patterns on commit

**`api/permissions.py`** — `IsOwnerOrReadOnly` base class; subclasses swap the owner field (`created_by` for collects, `payer` for payments).

**`dev_tools/`** — `generate_test_data` management command; uses Faker (`ru_RU`) with occasion-specific templates and weighted payment amounts.

## Key constraints

- `transaction_id` on `Payment` is unique; duplicates surface as a DRF validation error.
- Deleting a `Collect` with existing payments is blocked at the view layer.
- Cover images are auto-cleaned by `django-cleanup` on model delete/update.
- Cache invalidation uses `cache.delete_pattern` (django-redis glob support); this is typed as `# type: ignore[attr-defined]` throughout since django-redis extends the standard cache interface.
