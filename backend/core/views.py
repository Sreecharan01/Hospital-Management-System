"""
Views for Hospital Appointment Management System.
  Section 1 – Auth views (health, register, JWT, /me)
  Section 2 – ViewSets (specialty, doctor, slot, appointment, record, notification)
  Section 3 – Admin views (stats, announce)
"""

import datetime
import logging
import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import serializers as drf_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Appointment,
    AvailabilitySlot,
    DoctorProfile,
    MedicalRecord,
    Notification,
    PatientProfile,
    Specialty,
)
from .permissions import IsAdminRole, IsDoctor, IsPatient, IsOwnerOrAdmin
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentSerializer,
    AvailabilitySlotSerializer,
    AvailabilitySlotWriteSerializer,
    CustomTokenObtainPairSerializer,
    DoctorProfileDetailSerializer,
    DoctorProfileListSerializer,
    DoctorProfileUpdateSerializer,
    MedicalRecordSerializer,
    MeUpdateSerializer,
    NotificationSerializer,
    RegisterSerializer,
    SpecialtySerializer,
    SpecialtyWriteSerializer,
    UserSerializer,
)
from .tasks import send_appointment_email, send_bulk_announcement

User = get_user_model()
logger = logging.getLogger(__name__)


# ===========================================================================
# Section 1 – Auth Views
# ===========================================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """GET /api/health/ — liveness probe."""
    return Response({"status": "ok", "message": "Hospital API is running."})


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """POST /api/auth/register/ — create user + matching profile."""
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/auth/token/ — JWT with role/email/name in claims."""
    serializer_class = CustomTokenObtainPairSerializer


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    """GET|PATCH /api/auth/me/ — read or update current user + profile."""
    user = request.user
    if request.method == "GET":
        return Response(UserSerializer(user).data)
    serializer = MeUpdateSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(UserSerializer(serializer.instance).data)


# ===========================================================================
# Section 2 – ViewSets
# ===========================================================================

# ---------------------------------------------------------------------------
# Specialty
# ---------------------------------------------------------------------------

class SpecialtyViewSet(viewsets.ModelViewSet):
    """
    GET /api/specialties/         — public list
    GET /api/specialties/{id}/    — public detail
    POST/PATCH/PUT/DELETE         — admin only
    """
    queryset = Specialty.objects.order_by("name")

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return SpecialtyWriteSerializer
        return SpecialtySerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsAdminRole()]


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------

class DoctorViewSet(viewsets.ModelViewSet):
    """
    GET  /api/doctors/                         — public list (verified only)
                                                 ?search= &specialty= &available_day=
    GET  /api/doctors/{id}/                    — public detail
    PATCH /api/doctors/{id}/                   — doctor updates own profile
    POST /api/doctors/{id}/verify/             — admin verifies doctor
    GET|POST /api/doctors/{id}/slots/          — list or add slots
    DELETE /api/doctors/{id}/slots/{slot_id}/  — doctor removes own slot
    """
    http_method_names = ["get", "patch", "post", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        is_admin = (
            user.is_authenticated
            and (user.is_staff or getattr(user, "role", None) == "ADMIN")
        )
        is_own_doctor = (
            user.is_authenticated
            and getattr(user, "role", None) == "DOCTOR"
        )

        if is_admin:
            qs = DoctorProfile.objects.all()
        elif is_own_doctor:
            # Doctor sees all verified + their own (even if not verified)
            qs = DoctorProfile.objects.filter(
                Q(is_verified=True) | Q(user=user)
            )
        else:
            qs = DoctorProfile.objects.filter(is_verified=True)

        qs = qs.select_related("user", "specialty").prefetch_related("availability_slots")

        # Filters
        search = self.request.query_params.get("search")
        if search:
            qs = qs.filter(
                Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
                | Q(bio__icontains=search)
            )

        specialty = self.request.query_params.get("specialty")
        if specialty:
            try:
                specialty_uuid = uuid.UUID(specialty)
                qs = qs.filter(specialty__id=specialty_uuid)
            except ValueError:
                qs = qs.filter(specialty__name__icontains=specialty)

        available_day = self.request.query_params.get("available_day")
        if available_day is not None:
            try:
                qs = qs.filter(
                    availability_slots__day_of_week=int(available_day),
                    availability_slots__is_active=True,
                ).distinct()
            except (ValueError, TypeError):
                pass

        return qs.distinct()

    def get_serializer_class(self):
        if self.action == "list":
            return DoctorProfileListSerializer
        if self.action == "partial_update":
            return DoctorProfileUpdateSerializer
        return DoctorProfileDetailSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "verify":
            return [IsAdminRole()]
        if self.action == "partial_update":
            return [IsDoctor()]
        if self.action in ("slots", "delete_slot"):
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("You can only update your own doctor profile.")
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="verify")
    def verify(self, request, pk=None):
        """POST /api/doctors/{id}/verify/ — admin marks a doctor as verified."""
        doctor = self.get_object()
        if doctor.is_verified:
            return Response({"detail": "Doctor is already verified."})
        doctor.is_verified = True
        doctor.save(update_fields=["is_verified"])
        Notification.objects.create(
            user=doctor.user,
            title="Profile Verified",
            message=(
                "Your doctor profile has been verified by an administrator. "
                "You can now receive patient appointments."
            ),
        )
        return Response({"detail": "Doctor profile verified successfully."})

    @action(detail=True, methods=["get", "post"], url_path="slots")
    def slots(self, request, pk=None):
        """
        GET  /api/doctors/{id}/slots/ — list active slots for this doctor.
        POST /api/doctors/{id}/slots/ — doctor adds a slot to their own profile.
        """
        doctor = self.get_object()

        if request.method == "GET":
            qs = AvailabilitySlot.objects.filter(doctor=doctor, is_active=True)
            return Response(AvailabilitySlotSerializer(qs, many=True).data)

        # POST – only this doctor
        if not request.user.is_authenticated or request.user.role != "DOCTOR":
            raise PermissionDenied("Only doctors can manage their slots.")
        if doctor.user != request.user:
            raise PermissionDenied("You can only add slots to your own profile.")

        ser = AvailabilitySlotWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        slot = ser.save(doctor=doctor)
        return Response(AvailabilitySlotSerializer(slot).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"slots/(?P<slot_id>[0-9a-f-]+)",
    )
    def delete_slot(self, request, pk=None, slot_id=None):
        """DELETE /api/doctors/{id}/slots/{slot_id}/ — doctor deactivates a slot."""
        doctor = self.get_object()
        if doctor.user != request.user:
            raise PermissionDenied("You can only manage your own slots.")
        try:
            slot = AvailabilitySlot.objects.get(id=slot_id, doctor=doctor)
        except AvailabilitySlot.DoesNotExist:
            return Response({"detail": "Slot not found."}, status=status.HTTP_404_NOT_FOUND)
        slot.is_active = False
        slot.save(update_fields=["is_active"])
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# Availability Slot (standalone CRUD for doctors)
# ---------------------------------------------------------------------------

class AvailabilitySlotViewSet(viewsets.ModelViewSet):
    """
    GET  /api/slots/      — doctor sees own slots; public sees all active
    POST /api/slots/      — doctor creates a slot (auto-assigned to their profile)
    PATCH/DELETE          — doctor manages own slots
    """
    http_method_names = ["get", "post", "patch", "put", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == "DOCTOR":
            try:
                return AvailabilitySlot.objects.filter(
                    doctor=user.doctor_profile
                ).select_related("doctor", "doctor__user", "doctor__specialty")
            except DoctorProfile.DoesNotExist:
                return AvailabilitySlot.objects.none()
        if user.is_authenticated and (user.is_staff or user.role == "ADMIN"):
            return AvailabilitySlot.objects.all().select_related(
                "doctor", "doctor__user", "doctor__specialty"
            )
        # Public / patients: active slots only
        return AvailabilitySlot.objects.filter(is_active=True).select_related(
            "doctor", "doctor__user", "doctor__specialty"
        )

    def get_serializer_class(self):
        if self.request.method in ("POST", "PUT", "PATCH"):
            return AvailabilitySlotWriteSerializer
        return AvailabilitySlotSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [IsDoctor()]

    def perform_create(self, serializer):
        try:
            doctor_profile = self.request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            raise ValidationError({"detail": "No doctor profile found for this user."})
        serializer.save(doctor=doctor_profile)

    def perform_update(self, serializer):
        instance = self.get_object()
        if instance.doctor.user != self.request.user:
            raise PermissionDenied("You can only update your own slots.")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.doctor.user != self.request.user:
            raise PermissionDenied("You can only delete your own slots.")
        instance.is_active = False
        instance.save(update_fields=["is_active"])


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------

class AppointmentViewSet(viewsets.ModelViewSet):
    """
    GET  /api/appointments/                    — role-filtered list
    POST /api/appointments/                    — patient books (transactional)
    GET  /api/appointments/{id}/               — detail (own or admin)
    POST /api/appointments/{id}/confirm/       — doctor accepts a PENDING booking
    POST /api/appointments/{id}/cancel/        — patient or doctor or admin
    POST /api/appointments/{id}/reschedule/    — patient only
    POST /api/appointments/{id}/complete/      — doctor marks patient attended
    POST /api/appointments/{id}/expire/        — doctor marks patient didn't attend
    """
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related(
            "patient__user",
            "slot__doctor__user",
            "slot__doctor__specialty",
        )
        if user.role == "PATIENT":
            return qs.filter(patient__user=user)
        if user.role == "DOCTOR":
            return qs.filter(slot__doctor__user=user)
        return qs  # ADMIN

    def get_serializer_class(self):
        if self.action == "create":
            return AppointmentCreateSerializer
        return AppointmentSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsPatient()]
        if self.action == "available_times":
            return [IsAuthenticated()]
        return [IsAuthenticated()]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Book an appointment.
        Uses SELECT FOR UPDATE to prevent concurrent double-bookings.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        slot = serializer.validated_data["slot"]
        appt_date = serializer.validated_data["date"]
        appt_time = serializer.validated_data["appointment_time"]

        # Lock the slot row for the duration of this transaction
        slot = AvailabilitySlot.objects.select_for_update().get(pk=slot.pk)

        # Double-booking check: same slot + date + time
        exists = (
            Appointment.objects.filter(
                slot=slot, date=appt_date, appointment_time=appt_time
            )
            .exclude(status=Appointment.Status.CANCELLED)
            .exists()
        )
        if exists:
            raise ValidationError(
                {"detail": f"The time slot {appt_time.strftime('%H:%M')} is already booked for {appt_date}. Please select a different time."}
            )

        # Ensure patient has a profile
        try:
            patient_profile = request.user.patient_profile
        except PatientProfile.DoesNotExist:
            raise ValidationError({"detail": "Patient profile not found for this user."})

        appointment = serializer.save(
            patient=patient_profile,
            status=Appointment.Status.PENDING,
        )

        doctor_user = appointment.slot.doctor.user
        doctor_name = doctor_user.get_full_name()
        patient_name = request.user.get_full_name()

        # In-app notifications
        Notification.objects.bulk_create([
            Notification(
                user=request.user,
                title="Appointment Requested",
                message=(
                    f"Your appointment request with Dr. {doctor_name} on "
                    f"{appt_date} at {appt_time.strftime('%H:%M')} "
                    f"has been submitted. Waiting for doctor confirmation."
                ),
            ),
            Notification(
                user=doctor_user,
                title="New Appointment Request",
                message=(
                    f"{patient_name} has requested an appointment with you on "
                    f"{appt_date} at {appt_time.strftime('%H:%M')}. "
                    f"Please confirm or decline."
                ),
            ),
        ])

        # Async email notifications (wrapped – Redis/Celery may not be running in dev)
        try:
            send_appointment_email.apply_async(args=[
                request.user.email,
                "Appointment Request Submitted – Hospital",
                (
                    f"Dear {patient_name},\n\n"
                    f"Your appointment request with Dr. {doctor_name} has been submitted.\n"
                    f"Date: {appt_date}\nTime: {appt_time.strftime('%H:%M')}\n\n"
                    f"You will be notified once the doctor confirms your booking.\n\nHospital Team"
                ),
            ])
            send_appointment_email.apply_async(args=[
                doctor_user.email,
                "New Appointment Request – Hospital",
                (
                    f"Dear Dr. {doctor_name},\n\n"
                    f"A new appointment has been requested by {patient_name}.\n"
                    f"Date: {appt_date}\nTime: {appt_time.strftime('%H:%M')}\n\n"
                    f"Please log in to confirm or decline this booking.\n\nHospital Team"
                ),
            ])
        except Exception as exc:
            logger.warning("Could not queue email tasks: %s", exc)

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )

    def _assert_appointment_ownership(self, appointment, user):
        """Raise PermissionDenied if the user doesn't own this appointment."""
        if user.role == "PATIENT" and appointment.patient.user != user:
            raise PermissionDenied("You can only manage your own appointments.")
        if user.role == "DOCTOR" and appointment.slot.doctor.user != user:
            raise PermissionDenied("You can only manage appointments in your slots.")

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """POST /api/appointments/{id}/confirm/ — doctor accepts a pending booking."""
        appointment = self.get_object()
        if request.user.role != "DOCTOR":
            raise PermissionDenied("Only doctors can confirm appointments.")
        if appointment.slot.doctor.user != request.user:
            raise PermissionDenied("You can only confirm appointments in your own slots.")
        if appointment.status != Appointment.Status.PENDING:
            raise ValidationError(
                {"detail": "Only PENDING appointments can be confirmed."}
            )

        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(update_fields=["status", "updated_at"])

        Notification.objects.create(
            user=appointment.patient.user,
            title="Appointment Confirmed",
            message=(
                f"Your appointment on {appointment.date} at "
                f"{appointment.slot.start_time:%H:%M} has been confirmed by "
                f"Dr. {request.user.get_full_name()}. Please arrive 10 minutes early."
            ),
        )

        # Async email to patient
        try:
            patient_name = appointment.patient.user.get_full_name()
            send_appointment_email.apply_async(args=[
                appointment.patient.user.email,
                "Appointment Confirmed – Hospital",
                (
                    f"Dear {patient_name},\n\n"
                    f"Your appointment with Dr. {request.user.get_full_name()} has been confirmed.\n"
                    f"Date: {appointment.date}\nTime: {appointment.slot.start_time:%H:%M}\n\n"
                    f"Please arrive 10 minutes early.\n\nHospital Team"
                ),
            ])
        except Exception as exc:
            logger.warning("Could not queue confirmation email: %s", exc)

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """POST /api/appointments/{id}/cancel/ — patient, doctor, or admin."""
        appointment = self.get_object()
        self._assert_appointment_ownership(appointment, request.user)

        if appointment.status in (
            Appointment.Status.COMPLETED,
            Appointment.Status.CANCELLED,
            Appointment.Status.EXPIRED,
        ):
            raise ValidationError(
                {"detail": f"Cannot cancel an appointment with status '{appointment.status}'."}
            )

        appointment.status = Appointment.Status.CANCELLED
        appointment.save(update_fields=["status", "updated_at"])

        # Notify the other party
        if request.user.role == "PATIENT":
            Notification.objects.create(
                user=appointment.slot.doctor.user,
                title="Appointment Cancelled",
                message=(
                    f"{request.user.get_full_name()} cancelled their appointment "
                    f"on {appointment.date} at {appointment.slot.start_time:%H:%M}."
                ),
            )
        else:
            Notification.objects.create(
                user=appointment.patient.user,
                title="Appointment Cancelled",
                message=(
                    f"Your appointment on {appointment.date} at "
                    f"{appointment.slot.start_time:%H:%M} has been cancelled."
                ),
            )

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def reschedule(self, request, pk=None):
        """
        POST /api/appointments/{id}/reschedule/
        Body: { "slot": "<uuid>", "date": "YYYY-MM-DD", "appointment_time": "HH:MM" }
        Patient only; runs same double-booking checks.
        """
        appointment = self.get_object()

        if request.user.role != "PATIENT":
            raise PermissionDenied("Only patients can reschedule appointments.")
        if appointment.patient.user != request.user:
            raise PermissionDenied("You can only reschedule your own appointments.")
        if appointment.status not in (
            Appointment.Status.PENDING, Appointment.Status.CONFIRMED
        ):
            raise ValidationError(
                {"detail": "Only PENDING or CONFIRMED appointments can be rescheduled."}
            )

        new_slot_id = request.data.get("slot")
        new_date_str = request.data.get("date")
        new_time_str = request.data.get("appointment_time")

        if not new_slot_id or not new_date_str:
            raise ValidationError({"detail": "'slot' and 'date' are required."})

        try:
            new_slot = AvailabilitySlot.objects.select_for_update().get(id=new_slot_id)
        except (AvailabilitySlot.DoesNotExist, Exception):
            raise ValidationError({"slot": "Invalid slot ID."})

        try:
            new_date = datetime.date.fromisoformat(new_date_str)
        except ValueError:
            raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD."})

        if new_time_str:
            try:
                new_time = datetime.time.fromisoformat(new_time_str)
            except ValueError:
                raise ValidationError({"appointment_time": "Invalid time format. Use HH:MM."})
        else:
            new_time = new_slot.start_time
            raise ValidationError({"appointment_time": "Invalid time format. Use HH:MM."})

        if new_date <= datetime.date.today():
            raise ValidationError({"date": "Appointment date must be in the future."})

        if not new_slot.is_active:
            raise ValidationError({"slot": "This slot is not active."})

        if new_date.weekday() != new_slot.day_of_week:
            raise ValidationError({
                "date": (
                    f"This slot is only available on "
                    f"{new_slot.get_day_of_week_display()}s."
                )
            })

        # Validate time falls within the slot window
        if new_time < new_slot.start_time or new_time >= new_slot.end_time:
            raise ValidationError({
                "appointment_time": (
                    f"Appointment time must be between "
                    f"{new_slot.start_time.strftime('%H:%M')} and "
                    f"{new_slot.end_time.strftime('%H:%M')}."
                )
            })

        # Double-booking check (exclude current appointment)
        conflict = (
            Appointment.objects.filter(
                slot=new_slot, date=new_date, appointment_time=new_time
            )
            .exclude(status=Appointment.Status.CANCELLED)
            .exclude(pk=appointment.pk)
            .exists()
        )
        if conflict:
            raise ValidationError(
                {"detail": f"The time slot {new_time.strftime('%H:%M')} is already booked for {new_date}. Please select a different time."}
            )

        old_date = appointment.date
        appointment.slot = new_slot
        appointment.date = new_date
        appointment.appointment_time = new_time
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save(update_fields=["slot", "date", "appointment_time", "status", "updated_at"])

        # Notifications
        Notification.objects.bulk_create([
            Notification(
                user=request.user,
                title="Appointment Rescheduled",
                message=(
                    f"Your appointment has been rescheduled from {old_date} "
                    f"to {new_date} at {new_time.strftime('%H:%M')}."
                ),
            ),
            Notification(
                user=new_slot.doctor.user,
                title="Appointment Rescheduled",
                message=(
                    f"{request.user.get_full_name()} rescheduled their appointment "
                    f"from {old_date} to {new_date} at {new_time.strftime('%H:%M')}."
                ),
            ),
        ])

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """POST /api/appointments/{id}/complete/ — doctor marks patient as attended."""
        appointment = self.get_object()
        if request.user.role != "DOCTOR":
            raise PermissionDenied("Only doctors can mark appointments as completed.")
        if appointment.slot.doctor.user != request.user:
            raise PermissionDenied("You can only complete appointments in your own slots.")
        if appointment.status != Appointment.Status.CONFIRMED:
            raise ValidationError(
                {"detail": "Only CONFIRMED appointments can be marked as completed."}
            )

        appointment.status = Appointment.Status.COMPLETED
        appointment.save(update_fields=["status", "updated_at"])

        Notification.objects.create(
            user=appointment.patient.user,
            title="Appointment Completed",
            message=(
                f"Your appointment on {appointment.date} has been marked as completed. "
                f"The patient attended successfully. "
                f"A medical record may be created by your doctor."
            ),
        )

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"])
    def expire(self, request, pk=None):
        """POST /api/appointments/{id}/expire/ — doctor marks appointment as expired (patient didn't attend)."""
        appointment = self.get_object()
        if request.user.role != "DOCTOR":
            raise PermissionDenied("Only doctors can mark appointments as expired.")
        if appointment.slot.doctor.user != request.user:
            raise PermissionDenied("You can only expire appointments in your own slots.")
        if appointment.status not in (
            Appointment.Status.PENDING, Appointment.Status.CONFIRMED
        ):
            raise ValidationError(
                {"detail": "Only PENDING or CONFIRMED appointments can be marked as expired."}
            )

        appointment.status = Appointment.Status.EXPIRED
        appointment.save(update_fields=["status", "updated_at"])

        Notification.objects.create(
            user=appointment.patient.user,
            title="Appointment Expired",
            message=(
                f"Your appointment on {appointment.date} at "
                f"{appointment.slot.start_time:%H:%M} has been marked as expired "
                f"because you did not attend."
            ),
        )

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=False, methods=["get"], url_path="available-times")
    def available_times(self, request):
        """
        GET /api/appointments/available-times/?slot=<uuid>&date=YYYY-MM-DD
        Returns 10-minute intervals within the slot window, each marked
        as available or booked.
        """
        slot_id = request.query_params.get("slot")
        date_str = request.query_params.get("date")

        if not slot_id or not date_str:
            raise ValidationError({"detail": "'slot' and 'date' query params are required."})

        try:
            slot = AvailabilitySlot.objects.get(id=slot_id, is_active=True)
        except AvailabilitySlot.DoesNotExist:
            raise ValidationError({"detail": "Slot not found or inactive."})

        try:
            appt_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            raise ValidationError({"detail": "Invalid date format. Use YYYY-MM-DD."})

        # Get all booked times for this slot + date (excluding cancelled)
        booked_times = set(
            Appointment.objects.filter(slot=slot, date=appt_date)
            .exclude(status=Appointment.Status.CANCELLED)
            .values_list("appointment_time", flat=True)
        )

        # Generate 10-minute intervals
        intervals = []
        current = datetime.datetime.combine(appt_date, slot.start_time)
        end = datetime.datetime.combine(appt_date, slot.end_time)

        while current < end:
            t = current.time()
            intervals.append({
                "time": t.strftime("%H:%M"),
                "available": t not in booked_times,
            })
            current += datetime.timedelta(minutes=10)

        return Response({
            "slot_id": str(slot.id),
            "date": date_str,
            "interval_minutes": 10,
            "times": intervals,
        })


