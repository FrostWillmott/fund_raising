# Group Fundraising Service

A production-ready REST API for group fundraising with JWT authentication,
image processing, cache invalidation, and asynchronous email notifications.
The project focuses on practical backend concerns: transactional safety,
permissions, query optimization, and maintainable environment-based settings.

## What's inside

**Core stack:** Django 5.2, Django REST Framework, MySQL, Redis, Celery

**Features:**
- JWT authentication via djoser + simplejwt (not mentioned in the spec)
- Separate dev/prod settings with environment-specific email, DB, and debug config
- Cover image processing: auto-resize to 1200×800, JPEG optimization, format
  validation, 2MB size limit, auto-cleanup of old files on update
- Custom permission classes with inheritance (`IsOwnerOrReadOnly` →
  `IsCollectAuthorOrReadOnly`, `IsPaymentPayerOrReadOnly`)
- `transaction.atomic` on payment creation with atomic `collected_amount`
  update via `F()` expressions
- Guard against deleting a collection that already has payments
- `transaction_id` uniqueness validation with a clear error message
- DB index on `(collect, status)` for payment queries
- Pagination with configurable `page_size`
- Realistic seed data: Faker with `ru_RU` locale, occasion-specific title/
  description templates, weighted payment amount distribution, batch inserts
- Poetry for dependency management, mypy + django-stubs for type checking,
  ruff for linting
- MailHog with MongoDB backend for email testing in dev

## Quick start

Prerequisites: Docker and Docker Compose.
```bash
git clone https://github.com/FrostWillmott/fund_raising.git
cd fund_raising
cp .env.example .env
docker compose up --build
```

| Service | URL |
|---|---|
| API | http://localhost:8000/api/v1/ |
| Swagger UI | http://localhost:8000/docs/ |
| MailHog | http://localhost:8025/ |

## Production deployment

Use the production override to run Django via Gunicorn and force production settings:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Required production env vars:
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS` (comma-separated origins)

## API

Authentication: JWT Bearer token.
```bash
# Get token
curl -X POST http://localhost:8000/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'
```

Endpoints:
```
POST   /auth/users/                  — register
POST   /auth/jwt/create/             — get token
POST   /auth/jwt/refresh/            — refresh token

GET    /api/v1/collects/             — list collections
POST   /api/v1/collects/             — create collection (with cover image)
GET    /api/v1/collects/{id}/        — collection detail with payment feed
PATCH  /api/v1/collects/{id}/        — update (owner only)
DELETE /api/v1/collects/{id}/        — delete (owner only, no payments)

GET    /api/v1/payments/             — list payments
POST   /api/v1/payments/             — make a donation
```

Full interactive docs at `/docs/`.

## Seed data
```bash
docker compose exec web python manage.py generate_test_data \
  --users 50 --collects 100 --payments 5000
```

Generates realistic Russian-language collections (birthday, wedding,
new year, other) with occasion-specific titles and descriptions, and
payments with weighted amount distribution (50% small / 30% medium /
15% large / 5% whale).

## Project structure
```
fund_raising/
├── api/v1/
│   ├── collects/     # ViewSet, serializer, cache invalidation
│   └── payments/     # ViewSet, serializer, atomic updates
├── collects/         # Model, signals, image utils, tasks
├── payments/         # Model, tasks
├── dev_tools/        # generate_test_data management command
└── fund_raising/     # Settings (base / development / production)
```

## Development
```bash
# Install git hooks (once per clone)
poetry run pre-commit install --hook-type pre-commit --hook-type pre-push

# Linting
docker compose exec web ruff check .

# Type checking
docker compose exec web mypy .

# Run hooks manually for all files
poetry run pre-commit run --all-files
```
## Tests

API tests cover core scenarios: listing and creating collections, permission
enforcement, payment creation with atomic `collected_amount` update,
duplicate `transaction_id` rejection, and delete guards.

```bash
# Run with coverage (outputs term-missing summary + htmlcov/)
pytest

# Quick run without coverage
pytest --no-cov
```
