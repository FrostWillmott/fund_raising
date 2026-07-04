from typing import Any

from django.core.validators import FileExtensionValidator
from django.utils import timezone
from rest_framework import serializers

from api.v1.payments.serializers import PaymentListSerializer
from collects.models import Collect
from collects.validators import validate_file_size

# How many recent payments the detail endpoint embeds; the full feed is
# unbounded and would need a dedicated paginated endpoint.
_RECENT_PAYMENTS_LIMIT = 10


class CollectListSerializer(serializers.ModelSerializer):
    cover = serializers.ImageField(
        write_only=True,
        required=False,
        validators=[
            FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
            validate_file_size,
        ],
    )
    cover_url = serializers.SerializerMethodField(read_only=True)

    donations_count = serializers.IntegerField(read_only=True)
    successful_donations_count = serializers.IntegerField(read_only=True)
    donors_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collect
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "collected_amount",
            "start_date",
            "donations_count",
            "successful_donations_count",
        )
        fields: tuple[str, ...] = (
            "id",
            "title",
            "description",
            "occasion",
            "goal_amount",
            "collected_amount",
            "donors_count",
            "start_date",
            "end_date",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
            "cover",
            "cover_url",
            "donations_count",
            "successful_donations_count",
        )

    def get_cover_url(self, obj: Collect) -> str | None:
        request = self.context.get("request")
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        return None

    def validate(self, data: dict) -> dict:
        end_date = data.get("end_date")
        if end_date:
            start_date = (
                self.instance.start_date if self.instance else timezone.now()
            )
            if end_date <= start_date:
                raise serializers.ValidationError(
                    {"end_date": "end_date must be after start_date."}
                )
        return data


class CollectDetailSerializer(CollectListSerializer):
    payments = serializers.SerializerMethodField(read_only=True)

    class Meta(CollectListSerializer.Meta):
        fields = CollectListSerializer.Meta.fields + ("payments",)

    def get_payments(self, obj: Collect) -> list[dict[str, Any]]:
        # Single bounded query with LIMIT; sliced Prefetch is not an option
        # (Django rejects filtering a sliced prefetch queryset).
        recent = obj.payments.select_related("payer")[:_RECENT_PAYMENTS_LIMIT]
        return PaymentListSerializer(
            recent, many=True, context=self.context
        ).data
