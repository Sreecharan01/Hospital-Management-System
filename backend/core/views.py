"""
Views for Hospital Appointment Management System.
  Section 1 – Auth views (health, register, JWT, /me)
  Section 2 – ViewSets (specialty, doctor, slot, appointment, record, notification)
  Section 3 – Admin views (stats, announce)
"""

import datetime
import logging
import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
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
    Payment,
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
    PaymentSerializer,
    RegisterSerializer,
    SpecialtySerializer,
    SpecialtyWriteSerializer,
    UserSerializer,
)
from .tasks import send_appointment_email, send_bulk_announcement, safe_dispatch_email

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
        doctor_fee = appointment.slot.doctor.fee

        # Handle immediate online payment if provided
        payment_info = request.data.get("payment")
        if payment_info:
            method = payment_info.get("payment_method", Payment.Method.CARD)
            card_last4 = str(payment_info.get("card_last4", "4242"))[-4:]
            card_brand = payment_info.get("card_brand", "Visa")
            upi_id = payment_info.get("upi_id", "")
            txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"

            Payment.objects.create(
                appointment=appointment,
                patient=patient_profile,
                doctor=appointment.slot.doctor,
                amount=doctor_fee,
                currency="INR",
                payment_method=method,
                transaction_id=txn_id,
                status=Payment.Status.COMPLETED,
                card_last4=card_last4,
                card_brand=card_brand,
                upi_id=upi_id,
            )
            appointment.payment_status = Appointment.PaymentStatus.PAID
            appointment.save(update_fields=["payment_status"])

            Notification.objects.create(
                user=request.user,
                title="Payment Received",
                message=f"Consultation fee of ₹{doctor_fee} paid successfully (Txn: {txn_id}).",
            )
            Notification.objects.create(
                user=doctor_user,
                title="Fee Paid Online",
                message=f"{patient_name} paid the consultation fee of ₹{doctor_fee} for your appointment on {appt_date}.",
            )

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

        # Email notifications to Patient and Doctor on booking
        doctor_specialty = (
            slot.doctor.specialty.name if slot.doctor.specialty else "General Medicine"
        )
        if payment_info:
            pay_desc = (
                f"PAYMENT DETAILS:\n"
                f"• Consultation Fee Paid: ₹{doctor_fee} INR\n"
                f"• Payment Method: {method}\n"
                f"• Transaction ID: {txn_id}\n"
                f"• Status: Paid Online\n"
            )
        else:
            pay_desc = (
                f"PAYMENT DETAILS:\n"
                f"• Consultation Fee: ₹{doctor_fee} INR\n"
                f"• Status: Unpaid (You can pay online anytime from 'My Appointments')\n"
            )

        patient_booking_body = (
            f"Dear {patient_name},\n\n"
            f"Thank you for booking an appointment with CityCare Central Hospital.\n"
            f"Your booking has been successfully recorded.\n\n"
            f"BOOKING & ACCOUNT DETAILS:\n"
            f"• Logged-in Account Email: {request.user.email}\n"
            f"• Patient Name: {patient_name}\n"
            f"• Consulting Doctor: Dr. {doctor_name} ({doctor_specialty})\n"
            f"• Scheduled Date: {appt_date}\n"
            f"• Scheduled Time: {appt_time.strftime('%H:%M')}\n"
            f"• Current Status: {appointment.status}\n\n"
            f"{pay_desc}\n"
            f"Note: This booking confirmation has been sent directly to your account email: {request.user.email}.\n\n"
            f"You can view, reschedule, or cancel this appointment anytime by logging in at:\n"
            f"https://hospital-management-system-alpha-olive.vercel.app/appointments\n\n"
            f"Warm regards,\n"
            f"CityCare Central Hospital Team\n"
            f"Helpline: +91 1800-123-4567 | Email: care@citycarehospital.in\n"
        )

        doctor_booking_body = (
            f"Dear Dr. {doctor_name},\n\n"
            f"A new appointment has been scheduled with you:\n\n"
            f"• Patient Name: {patient_name}\n"
            f"• Patient Account Email: {request.user.email}\n"
            f"• Date: {appt_date}\n"
            f"• Time: {appt_time.strftime('%H:%M')}\n"
            f"• Reason for Visit: {appointment.reason or 'General Consultation'}\n\n"
            f"You can view and manage this appointment on your Doctor Dashboard:\n"
            f"https://hospital-management-system-alpha-olive.vercel.app/doctor/dashboard\n\n"
            f"Regards,\n"
            f"CityCare Central Hospital Scheduling Desk\n"
        )

        safe_dispatch_email(
            request.user.email,
            "Appointment Booking Confirmation – CityCare Central Hospital",
            patient_booking_body,
        )
        safe_dispatch_email(
            doctor_user.email,
            f"New Appointment Booking: {patient_name} – CityCare Central Hospital",
            doctor_booking_body,
        )

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

    def get_object(self):
        if self.action in ("cancel", "reschedule", "complete", "expire", "confirm"):
            obj = get_object_or_404(
                Appointment.objects.select_related(
                    "patient__user",
                    "slot__doctor__user",
                    "slot__doctor__specialty",
                ),
                pk=self.kwargs["pk"],
            )
            self._assert_appointment_ownership(obj, self.request.user)
            return obj
        return super().get_object()

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

        # Email to patient on doctor confirmation
        patient_name = appointment.patient.user.get_full_name() or appointment.patient.user.email
        doctor_name = request.user.get_full_name() or request.user.email
        confirm_email_body = (
            f"Dear {patient_name},\n\n"
            f"Good news! Your appointment with Dr. {doctor_name} has been CONFIRMED.\n\n"
            f"APPOINTMENT DETAILS:\n"
            f"• Logged-in Account Email: {appointment.patient.user.email}\n"
            f"• Consulting Doctor: Dr. {doctor_name}\n"
            f"• Date: {appointment.date}\n"
            f"• Time: {appointment.slot.start_time:%H:%M}\n"
            f"• Status: CONFIRMED\n\n"
            f"Please arrive at the clinic 10 minutes prior to your scheduled slot.\n\n"
            f"Note: This confirmation was delivered to your registered login email: {appointment.patient.user.email}.\n\n"
            f"Warm regards,\n"
            f"CityCare Central Hospital Team\n"
        )
        safe_dispatch_email(
            appointment.patient.user.email,
            "Appointment Confirmed – CityCare Central Hospital",
            confirm_email_body,
        )

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

        is_paid = appointment.payment_status == Appointment.PaymentStatus.PAID
        appointment.status = Appointment.Status.CANCELLED
        refund_amt = Decimal("0.00")

        # If patient cancelled a paid appointment, initiate 50% refund workflow for admin review
        if is_paid:
            appointment.payment_status = Appointment.PaymentStatus.REFUND_PENDING
            if hasattr(appointment, "payment") and appointment.payment:
                payment = appointment.payment
                refund_amt = round(payment.amount * Decimal("0.50"), 2)
                payment.status = Payment.Status.REFUND_PENDING
                payment.refund_amount = refund_amt
                payment.save(update_fields=["status", "refund_amount"])

            # Notify Admins to review and process the 50% refund
            User = get_user_model()
            admins = User.objects.filter(role=User.Role.ADMIN)
            doctor_name = appointment.slot.doctor.user.get_full_name()
            patient_name = appointment.patient.user.get_full_name()
            admin_notifications = [
                Notification(
                    user=admin_user,
                    title="Action Required: 50% Refund Pending",
                    message=(
                        f"Patient {patient_name} cancelled paid appointment "
                        f"with Dr. {doctor_name}. Eligible for 50% refund "
                        f"(₹{refund_amt} of ₹{appointment.payment.amount}). Please review and initiate."
                    ),
                )
                for admin_user in admins
            ]
            if admin_notifications:
                Notification.objects.bulk_create(admin_notifications)

        appointment.save(update_fields=["status", "payment_status", "updated_at"])

        # Notify the other party
        doctor_user = appointment.slot.doctor.user
        patient_user = appointment.patient.user

        if request.user.role == "PATIENT":
            Notification.objects.create(
                user=doctor_user,
                title="Appointment Cancelled",
                message=(
                    f"{request.user.get_full_name()} cancelled their appointment "
                    f"on {appointment.date} at {appointment.slot.start_time:%H:%M}."
                ),
            )
            if is_paid:
                Notification.objects.create(
                    user=patient_user,
                    title="Appointment Cancelled (50% Refund Pending)",
                    message=(
                        f"Your appointment on {appointment.date} has been cancelled. "
                        f"As per hospital cancellation policy, a 50% refund of ₹{refund_amt} "
                        f"is pending admin approval and will be credited to your original payment method."
                    ),
                )
        else:
            Notification.objects.create(
                user=patient_user,
                title="Appointment Cancelled",
                message=(
                    f"Your appointment on {appointment.date} at "
                    f"{appointment.slot.start_time:%H:%M} has been cancelled."
                ),
            )

        # Email notifications to Patient and Doctor on cancellation
        doctor_name = doctor_user.get_full_name() or doctor_user.email
        patient_name = patient_user.get_full_name() or patient_user.email
        specialty_name = (
            appointment.slot.doctor.specialty.name
            if appointment.slot.doctor.specialty
            else "General Medicine"
        )
        time_str = (
            appointment.appointment_time.strftime("%H:%M")
            if appointment.appointment_time
            else appointment.slot.start_time.strftime("%H:%M")
        )

        if is_paid and hasattr(appointment, "payment") and appointment.payment:
            orig_fee = appointment.payment.amount
            retained_fee = orig_fee - refund_amt
            refund_info = (
                f"PAYMENT & 50% REFUND DETAILS:\n"
                f"• Original Consultation Fee Paid: ₹{orig_fee}\n"
                f"• Eligible 50% Refund Amount: ₹{refund_amt} (Pending Admin Approval)\n"
                f"• Hospital Retained Fee (50%): ₹{retained_fee}\n"
                f"• Status: 50% refund request submitted to hospital admin. Once approved, it will be credited to your original payment method.\n"
            )
        else:
            refund_info = "PAYMENT STATUS: Unpaid (No refund applicable).\n"

        patient_cancel_body = (
            f"Dear {patient_name},\n\n"
            f"This email confirms that your appointment at CityCare Central Hospital has been CANCELLED.\n\n"
            f"APPOINTMENT & ACCOUNT DETAILS:\n"
            f"• Logged-in Account Email: {patient_user.email}\n"
            f"• Patient Name: {patient_name}\n"
            f"• Consulting Doctor: Dr. {doctor_name} ({specialty_name})\n"
            f"• Appointment Date: {appointment.date}\n"
            f"• Appointment Time: {time_str}\n"
            f"• Appointment Status: CANCELLED\n\n"
            f"{refund_info}\n"
            f"Note: This notification has been delivered directly to the account email you logged in with: {patient_user.email}.\n\n"
            f"If you wish to reschedule or book another consultation, please log in to your patient dashboard:\n"
            f"https://hospital-management-system-alpha-olive.vercel.app/\n\n"
            f"Warm regards,\n"
            f"CityCare Central Hospital Team\n"
            f"Helpline: +91 1800-123-4567 | Email: care@citycarehospital.in\n"
        )

        doctor_cancel_body = (
            f"Dear Dr. {doctor_name},\n\n"
            f"An appointment on your schedule has been CANCELLED:\n\n"
            f"• Patient Name: {patient_name}\n"
            f"• Patient Account Email: {patient_user.email}\n"
            f"• Date: {appointment.date}\n"
            f"• Time: {time_str}\n\n"
            f"The slot is now reopened and available for other patients.\n\n"
            f"Regards,\n"
            f"CityCare Central Hospital Scheduling Desk\n"
        )

        safe_dispatch_email(
            patient_user.email,
            "Appointment Cancelled – CityCare Central Hospital",
            patient_cancel_body,
        )
        safe_dispatch_email(
            doctor_user.email,
            f"Appointment Cancelled: {patient_name} – CityCare Central Hospital",
            doctor_cancel_body,
        )

        return Response(AppointmentSerializer(appointment).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAdminRole], url_path="process-refund")
    def process_refund(self, request, pk=None):
        """
        POST /api/appointments/{id}/process-refund/
        Admin initiates and approves the 50% refund for a cancelled appointment.
        """
        appointment = self.get_object()
        if not hasattr(appointment, "payment") or not appointment.payment:
            raise ValidationError({"detail": "No payment record found for this appointment."})

        payment = appointment.payment
        if payment.status == Payment.Status.REFUNDED:
            raise ValidationError({"detail": "This appointment has already been refunded."})

        # Calculate 50% refund amount
        refund_amount = round(payment.amount * Decimal("0.50"), 2)
        refund_txn_id = f"REF-{uuid.uuid4().hex[:10].upper()}"

        payment.status = Payment.Status.REFUNDED
        payment.refund_amount = refund_amount
        payment.refund_transaction_id = refund_txn_id
        payment.refunded_at = timezone.now()
        payment.save(update_fields=["status", "refund_amount", "refund_transaction_id", "refunded_at"])

        appointment.payment_status = Appointment.PaymentStatus.REFUNDED
        appointment.save(update_fields=["payment_status"])

        # Notify the patient
        doctor_name = appointment.slot.doctor.user.get_full_name()
        Notification.objects.create(
            user=appointment.patient.user,
            title="50% Refund Approved & Initiated",
            message=(
                f"Your 50% refund of ₹{refund_amount} for appointment with Dr. {doctor_name} "
                f"has been approved by Admin and initiated. (Refund Ref: {refund_txn_id})"
            ),
        )

        # Email patient with 50% refund details and account login email
        patient_name = appointment.patient.user.get_full_name() or appointment.patient.user.email
        refund_email_body = (
            f"Dear {patient_name},\n\n"
            f"Your 50% cancellation refund has been APPROVED and INITIATED by CityCare Hospital administration.\n\n"
            f"REFUND TRANSACTION SUMMARY:\n"
            f"• Logged-in Account Email: {appointment.patient.user.email}\n"
            f"• Patient Name: {patient_name}\n"
            f"• Consulting Doctor: Dr. {doctor_name}\n"
            f"• Original Consultation Fee Paid: ₹{payment.amount}\n"
            f"• Approved 50% Refund Amount: ₹{refund_amount}\n"
            f"• Hospital Cancellation Fee (50%): ₹{payment.amount - refund_amount}\n"
            f"• Refund Reference ID: {refund_txn_id}\n"
            f"• Initiation Date: {payment.refunded_at.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"The refund of ₹{refund_amount} has been dispatched to your original payment method.\n"
            f"Depending on your bank or payment provider, it typically reflects within 2 to 5 business days.\n\n"
            f"This email was sent to your registered account: {appointment.patient.user.email}.\n\n"
            f"Thank you,\n"
            f"CityCare Central Hospital Billing & Administration\n"
            f"Email: billing@citycarehospital.in\n"
        )
        safe_dispatch_email(
            appointment.patient.user.email,
            f"50% Refund Approved & Initiated (Ref: {refund_txn_id}) – CityCare Central Hospital",
            refund_email_body,
        )

        return Response({
            "detail": f"50% refund of ₹{refund_amount} approved and initiated successfully.",
            "refund_amount": str(refund_amount),
            "refund_transaction_id": refund_txn_id,
            "refunded_at": payment.refunded_at.isoformat(),
            "payment": PaymentSerializer(payment).data,
            "appointment": AppointmentSerializer(appointment).data,
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], permission_classes=[IsAdminRole], url_path="pending-refunds")
    def pending_refunds(self, request):
        """
        GET /api/appointments/pending-refunds/
        Returns list of appointments with pending refund requests.
        """
        qs = Appointment.objects.filter(
            payment_status=Appointment.PaymentStatus.REFUND_PENDING
        ).select_related(
            "patient__user", "slot__doctor__user", "slot__doctor__specialty", "payment"
        ).order_by("-updated_at")
        return Response(AppointmentSerializer(qs, many=True).data)

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

        # Email notifications to Patient and Doctor on completion
        doctor_name = appointment.slot.doctor.user.get_full_name() or appointment.slot.doctor.user.email
        patient_name = appointment.patient.user.get_full_name() or appointment.patient.user.email
        specialty_name = (
            appointment.slot.doctor.specialty.name
            if appointment.slot.doctor.specialty
            else "General Medicine"
        )
        time_str = (
            appointment.appointment_time.strftime("%H:%M")
            if appointment.appointment_time
            else appointment.slot.start_time.strftime("%H:%M")
        )

        patient_complete_body = (
            f"Dear {patient_name},\n\n"
            f"Thank you for attending your consultation today at CityCare Central Hospital.\n"
            f"Your appointment has been officially marked as COMPLETED.\n\n"
            f"CONSULTATION & ACCOUNT SUMMARY:\n"
            f"• Logged-in Account Email: {appointment.patient.user.email}\n"
            f"• Patient Name: {patient_name}\n"
            f"• Consulting Doctor: Dr. {doctor_name} ({specialty_name})\n"
            f"• Date: {appointment.date}\n"
            f"• Time: {time_str}\n"
            f"• Status: COMPLETED / ATTENDED\n\n"
            f"MEDICAL RECORDS & PRESCRIPTIONS:\n"
            f"Your consulting doctor may have documented clinical findings, diagnoses, or prescriptions for this consultation.\n"
            f"You can view and download all your medical records at any time by logging in with your account email: {appointment.patient.user.email}.\n\n"
            f"OFFICIAL RECEIPT:\n"
            f"Your official receipt can be viewed or printed directly from 'My Appointments' in your dashboard.\n\n"
            f"Note: This confirmation was delivered to your registered login email: {appointment.patient.user.email}.\n\n"
            f"We wish you good health and a speedy recovery!\n\n"
            f"Warm regards,\n"
            f"CityCare Central Hospital Healthcare Team\n"
            f"Helpline: +91 1800-123-4567 | Email: care@citycarehospital.in\n"
            f"Portal: https://hospital-management-system-alpha-olive.vercel.app/\n"
        )

        doctor_complete_body = (
            f"Dear Dr. {doctor_name},\n\n"
            f"You have marked the appointment for {patient_name} (Account: {appointment.patient.user.email}) as COMPLETED.\n\n"
            f"• Date: {appointment.date}\n"
            f"• Time: {time_str}\n\n"
            f"You can add or update clinical records, notes, and prescriptions for this patient from your Doctor Dashboard:\n"
            f"https://hospital-management-system-alpha-olive.vercel.app/doctor/dashboard\n\n"
            f"Thank you for your service,\n"
            f"CityCare Central Hospital Administration\n"
        )

        safe_dispatch_email(
            appointment.patient.user.email,
            "Consultation Completed – CityCare Central Hospital",
            patient_complete_body,
        )
        safe_dispatch_email(
            appointment.slot.doctor.user.email,
            f"Consultation Completed: {patient_name} – CityCare Central Hospital",
            doctor_complete_body,
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

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def pay(self, request, pk=None):
        """
        POST /api/appointments/{id}/pay/
        Pay doctor consultation fee for an existing appointment.
        """
        appointment = self.get_object()
        self._assert_appointment_ownership(appointment, request.user)

        if appointment.payment_status == Appointment.PaymentStatus.PAID:
            return Response(
                {"detail": "This appointment consultation fee is already paid."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if appointment.status == Appointment.Status.CANCELLED:
            return Response(
                {"detail": "Cannot pay for a cancelled appointment."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor_fee = appointment.slot.doctor.fee
        payment_data = request.data or {}
        method = payment_data.get("payment_method", Payment.Method.CARD)
        card_last4 = str(payment_data.get("card_last4", "4242"))[-4:]
        card_brand = payment_data.get("card_brand", "Visa")
        upi_id = payment_data.get("upi_id", "")
        txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"

        payment, _ = Payment.objects.update_or_create(
            appointment=appointment,
            defaults={
                "patient": appointment.patient,
                "doctor": appointment.slot.doctor,
                "amount": doctor_fee,
                "currency": "INR",
                "payment_method": method,
                "transaction_id": txn_id,
                "status": Payment.Status.COMPLETED,
                "card_last4": card_last4,
                "card_brand": card_brand,
                "upi_id": upi_id,
            },
        )
        appointment.payment_status = Appointment.PaymentStatus.PAID
        appointment.save(update_fields=["payment_status"])

        Notification.objects.create(
            user=appointment.patient.user,
            title="Payment Successful",
            message=f"Consultation fee of ₹{doctor_fee} paid successfully (Txn: {txn_id}).",
        )
        Notification.objects.create(
            user=appointment.slot.doctor.user,
            title="Consultation Fee Paid",
            message=f"{appointment.patient.user.get_full_name()} paid the consultation fee of ₹{doctor_fee} for appointment on {appointment.date}.",
        )

        return Response(
            {
                "detail": "Payment successful!",
                "payment": PaymentSerializer(payment).data,
                "receipt_url": f"/api/appointments/{appointment.id}/receipt/",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], permission_classes=[IsAuthenticated])
    def receipt(self, request, pk=None):
        """
        GET /api/appointments/{id}/receipt/
        Returns full official consultation invoice / receipt details.
        """
        appointment = self.get_object()
        self._assert_appointment_ownership(appointment, request.user)

        if not hasattr(appointment, "payment") or not appointment.payment:
            return Response(
                {"detail": "No payment record found for this appointment."},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment = appointment.payment
        receipt_data = {
            "receipt_number": f"REC-{payment.transaction_id.replace('TXN-', '')}",
            "transaction_id": payment.transaction_id,
            "paid_at": payment.paid_at.strftime("%Y-%m-%d %H:%M:%S") if payment.paid_at else str(payment.created_at),
            "amount": str(payment.amount),
            "currency": payment.currency,
            "payment_method": payment.get_payment_method_display(),
            "status": payment.status,
            "card_last4": payment.card_last4,
            "card_brand": payment.card_brand,
            "upi_id": payment.upi_id,
            "refund_amount": str(payment.refund_amount),
            "refund_transaction_id": payment.refund_transaction_id,
            "refunded_at": payment.refunded_at.strftime("%Y-%m-%d %H:%M:%S") if payment.refunded_at else None,
            "patient": {
                "name": appointment.patient.user.get_full_name() or appointment.patient.user.email,
                "email": appointment.patient.user.email,
                "phone": appointment.patient.phone or "N/A",
                "blood_group": appointment.patient.blood_group or "N/A",
            },
            "doctor": {
                "name": f"Dr. {appointment.slot.doctor.user.get_full_name() or appointment.slot.doctor.user.email}",
                "specialty": appointment.slot.doctor.specialty.name if appointment.slot.doctor.specialty else "General Consultation",
                "email": appointment.slot.doctor.user.email,
            },
            "appointment": {
                "id": str(appointment.id),
                "date": str(appointment.date),
                "time": appointment.appointment_time.strftime("%H:%M") if appointment.appointment_time else "",
                "status": appointment.status,
            },
            "hospital": {
                "name": "CityCare Central Hospital",
                "tagline": "Compassionate & Advanced Healthcare",
                "address": "Healthcare Boulevard, Medical District",
                "support_phone": "+91 (800) 555-CARE",
                "billing_email": "billing@citycarehospital.in",
                "tax_id": "GSTIN-29AAAAA0000A1Z5",
            },
        }
        return Response(receipt_data, status=status.HTTP_200_OK)


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


# ---------------------------------------------------------------------------
# Payment ViewSet
# ---------------------------------------------------------------------------

class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/payments/      - list payments for user
    GET /api/payments/{id}/ - payment detail
    """
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Payment.objects.select_related(
            "appointment", "patient__user", "doctor__user", "doctor__specialty"
        )
        if user.role == "PATIENT":
            return qs.filter(patient__user=user)
        elif user.role == "DOCTOR":
            return qs.filter(doctor__user=user)
        return qs


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
