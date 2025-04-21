# from rest_framework import serializers
# from drf_spectacular.utils import extend_schema_field, OpenApiTypes
#
# from collects.models import Collect
# from payments.serializers import PaymentSerializer
#
#
# class CollectSerializer(serializers.ModelSerializer):
#     payments = PaymentSerializer(many=True, read_only=True)
#     donors_count = serializers.IntegerField(read_only=True)
#     collected_amount = serializers.DecimalField(
#         max_digits=12, decimal_places=2, read_only=True
#     )
#
#     # Read-only field for displaying the URL
#     cover_url = serializers.SerializerMethodField(read_only=True)
#
#     # Use FileField instead of ImageField with explicit style
#     cover_upload = serializers.FileField(
#         write_only=True,
#         required=False,
#         style={'input_type': 'file'},
#         help_text="Upload an image file"
#     )
#
#     class Meta:
#         model = Collect
#         read_only_fields = ("id", "created_by", "created_at", "updated_at", "collected_amount")
#         fields = (
#             "id",
#             "title",
#             "description",
#             "occasion",
#             "goal_amount",
#             "collected_amount",
#             "donors_count",
#             "start_date",
#             "end_date",
#             "cover_upload",
#             "cover_url",
#             "is_active",
#             "created_by",
#             "created_at",
#             "updated_at",
#             "payments",
#         )
#         extra_kwargs = {
#             'cover_upload': {'write_only': True}
#         }
#
#     def get_cover_url(self, instance):
#         request = self.context.get('request')
#         if instance.cover and request:
#             return request.build_absolute_uri(instance.cover.url)
#         return None

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
