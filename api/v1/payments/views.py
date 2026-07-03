from django.db.models import QuerySet
from rest_framework import permissions, viewsets

from api.pagination import ResultsSetPagination
from api.permissions import IsPaymentPayerOrReadOnly
from api.v1.payments.serializers import PaymentSerializer
from payments.models import Payment
from payments.services import create_payment


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
        # Payments are private to the payer. Because the responses are
        # per-user, they must not sit behind a shared page cache either.
        return Payment.objects.select_related("collect", "payer").filter(
            payer=self.request.user
        )

    def perform_create(self, serializer: PaymentSerializer) -> None:
        serializer.instance = create_payment(
            payer=self.request.user, **serializer.validated_data
        )