# ---------------------------------------------------------------------------
# Medical Record
# ---------------------------------------------------------------------------

class MedicalRecordViewSet(viewsets.ModelViewSet):
    """
    GET  /api/records/      — patient: own records; doctor: records they created; admin: all
    POST /api/records/      — doctor only, appointment must be COMPLETED
    """
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = MedicalRecord.objects.select_related(
            "appointment__patient__user",
            "appointment__slot__doctor__user",
            "created_by__user",
        )
        if user.role == "PATIENT":
            return qs.filter(appointment__patient__user=user)
        if user.role == "DOCTOR":
            return qs.filter(created_by__user=user)
        return qs  # ADMIN

    def get_serializer_class(self):
        return MedicalRecordSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsDoctor()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        appointment = serializer.validated_data["appointment"]

        if appointment.status != Appointment.Status.COMPLETED:
            raise ValidationError(
                {"detail": "Medical records can only be created for COMPLETED appointments."}
            )
        try:
            doctor_profile = self.request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            raise ValidationError({"detail": "No doctor profile found."})

        if appointment.slot.doctor != doctor_profile:
            raise PermissionDenied(
                "You can only create medical records for your own appointments."
            )

        if hasattr(appointment, "medical_record"):
            raise ValidationError(
                {"detail": "A medical record already exists for this appointment."}
            )

        serializer.save(created_by=doctor_profile)

        # Notify patient
        Notification.objects.create(
            user=appointment.patient.user,
            title="Medical Record Created",
            message=(
                f"Dr. {doctor_profile.user.get_full_name()} has created a medical "
                f"record for your appointment on {appointment.date}."
            ),
        )


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/notifications/                    — own notifications
    POST /api/notifications/{id}/mark_read/   — mark one as read
    POST /api/notifications/mark_all_read/    — mark all as read
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"], url_path="mark_read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["post"], url_path="mark_all_read")
    def mark_all_read(self, request):
        count = request.user.notifications.filter(is_read=False).update(is_read=True)
        return Response({"marked_read": count})


