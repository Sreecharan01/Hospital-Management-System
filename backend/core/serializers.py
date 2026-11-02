"""
Serializers for Hospital Appointment Management System.
Sections:
  1. Auth serializers (register, /me, JWT)
  2. Domain serializers (doctors, slots, appointments, records, notifications)
"""

import datetime
import uuid as uuid_lib

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    PatientProfile,
    DoctorProfile,
    Specialty,
    AvailabilitySlot,
    Appointment,
    MedicalRecord,
    Notification,
    Payment,
)

User = get_user_model()


# ===========================================================================
# Section 1 – Auth Serializers
# ===========================================================================

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ["id", "dob", "phone", "address", "blood_group", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "description"]


class DoctorProfileSerializer(serializers.ModelSerializer):
    """Used inside /me response for doctor users."""
    specialty = SpecialtySerializer(read_only=True)
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        source="specialty",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "specialty", "specialty_id",
            "bio", "fee", "experience_years",
            "is_verified", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at", "updated_at"]


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation with nested profile."""
    patient_profile = PatientProfileSerializer(read_only=True)
    doctor_profile = DoctorProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "is_active", "date_joined",
            "patient_profile", "doctor_profile",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "date_joined"]


class RegisterSerializer(serializers.Serializer):
    """
    Unified registration serializer.
    Creates User + role-specific profile atomically.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(
        choices=[User.Role.PATIENT, User.Role.DOCTOR],
        default=User.Role.PATIENT,
    )

    # Patient-specific
    dob = serializers.DateField(required=False, allow_null=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    blood_group = serializers.ChoiceField(
        choices=PatientProfile.BloodGroup.choices,
        required=False,
        allow_blank=True,
        default="",
    )

    # Doctor-specific
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        required=False,
        allow_null=True,
        source="specialty",
    )
    bio = serializers.CharField(required=False, allow_blank=True)
    fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0.00)
    experience_years = serializers.IntegerField(min_value=0, required=False, default=0)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        role = validated_data.get("role", User.Role.PATIENT)
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            role=role,
        )
        if role == User.Role.PATIENT:
            PatientProfile.objects.create(
                user=user,
                dob=validated_data.get("dob"),
                phone=validated_data.get("phone", ""),
                address=validated_data.get("address", ""),
                blood_group=validated_data.get("blood_group", ""),
            )
        elif role == User.Role.DOCTOR:
            DoctorProfile.objects.create(
                user=user,
                specialty=validated_data.get("specialty"),
                bio=validated_data.get("bio", ""),
                fee=validated_data.get("fee", 0.00),
                experience_years=validated_data.get("experience_years", 0),
            )
        return user


class MeUpdateSerializer(serializers.ModelSerializer):
    """PATCH /api/auth/me/ — update base user + nested profile."""
    dob = serializers.DateField(required=False, allow_null=True, write_only=True)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True, write_only=True)
    address = serializers.CharField(required=False, allow_blank=True, write_only=True)
    blood_group = serializers.ChoiceField(
        choices=PatientProfile.BloodGroup.choices,
        required=False, allow_blank=True, write_only=True,
    )
    bio = serializers.CharField(required=False, allow_blank=True, write_only=True)
    fee = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, write_only=True)
    experience_years = serializers.IntegerField(min_value=0, required=False, write_only=True)
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        source="specialty",
        required=False, allow_null=True, write_only=True,
    )
    patient_profile = PatientProfileSerializer(read_only=True)
    doctor_profile = DoctorProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name",
            "role", "is_active", "date_joined",
            "patient_profile", "doctor_profile",
            "dob", "phone", "address", "blood_group",
            "bio", "fee", "experience_years", "specialty_id",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "date_joined"]

    @transaction.atomic
    def update(self, instance, validated_data):
        patient_fields = {
            k: validated_data.pop(k)
            for k in ("dob", "phone", "address", "blood_group")
            if k in validated_data
        }
        doctor_fields = {
            k: validated_data.pop(k)
            for k in ("specialty", "bio", "fee", "experience_years")
            if k in validated_data
        }
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if instance.role == User.Role.PATIENT and patient_fields:
            PatientProfile.objects.filter(user=instance).update(**patient_fields)
        elif instance.role == User.Role.DOCTOR and doctor_fields:
            DoctorProfile.objects.filter(user=instance).update(**doctor_fields)

        instance.refresh_from_db()
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Add role, email and full name to JWT payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["email"] = user.email
        token["name"] = user.get_full_name()
        return token


