import os

from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    f"fund_raising.{os.getenv('DJANGO_ENV', 'development')}",
)

app = Celery("fund_raising")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
