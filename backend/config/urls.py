"""
URL configuration for the Hospital Appointment Management System.
"""

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
)

def root_health_view(request):
    return JsonResponse({
        "status": "online",
        "service": "Hospital Appointment Management API",
        "database": "Neon PostgreSQL (Connected)",
        "docs": "/api/docs/",
        "admin": "/admin/",
        "endpoints": "/api/",
    })

urlpatterns = [
    path("", root_health_view, name="root_health"),
    path("admin/", admin.site.urls),
    # OpenAPI schema & Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # App endpoints
    path("api/", include("core.urls")),
]
