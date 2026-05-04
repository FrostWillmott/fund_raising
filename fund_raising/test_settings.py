import os

os.environ.setdefault("SECRET_KEY", "test-only-not-secret")

from fund_raising.development import *

SECRET_KEY = "test-only-not-secret"

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
