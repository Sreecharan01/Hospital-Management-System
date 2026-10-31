"""
Custom DRF permission classes for Hospital Appointment Management System.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsPatient(BasePermission):
    """Allow access only to users with role=PATIENT."""
    message = "Only patients can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "PATIENT"
        )


class IsDoctor(BasePermission):
    """Allow access only to users with role=DOCTOR."""
    message = "Only doctors can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == "DOCTOR"
        )


class IsAdminRole(BasePermission):
    """Allow access only to users with role=ADMIN or is_staff=True."""
    message = "Only admin users can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.role == "ADMIN" or request.user.is_staff)
        )


class IsPatientOrReadOnly(BasePermission):
    """Patients can write; anyone authenticated can read."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == "PATIENT"


class IsDoctorOrReadOnly(BasePermission):
    """Doctors can write; anyone authenticated can read."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == "DOCTOR"


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: allow if the object belongs to the requesting
    user, or the requesting user is an admin/staff.
    Checks obj.user, obj.patient.user, obj.doctor.user in that order.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff or getattr(user, "role", None) == "ADMIN":
            return True
        # Direct user ownership
        if hasattr(obj, "user") and obj.user == user:
            return True
        # Patient profile link
        if hasattr(obj, "patient") and hasattr(obj.patient, "user") and obj.patient.user == user:
            return True
        # Doctor profile link
        if hasattr(obj, "doctor") and hasattr(obj.doctor, "user") and obj.doctor.user == user:
            return True
        # Created_by doctor link
        if hasattr(obj, "created_by") and hasattr(obj.created_by, "user") and obj.created_by.user == user:
            return True
        return False
