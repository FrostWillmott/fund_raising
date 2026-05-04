import pymysql  # type: ignore[import-untyped]

from .celery import app as celery_app

__all__ = ("celery_app",)
pymysql.install_as_MySQLdb()
