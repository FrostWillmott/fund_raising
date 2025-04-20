from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import permissions, viewsets
from django.core.cache import cache

from collects.models import Collect
from collects.serializers import CollectSerializer
from collects.tasks import send_donation_email

class CollectViewSet(viewsets.ModelViewSet):
    serializer_class = CollectSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "id"

    def get_queryset(self):
        # donors_count сразу приходит из БД
        return (
            Collect.objects
            .select_related("created_by")
            .prefetch_related("payments")
        )

    def perform_create(self, serializer):
        collect = serializer.save(created_by=self.request.user)
        author = collect.created_by
        if author.email:
            send_donation_email.delay(
                amount=str(collect.goal_amount),
                title=collect.title,
                email=author.email,
            )

        cache.delete_pattern(f"*collects*")

    @method_decorator(cache_page(60 * 5))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
