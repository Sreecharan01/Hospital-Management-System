"""
URL configuration for the core app.
Mounts:
  auth/*           — register, JWT, /me
  specialties/     — SpecialtyViewSet
  doctors/         — DoctorViewSet
  slots/           — AvailabilitySlotViewSet
  appointments/    — AppointmentViewSet
  records/         — MedicalRecordViewSet
  notifications/   — NotificationViewSet
  admin/stats/     — AdminStatsView
  admin/announce/  — AdminAnnounceView
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views

# DRF Router
router = DefaultRouter()
router.register("specialties", views.SpecialtyViewSet, basename="specialty")
router.register("doctors", views.DoctorViewSet, basename="doctor")
router.register("slots", views.AvailabilitySlotViewSet, basename="slot")
router.register("appointments", views.AppointmentViewSet, basename="appointment")
router.register("records", views.MedicalRecordViewSet, basename="record")
router.register("notifications", views.NotificationViewSet, basename="notification")

urlpatterns = [
    # Health check
    path("health/", views.health_check, name="health-check"),

    # Auth
    path("auth/register/", views.register, name="auth-register"),
    path("auth/token/", views.CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("auth/me/", views.me, name="auth-me"),

    # Admin
    path("admin/stats/", views.AdminStatsView.as_view(), name="admin-stats"),
    path("admin/announce/", views.AdminAnnounceView.as_view(), name="admin-announce"),

    # Router-generated URLs (specialties, doctors, slots, appointments, records, notifications)
    path("", include(router.urls)),
]
