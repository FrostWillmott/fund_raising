from django.db.models import QuerySet
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions, viewsets

from api.pagination import ResultsSetPagination
from api.permissions import IsPaymentPayerOrReadOnly
from api.v1.payments.serializers import PaymentSerializer
from payments.models import Payment
from payments.services import create_payment

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

    def perform_create(self, serializer: PaymentSerializer) -> None:
        serializer.instance = create_payment(
            payer=self.request.user, **serializer.validated_data
        )

    @method_decorator(cache_page(_CACHE_TTL, key_prefix="payments"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(_CACHE_TTL, key_prefix="payments"))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
