from django.contrib.gis.db.models import Collect
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.viewsets import ModelViewSet


@method_decorator(cache_page(60*5), name='list')
class CollectViewSet(ModelViewSet):
    queryset = Collect.objects.all()
    serializer_class = CollectSerializer
