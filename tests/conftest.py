import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from tests.factories import CollectFactory, PaymentFactory, UserFactory


@pytest.fixture(autouse=True)
def isolate_cache():
    """LocMemCache persists across tests in-process — start each test cold."""
    cache.clear()
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
