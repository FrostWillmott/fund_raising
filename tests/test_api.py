from decimal import Decimal

import pytest
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from collects.models import Collect


@pytest.mark.django_db
class TestCollectAPI:
    def test_list_collects(self, auth_client, collect_factory):
        # Create some collects
        collect_factory.create_batch(3)

        url = reverse("v1:collect-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Pagination might be active
        if "results" in response.data:
            assert len(response.data["results"]) >= 3
        else:
            assert len(response.data) >= 3

    def test_create_collect(self, auth_client):
        url = reverse("v1:collect-list")
        data = {
            "title": "New Fund",
            "occasion": "birthday",
            "description": "Celebrating birthday",
            "goal_amount": "5000.00",
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Collect.objects.filter(title="New Fund").exists()
        assert response.data["title"] == "New Fund"

    def test_unauthorized_access(self, api_client):
        url = reverse("v1:collect-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_non_owner_cannot_update_collect(
        self, auth_client, user_factory, collect_factory
    ):
        collect = collect_factory(created_by=user_factory())
        url = reverse("v1:collect-detail", kwargs={"id": collect.id})
        response = auth_client.patch(url, {"title": "Changed title"})

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_owner_cannot_delete_collect(
        self, auth_client, user_factory, collect_factory
    ):
        collect = collect_factory(created_by=user_factory())
        url = reverse("v1:collect-detail", kwargs={"id": collect.id})
        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_delete_collect_with_payments(
        self, auth_client, user, collect_factory, payment_factory
    ):
        collect = collect_factory(created_by=user)
        payment_factory(collect=collect)
        url = reverse("v1:collect-detail", kwargs={"id": collect.id})

        response = auth_client.delete(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert Collect.objects.filter(id=collect.id).exists()

    def test_list_collects_contains_annotated_donors_count(
        self, auth_client, user_factory, collect_factory, payment_factory
    ):
        collect = collect_factory()
        first_donor = user_factory()
        second_donor = user_factory()
        payment_factory(collect=collect, payer=first_donor, status="completed")
        payment_factory(collect=collect, payer=first_donor, status="completed")
        payment_factory(
            collect=collect, payer=second_donor, status="completed"
        )

        cache.clear()
        url = reverse("v1:collect-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        items = response.data.get("results", response.data)
        item = next(obj for obj in items if obj["id"] == collect.id)
        assert item["donors_count"] == 2


@pytest.mark.django_db
class TestPaymentAPI:
    def test_create_payment_updates_collect(
        self, auth_client, collect_factory
    ):
        collect = collect_factory(
            goal_amount=Decimal("1000.00"), collected_amount=Decimal("0.00")
        )
        url = reverse("v1:payment-list")
        data = {
            "collect": collect.id,
            "amount": "150.00",
            "transaction_id": "test_unique_id_123",
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED

        collect.refresh_from_db()
        assert collect.collected_amount == Decimal("150.00")

    def test_payment_list(self, auth_client, payment_factory):
        payment_factory.create_batch(2)
        url = reverse("v1:payment-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        if "results" in response.data:
            assert len(response.data["results"]) == 2
        else:
            assert len(response.data) == 2

    def test_duplicate_transaction_id_returns_400(
        self, auth_client, collect_factory
    ):
        collect = collect_factory()
        url = reverse("v1:payment-list")
        data = {
            "collect": collect.id,
            "amount": "120.00",
            "transaction_id": "duplicate_tx_001",
        }

        first_response = auth_client.post(url, data)
        second_response = auth_client.post(url, data)

        assert first_response.status_code == status.HTTP_201_CREATED
        assert second_response.status_code == status.HTTP_400_BAD_REQUEST

    def test_payment_patch_is_not_allowed_for_other_user(
        self, auth_client, user_factory, payment_factory
    ):
        other_client = APIClient()
        other_client.force_authenticate(user=user_factory())
        payment = payment_factory()
        url = reverse("v1:payment-detail", kwargs={"id": payment.id})

        response = other_client.patch(url, {"amount": "999.00"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
