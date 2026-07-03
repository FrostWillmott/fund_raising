from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from collects.models import Collect
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    transaction_id = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal("0.01")
    )
    # The model FK is nullable, but the API must not accept orphan
    # payments: required and non-null here.
    collect = serializers.PrimaryKeyRelatedField(
        queryset=Collect.objects.all()
    )

    class Meta:
        model = Payment
        read_only_fields = ("id", "status", "payment_date")
        fields = (
            "id",
            "collect",
            "amount",
            "status",
            "transaction_id",
            "payment_date",
            "metadata",
        )

    def validate_transaction_id(self, value: str) -> str:
        if (
            self.instance is None
            and Payment.objects.filter(transaction_id=value).exists()
        ):
            raise serializers.ValidationError("transaction_id must be unique")
        return value

    def validate_collect(self, value: Collect) -> Collect:
        if not value.is_active or (
            value.end_date and value.end_date < timezone.now()
        ):
            raise serializers.ValidationError(
                "This collect is not accepting donations."
            )
        return value


class PaymentListSerializer(serializers.ModelSerializer):
    donor_name = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ("amount", "payment_date", "donor_name")

    def get_donor_name(self, obj):
        if obj.payer:
            full_name = f"{obj.payer.first_name} {obj.payer.last_name}".strip()
            return full_name or obj.payer.username
        return "Anonymous"
