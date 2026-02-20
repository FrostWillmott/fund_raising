from fund_raising.development import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db_test.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

if not hasattr(CACHES, 'delete_pattern'):
    from django.core.cache import cache
    cache.delete_pattern = lambda pattern, **kwargs: None

CELERY_TASK_ALWAYS_EAGER = True
