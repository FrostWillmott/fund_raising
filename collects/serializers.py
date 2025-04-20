from rest_framework import serializers

from collects.models import Collect
from payments.serializers import PaymentSerializer


class CollectSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    donors_count = serializers.IntegerField(read_only=True)
    collected_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Collect
        read_only_fields = ("id", "created_by", "created_at", "updated_at", "collected_amount")
        fields = (
            "id",
            "title",
            "description",
            "occasion",
            "goal_amount",
            "collected_amount",
            "donors_count",
            "start_date",
            "end_date",
            "cover",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
            "payments",
        )

    def validate_goal_amount(self, value):
        """Цель должна быть > 0 (или None — для бесконечного сбора)."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("goal_amount must be positive")
        return value
