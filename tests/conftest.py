from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from tests.factories import CollectFactory, PaymentFactory, UserFactory


@pytest.fixture(autouse=True)
def isolate_cache():
    """LocMemCache persists across tests in-process — start each test cold."""
    cache.clear()
    yield


@pytest.fixture(autouse=True)
def mock_celery_tasks_delay():
    """Avoid running Celery tasks during tests and silence Celery eager deprecation.

    Celery 5 deprecates `CELERY_TASK_ALWAYS_EAGER`. Instead of configuring eager mode,
    we patch `.delay` on our tasks to be no-ops.
    """
    with (
        patch("collects.tasks.send_donation_email.delay", return_value=None),
        patch("payments.tasks.send_payment_email.delay", return_value=None),
    ):
        yield


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def collect_factory():
    return CollectFactory


@pytest.fixture
def payment_factory():
    return PaymentFactory


@pytest.fixture
def user_factory():
    return UserFactory
