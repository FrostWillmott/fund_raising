from typing import Any

from django.db import models, transaction
from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import exceptions, permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from api.pagination import ResultsSetPagination
from api.permissions import IsCollectAuthorOrReadOnly
from api.v1.collects.serializers import (
    CollectDetailSerializer,
    CollectListSerializer,
)
from collects.models import Collect
from collects.services import create_collect
from collects.tasks import process_cover_image_task
from fund_raising.cache import invalidate_cache

_CACHE_TTL = 60


class CollectViewSet(viewsets.ModelViewSet):
    serializer_class = CollectDetailSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsCollectAuthorOrReadOnly,
    )
    parser_classes = (
        MultiPartParser,
        FormParser,
    )
    lookup_field = "id"
    pagination_class = ResultsSetPagination

    def get_serializer_class(self) -> type[BaseSerializer]:
        if self.action == "list":
            return CollectListSerializer
        return CollectDetailSerializer

    def get_queryset(self) -> QuerySet[Collect]:
        return (
            Collect.objects.select_related("created_by")
            .annotate(
                donations_count=models.Count("payments"),
                successful_donations_count=models.Count(
                    "payments", filter=models.Q(payments__status="completed")
                ),
                donors_count=models.Count("payments__payer", distinct=True),
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer) -> None:
        serializer.instance = create_collect(
            created_by=self.request.user, **serializer.validated_data
        )

    @transaction.atomic
    def perform_update(self, serializer) -> None:
        instance = serializer.instance
        cover_changed = "cover" in serializer.validated_data
        serializer.save()
        if cover_changed and instance.cover:
            transaction.on_commit(
                lambda: process_cover_image_task.delay(instance.id)
            )
        transaction.on_commit(lambda: invalidate_cache("collects"))

    @transaction.atomic
    def perform_destroy(self, instance) -> None:
        if instance.payments.exists():
            raise exceptions.ValidationError(
                {
                    "detail": "Cannot delete a collect that already has payments. Set it as inactive instead."
                }
            )

        instance.delete()
        transaction.on_commit(lambda: invalidate_cache("collects"))

    # key_prefix lands in the cache key verbatim (the URL part is MD5-hashed),
    # so invalidate_cache("collects") can actually match these entries.
    @method_decorator(cache_page(_CACHE_TTL, key_prefix="collects"))
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(_CACHE_TTL, key_prefix="collects"))
    def retrieve(
        self, request: Request, *args: Any, **kwargs: Any
    ) -> Response:
        return super().retrieve(request, *args, **kwargs)
