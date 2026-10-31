# Hospital Appointment Management System

A full-stack application for managing hospital appointments, built with **Django REST Framework** (backend) and **React + Vite** (frontend).

---

## Project Structure

```
Hospital management/
├── backend/          # Django REST API
│   ├── config/       # Django project settings
│   ├── core/         # Main application (Models, Views, Serializers, Tasks)
│   ├── manage.py
│   ├── requirements.txt
│   └── .env
├── frontend/         # React + Vite + Tailwind CSS
│   ├── src/          # React components, pages, context, API
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml # Local infrastructure (Postgres + Redis)
```

## Tech Stack

### Backend
- Python 3.12+ / Django 4.2
- Django REST Framework + SimpleJWT
- drf-spectacular (OpenAPI / Swagger)
- Celery + Redis (async tasks & periodic jobs)
- PostgreSQL

### Frontend
- React 18 + Vite
- Tailwind CSS (Custom Medical Theme)
- Axios + React Router + Recharts + Lucide Icons

---

## Local Development Setup

### 1. Infrastructure (Database & Message Broker)
Make sure you have Docker Desktop installed and running.
```bash
docker-compose up -d
```
*This starts PostgreSQL on port 5432 and Redis on port 6379.*

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Edit .env and set your DB credentials and email settings

# Database migrations
python manage.py migrate

# Seed initial data (Doctors, Patients, Specialties, Slots, Admin)
python manage.py seed_data

# Start the Django server
python manage.py runserver
```
API docs available at: `http://localhost:8000/api/docs/`

### 3. Background Tasks (Celery)
In a new terminal (with the virtual environment activated):
```bash
cd backend
# Start the Celery worker (processes emails)
celery -A config worker -l info --pool=solo

# Start the Celery beat (processes periodic reminders)
celery -A config beat -l info
```

### 4. Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
App runs at: `http://localhost:5173`

---

## Key Features & End-to-End Flows

1. **Authentication:** JWT-based login with role separation (Admin, Doctor, Patient).
2. **Booking Flow:** Patient selects Doctor -> Picks Date/Slot -> Appointment Confirmed -> Email sent via Celery.
3. **Appointment Lifecycle:** Patient can reschedule/cancel. Doctor marks as Completed or No Show.
4. **Medical Records:** Doctor adds diagnosis/prescription post-completion. Patient views them securely.
5. **Admin Dashboard:** System-wide stats, Recharts visualizations, doctor verification, and broadcast announcements.
6. **Background Jobs:** Celery Beat runs hourly to send reminders for upcoming appointments (within 24 hours).

---

## Testing

Comprehensive edge case tests cover booking rules, permission checks, overlapping constraints, and medical record logic.

```bash
cd backend
python manage.py test core.tests -v 2
```

---

## License
This project is for educational purposes.
