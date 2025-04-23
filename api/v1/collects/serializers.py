from rest_framework import serializers

from api.v1.payments.serializers import PaymentListSerializer
from collects.models import Collect


class CollectSerializer(serializers.ModelSerializer):
    # write_only so it doesn’t echo the raw file back
    cover = serializers.ImageField(write_only=True, required=False)
    # read_only URL for clients to display
    cover_url = serializers.SerializerMethodField(read_only=True)
    payments = PaymentListSerializer(many=True, read_only=True)

    donations_count = serializers.IntegerField(read_only=True)
    successful_donations_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Collect
        read_only_fields = (
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "collected_amount",
            "donors_count",
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

    def get_cover_url(self, obj):
        request = self.context.get("request")
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        return None
