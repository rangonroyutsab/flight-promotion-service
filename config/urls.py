from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

urlpatterns = [
    path("health", lambda r: JsonResponse({"status": "ok"})),
    path("admin/", admin.site.urls),
    path("api/v1/promotions/", include("apps.promotions.api.urls")),
]
