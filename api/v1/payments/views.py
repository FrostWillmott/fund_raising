from django.core.cache import cache
from django.db import transaction
from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions, viewsets

from api.pagination import ResultsSetPagination
from api.permissions import IsPaymentPayerOrReadOnly
from api.v1.payments.serializers import PaymentSerializer
from payments.models import Payment
from payments.tasks import send_payment_email

_CACHE_TTL = 60


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPaymentPayerOrReadOnly,
    )
    lookup_field = "id"
    http_method_names = "get", "post"
    pagination_class = ResultsSetPagination

    def get_queryset(self) -> QuerySet[Payment]:
        return Payment.objects.select_related("collect", "payer")

    @transaction.atomic
    def perform_create(self, serializer: PaymentSerializer) -> None:
        payment = serializer.save(
            payer=self.request.user,
            status=Payment.Status.COMPLETED,
        )
        if payment.payer and payment.payer.email and payment.collect:
            transaction.on_commit(
                lambda: send_payment_email.delay(
                    amount=str(payment.amount),
                    title=payment.collect.title,
                    email=payment.payer.email,
                )
            )
        transaction.on_commit(lambda: cache.delete_pattern("*collects*"))  # type: ignore[attr-defined]
        transaction.on_commit(lambda: cache.delete_pattern("*payments*"))  # type: ignore[attr-defined]

    @method_decorator(cache_page(_CACHE_TTL))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(_CACHE_TTL))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