# ===========================================================================
# Section 2 – Domain Serializers
# ===========================================================================

# ---------------------------------------------------------------------------
# Minimal nested helpers
# ---------------------------------------------------------------------------

class UserMinimalSerializer(serializers.ModelSerializer):
    """Compact user info used inside nested serializers."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name"]

    def get_full_name(self, obj):
        return obj.get_full_name()


class DoctorMinimalSerializer(serializers.ModelSerializer):
    """Compact doctor representation used inside Appointment / Slot serializers."""
    full_name = serializers.SerializerMethodField()
    specialty_name = serializers.CharField(source="specialty.name", read_only=True, default="")

    class Meta:
        model = DoctorProfile
        fields = ["id", "full_name", "specialty_name", "fee"]

    def get_full_name(self, obj):
        return obj.user.get_full_name()


# ---------------------------------------------------------------------------
# Specialty
# ---------------------------------------------------------------------------

class SpecialtyWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "name", "description"]


# ---------------------------------------------------------------------------
# Availability Slot
# ---------------------------------------------------------------------------

class AvailabilitySlotSerializer(serializers.ModelSerializer):
    doctor = DoctorMinimalSerializer(read_only=True)
    day_of_week_display = serializers.CharField(
        source="get_day_of_week_display", read_only=True
    )

    class Meta:
        model = AvailabilitySlot
        fields = [
            "id", "doctor", "day_of_week", "day_of_week_display",
            "start_time", "end_time", "is_active",
        ]
        read_only_fields = ["id", "doctor"]

    def validate(self, attrs):
        start = attrs.get("start_time")
        end = attrs.get("end_time")
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )
        return attrs


class AvailabilitySlotWriteSerializer(serializers.ModelSerializer):
    """Used by doctor to create/update their own slots (no doctor field in input)."""
    class Meta:
        model = AvailabilitySlot
        fields = ["id", "day_of_week", "start_time", "end_time", "is_active"]
        read_only_fields = ["id"]

    def validate(self, attrs):
        start = attrs.get("start_time") or getattr(self.instance, "start_time", None)
        end = attrs.get("end_time") or getattr(self.instance, "end_time", None)
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )
        return attrs


# ---------------------------------------------------------------------------
# Doctor Profile
# ---------------------------------------------------------------------------

class DoctorProfileListSerializer(serializers.ModelSerializer):
    """Public doctor list — only verified doctors, concise fields."""
    full_name = serializers.SerializerMethodField()
    specialty = SpecialtySerializer(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "full_name", "email", "specialty",
            "bio", "fee", "experience_years", "is_verified",
        ]

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class DoctorProfileDetailSerializer(serializers.ModelSerializer):
    """Full doctor detail including availability slots."""
    full_name = serializers.SerializerMethodField()
    email = serializers.EmailField(source="user.email", read_only=True)
    specialty = SpecialtySerializer(read_only=True)
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        source="specialty",
        write_only=True,
        required=False,
        allow_null=True,
    )
    availability_slots = AvailabilitySlotSerializer(many=True, read_only=True)

    class Meta:
        model = DoctorProfile
        fields = [
            "id", "full_name", "email", "specialty", "specialty_id",
            "bio", "fee", "experience_years", "is_verified",
            "availability_slots", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_verified", "created_at", "updated_at"]

    def get_full_name(self, obj):
        return obj.user.get_full_name()


class DoctorProfileUpdateSerializer(serializers.ModelSerializer):
    """Doctor self-update: bio, fee, experience, specialty only."""
    specialty_id = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(),
        source="specialty",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = DoctorProfile
        fields = ["specialty_id", "bio", "fee", "experience_years"]


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------

class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Write-only serializer for booking a new appointment."""
    appointment_time = serializers.TimeField(required=False)

    class Meta:
        model = Appointment
        fields = ["id", "slot", "date", "appointment_time", "reason"]
        read_only_fields = ["id"]
        validators = []  # Concurrency/uniqueness checked transactionally in view with SELECT FOR UPDATE

    def validate_slot(self, value):
        if not value.is_active:
            raise serializers.ValidationError("This availability slot is not active.")
        return value

    def validate(self, attrs):
        slot = attrs.get("slot")
        appt_date = attrs.get("date")
        appt_time = attrs.get("appointment_time")

        if slot and not appt_time:
            appt_time = slot.start_time
            attrs["appointment_time"] = appt_time

        if appt_date is None:
            return attrs

        # Date must be in the future
        if appt_date <= datetime.date.today():
            raise serializers.ValidationError(
                {"date": "Appointment date must be in the future (not today)."}
            )

        # Date must match the slot's day of week
        if slot and appt_date.weekday() != slot.day_of_week:
            raise serializers.ValidationError({
                "date": (
                    f"This slot is only available on "
                    f"{slot.get_day_of_week_display()}s. "
                    f"{appt_date.strftime('%A')} is not valid."
                )
            })

        # appointment_time must fall within the slot's time window
        if slot and appt_time:
            if appt_time < slot.start_time or appt_time >= slot.end_time:
                raise serializers.ValidationError({
                    "appointment_time": (
                        f"Appointment time must be between "
                        f"{slot.start_time.strftime('%H:%M')} and "
                        f"{slot.end_time.strftime('%H:%M')}."
                    )
                })
            # Must be on a 10-minute boundary
            if appt_time.minute % 10 != 0:
                raise serializers.ValidationError({
                    "appointment_time": "Appointment time must be on a 10-minute interval (e.g. 09:00, 09:10, 09:20)."
                })

        return attrs


