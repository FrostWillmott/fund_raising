from django.core.cache import cache
from django.db import transaction
from django.db.models import F, QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions, viewsets

from api.pagination import ResultsSetPagination
from api.permissions import IsPaymentPayerOrReadOnly
from api.v1.payments.serializers import PaymentSerializer
from collects.models import Collect
from payments.models import Payment
from payments.tasks import send_payment_email


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = (permissions.IsAuthenticated, IsPaymentPayerOrReadOnly,)
    lookup_field = "id"
    http_method_names = "get", "post"
    pagination_class = ResultsSetPagination

    def get_queryset(self) -> QuerySet[Payment]:
        return Payment.objects.select_related("collect", "payer")

    @transaction.atomic
    def perform_create(self, serializer: PaymentSerializer) -> None:
        payment = serializer.save(payer=self.request.user)
        payment.status = Payment.Status.COMPLETED
        payment.save(update_fields=["status"])
        Collect.objects.filter(id=payment.collect_id).update(
            collected_amount=F("collected_amount") + payment.amount
        )
        if payment.payer and payment.payer.email:
            send_payment_email.delay(
                amount=str(payment.amount),
                title=payment.collect.title,
                email=payment.payer.email,
            )
        cache_key = f"view_collect_{payment.collect_id}"
        cache.delete(cache_key)
        cache.delete("view_collect_list")

    @method_decorator(cache_page(60*1))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60*1))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