# ===========================================================================
# Section 3 – Admin Views
# ===========================================================================

class AdminStatsView(APIView):
    """GET /api/admin/stats/ — aggregate stats for the admin dashboard."""
    permission_classes = [IsAdminRole]

    def get(self, request):
        from datetime import timedelta

        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)

        appt_status_counts = {
            row["status"]: row["count"]
            for row in Appointment.objects.values("status").annotate(count=Count("id"))
        }

        daily_appointments = list(
            Appointment.objects.filter(date__gte=thirty_days_ago)
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )

        stats = {
            "users": {
                "total": User.objects.count(),
                "patients": User.objects.filter(role="PATIENT").count(),
                "doctors": User.objects.filter(role="DOCTOR").count(),
                "admins": User.objects.filter(role="ADMIN").count(),
            },
            "doctors": {
                "total": DoctorProfile.objects.count(),
                "verified": DoctorProfile.objects.filter(is_verified=True).count(),
                "pending_verification": DoctorProfile.objects.filter(is_verified=False).count(),
            },
            "specialties": Specialty.objects.count(),
            "appointments": {
                "total": Appointment.objects.count(),
                **{k.lower(): v for k, v in appt_status_counts.items()},
            },
            "medical_records": MedicalRecord.objects.count(),
            "notifications": {
                "total": Notification.objects.count(),
                "unread": Notification.objects.filter(is_read=False).count(),
            },
            "appointments_per_day": [
                {"date": str(row["date"]), "count": row["count"]}
                for row in daily_appointments
            ],
        }

        return Response(stats)


