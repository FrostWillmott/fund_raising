from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import exceptions, permissions, viewsets

from api.cache import invalidate_cache
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
        try:
            # Nested atomic (savepoint): an IntegrityError from a concurrent
            # duplicate transaction_id must not poison the outer transaction.
            with transaction.atomic():
                payment = serializer.save(
                    payer=self.request.user,
                    status=Payment.Status.COMPLETED,
                )
        except IntegrityError as exc:
            raise exceptions.ValidationError(
                {"transaction_id": "transaction_id must be unique"}
            ) from exc
        if payment.payer and payment.payer.email and payment.collect:
            transaction.on_commit(
                lambda: send_payment_email.delay(
                    amount=str(payment.amount),
                    title=payment.collect.title,
                    email=payment.payer.email,
                )
            )
        transaction.on_commit(lambda: invalidate_cache("collects", "payments"))

    @method_decorator(cache_page(_CACHE_TTL, key_prefix="payments"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(_CACHE_TTL, key_prefix="payments"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
