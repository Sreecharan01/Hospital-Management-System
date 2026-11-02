"""
Test suite for Hospital Appointment Management System.
Covers double-booking prevention and appointment booking business rules.

Run with:
    python manage.py test core.tests -v 2
"""

import datetime

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import (
    Appointment,
    AvailabilitySlot,
    DoctorProfile,
    Notification,
    PatientProfile,
    Specialty,
)

User = get_user_model()


def next_weekday(weekday: int, days_ahead_min: int = 1) -> datetime.date:
    """
    Return the next date matching the given weekday (0=Mon … 6=Sun)
    that is at least `days_ahead_min` days in the future.
    """
    candidate = datetime.date.today() + datetime.timedelta(days=days_ahead_min)
    while candidate.weekday() != weekday:
        candidate += datetime.timedelta(days=1)
    return candidate


class BaseTestCase(APITestCase):
    """Shared setUp for all test classes: one doctor (Mon slot) + two patients."""

    @classmethod
    def setUpTestData(cls):
        # Specialty
        cls.specialty = Specialty.objects.create(
            name="Test Specialty", description="For testing."
        )

        # Doctor
        cls.doctor_user = User.objects.create_user(
            email="dr.test@hospital.com",
            password="Doctor123!",
            first_name="Test",
            last_name="Doctor",
            role="DOCTOR",
        )
        cls.doctor_profile = DoctorProfile.objects.create(
            user=cls.doctor_user,
            specialty=cls.specialty,
            fee="100.00",
            experience_years=5,
            is_verified=True,
        )
        # Slot: Monday 09:00-10:00
        cls.slot = AvailabilitySlot.objects.create(
            doctor=cls.doctor_profile,
            day_of_week=0,  # Monday
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            is_active=True,
        )

        # Patient 1
        cls.patient1_user = User.objects.create_user(
            email="patient1@test.com",
            password="Patient123!",
            first_name="Alice",
            last_name="Test",
            role="PATIENT",
        )
        cls.patient1_profile = PatientProfile.objects.create(user=cls.patient1_user)

        # Patient 2
        cls.patient2_user = User.objects.create_user(
            email="patient2@test.com",
            password="Patient123!",
            first_name="Bob",
            last_name="Test",
            role="PATIENT",
        )
        cls.patient2_profile = PatientProfile.objects.create(user=cls.patient2_user)

        # Admin
        cls.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="Admin123!",
            first_name="Admin",
            last_name="Test",
            role="ADMIN",
            is_staff=False,   # not is_staff so DRF doesn't bypass IsPatient
            is_superuser=False,
        )

        # Next Monday (in the future)
        cls.next_monday = next_weekday(weekday=0, days_ahead_min=1)

    def _book(self, user, slot=None, date=None, reason="Checkup"):
        """Helper: authenticate as `user` and POST an appointment."""
        self.client.force_authenticate(user=user)
        return self.client.post(
            reverse("appointment-list"),
            data={
                "slot": str(slot or self.slot.id),
                "date": str(date or self.next_monday),
                "reason": reason,
            },
            format="json",
        )


# ---------------------------------------------------------------------------
# Double-Booking Tests
# ---------------------------------------------------------------------------