class AdminAnnounceView(APIView):
    """
    POST /api/admin/announce/
    Body: { "title": "...", "message": "...", "roles": ["PATIENT", "DOCTOR"] }
    Creates in-app notifications for matching users and dispatches bulk email.
    """
    permission_classes = [IsAdminRole]

    def post(self, request):
        title = request.data.get("title", "").strip()
        message = request.data.get("message", "").strip()
        roles = request.data.get("roles", ["PATIENT", "DOCTOR", "ADMIN"])

        if not title or not message:
            return Response(
                {"detail": "'title' and 'message' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_roles = {User.Role.PATIENT, User.Role.DOCTOR, User.Role.ADMIN}
        roles = [r for r in roles if r in valid_roles]
        if not roles:
            return Response(
                {"detail": "No valid roles specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        target_users = User.objects.filter(role__in=roles, is_active=True)

        # Bulk create in-app notifications
        Notification.objects.bulk_create([
            Notification(user=u, title=title, message=message)
            for u in target_users
        ])

        # Async bulk email
        emails = list(target_users.values_list("email", flat=True))
        try:
            send_bulk_announcement.apply_async(args=[emails, title, message])
        except Exception as exc:
            logger.warning("Could not queue bulk announcement emails: %s", exc)

        return Response(
            {
                "detail": "Announcement sent.",
                "notified_users": target_users.count(),
                "roles": roles,
            },
            status=status.HTTP_201_CREATED,
        )
