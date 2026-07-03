from django.utils import timezone
from rest_framework import serializers

from api.v1.payments.serializers import PaymentListSerializer
from collects.models import Collect
from collects.validators import validate_file_size


class CollectSerializer(serializers.ModelSerializer):
    cover = serializers.ImageField(
        write_only=True, required=False, validators=[validate_file_size]
    )
    cover_url = serializers.SerializerMethodField(read_only=True)
    payments = PaymentListSerializer(many=True, read_only=True)

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
            "payments",
            "donations_count",
            "successful_donations_count",
        )
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
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
            "payments",
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