class DoubleBookingTest(BaseTestCase):
    """Core double-booking prevention rules."""

    def test_first_booking_succeeds(self):
        """A booking on a free slot+date should return 201."""
        response = self._book(self.patient1_user)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "PENDING")

    def test_double_booking_is_rejected(self):
        """Second booking on the same slot+date (different patient) must return 400."""
        self._book(self.patient1_user)  # First booking succeeds

        response = self._book(self.patient2_user)  # Second must fail
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_patient_cannot_double_book(self):
        """A patient cannot book the same slot+date twice."""
        self._book(self.patient1_user)
        response = self._book(self.patient1_user)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cancelled_slot_can_be_rebooked(self):
        """After cancellation the slot+date becomes available again."""
        # Book and get appointment id
        r = self._book(self.patient1_user)
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        appt_id = r.data["id"]

        # Cancel it
        self.client.force_authenticate(user=self.patient1_user)
        cancel_resp = self.client.post(reverse("appointment-cancel", kwargs={"pk": appt_id}))
        self.assertEqual(cancel_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(cancel_resp.data["status"], "CANCELLED")

        # Patient2 can now book the same slot+date
        r2 = self._book(self.patient2_user)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)

    def test_different_date_is_independent(self):
        """Same slot on a different (next) week's Monday is always available."""
        self._book(self.patient1_user, date=self.next_monday)

        next_next_monday = next_weekday(weekday=0, days_ahead_min=8)
        response = self._book(self.patient2_user, date=next_next_monday)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Date Validation Tests
# ---------------------------------------------------------------------------

class DateValidationTest(BaseTestCase):
    """Validates date-related booking rules."""

    def test_past_date_rejected(self):
        """Booking a date in the past should return 400."""
        past_date = datetime.date.today() - datetime.timedelta(days=1)
        response = self._book(self.patient1_user, date=past_date)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_today_rejected(self):
        """Booking for today should return 400 (must be strictly in future)."""
        response = self._book(self.patient1_user, date=datetime.date.today())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_wrong_weekday_rejected(self):
        """A date whose weekday doesn't match the slot's day_of_week → 400."""
        # Slot is Monday (0); pick next Tuesday
        next_tuesday = next_weekday(weekday=1, days_ahead_min=1)
        response = self._book(self.patient1_user, date=next_tuesday)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_correct_weekday_accepted(self):
        """A future date matching the slot's weekday should succeed."""
        response = self._book(self.patient1_user, date=self.next_monday)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Permission Tests
# ---------------------------------------------------------------------------

