import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from tests.factories import UserFactory, CollectFactory, PaymentFactory


@pytest.fixture(autouse=True)
def mock_cache_delete_pattern():
    """LocMemCache doesn't have delete_pattern — mock it globally for all tests."""
    with patch("django.core.cache.cache.delete_pattern", create=True, return_value=None):
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
