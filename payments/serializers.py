from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Payment serializer with the following constraints:
    - Fields 'id', 'status', 'transaction_id', 'payment_date' are read-only
    - Field 'amount' cannot be modified after payment creation
    - Field 'collect' cannot be changed after payment creation
    """

    transaction_id = serializers.CharField(max_length=255)

    class Meta:
        model = Payment
        read_only_fields = ("id", "status", "transaction_id", "payment_date")
        fields = (
            "id",
            "collect",
            "amount",
            "status",
            "transaction_id",
            "payment_date",
            "metadata",
        )

    def validate_transaction_id(self, value):
        if self.instance is None and Payment.objects.filter(transaction_id=value).exists():
            raise serializers.ValidationError("transaction_id must be unique")
        return value

    def validate(self, data):
        if self.instance:  # Only in update operations
            protected_fields = ["amount", "transaction_id"]
            for field in protected_fields:
                if field in data:
                    raise serializers.ValidationError({
                        field: f"Поле '{field}' нельзя изменить после создания платежа"
                    })
        return data
