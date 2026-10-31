<div align="center">

<!-- Animated Header Banner -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0ea5e9,100:2563eb&height=220&section=header&text=Hospital%20Management%20System&fontSize=38&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Full-Stack%20Healthcare%20Platform%20%E2%80%A2%20Smart%2010-Min%20Slot%20Booking%20%E2%80%A2%20Doctor%20Acceptance%20Flow&descAlignY=58&descAlign=50" width="100%" alt="Header" />

<!-- Dynamic Typing SVG Animation -->
<p align="center">
  <a href="https://github.com/Sreecharan01/Hospital-Management-System">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=20&duration=3000&pause=1000&color=0284C7&center=true&vCenter=true&width=650&lines=Seamless+Doctor+%26+Patient+Management;Smart+10-Minute+Time-Slot+Booking;Real-Time+Overlap+Detection+%26+Conflict+Alerts;Doctor+Acceptance+%26+Patient+Attendance+Flow;Automated+Email+Reminders+via+Celery" alt="Typing SVG" />
  </a>
</p>

<!-- Badges Strip -->
<p align="center">
  <img src="https://img.shields.io/badge/Django_REST-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django" />
  <img src="https://img.shields.io/badge/React_18-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind" />
  <img src="https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white" alt="Celery" />
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="Postgres" />
  <img src="https://img.shields.io/badge/Tests-46%20Passed-success?style=for-the-badge&logo=pytest&logoColor=white" alt="Tests" />
</p>

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-system-architecture">Architecture</a> •
  <a href="#-appointment-lifecycle">Lifecycle Flow</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-api-endpoints">API Docs</a> •
  <a href="#-testing">Testing</a>
</p>

</div>

---

## 🩺 Overview

The **Hospital Appointment Management System** is an enterprise-grade healthcare management application designed to streamline the appointment booking, confirmation, and medical consultation pipeline. Built with **Django REST Framework** on the backend and **React + Vite + Tailwind CSS** on the frontend, it provides a high-reliability booking experience with concurrency safeguards, precise **10-minute slot scheduling**, and transparent doctor-patient interactions.

---

## ✨ Key Features

<table>
  <tr>
    <td width="50%">
      <h3>⏱️ 10-Minute Smart Booking</h3>
      <ul>
        <li>Doctor availability windows broken into selectable <b>10-minute intervals</b>.</li>
        <li>Real-time slot availability indicators (active vs. booked).</li>
        <li>Instant visual alerts and API validation preventing duplicate bookings.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>🤝 Doctor Acceptance Workflow</h3>
      <ul>
        <li>Appointments begin in <code>PENDING</code> status upon booking.</li>
        <li>Doctor reviews and can <b>Accept</b> (<code>CONFIRMED</code>) or <b>Decline</b>.</li>
        <li>Attended appointments transition to <code>COMPLETED</code>; no-shows become <code>EXPIRED</code>.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>🛡️ Concurrency & Overlap Protection</h3>
      <ul>
        <li><code>SELECT FOR UPDATE</code> database locking during booking transactions.</li>
        <li>Conditional unique constraints permitting re-booking of cancelled time slots.</li>
        <li>Role-based access control protecting medical history and slot modifications.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📬 Notifications & Background Tasks</h3>
      <ul>
        <li>In-app notifications for patients and doctors upon booking and state changes.</li>
        <li>Asynchronous transactional email confirmations dispatched via <b>Celery</b>.</li>
        <li><b>Celery Beat</b> cron scheduler dispatching 24-hour pre-appointment reminders.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%">
      <h3>📋 Digital Medical Records</h3>
      <ul>
        <li>Doctors generate diagnosis, prescriptions, and follow-up notes post-visit.</li>
        <li>Strict one-record-per-appointment rule to preserve audit integrity.</li>
        <li>Secure patient portal for accessing historical consultations.</li>
      </ul>
    </td>
    <td width="50%">
      <h3>📊 Admin Analytics Dashboard</h3>
      <ul>
        <li>Interactive consultation analytics with <b>Recharts</b>.</li>
        <li>Doctor verification pipeline for regulatory onboarding.</li>
        <li>System-wide broadcast announcements via push notifications and bulk email.</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🔄 Appointment Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Patient Books 10-Min Slot
    PENDING --> CONFIRMED: Doctor Accepts
    PENDING --> CANCELLED: Doctor Declines / Patient Cancels

    CONFIRMED --> COMPLETED: Patient Attended (Doctor Marks)
    CONFIRMED --> EXPIRED: Patient Did Not Show
    CONFIRMED --> CANCELLED: Patient or Doctor Cancels

    COMPLETED --> MedicalRecord: Doctor Writes Diagnosis & Rx
    CANCELLED --> [*]: Slot Automatically Reopened
    EXPIRED --> [*]
    MedicalRecord --> [*]
