"""
Management command: python manage.py seed_data

Seeds the database with:
  - 4 Specialties
  - 1 Admin user
  - 5 Doctor users + DoctorProfile (with AvailabilitySlots for the next 7 days)
  - 5 Patient users + PatientProfile

All created records are idempotent — running the command twice won't create duplicates.
"""

import datetime
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Specialty,
    DoctorProfile,
    PatientProfile,
    AvailabilitySlot,
)

User = get_user_model()


SPECIALTIES = [
    {"name": "Cardiology", "description": "Diagnosis and treatment of heart disorders."},
    {"name": "Dermatology", "description": "Diagnosis and treatment of skin conditions."},
    {"name": "Pediatrics", "description": "Medical care for infants, children, and adolescents."},
    {"name": "Orthopedics", "description": "Diagnosis and treatment of musculoskeletal conditions."},
]

DOCTORS = [
    {
        "email": "dr.smith@hospital.com",
        "password": "Doctor123!",
        "first_name": "James",
        "last_name": "Smith",
        "specialty": "Cardiology",
        "bio": "Board-certified cardiologist with 15 years of experience.",
        "fee": "800.00",
        "experience_years": 15,
        "is_verified": True,
        # Slots: Mon Wed Fri 09:00-10:00 and 10:00-11:00
        "slots": [
            {"day": 0, "start": "09:00", "end": "10:00"},
            {"day": 0, "start": "10:00", "end": "11:00"},
            {"day": 2, "start": "09:00", "end": "10:00"},
            {"day": 2, "start": "10:00", "end": "11:00"},
            {"day": 4, "start": "09:00", "end": "10:00"},
        ],
    },
    {
        "email": "dr.johnson@hospital.com",
        "password": "Doctor123!",
        "first_name": "Emily",
        "last_name": "Johnson",
        "specialty": "Dermatology",
        "bio": "Specialist in skin diseases and cosmetic dermatology.",
        "fee": "650.00",
        "experience_years": 10,
        "is_verified": True,
        "slots": [
            {"day": 1, "start": "10:00", "end": "11:00"},
            {"day": 1, "start": "11:00", "end": "12:00"},
            {"day": 3, "start": "14:00", "end": "15:00"},
            {"day": 3, "start": "15:00", "end": "16:00"},
            {"day": 5, "start": "10:00", "end": "11:00"},
        ],
    },
    {
        "email": "dr.patel@hospital.com",
        "password": "Doctor123!",
        "first_name": "Anika",
        "last_name": "Patel",
        "specialty": "Pediatrics",
        "bio": "Dedicated pediatrician focused on child wellness and development.",
        "fee": "500.00",
        "experience_years": 8,
        "is_verified": True,
        "slots": [
            {"day": 0, "start": "11:00", "end": "12:00"},
            {"day": 2, "start": "11:00", "end": "12:00"},
            {"day": 4, "start": "11:00", "end": "12:00"},
            {"day": 4, "start": "12:00", "end": "13:00"},
        ],
    },
    {
        "email": "dr.lee@hospital.com",
        "password": "Doctor123!",
        "first_name": "Michael",
        "last_name": "Lee",
        "specialty": "Orthopedics",
        "bio": "Expert in joint replacement and sports medicine.",
        "fee": "1200.00",
        "experience_years": 20,
        "is_verified": True,
        "slots": [
            {"day": 1, "start": "09:00", "end": "10:00"},
            {"day": 3, "start": "09:00", "end": "10:00"},
            {"day": 5, "start": "09:00", "end": "10:00"},
            {"day": 5, "start": "10:00", "end": "11:00"},
        ],
    },
    {
        "email": "dr.garcia@hospital.com",
        "password": "Doctor123!",
        "first_name": "Sofia",
        "last_name": "Garcia",
        "specialty": "Cardiology",
        "bio": "Specializes in non-invasive cardiology and preventive care.",
        "fee": "750.00",
        "experience_years": 12,
        "is_verified": False,
        "slots": [
            {"day": 0, "start": "14:00", "end": "15:00"},
            {"day": 2, "start": "14:00", "end": "15:00"},
            {"day": 4, "start": "14:00", "end": "15:00"},
        ],
    },
]

