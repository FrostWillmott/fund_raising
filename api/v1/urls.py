from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from api.v1.collects.views import CollectViewSet
from api.v1.payments.views import PaymentViewSet

app_name = "v1"

router = DefaultRouter()
router.register(r"collects", CollectViewSet, basename="collect")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = router.urls + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
