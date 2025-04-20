from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from api.v1.urls import urlpatterns as api_v1_urls

cache_timeout = 0 if settings.DEBUG else 3600

schema_view_api_v1 = get_schema_view(
    openapi.Info(
        title="API Documentation",
        default_version="v1",
        description="API Documentation for Fundraising Project",
        contact=openapi.Contact(email="i.tkachenko@zohomail.eu"),
    ),
    public=True,
    permission_classes=(permissions.IsAuthenticated,) if not settings.DEBUG else (permissions.AllowAny,),

)

if settings.DEBUG:
    cache_timeout = 0
else:
    cache_timeout = 3600
ui_view = schema_view_api_v1.with_ui("swagger", cache_timeout=cache_timeout)
raw_view = schema_view_api_v1.without_ui(cache_timeout=cache_timeout)

urlpatterns = [
    path("admin/", admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path("api/v1/", include((api_v1_urls, "api"), namespace="v1")),
    path("api-auth/", include("rest_framework.urls")),
]


urlpatterns += [
    path("swagger.<str:format>/", raw_view, name="schema-json"),
    path("docs/",    ui_view,  name="schema-swagger-ui"),
]
