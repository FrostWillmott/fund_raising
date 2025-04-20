from .base import *  # noqa

DEBUG = True

INSTALLED_APPS += [
    'django_extensions',
    'dev_tools.apps.DevToolsConfig',
]

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_CACHE_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('DEV_EMAIL_HOST', 'mailhog')
EMAIL_PORT = int(os.getenv('DEV_EMAIL_PORT', 1025))
EMAIL_USE_TLS = os.getenv('DEV_EMAIL_USE_TLS', 'False').lower() == 'true'
EMAIL_HOST_USER = os.getenv('DEV_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('DEV_EMAIL_HOST_PASSWORD', '')

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.core.mail': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}