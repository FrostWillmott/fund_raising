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
- `validators.py` — `validate_file_size`: 2 MB limit; raises Django `ValidationError` (caught by DRF serializers, Django forms, and admin)
- `services.py` — `create_collect()` owns the creation transaction and post-commit side effects (cover processing, author email, cache invalidation)
- `tasks.py` — Celery tasks: email to collect author on creation, async cover image processing (resize to 1200×800, JPEG optimisation), periodic deactivation of expired collects
- `utils.py` — image processing implementation

**`payments/`**
- `models.py` — `Payment` model, no `save()` override; `amount` ≥ 0.01; `collect` FK is `on_delete=PROTECT`; DB index on `(collect, status)`
- `services.py` — `create_payment()` is the single owner of the payment lifecycle: transaction, forced `COMPLETED` status, `F()`-increment of `Collect.collected_amount`, `IntegrityError` → DRF 400 for concurrent duplicate `transaction_id`, post-commit email and cache invalidation. Direct ORM writes do NOT maintain the counter.
- `tasks.py` — Celery task: email to payer on donation

**`api/v1/collects/views.py`** — `CollectViewSet`:
- `CollectListSerializer` for `list` (no payments feed), `CollectDetailSerializer` for other actions (10 most recent payments via a bounded query)
- List/retrieve cached for 60 s with `cache_page(key_prefix="collects")`; writes invalidate via `invalidate_cache("collects")` inside `transaction.on_commit`
- `perform_create` delegates to `create_collect()`; `perform_destroy` raises `ValidationError` if the collect has payments

**`api/v1/payments/views.py`** — `PaymentViewSet`:
- POST only (no PATCH/PUT/DELETE); `perform_create` delegates to `create_payment()`
- Queryset is payer-scoped (`payer=request.user`) — users see only their own payments; responses are deliberately NOT page-cached (per-user data)

**`api/permissions.py`** — `IsOwnerOrReadOnly` base class; subclasses swap the owner field (`created_by` for collects, `payer` for payments).

**`dev_tools/`** — `generate_test_data` management command; uses Faker (`ru_RU`) with occasion-specific templates and weighted payment amounts.

**`fund_raising/cache.py`** — `invalidate_cache(*patterns)`: uses django-redis `delete_pattern` when available, falls back to `cache.clear()` (LocMem in tests).

**`fund_raising/utils.py`** — `safe_enqueue_task(task_delay, log_label, *args, **kwargs)`: wraps `task.delay()` so a broker outage after commit logs instead of raising a 500.

## Key constraints

- `transaction_id` on `Payment` is unique; duplicates surface as a DRF validation error (serializer check for the friendly message, `IntegrityError` catch in the service for races).
- Deleting a `Collect` with existing payments is blocked twice: friendly 400 in `perform_destroy`, `on_delete=PROTECT` at the DB level (admin/shell).
- `Collect.collected_amount` is maintained only by `payments/services.py::create_payment()`; any other write path must handle it itself.
- Celery email tasks auto-retry on `OSError`/`SMTPException` (backoff, max 3); `.delay()` calls in services are wrapped in `safe_enqueue_task` so a broker outage after commit logs instead of raising.
- Redis being down degrades reads to uncached (`IGNORE_EXCEPTIONS: True`), it must not 500.
- Cover images are auto-cleaned by `django-cleanup` on model delete/update.
