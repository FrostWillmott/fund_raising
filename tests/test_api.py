import os
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.cache import get_cache_key
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient

from collects.models import Collect


def _make_image(
    width: int, height: int, mode: str = "RGB", fmt: str = "JPEG"
) -> SimpleUploadedFile:
    buf = BytesIO()
    Image.new(mode, (width, height), color=(100, 150, 200)).save(
        buf, format=fmt
    )
    buf.seek(0)
    ext = "jpg" if fmt == "JPEG" else fmt.lower()
    return SimpleUploadedFile(
        f"test.{ext}", buf.read(), content_type=f"image/{fmt.lower()}"
    )


def _make_large_image() -> SimpleUploadedFile:
    """Return a valid PNG over 2 MB by storing uncompressed random pixel data."""
    raw = os.urandom(
        900 * 800 * 3
    )  # ~2.16 MB raw; PNG compress_level=0 keeps it above 2 MB
    img = Image.frombytes("RGB", (900, 800), raw)
    buf = BytesIO()
    img.save(buf, format="PNG", compress_level=0)
    buf.seek(0)
    return SimpleUploadedFile(
        "large.png", buf.read(), content_type="image/png"
    )


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

    def test_create_collect_with_end_date_in_past_returns_400(
        self, auth_client
    ):
        url = reverse("v1:collect-list")
        data = {
            "title": "New Fund",
            "occasion": "birthday",
            "end_date": (timezone.now() - timedelta(days=1)).isoformat(),
        }
        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

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

        url = reverse("v1:collect-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        items = response.data.get("results", response.data)
        item = next(obj for obj in items if obj["id"] == collect.id)
        assert item["donors_count"] == 2

    def test_created_collect_appears_in_list_immediately(
        self, auth_client, django_capture_on_commit_callbacks
    ):
        url = reverse("v1:collect-list")
        warm_response = auth_client.get(url)
        assert warm_response.status_code == status.HTTP_200_OK

        with django_capture_on_commit_callbacks(execute=True):
            create_response = auth_client.post(
                url, {"title": "Fresh Fund", "occasion": "birthday"}
            )
        assert create_response.status_code == status.HTTP_201_CREATED

        response = auth_client.get(url)
        items = response.data.get("results", response.data)
        assert any(item["title"] == "Fresh Fund" for item in items)

    def test_cache_key_contains_collects_prefix(self, auth_client):
        """Guard the key_prefix wiring: delete_pattern("*collects*") can only
        match keys that literally contain "collects" (the URL part is MD5-hashed).
        """
        url = reverse("v1:collect-list")
        assert auth_client.get(url).status_code == status.HTTP_200_OK

        request = RequestFactory().get(url)
        key = get_cache_key(request, key_prefix="collects", method="GET")
        assert key is not None
        assert "collects" in key

    def test_list_query_count_does_not_grow_with_payments(
        self,
        auth_client,
        collect_factory,
        payment_factory,
        django_assert_num_queries,
    ):
        for _ in range(3):
            payment_factory.create_batch(5, collect=collect_factory())

        cache.clear()
        url = reverse("v1:collect-list")
        # Pagination COUNT + annotated collects; payments are not fetched
        # for the list action at all.
        with django_assert_num_queries(2):
            response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_list_response_has_no_payments_key(
        self, auth_client, collect_factory, payment_factory
    ):
        payment_factory(collect=collect_factory())

        cache.clear()
        url = reverse("v1:collect-list")
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        items = response.data.get("results", response.data)
        assert items
        assert all("payments" not in item for item in items)

    def test_detail_payments_feed_is_limited(
        self, auth_client, collect_factory, payment_factory
    ):
        collect = collect_factory()
        payment_factory.create_batch(12, collect=collect)

        cache.clear()
        url = reverse("v1:collect-detail", kwargs={"id": collect.id})
        response = auth_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["payments"]) == 10


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

    def test_payment_list(self, auth_client, user, payment_factory):
        payment_factory.create_batch(2, payer=user)
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

    def test_negative_amount_returns_400(self, auth_client, collect_factory):
        collect = collect_factory()
        url = reverse("v1:payment-list")
        data = {
            "collect": collect.id,
            "amount": "-100.00",
            "transaction_id": "test_negative_amount",
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_zero_amount_returns_400(self, auth_client, collect_factory):
        collect = collect_factory()
        url = reverse("v1:payment-list")
        data = {
            "collect": collect.id,
            "amount": "0.00",
            "transaction_id": "test_zero_amount",
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_donation_to_inactive_collect_returns_400(
        self, auth_client, collect_factory
    ):
        collect = collect_factory(is_active=False)
        url = reverse("v1:payment-list")
        data = {
            "collect": collect.id,
            "amount": "100.00",
            "transaction_id": "test_inactive_collect",
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_donation_to_expired_collect_returns_400(
        self, auth_client, collect_factory
    ):
        collect = collect_factory(end_date=timezone.now() - timedelta(days=1))
        url = reverse("v1:payment-list")
        data = {
            "collect": collect.id,
            "amount": "100.00",
            "transaction_id": "test_expired_collect",
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_cannot_see_others_payments(
        self, auth_client, user_factory, payment_factory
    ):
        other_payment = payment_factory(payer=user_factory())

        list_response = auth_client.get(reverse("v1:payment-list"))
        assert list_response.status_code == status.HTTP_200_OK
        items = list_response.data.get("results", list_response.data)
        assert all(item["id"] != other_payment.id for item in items)

        retrieve_response = auth_client.get(
            reverse("v1:payment-detail", kwargs={"id": other_payment.id})
        )
        assert retrieve_response.status_code == status.HTTP_404_NOT_FOUND

    def test_null_collect_returns_400(self, auth_client):
        url = reverse("v1:payment-list")
        data = {
            "collect": None,
            "amount": "100.00",
            "transaction_id": "test_null_collect",
        }

        response = auth_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_collect_returns_400(self, auth_client):
        url = reverse("v1:payment-list")
        data = {
            "amount": "100.00",
            "transaction_id": "test_missing_collect",
        }

        response = auth_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_payment_patch_returns_405(
        self, auth_client, user_factory, payment_factory
    ):
        other_client = APIClient()
        other_client.force_authenticate(user=user_factory())
        payment = payment_factory()
        url = reverse("v1:payment-detail", kwargs={"id": payment.id})

        response = other_client.patch(url, {"amount": "999.00"})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
class TestCoverImage:
    def test_oversized_file_rejected(self, auth_client):
        url = reverse("v1:collect-list")
        data = {
            "title": "Test",
            "occasion": "other",
            "cover": _make_large_image(),
        }
        response = auth_client.post(url, data, format="multipart")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_png_cover_stored_as_jpg(self, auth_client):
        url = reverse("v1:collect-list")
        cover = _make_image(100, 100, mode="RGB", fmt="PNG")
        data = {
            "title": "PNG upload",
            "occasion": "other",
            "cover": cover,
        }
        response = auth_client.post(url, data, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["cover_url"].endswith(".jpg")

    def test_oversized_image_is_resized(self, auth_client):
        url = reverse("v1:collect-list")
        cover = _make_image(2000, 1500, fmt="JPEG")
        data = {
            "title": "Large image",
            "occasion": "other",
            "cover": cover,
        }
        response = auth_client.post(url, data, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        collect = Collect.objects.get(id=response.data["id"])
        img = Image.open(collect.cover)
        assert img.width <= 1200
        assert img.height <= 800

    def test_rgba_png_cover_stored_as_jpg(self, auth_client):
        url = reverse("v1:collect-list")
        cover = _make_image(100, 100, mode="RGBA", fmt="PNG")
        data = {
            "title": "RGBA upload",
            "occasion": "other",
            "cover": cover,
        }
        response = auth_client.post(url, data, format="multipart")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["cover_url"].endswith(".jpg")
