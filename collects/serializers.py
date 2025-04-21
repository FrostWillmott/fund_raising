from rest_framework import serializers

from collects.models import Collect
from payments.serializers import PaymentListSerializer


class CollectSerializer(serializers.ModelSerializer):
    # write_only so it doesn’t echo the raw file back
    cover = serializers.ImageField(write_only=True, required=False)
    # read_only URL for clients to display
    cover_url = serializers.SerializerMethodField(read_only=True)
    payments = PaymentListSerializer(many=True, read_only=True)

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
        )

    def get_cover_url(self, obj):
        request = self.context.get("request")
        if obj.cover and request:
            return request.build_absolute_uri(obj.cover.url)
        return None
