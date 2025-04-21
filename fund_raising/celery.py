import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fund_raising.settings")

app = Celery("fund_raising")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