```

---

## 🛠️ Tech Stack

<div align="center">

<a href="https://skillicons.dev">
  <img src="https://skillicons.dev/icons?i=react,vite,tailwind,django,python,postgres,redis,docker,git,postman" />
</a>

</div>

<br/>

| Layer | Technologies | Highlights |
|---|---|---|
| **Frontend** | React 18, Vite, Tailwind CSS, Lucide React, Axios | Responsive healthcare UI, interactive time-grid selector, live status badges |
| **Backend** | Python 3.12, Django 4.2, Django REST Framework | RESTful API, SimpleJWT authentication, atomic transactional locks |
| **Async Workers** | Celery, Redis | Event-driven status email dispatch, periodic appointment reminder scheduler |
| **Database** | PostgreSQL / SQLite | Partial unique constraints, foreign key cascades, JSON query support |
| **Testing** | Django Test Runner, unittest | 46 comprehensive unit & integration tests covering edge cases |

---

## 📂 Project Structure

```bash
Hospital management/
├── backend/
│   ├── config/              # Project settings, Celery app, URL routing
│   │   ├── settings.py      # Environment config & DRF settings
│   │   ├── celery.py        # Celery broker configuration
│   │   └── urls.py          # API route definitions & Swagger schema
│   ├── core/                # Core hospital domain
│   │   ├── models.py        # User, Doctor, Patient, Slot, Appointment, Records
│   │   ├── views.py         # ViewSets (Auth, Doctors, Appointments, Records)
│   │   ├── serializers.py   # Serializers with 10-minute interval validation
│   │   ├── tasks.py         # Celery tasks (reminders & transactional emails)
│   │   ├── tests.py         # 46 automated integration & unit tests
│   │   └── migrations/      # Versioned schema migrations
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI (Navbar, Badges, Modals, Spinners)
│   │   ├── contexts/        # AuthContext & persistent token session state
│   │   ├── pages/           # DoctorDashboard, DoctorDetail, MyAppointments, Admin
│   │   └── api/axios.js     # Axios instance with JWT interceptors
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml       # Local PostgreSQL + Redis infrastructure
```

---

## 🚀 Getting Started

<details open>
<summary><b>1. Prerequisites & Infrastructure</b></summary>

Make sure you have installed:
- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- [Docker Desktop](https://www.docker.com/) (for Postgres & Redis)

Start database & message broker:
```bash
docker-compose up -d
```
*Starts PostgreSQL on port `5432` and Redis on port `6379`.*

</details>

<details open>
<summary><b>2. Backend Setup (Django + Celery)</b></summary>

```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Apply database migrations
python manage.py migrate

# Seed sample data (Specialties, Doctors, Patients, Slots, Admin)
python manage.py seed_data

# Start the Django development server
python manage.py runserver
```
- API Base URL: `http://localhost:8000/api/`
- Interactive Swagger Docs: `http://localhost:8000/api/docs/`

#### Start Background Workers (Optional for Local Email/Reminders)
```bash
# Celery worker (processes async emails)
celery -A config worker -l info --pool=solo

# Celery beat (processes 24h reminders)
celery -A config beat -l info
```

</details>

<details open>
<summary><b>3. Frontend Setup (React + Vite)</b></summary>

```bash
# Navigate to frontend directory
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```
- Web Application: `http://localhost:5173`

</details>

---

## 🔑 Default Seed Credentials

After running `python manage.py seed_data`, you can sign in with:

| Role | Email | Password | Permissions |
|---|---|---|---|
| **Admin** | `admin@hospital.com` | `Admin123!` | System stats, verify doctors, broadcast announcements |
| **Doctor** | `dr.smith@hospital.com` | `Doctor123!` | Manage slots, accept/decline bookings, attend/expire, write records |
| **Patient** | `patient.alice@example.com` | `Patient123!` | Browse doctors, select 10-min slots, reschedule, view records |

---

## 📡 API Reference

<details>
<summary><b>View API Endpoints</b></summary>

### Authentication
- `POST /api/auth/register/` — Register user & profile (`PATIENT` or `DOCTOR`)
- `POST /api/auth/token/` — Obtain JWT access & refresh tokens
- `GET/PATCH /api/auth/me/` — Retrieve or update current user profile

### Appointments & Slots
- `GET /api/doctors/` — List verified doctors (search by name, specialty, day)
- `GET /api/doctors/{id}/` — Doctor details including availability slots
- `GET /api/appointments/available-times/?slot=<id>&date=<YYYY-MM-DD>` — Get all 10-minute intervals with availability
- `POST /api/appointments/` — Book a 10-minute slot (starts as `PENDING`)
- `POST /api/appointments/{id}/confirm/` — Doctor confirms appointment
- `POST /api/appointments/{id}/complete/` — Doctor marks patient as attended
- `POST /api/appointments/{id}/expire/` — Doctor marks appointment expired (no-show)
- `POST /api/appointments/{id}/cancel/` — Cancel appointment (frees slot)
- `POST /api/appointments/{id}/reschedule/` — Reschedule to a new slot & 10-min interval

### Medical Records & Admin
- `GET /api/records/` — Access medical consultation history
- `POST /api/records/` — Doctor writes record for attended appointment
- `GET /api/admin/stats/` — System analytics for admin dashboard
- `POST /api/admin/announce/` — Broadcast message to user roles

</details>

---

## 🧪 Automated Testing

The backend includes a comprehensive test suite of 46 automated tests validating business rules, overlap detection, permission boundaries, and concurrency constraints.

```bash
cd backend
python manage.py test core.tests -v 2
```

```
Found 46 test(s).
System check identified no issues (0 silenced).
..............................................
----------------------------------------------------------------------
Ran 46 tests in 8.504s

OK
```

---

<div align="center">

<!-- Animated Footer Wave -->
<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0ea5e9,100:2563eb&height=120&section=footer" width="100%" alt="Footer" />

<sub>Built with ❤️ for modern healthcare management.</sub>

</div>