PATIENTS = [
    {
        "email": "patient.alice@example.com",
        "password": "Patient123!",
        "first_name": "Alice",
        "last_name": "Walker",
        "dob": "1990-05-12",
        "phone": "+1-555-0101",
        "address": "123 Oak Street, Springfield",
        "blood_group": "A+",
    },
    {
        "email": "patient.bob@example.com",
        "password": "Patient123!",
        "first_name": "Bob",
        "last_name": "Martin",
        "dob": "1985-11-23",
        "phone": "+1-555-0102",
        "address": "456 Elm Avenue, Shelbyville",
        "blood_group": "O-",
    },
    {
        "email": "patient.carol@example.com",
        "password": "Patient123!",
        "first_name": "Carol",
        "last_name": "Davis",
        "dob": "2000-03-08",
        "phone": "+1-555-0103",
        "address": "789 Pine Road, Capital City",
        "blood_group": "B+",
    },
    {
        "email": "patient.david@example.com",
        "password": "Patient123!",
        "first_name": "David",
        "last_name": "Wilson",
        "dob": "1975-07-19",
        "phone": "+1-555-0104",
        "address": "321 Maple Lane, Ogdenville",
        "blood_group": "AB+",
    },
    {
        "email": "patient.emma@example.com",
        "password": "Patient123!",
        "first_name": "Emma",
        "last_name": "Thompson",
        "dob": "1995-09-30",
        "phone": "+1-555-0105",
        "address": "654 Birch Boulevard, North Haverbrook",
        "blood_group": "O+",
    },
]


class Command(BaseCommand):
    help = "Seeds the database with specialties, doctors, patients, and availability slots."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Seeding Database ===\n"))

        # 1. Specialties
        self.stdout.write("Creating specialties...")
        specialty_map = {}
        for spec_data in SPECIALTIES:
            spec, created = Specialty.objects.get_or_create(
                name=spec_data["name"],
                defaults={"description": spec_data["description"]},
            )
            specialty_map[spec.name] = spec
            status_label = "created" if created else "exists"
            marker = "[OK]" if created else "[--]"
            self.stdout.write(f"  {marker} {spec.name} [{status_label}]")

        # 2. Admin user
        self.stdout.write("\nCreating admin user...")
        admin_user, created = User.objects.get_or_create(
            email="admin@hospital.com",
            defaults={
                "first_name": "System",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            admin_user.set_password("Admin123!")
            admin_user.save()
            self.stdout.write("  [OK] admin@hospital.com (password: Admin123!)")
        else:
            self.stdout.write("  [--] admin@hospital.com [exists]")

        # 3. Doctors + slots
        self.stdout.write("\nCreating doctors and availability slots...")
        for doc_data in DOCTORS:
            user, created = User.objects.get_or_create(
                email=doc_data["email"],
                defaults={
                    "first_name": doc_data["first_name"],
                    "last_name": doc_data["last_name"],
                    "role": User.Role.DOCTOR,
                },
            )
            if created:
                user.set_password(doc_data["password"])
                user.save()

            profile, _ = DoctorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "specialty": specialty_map.get(doc_data["specialty"]),
                    "bio": doc_data["bio"],
                    "fee": doc_data["fee"],
                    "experience_years": doc_data["experience_years"],
                    "is_verified": doc_data["is_verified"],
                },
            )

            slot_count = 0
            for slot_def in doc_data["slots"]:
                start = datetime.time(*map(int, slot_def["start"].split(":")))
                end = datetime.time(*map(int, slot_def["end"].split(":")))
                _, slot_created = AvailabilitySlot.objects.get_or_create(
                    doctor=profile,
                    day_of_week=slot_def["day"],
                    start_time=start,
                    defaults={"end_time": end, "is_active": True},
                )
                if slot_created:
                    slot_count += 1

            status_label = "created" if created else "exists"
            marker = "[OK]" if created else "[--]"
            self.stdout.write(
                f"  {marker} Dr. {doc_data['first_name']} {doc_data['last_name']}"
                f" [{status_label}] - {slot_count} new slot(s)"
            )

        # 4. Patients
        self.stdout.write("\nCreating patients...")
        for pat_data in PATIENTS:
            user, created = User.objects.get_or_create(
                email=pat_data["email"],
                defaults={
                    "first_name": pat_data["first_name"],
                    "last_name": pat_data["last_name"],
                    "role": User.Role.PATIENT,
                },
            )
            if created:
                user.set_password(pat_data["password"])
                user.save()

            PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    "dob": datetime.date.fromisoformat(pat_data["dob"]),
                    "phone": pat_data["phone"],
                    "address": pat_data["address"],
                    "blood_group": pat_data["blood_group"],
                },
            )

            status_label = "created" if created else "exists"
            marker = "[OK]" if created else "[--]"
            self.stdout.write(
                f"  {marker} {pat_data['first_name']} {pat_data['last_name']}"
                f" [{status_label}]"
            )

        # Summary
        self.stdout.write(self.style.SUCCESS(
            f"\n=== Seed Complete ===\n"
            f"  Specialties : {Specialty.objects.count()}\n"
            f"  Doctors     : {DoctorProfile.objects.count()}\n"
            f"  Patients    : {PatientProfile.objects.count()}\n"
            f"  Slots       : {AvailabilitySlot.objects.count()}\n"
        ))
