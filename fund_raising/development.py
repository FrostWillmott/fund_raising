from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += [
    'django_extensions',
    'dev_tools.apps.DevToolsConfig',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 5,
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'