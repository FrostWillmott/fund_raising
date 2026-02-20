import pytest
from django.urls import reverse
from rest_framework import status
from decimal import Decimal
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
            assert len(response.data["results"]) == 3
        else:
            assert len(response.data) == 3

    def test_create_collect(self, auth_client):
        url = reverse("v1:collect-list")
        data = {
            "title": "New Fund",
            "occasion": "birthday",
            "description": "Celebrating birthday",
            "goal_amount": "5000.00"
        }
        response = auth_client.post(url, data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Collect.objects.filter(title="New Fund").exists()
        assert response.data["title"] == "New Fund"

    def test_unauthorized_access(self, api_client):
        url = reverse("v1:collect-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.django_db
class TestPaymentAPI:
    def test_create_payment_updates_collect(self, auth_client, collect_factory):
        collect = collect_factory(goal_amount=Decimal("1000.00"), collected_amount=Decimal("0.00"))
        url = reverse("v1:payment-list")
        data = {
            "collect": collect.id,
            "amount": "150.00",
            "transaction_id": "test_unique_id_123"
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
