import os

os.environ.setdefault("SECRET_KEY", "test-only-not-secret")

from fund_raising.development import *  # noqa

SECRET_KEY = "test-only-not-secret"

if os.getenv("MYSQL_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("MYSQL_DATABASE", "fund_raising_test"),
            "USER": os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
            "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
            "PORT": os.environ.get("MYSQL_PORT", "3306"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db_test.sqlite3",
        }
    }

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Run Celery tasks synchronously during tests so side-effects (cover image
# processing, email) are observable without a live broker.
CELERY_TASK_ALWAYS_EAGER = True

# Console backend writes email bodies to stdout instead of connecting to
# MailHog, so email tasks can run eagerly in tests without external services.
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