class AppointmentSerializer(serializers.ModelSerializer):
    """Full read serializer with nested slot/doctor/patient info."""
    slot = AvailabilitySlotSerializer(read_only=True)
    patient = PatientProfileSerializer(read_only=True)
    patient_name = serializers.SerializerMethodField()
    patient_email = serializers.SerializerMethodField()
    has_medical_record = serializers.SerializerMethodField()
    doctor_fee = serializers.SerializerMethodField()
    payment = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "slot", "date",
            "appointment_time", "status", "payment_status", "reason",
            "patient_name", "patient_email",
            "has_medical_record", "doctor_fee", "payment",
            "created_at", "updated_at",
        ]

    def get_patient_name(self, obj):
        return obj.patient.user.get_full_name() if obj.patient and obj.patient.user else ""

    def get_patient_email(self, obj):
        return obj.patient.user.email if obj.patient and obj.patient.user else ""

    def get_has_medical_record(self, obj):
        return hasattr(obj, "medical_record") and obj.medical_record is not None

    def get_doctor_fee(self, obj):
        if obj.slot and obj.slot.doctor:
            return str(obj.slot.doctor.fee)
        return "0.00"

    def get_payment(self, obj):
        if hasattr(obj, "payment") and obj.payment:
            p = obj.payment
            return {
                "id": str(p.id),
                "transaction_id": p.transaction_id,
                "amount": str(p.amount),
                "currency": p.currency,
                "payment_method": p.payment_method,
                "status": p.status,
                "card_last4": p.card_last4,
                "card_brand": p.card_brand,
                "upi_id": p.upi_id,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
        return None


# ---------------------------------------------------------------------------
# Payment
# ---------------------------------------------------------------------------

class PaymentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.user.get_full_name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.user.get_full_name", read_only=True)
    doctor_specialty = serializers.CharField(source="doctor.specialty.name", read_only=True, default="")
    appointment_date = serializers.DateField(source="appointment.date", read_only=True)
    appointment_time = serializers.TimeField(source="appointment.appointment_time", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "appointment", "patient", "doctor",
            "patient_name", "doctor_name", "doctor_specialty",
            "appointment_date", "appointment_time",
            "amount", "currency", "payment_method",
            "transaction_id", "status", "card_last4",
            "card_brand", "upi_id", "paid_at", "created_at",
        ]
        read_only_fields = ["id", "transaction_id", "status", "paid_at", "created_at"]



# ---------------------------------------------------------------------------
# Medical Record
# ---------------------------------------------------------------------------

class MedicalRecordSerializer(serializers.ModelSerializer):
    """Full read + write serializer for medical records."""
    appointment_id = serializers.PrimaryKeyRelatedField(
        queryset=Appointment.objects.all(),
        source="appointment",
        write_only=True,
    )
    created_by = DoctorMinimalSerializer(read_only=True)
    appointment = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = MedicalRecord
        fields = [
            "id", "appointment_id", "appointment",
            "created_by", "diagnosis", "prescription", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_appointment(self, obj):
        return {
            "id": str(obj.appointment.id),
            "date": str(obj.appointment.date),
            "status": obj.appointment.status,
            "patient": {
                "id": str(obj.appointment.patient.id),
                "name": obj.appointment.patient.user.get_full_name(),
            },
        }


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "is_read", "created_at"]
        read_only_fields = ["id", "is_read", "created_at"]
