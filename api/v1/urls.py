from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

from api.v1.views import UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = router.urls + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)