class BookingPermissionTest(BaseTestCase):
    """Role-based access control on appointment creation."""

    def test_doctor_cannot_book(self):
        """Doctors should receive 403 when trying to book an appointment."""
        response = self._book(self.doctor_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_cannot_book(self):
        """Admins (who don't have a patient profile) should receive 403."""
        response = self._book(self.admin_user)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_book(self):
        """Unauthenticated requests should receive 401."""
        response = self.client.post(
            reverse("appointment-list"),
            data={"slot": str(self.slot.id), "date": str(self.next_monday)},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patient_cannot_cancel_others_appointment(self):
        """Patient2 cannot cancel Patient1's appointment."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]

        self.client.force_authenticate(user=self.patient2_user)
        resp = self.client.post(reverse("appointment-cancel", kwargs={"pk": appt_id}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Slot Validation Tests
# ---------------------------------------------------------------------------

class SlotValidationTest(BaseTestCase):
    """Validates slot activity and ownership rules."""

    def test_inactive_slot_rejected(self):
        """Booking an inactive slot should return 400."""
        inactive_slot = AvailabilitySlot.objects.create(
            doctor=self.doctor_profile,
            day_of_week=0,  # Monday
            start_time=datetime.time(11, 0),
            end_time=datetime.time(12, 0),
            is_active=False,
        )
        response = self._book(self.patient1_user, slot=inactive_slot.id)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_doctor_can_create_slot(self):
        """A doctor can create an availability slot."""
        self.client.force_authenticate(user=self.doctor_user)
        response = self.client.post(
            reverse("slot-list"),
            data={"day_of_week": 2, "start_time": "14:00:00", "end_time": "15:00:00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_patient_cannot_create_slot(self):
        """A patient must receive 403 when trying to create a slot."""
        self.client.force_authenticate(user=self.patient1_user)
        response = self.client.post(
            reverse("slot-list"),
            data={"day_of_week": 2, "start_time": "14:00:00", "end_time": "15:00:00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Reschedule Tests
# ---------------------------------------------------------------------------

class RescheduleTest(BaseTestCase):
    """Tests for the /reschedule/ action."""

    def test_reschedule_to_free_slot(self):
        """Patient can reschedule to a free slot+date."""
        r = self._book(self.patient1_user, date=self.next_monday)
        appt_id = r.data["id"]

        next_next_monday = next_weekday(weekday=0, days_ahead_min=8)

        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.post(
            reverse("appointment-reschedule", kwargs={"pk": appt_id}),
            data={"slot": str(self.slot.id), "date": str(next_next_monday)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["date"], str(next_next_monday))

    def test_reschedule_conflict_rejected(self):
        """Reschedule to an already-booked slot+date must fail."""
        # Book slot for patient1 on next_monday
        self._book(self.patient1_user, date=self.next_monday)

        # Book a different week for patient2
        next_next_monday = next_weekday(weekday=0, days_ahead_min=8)
        r2 = self._book(self.patient2_user, date=next_next_monday)
        appt2_id = r2.data["id"]

        # Try to reschedule patient2's appt to next_monday (already taken by patient1)
        self.client.force_authenticate(user=self.patient2_user)
        resp = self.client.post(
            reverse("appointment-reschedule", kwargs={"pk": appt2_id}),
            data={"slot": str(self.slot.id), "date": str(self.next_monday)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Notification Tests
# ---------------------------------------------------------------------------

class NotificationTest(BaseTestCase):
    """Verify notifications are created on booking events."""

    def test_booking_creates_two_notifications(self):
        """Booking should create one notification for patient, one for doctor."""
        before_count = Notification.objects.count()
        self._book(self.patient1_user)
        after_count = Notification.objects.count()
        self.assertEqual(after_count - before_count, 2)

    def test_patient_notification_belongs_to_patient(self):
        """Patient's notification should be in their inbox."""
        self._book(self.patient1_user)
        patient_notifs = Notification.objects.filter(user=self.patient1_user)
        self.assertTrue(patient_notifs.exists())

    def test_mark_all_read(self):
        """mark_all_read should flip all unread notifications to is_read=True."""
        self._book(self.patient1_user)

        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.post(reverse("notification-mark-all-read"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            Notification.objects.filter(user=self.patient1_user, is_read=False).count(), 0
        )


# ---------------------------------------------------------------------------
# Doctor Filter Tests
# ---------------------------------------------------------------------------

class DoctorFilterTest(BaseTestCase):
    """Tests for GET /api/doctors/ query parameters."""

    def test_list_shows_only_verified(self):
        """Public doctor list should only include verified doctors."""
        # Create an unverified doctor
        unverified_user = User.objects.create_user(
            email="unverified@test.com", password="test123", role="DOCTOR"
        )
        DoctorProfile.objects.create(user=unverified_user, is_verified=False)

        response = self.client.get(reverse("doctor-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids_in_response = {d["id"] for d in response.data}
        all_unverified = DoctorProfile.objects.filter(is_verified=False).values_list(
            "id", flat=True
        )
        for uid in all_unverified:
            self.assertNotIn(str(uid), ids_in_response)

    def test_filter_by_available_day(self):
        """?available_day=0 should return doctors with active Monday slots."""
        response = self.client.get(reverse("doctor-list") + "?available_day=0")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Our test doctor has a Monday slot and is verified
        ids = [d["id"] for d in response.data]
        self.assertIn(str(self.doctor_profile.id), ids)

    def test_filter_by_specialty(self):
        """?specialty=<name> filter should work."""
        response = self.client.get(
            reverse("doctor-list") + f"?specialty=Test+Specialty"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)


# ---------------------------------------------------------------------------
# Booking Lifecycle Edge Case Tests
# ---------------------------------------------------------------------------

class BookingLifecycleTest(BaseTestCase):
    """End-to-end lifecycle: book → complete → add record."""

    def test_complete_flow(self):
        """Doctor can mark a CONFIRMED appointment as COMPLETED."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]

        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(reverse("appointment-confirm", kwargs={"pk": appt_id}))
        resp = self.client.post(reverse("appointment-complete", kwargs={"pk": appt_id}))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "COMPLETED")

    def test_expire_flow(self):
        """Doctor can mark an appointment as EXPIRED."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]

        self.client.force_authenticate(user=self.doctor_user)
        resp = self.client.post(reverse("appointment-expire", kwargs={"pk": appt_id}))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["status"], "EXPIRED")

    def test_cannot_complete_cancelled(self):
        """Cannot complete an already cancelled appointment."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]

        # Confirm
        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(reverse("appointment-confirm", kwargs={"pk": appt_id}))

        # Cancel
        self.client.force_authenticate(user=self.patient1_user)
        self.client.post(reverse("appointment-cancel", kwargs={"pk": appt_id}))

        # Try to complete
        self.client.force_authenticate(user=self.doctor_user)
        resp = self.client.post(reverse("appointment-complete", kwargs={"pk": appt_id}))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_cancel_completed(self):
        """Cannot cancel an already completed appointment."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]

        # Confirm and Complete
        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(reverse("appointment-confirm", kwargs={"pk": appt_id}))
        self.client.post(reverse("appointment-complete", kwargs={"pk": appt_id}))

        # Try to cancel
        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.post(reverse("appointment-cancel", kwargs={"pk": appt_id}))
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patient_cannot_complete(self):
        """Only doctors can mark appointments as completed."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]

        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.post(reverse("appointment-complete", kwargs={"pk": appt_id}))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# Medical Record Edge Case Tests
# ---------------------------------------------------------------------------

class MedicalRecordEdgeCaseTest(BaseTestCase):
    """Tests for medical record creation rules."""

    def _complete_appointment(self):
        """Helper: book and complete an appointment, return appt_id."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]
        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(reverse("appointment-confirm", kwargs={"pk": appt_id}))
        self.client.post(reverse("appointment-complete", kwargs={"pk": appt_id}))
        return appt_id

    def test_record_for_completed_appointment(self):
        """Doctor can create a medical record for a COMPLETED appointment."""
        appt_id = self._complete_appointment()
        self.client.force_authenticate(user=self.doctor_user)
        resp = self.client.post(
            reverse("record-list"),
            data={
                "appointment_id": appt_id,
                "diagnosis": "Mild hypertension",
                "prescription": "Amlodipine 5mg daily",
                "notes": "Follow up in 2 weeks",
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_record_for_non_completed_rejected(self):
        """Cannot create a record for a CONFIRMED (not completed) appointment."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]

        self.client.force_authenticate(user=self.doctor_user)
        resp = self.client.post(
            reverse("record-list"),
            data={"appointment_id": appt_id, "diagnosis": "Test"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_record_rejected(self):
        """Cannot create two records for the same appointment."""
        appt_id = self._complete_appointment()
        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(
            reverse("record-list"),
            data={"appointment_id": appt_id, "diagnosis": "First"},
            format="json",
        )
        resp = self.client.post(
            reverse("record-list"),
            data={"appointment_id": appt_id, "diagnosis": "Second"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patient_cannot_create_record(self):
        """Patients cannot create medical records."""
        appt_id = self._complete_appointment()
        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.post(
            reverse("record-list"),
            data={"appointment_id": appt_id, "diagnosis": "Self-diagnosis"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_patient_can_view_own_records(self):
        """Patient can see records for their own appointments."""
        appt_id = self._complete_appointment()
        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(
            reverse("record-list"),
            data={"appointment_id": appt_id, "diagnosis": "Diagnosis text"},
            format="json",
        )

        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.get(reverse("record-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        records = resp.data if isinstance(resp.data, list) else resp.data.get("results", [])
        self.assertEqual(len(records), 1)


# ---------------------------------------------------------------------------
# Cancel Notification Tests
# ---------------------------------------------------------------------------

class CancelNotificationTest(BaseTestCase):
    """Verify cancel creates the right notifications."""

    def test_patient_cancel_notifies_doctor(self):
        """When patient cancels, doctor gets a notification."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]
        doctor_notif_before = Notification.objects.filter(user=self.doctor_user).count()

        self.client.force_authenticate(user=self.patient1_user)
        self.client.post(reverse("appointment-cancel", kwargs={"pk": appt_id}))

        doctor_notif_after = Notification.objects.filter(user=self.doctor_user).count()
        self.assertGreater(doctor_notif_after, doctor_notif_before)

    def test_doctor_cancel_notifies_patient(self):
        """When doctor cancels, patient gets a notification."""
        r = self._book(self.patient1_user)
        appt_id = r.data["id"]
        patient_notif_before = Notification.objects.filter(user=self.patient1_user).count()

        self.client.force_authenticate(user=self.doctor_user)
        self.client.post(reverse("appointment-cancel", kwargs={"pk": appt_id}))

        patient_notif_after = Notification.objects.filter(user=self.patient1_user).count()
        self.assertGreater(patient_notif_after, patient_notif_before)


# ---------------------------------------------------------------------------
# Reschedule Validation Edge Cases
# ---------------------------------------------------------------------------

class RescheduleEdgeCaseTest(BaseTestCase):
    """Additional reschedule validations."""

    def test_reschedule_to_wrong_weekday(self):
        """Reschedule date must match the slot's weekday."""
        r = self._book(self.patient1_user, date=self.next_monday)
        appt_id = r.data["id"]

        next_tuesday = next_weekday(weekday=1, days_ahead_min=1)
        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.post(
            reverse("appointment-reschedule", kwargs={"pk": appt_id}),
            data={"slot": str(self.slot.id), "date": str(next_tuesday)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reschedule_to_past_date(self):
        """Cannot reschedule to a past date."""
        r = self._book(self.patient1_user, date=self.next_monday)
        appt_id = r.data["id"]

        past = datetime.date.today() - datetime.timedelta(days=7)
        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.post(
            reverse("appointment-reschedule", kwargs={"pk": appt_id}),
            data={"slot": str(self.slot.id), "date": str(past)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_doctor_cannot_reschedule(self):
        """Only patients can reschedule."""
        r = self._book(self.patient1_user, date=self.next_monday)
        appt_id = r.data["id"]

        next_next_monday = next_weekday(weekday=0, days_ahead_min=8)
        self.client.force_authenticate(user=self.doctor_user)
        resp = self.client.post(
            reverse("appointment-reschedule", kwargs={"pk": appt_id}),
            data={"slot": str(self.slot.id), "date": str(next_next_monday)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_reschedule_cancelled_rejected(self):
        """Cannot reschedule a CANCELLED appointment."""
        r = self._book(self.patient1_user, date=self.next_monday)
        appt_id = r.data["id"]

        # Cancel first
        self.client.force_authenticate(user=self.patient1_user)
        self.client.post(reverse("appointment-cancel", kwargs={"pk": appt_id}))

        # Try reschedule
        next_next_monday = next_weekday(weekday=0, days_ahead_min=8)
        resp = self.client.post(
            reverse("appointment-reschedule", kwargs={"pk": appt_id}),
            data={"slot": str(self.slot.id), "date": str(next_next_monday)},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Admin Stats Access Control
# ---------------------------------------------------------------------------

class AdminStatsAccessTest(BaseTestCase):
    """Ensure only admins can access the stats endpoint."""

    def test_admin_can_access_stats(self):
        self.client.force_authenticate(user=self.admin_user)
        # Make admin_user a proper admin with is_staff so IsAdminRole passes
        self.admin_user.is_staff = True
        self.admin_user.save()
        resp = self.client.get(reverse("admin-stats"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("users", resp.data)
        self.assertIn("appointments", resp.data)
        self.assertIn("appointments_per_day", resp.data)

    def test_patient_cannot_access_stats(self):
        self.client.force_authenticate(user=self.patient1_user)
        resp = self.client.get(reverse("admin-stats"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_doctor_cannot_access_stats(self):
        self.client.force_authenticate(user=self.doctor_user)
        resp = self.client.get(reverse("admin-stats"))
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


# ---------------------------------------------------------------------------
# 10-Minute Interval Booking Tests
# ---------------------------------------------------------------------------

class TenMinuteIntervalBookingTest(BaseTestCase):
    """Test 10-minute intervals and overlap detection."""

    def test_booking_different_10_min_slots_succeeds(self):
        """Two patients can book different 10-minute intervals in the same doctor slot."""
        self.client.force_authenticate(user=self.patient1_user)
        r1 = self.client.post(
            reverse("appointment-list"),
            data={
                "slot": str(self.slot.id),
                "date": str(self.next_monday),
                "appointment_time": "09:10",
            },
            format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r1.data["appointment_time"], "09:10:00")

        # Patient 2 books 09:20 on the same date and doctor slot
        self.client.force_authenticate(user=self.patient2_user)
        r2 = self.client.post(
            reverse("appointment-list"),
            data={
                "slot": str(self.slot.id),
                "date": str(self.next_monday),
                "appointment_time": "09:20",
            },
            format="json",
        )
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.data["appointment_time"], "09:20:00")

    def test_overlapping_10_min_slot_is_rejected(self):
        """Booking the exact same 10-minute slot should be rejected and notify patient."""
        self.client.force_authenticate(user=self.patient1_user)
        r1 = self.client.post(
            reverse("appointment-list"),
            data={
                "slot": str(self.slot.id),
                "date": str(self.next_monday),
                "appointment_time": "09:10",
            },
            format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)

        # Patient 2 tries to book the same 09:10 time
        self.client.force_authenticate(user=self.patient2_user)
        r2 = self.client.post(
            reverse("appointment-list"),
            data={
                "slot": str(self.slot.id),
                "date": str(self.next_monday),
                "appointment_time": "09:10",
            },
            format="json",
        )
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already booked", str(r2.data))

    def test_available_times_query(self):
        """GET /api/appointments/available-times/ returns intervals with availability."""
        self.client.force_authenticate(user=self.patient1_user)
        self.client.post(
            reverse("appointment-list"),
            data={
                "slot": str(self.slot.id),
                "date": str(self.next_monday),
                "appointment_time": "09:10",
            },
            format="json",
        )

        resp = self.client.get(
            reverse("appointment-available-times"),
            {"slot": str(self.slot.id), "date": str(self.next_monday)},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        times = {item["time"]: item["available"] for item in resp.data["times"]}
        self.assertIn("09:00", times)
        self.assertTrue(times["09:00"])
        self.assertIn("09:10", times)
        self.assertFalse(times["09:10"])  # booked
        self.assertIn("09:20", times)
        self.assertTrue(times["09:20"])

    def test_payment_for_appointment(self):
        """Patient can pay doctor consultation fee online and fetch receipt."""
        self.client.force_authenticate(user=self.patient1_user)
        r = self.client.post(
            reverse("appointment-list"),
            data={
                "slot": str(self.slot.id),
                "date": str(self.next_monday),
                "appointment_time": "09:00",
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        appt_id = r.data["id"]

        # Pay for appointment
        pay_res = self.client.post(
            f"/api/appointments/{appt_id}/pay/",
            data={
                "payment_method": "CARD",
                "card_last4": "4242",
                "card_brand": "Visa",
            },
            format="json",
        )
        self.assertEqual(pay_res.status_code, status.HTTP_200_OK)
        self.assertEqual(pay_res.data["payment"]["status"], "COMPLETED")
        self.assertEqual(pay_res.data["payment"]["amount"], "100.00")

        # Fetch receipt
        rec_res = self.client.get(f"/api/appointments/{appt_id}/receipt/")
        self.assertEqual(rec_res.status_code, status.HTTP_200_OK)
        self.assertEqual(rec_res.data["amount"], "100.00")
        self.assertIn("REC-", rec_res.data["receipt_number"])



