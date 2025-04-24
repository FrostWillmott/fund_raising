from typing import Any
from rest_framework.request import Request

from django.core.cache import cache
from django.db import models, transaction
from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import exceptions, permissions, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from api.pagination import ResultsSetPagination
from api.permissions import IsCollectAuthorOrReadOnly
from api.v1.collects.serializers import CollectSerializer
from collects.models import Collect
from collects.tasks import send_donation_email


class CollectViewSet(viewsets.ModelViewSet):
    serializer_class = CollectSerializer
    permission_classes = (permissions.IsAuthenticated,  IsCollectAuthorOrReadOnly,)
    parser_classes = (MultiPartParser, FormParser,)
    lookup_field = "id"
    pagination_class = ResultsSetPagination

    def get_queryset(self) -> QuerySet[Collect]:
        return (
            Collect.objects.select_related("created_by")
            .prefetch_related("payments")
            .annotate(
                donations_count=models.Count("payments"),
                successful_donations_count=models.Count(
                    "payments", filter=models.Q(payments__status="completed")
                ),
            )
        )

    @transaction.atomic
    def perform_create(self, serializer) -> None:
        collect = serializer.save(created_by=self.request.user)
        author = collect.created_by
        if author.email:
            send_donation_email.delay(
                amount=str(collect.goal_amount),
                title=collect.title,
                email=author.email,
            )

        cache.delete_pattern("*collects*")

    def perform_update(self, serializer) -> None:
        serializer.save()
        cache.delete_pattern("*collects*")

    def perform_destroy(self, instance) -> None:
        if instance.payments.exists():
            raise exceptions.ValidationError(
                {
                    "detail": "Невозможно удалить сбор, в котором уже есть платежи. Сделайте его неактивным вместо удаления."
                }
            )

        instance.delete()
        cache.delete_pattern("*collects*")

    @method_decorator(cache_page(60 * 1))
    def list(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 1))
    def retrieve(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        return super().retrieve(request, *args, **kwargs)
