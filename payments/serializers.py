from rest_framework import serializers

from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
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

    def update(self, instance, validated_data):
        for field in ("amount", "transaction_id"):
            validated_data.pop(field, None)
        return super().update(instance, validated_data)