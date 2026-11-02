"""
Automated PowerPoint Presentation Generator for Hospital Appointment Management System
Generates a 14-slide presentation with modern healthcare styling.
Requirements: pip install python-pptx
"""

import sys

try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    from pptx.enum.shapes import MSO_SHAPE
except ImportError:
    print("\n[!] 'python-pptx' is required to generate the PPTX file.")
    print("Please install it by running:")
    print("    pip install python-pptx")
    print("\nThen run this script again:")
    print("    python generate_presentation.py\n")
    sys.exit(1)


# Palette
PRIMARY_COLOR = RGBColor(15, 41, 66)      # Deep Navy Blue (#0F2942)
TEAL_COLOR = RGBColor(14, 165, 233)        # Clinical Cyan (#0EA5E9)
SUCCESS_COLOR = RGBColor(16, 185, 129)     # Mint Green (#10B981)
DARK_TEXT = RGBColor(30, 41, 59)          # Slate (#1E293B)
MUTED_TEXT = RGBColor(100, 116, 139)      # Gray (#64748B)
CARD_BG = RGBColor(248, 250, 252)         # Light Slate (#F8FAFC)
WHITE = RGBColor(255, 255, 255)


def add_header(slide, title_text, subtitle_text):
    """Adds a standard branded header banner to content slides."""
    # Top banner bar
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = TEAL_COLOR
    top_bar.line.fill.background()

    # Title box
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(8.4), Inches(1.1))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    tf.margin_left = Inches(0)

    p1 = tf.paragraphs[0]
    p1.text = title_text
    p1.font.size = Pt(24)
    p1.font.bold = True
    p1.font.color.rgb = PRIMARY_COLOR

    p2 = tf.add_paragraph()
    p2.text = subtitle_text
    p2.font.size = Pt(12)
    p2.font.color.rgb = MUTED_TEXT


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)  # 16:9 widescreen ratio
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # Slide 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(5.625))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = PRIMARY_COLOR
    bg1.line.fill.background()

    # Accent Stripe
    stripe = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.4), Inches(0.15), Inches(2.2))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = TEAL_COLOR
    stripe.line.fill.background()

    # Title
    tbox1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.3), Inches(8.0), Inches(2.5))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "Hospital Appointment\nManagement System"
    p.font.size = Pt(34)
    p.font.bold = True
    p.font.color.rgb = WHITE

    p_sub = tf1.add_paragraph()
    p_sub.text = "Enterprise Healthcare Platform with 10-Minute Smart Slot Scheduling"
    p_sub.font.size = Pt(14)
    p_sub.font.color.rgb = TEAL_COLOR

    p_meta = tf1.add_paragraph()
    p_meta.text = "Django REST Framework • React 18 + Vite • Celery + Redis • JWT Auth"
    p_meta.font.size = Pt(11)
    p_meta.font.color.rgb = RGBColor(203, 213, 225)

    s1.notes_slide.notes_text_frame.text = (
        "Welcome everyone. Today I am presenting the Hospital Appointment Management System, "
        "a full-stack healthcare platform engineered with 10-minute micro-slot scheduling, "
        "anti-concurrency double-booking guarantees, and an accountable doctor acceptance workflow."
    )

    # =========================================================================
    # Slide 2: Executive Summary
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Executive Summary & Vision", "Modernizing outpatient scheduling with precision time slots and clinical governance.")

    cards = [
        ("Precision Time Granularity", "Subdivides doctor windows into discrete 10-minute slots to reduce hospital wait times."),
        ("Doctor Governance", "Two-step acceptance: appointments start as PENDING until confirmed by the physician."),
        ("Concurrency Shield", "Transactional SELECT FOR UPDATE database locking and conditional unique constraints."),
        ("Automated Engagement", "Async Celery transactional emails and hourly Celery Beat 24-hour reminder scheduler.")
    ]

    for i, (title, desc) in enumerate(cards):
        x = Inches(0.8 + (i % 2) * 4.3)
        y = Inches(1.6 + (i // 2) * 1.8)
        card = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(4.0), Inches(1.5))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = RGBColor(226, 232, 240)

        tf = card.text_frame
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.2)
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(14)
        p1.font.color.rgb = PRIMARY_COLOR

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = DARK_TEXT

    s2.notes_slide.notes_text_frame.text = (
        "Our vision bridges the gap between patient accessibility and clinical efficiency. "
        "With 46 passing tests and 3 distinct user roles, the platform guarantees zero scheduling conflicts."
    )

    # =========================================================================
    # Slide 3: Problem Statement
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "The Healthcare Scheduling Bottleneck", "Why basic appointment systems fail in clinical operations.")

    problems = [
        ("Overcrowded Waiting Rooms", "Vague shift scheduling (e.g. 9 AM–12 PM) causes patient clustering and 60+ minute delays."),
        ("Race Conditions & Overlaps", "Basic booking apps fail under concurrent traffic, generating multiple bookings for the same time."),
        ("Lack of Doctor Confirmation", "Auto-confirming bookings without doctor review results in physician unavailability conflicts."),
        ("Ambiguous 'No-Show' Auditing", "Unclear attendance tracking compromises clinical audit trails and medical record integrity.")
    ]

    for i, (p_title, p_desc) in enumerate(problems):
        y = Inches(1.6 + i * 0.9)
        dot = s3.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.9), y + Inches(0.08), Inches(0.18), Inches(0.18))
        dot.fill.solid()
        dot.fill.fore_color.rgb = RGBColor(239, 68, 68)  # Red accent
        dot.line.fill.background()

        tbox = s3.shapes.add_textbox(Inches(1.2), y, Inches(7.8), Inches(0.75))
        tf = tbox.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{p_title} — "
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = PRIMARY_COLOR

        run = p1.add_run()
        run.text = p_desc
        run.font.bold = False
        run.font.color.rgb = DARK_TEXT

    s3.notes_slide.notes_text_frame.text = (
        "Traditional hospital booking fails in three critical areas: concurrency management, "
        "waiting room crowding, and doctor workflow governance. Our platform systematically addresses each."
    )

    # =========================================================================
    # Slide 4: Proposed Solution
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "The Proposed Solution", "An integrated, conflict-free clinical appointment management pipeline.")

    solutions = [
        ("10-Minute Smart Intervals", "Doctor shift blocks break into selectable 10-minute intervals with live visual status."),
        ("Concurrency Shielding", "Row-level database locks (SELECT FOR UPDATE) ensure absolute zero double-bookings."),
        ("Doctor Governance Flow", "Bookings begin as PENDING. Doctors actively Accept or Decline requests."),
        ("Attendance & EMR Integration", "Explicit Attended (COMPLETED) vs. Expired tracking with integrated digital prescriptions.")
    ]

    for i, (s_title, s_desc) in enumerate(solutions):
        y = Inches(1.6 + i * 0.9)
        dot = s4.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.9), y + Inches(0.08), Inches(0.18), Inches(0.18))
        dot.fill.solid()
        dot.fill.fore_color.rgb = SUCCESS_COLOR
        dot.line.fill.background()

        tbox = s4.shapes.add_textbox(Inches(1.2), y, Inches(7.8), Inches(0.75))
        tf = tbox.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{s_title} — "
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = PRIMARY_COLOR

        run = p1.add_run()
        run.text = s_desc
        run.font.bold = False
        run.font.color.rgb = DARK_TEXT

    s4.notes_slide.notes_text_frame.text = (
        "Our solution replaces ambiguity with granular 10-minute slots. Doctors have clear governance, "
        "and patients experience zero unexpected delays or schedule collisions."
    )

    # =========================================================================
    # Slide 5: System Architecture
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "System Architecture & Data Pipeline", "Decoupled multi-tier architecture with asynchronous message queuing.")

    tiers = [
        ("Client Tier (React 18 + Vite)", "• Single-Page Application (SPA)\n• Tailwind CSS Custom Medical Theme\n• Axios with JWT Auto-Refresh\n• Interactive 10-min slot grid"),
        ("API Tier (Django REST Framework)", "• Stateless RESTful endpoints\n• Strict serializer validation\n• Role-based permission checks\n• Transactional atomic decorators"),
        ("Async & Data Tier (PostgreSQL + Celery)", "• ACID database with row locks\n• Celery worker for email queues\n• Celery Beat 24h cron reminders\n• Redis distributed broker")
    ]

    for i, (tier_title, tier_points) in enumerate(tiers):
        x = Inches(0.8 + i * 2.85)
        card = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.6), Inches(2.7), Inches(3.4))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = RGBColor(203, 213, 225)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.2)

        p1 = tf.paragraphs[0]
        p1.text = tier_title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = PRIMARY_COLOR

        p2 = tf.add_paragraph()
        p2.text = tier_points
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = DARK_TEXT

    s5.notes_slide.notes_text_frame.text = (
        "The architecture is fully decoupled. The client communicates via JSON REST APIs. "
        "Heavy email dispatching is entirely offloaded to Celery workers so user response times stay under 50ms."
    )

    # =========================================================================
    # Slide 6: 10-Minute Slot Scheduling
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "10-Minute Smart Scheduling & Overlap Protection", "Dynamic interval division with transactional database row locking.")

    card_left = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(4.1), Inches(3.4))
    card_left.fill.solid()
    card_left.fill.fore_color.rgb = CARD_BG
    card_left.line.color.rgb = RGBColor(226, 232, 240)
    tf_l = card_left.text_frame
    tf_l.word_wrap = True
    tf_l.margin_left = Inches(0.25)
    tf_l.margin_top = Inches(0.25)

    p_l1 = tf_l.paragraphs[0]
    p_l1.text = "10-Minute Interval Division"
    p_l1.font.bold = True
    p_l1.font.size = Pt(14)
    p_l1.font.color.rgb = PRIMARY_COLOR

    p_l2 = tf_l.add_paragraph()
    p_l2.text = (
        "• Shift windows (e.g. 09:00 - 10:00) break into 6 discrete 10-min intervals.\n"
        "• API endpoint /api/appointments/available-times/ evaluates real-time occupancy.\n"
        "• Frontend renders available slots in Cyan, booked slots in Red with strikethrough.\n"
        "• Real-time badge shows exact count of available slots remaining."
    )
    p_l2.font.size = Pt(11)
    p_l2.font.color.rgb = DARK_TEXT

    card_right = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.1), Inches(1.6), Inches(4.1), Inches(3.4))
    card_right.fill.solid()
    card_right.fill.fore_color.rgb = CARD_BG
    card_right.line.color.rgb = RGBColor(226, 232, 240)
    tf_r = card_right.text_frame
    tf_r.word_wrap = True
    tf_r.margin_left = Inches(0.25)
    tf_r.margin_top = Inches(0.25)

    p_r1 = tf_r.paragraphs[0]
    p_r1.text = "Anti-Double-Booking Concurrency Shield"
    p_r1.font.bold = True
    p_r1.font.size = Pt(14)
    p_r1.font.color.rgb = PRIMARY_COLOR

    p_r2 = tf_r.add_paragraph()
    p_r2.text = (
        "1. Row Locking: select_for_update() locks slot row during transaction.\n"
        "2. Double-Booking Query: Checks active bookings for slot + date + time.\n"
        "3. Database Constraint: UniqueConstraint on (slot, date, time) condition=~Q(status='CANCELLED').\n"
        "4. Overlap Notification: Returns immediate 400 Bad Request with explanatory message."
    )
    p_r2.font.size = Pt(11)
    p_r2.font.color.rgb = DARK_TEXT

    s6.notes_slide.notes_text_frame.text = (
        "Here is the technical core: when two patients click book simultaneously, row-level locking "
        "forces sequential evaluation. The first succeeds; the second receives an instant overlap warning."
    )

    # =========================================================================
    # Slide 7: Doctor Acceptance Lifecycle
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Doctor Acceptance & Attendance Lifecycle", "Explicit clinical state transitions with complete auditing.")

    states = [
        ("1. PENDING", "Default booking state. Doctor receives notification to accept or decline.", TEAL_COLOR),
        ("2. CONFIRMED", "Doctor clicks 'Accept'. Confirmation email dispatched to patient.", PRIMARY_COLOR),
        ("3. ATTENDED", "Consultation conducted. Doctor marks completed; unlocks EMR entry.", SUCCESS_COLOR),
        ("4. EXPIRED", "Patient did not attend. Clarifies ambiguous 'no-show' status.", RGBColor(148, 163, 184)),
        ("5. CANCELLED", "Cancelled by patient or declined by doctor. Slot reopens instantly.", RGBColor(239, 68, 68))
    ]

    for i, (st_name, st_desc, col) in enumerate(states):
        y = Inches(1.6 + i * 0.72)
        badge = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(2.2), Inches(0.55))
        badge.fill.solid()
        badge.fill.fore_color.rgb = col
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = st_name
        p_b.font.bold = True
        p_b.font.size = Pt(11)
        p_b.font.color.rgb = WHITE
        p_b.alignment = PP_ALIGN.CENTER

        tbox = s7.shapes.add_textbox(Inches(3.2), y, Inches(6.0), Inches(0.55))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = st_desc
        p.font.size = Pt(11)
        p.font.color.rgb = DARK_TEXT

    s7.notes_slide.notes_text_frame.text = (
        "Our state machine eliminates misunderstandings: bookings begin as Pending. "
        "Doctors explicitly confirm them, and attendance is tracked as Attended or Expired."
    )

    # =========================================================================
    # Slide 8: Role-Based User Portals
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "Role-Based Portals & Access Control", "Tailored clinical dashboards for Patients, Doctors, and Administrators.")

    portals = [
        ("Patient Portal", "• Search verified doctors & specialties\n• 10-minute interactive booking grid\n• Reschedule appointments with overlap check\n• View medical history & prescriptions"),
        ("Doctor Dashboard", "• Weekly availability slot management\n• One-click Accept / Decline requests\n• Mark visits Attended vs. Expired\n• Diagnostic & prescription entry modal"),
        ("Admin Control Center", "• Hospital-wide consultation analytics\n• Recharts daily appointment volume trends\n• Doctor credential verification gate\n• Broadcast announcement notification center")
    ]

    for i, (p_title, p_body) in enumerate(portals):
        x = Inches(0.8 + i * 2.85)
        card = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.6), Inches(2.7), Inches(3.4))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = RGBColor(203, 213, 225)

        tf = card.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.2)
        tf.margin_top = Inches(0.2)

        p1 = tf.paragraphs[0]
        p1.text = p_title
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = PRIMARY_COLOR

        p2 = tf.add_paragraph()
        p2.text = p_body
        p2.font.size = Pt(10.5)
        p2.font.color.rgb = DARK_TEXT

    s8.notes_slide.notes_text_frame.text = (
        "Security and context are paramount. Patients manage their own health history, "
        "doctors manage their patient flow, and administrators maintain hospital governance."
    )

    # =========================================================================
    # Slide 9: Digital Medical Records
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Integrated Electronic Medical Records (EMR)", "Closing the consultation loop with secure diagnostic documentation.")

    emr_points = [
        ("Precondition Enforcement", "Medical records can only be created for appointments with status COMPLETED (Attended)."),
        ("Single-Record Immutability", "Strict one-to-one relationship prevents duplicate or conflicting medical records."),
        ("Comprehensive Clinical Fields", "Captures clinical Diagnosis, detailed Prescription regimen, and doctor follow-up Notes."),
        ("Patient Medical History", "Patients have secure, permanent digital access to review historical records anytime.")
    ]

    for i, (title, desc) in enumerate(emr_points):
        y = Inches(1.6 + i * 0.9)
        dot = s9.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.9), y + Inches(0.08), Inches(0.18), Inches(0.18))
        dot.fill.solid()
        dot.fill.fore_color.rgb = TEAL_COLOR
        dot.line.fill.background()

        tbox = s9.shapes.add_textbox(Inches(1.2), y, Inches(7.8), Inches(0.75))
        tf = tbox.text_frame
        tf.word_wrap = True
        p1 = tf.paragraphs[0]
        p1.text = f"{title} — "
        p1.font.bold = True
        p1.font.size = Pt(13)
        p1.font.color.rgb = PRIMARY_COLOR

        run = p1.add_run()
        run.text = desc
        run.font.bold = False
        run.font.color.rgb = DARK_TEXT

    s9.notes_slide.notes_text_frame.text = (
        "Medical records link directly to attended appointments. This ensures full regulatory compliance, "
        "preventing prescriptions from being generated for patients who never attended."
    )

    # =========================================================================
    # Slide 10: Background Services (Celery)
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Background Services & Automated Reminders", "Asynchronous task execution with Celery worker and Celery Beat scheduler.")

    c_left = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(4.1), Inches(3.4))
    c_left.fill.solid()
    c_left.fill.fore_color.rgb = CARD_BG
    c_left.line.color.rgb = RGBColor(226, 232, 240)
    tf_cl = c_left.text_frame
    tf_cl.word_wrap = True
    tf_cl.margin_left = Inches(0.25)
    tf_cl.margin_top = Inches(0.25)

    p_cl1 = tf_cl.paragraphs[0]
    p_cl1.text = "Celery Worker (Async Tasks)"
    p_cl1.font.bold = True
    p_cl1.font.size = Pt(14)
    p_cl1.font.color.rgb = PRIMARY_COLOR

    p_cl2 = tf_cl.add_paragraph()
    p_cl2.text = (
        "• Event-driven transactional email dispatching.\n"
        "• Booking request, confirmation, reschedule, and cancellation emails.\n"
        "• Offloads SMTP network overhead from the HTTP thread.\n"
        "• API response times remain sub-50ms regardless of mail provider latency."
    )
    p_cl2.font.size = Pt(11)
    p_cl2.font.color.rgb = DARK_TEXT

    c_right = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(5.1), Inches(1.6), Inches(4.1), Inches(3.4))
    c_right.fill.solid()
    c_right.fill.fore_color.rgb = CARD_BG
    c_right.line.color.rgb = RGBColor(226, 232, 240)
    tf_cr = c_right.text_frame
    tf_cr.word_wrap = True
    tf_cr.margin_left = Inches(0.25)
    tf_cr.margin_top = Inches(0.25)

    p_cr1 = tf_cr.paragraphs[0]
    p_cr1.text = "Celery Beat (Periodic Cron)"
    p_cr1.font.bold = True
    p_cr1.font.size = Pt(14)
    p_cr1.font.color.rgb = PRIMARY_COLOR

    p_cr2 = tf_cr.add_paragraph()
    p_cr2.text = (
        "• Hourly automated cron job: check_upcoming_appointments.\n"
        "• Scans for upcoming appointments within the next 24 hours.\n"
        "• Dispatches automated preparation and arrival email reminder.\n"
        "• Updates reminder_sent=True flag to eliminate redundant notifications."
    )
    p_cr2.font.size = Pt(11)
    p_cr2.font.color.rgb = DARK_TEXT

    s10.notes_slide.notes_text_frame.text = (
        "Celery Beat operates as our virtual clinic coordinator. It automatically scans the database "
        "every hour and alerts patients 24 hours prior to their appointment, significantly reducing no-show rates."
    )

    # =========================================================================
    # Slide 11: Technology Stack
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Technology Stack Deep Dive", "Enterprise-grade open-source technologies selected for performance and scalability.")

    stack_items = [
        ("Django REST Framework", "Python 3.12, robust ORM, atomic transactions, SimpleJWT authentication."),
        ("React 18 + Vite", "High-performance SPA, sub-second HMR, modular component architecture."),
        ("Tailwind CSS", "Utility-first design system with responsive medical theme and custom badges."),
        ("Celery + Redis", "Distributed message broker handling asynchronous emails and periodic reminders."),
        ("PostgreSQL / SQLite", "Relational ACID compliance, row-level locking, and partial index constraints.")
    ]

    for i, (tech, reason) in enumerate(stack_items):
        y = Inches(1.6 + i * 0.72)
        badge = s11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y, Inches(2.5), Inches(0.55))
        badge.fill.solid()
        badge.fill.fore_color.rgb = PRIMARY_COLOR
        badge.line.fill.background()
        tf_b = badge.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = tech
        p_b.font.bold = True
        p_b.font.size = Pt(11)
        p_b.font.color.rgb = WHITE
        p_b.alignment = PP_ALIGN.CENTER

        tbox = s11.shapes.add_textbox(Inches(3.5), y, Inches(5.7), Inches(0.55))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = reason
        p.font.size = Pt(11)
        p.font.color.rgb = DARK_TEXT

    s11.notes_slide.notes_text_frame.text = (
        "Every tier in our stack was chosen with deliberate care: React ensures an intuitive UI, "
        "Django provides rock-solid security and data modeling, and Celery ensures non-blocking performance."
    )

    # =========================================================================
    # Slide 12: Database Schema
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Database Schema & Entity Relationships", "Third normal form (3NF) relational design with integrity cascades.")

    entities = [
        ("User & Profiles", "Custom User (Role: PATIENT, DOCTOR, ADMIN) linked 1-to-1 with DoctorProfile and PatientProfile."),
        ("Specialty", "Medical disciplines (Cardiology, Dermatology, Orthopedics) categorizing physicians."),
        ("AvailabilitySlot", "Doctor FK, day_of_week (0-6), start_time, end_time, and is_active flag."),
        ("Appointment", "Patient FK, Slot FK, date, appointment_time (10-min slot), status, reminder_sent flag."),
        ("MedicalRecord", "1-to-1 relationship with completed Appointment, diagnosis, prescription, doctor FK."),
        ("Notification", "User FK, title, message, is_read flag, and timestamp.")
    ]

    for i, (e_title, e_desc) in enumerate(entities):
        y = Inches(1.6 + i * 0.6)
        dot = s12.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.9), y + Inches(0.06), Inches(0.14), Inches(0.14))
        dot.fill.solid()
        dot.fill.fore_color.rgb = TEAL_COLOR
        dot.line.fill.background()

        tbox = s12.shapes.add_textbox(Inches(1.2), y, Inches(7.8), Inches(0.5))
        tf = tbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = f"{e_title}: "
        p.font.bold = True
        p.font.size = Pt(11)
        p.font.color.rgb = PRIMARY_COLOR

        run = p.add_run()
        run.text = e_desc
        run.font.bold = False
        run.font.color.rgb = DARK_TEXT

    s12.notes_slide.notes_text_frame.text = (
        "Foreign key constraints enforce referential integrity. When availability slots are retired, "
        "historical appointments remain preserved thanks to protected deletion policies."
    )

    # =========================================================================
    # Slide 13: Testing & Quality Assurance
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Quality Assurance & Edge-Case Testing", "46 automated integration and edge-case unit tests passing with zero errors.")

    test_cards = [
        ("Concurrency & Overlap", "Verifies concurrent bookings on identical 10-minute intervals are rejected with 400 Bad Request."),
        ("Lifecycle State Machine", "Validates PENDING -> CONFIRMED -> COMPLETED / EXPIRED state flow and permissions."),
        ("Access Control & Security", "Ensures patients cannot modify other patients' appointments; non-doctors cannot create records."),
        ("Validation & Scheduling", "Verifies weekday matching, future date rules, and cancelled slot rebooking.")
    ]

    for i, (title, desc) in enumerate(test_cards):
        x = Inches(0.8 + (i % 2) * 4.3)
        y = Inches(1.6 + (i // 2) * 1.8)
        card = s13.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, Inches(4.0), Inches(1.5))
        card.fill.solid()
        card.fill.fore_color.rgb = CARD_BG
        card.line.color.rgb = RGBColor(226, 232, 240)

        tf = card.text_frame
        tf.margin_left = Inches(0.3)
        tf.margin_top = Inches(0.2)
        tf.word_wrap = True

        p1 = tf.paragraphs[0]
        p1.text = title
        p1.font.bold = True
        p1.font.size = Pt(14)
        p1.font.color.rgb = PRIMARY_COLOR

        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11)
        p2.font.color.rgb = DARK_TEXT

    s13.notes_slide.notes_text_frame.text = (
        "We backed our implementation with a comprehensive test suite of 46 automated tests. "
        "Every edge case—including race conditions, invalid rescheduling, and permission boundaries—is verified."
    )

    # =========================================================================
    # Slide 14: Conclusion & Future Scope
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    bg14 = s14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(5.625))
    bg14.fill.solid()
    bg14.fill.fore_color.rgb = PRIMARY_COLOR
    bg14.line.fill.background()

    tbox14 = s14.shapes.add_textbox(Inches(1.0), Inches(1.0), Inches(8.0), Inches(3.6))
    tf14 = tbox14.text_frame
    tf14.word_wrap = True

    p = tf14.paragraphs[0]
    p.text = "Conclusion & Future Roadmap"
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = WHITE

    p_f1 = tf14.add_paragraph()
    p_f1.text = "\nKey Achievements:"
    p_f1.font.size = Pt(14)
    p_f1.font.bold = True
    p_f1.font.color.rgb = TEAL_COLOR

    p_f2 = tf14.add_paragraph()
    p_f2.text = (
        "• Production-grade 10-minute micro-slot scheduling with real-time availability.\n"
        "• Concurrency-proof transactional integrity with SELECT FOR UPDATE.\n"
        "• Structured doctor governance with clear Attended and Expired visit outcomes.\n"
        "• Fully automated asynchronous notification pipelines via Celery."
    )
    p_f2.font.size = Pt(11)
    p_f2.font.color.rgb = RGBColor(226, 232, 240)

    p_f3 = tf14.add_paragraph()
    p_f3.text = "\nNext Horizons: Telemedicine (WebRTC) • Payment Gateway (Stripe) • SMS/WhatsApp Alerts"
    p_f3.font.size = Pt(11)
    p_f3.font.color.rgb = TEAL_COLOR

    s14.notes_slide.notes_text_frame.text = (
        "In conclusion, this project provides a robust, scalable foundation for modern outpatient healthcare. "
        "It solves the core operational challenges of scheduling, attendance tracking, and medical documentation. "
        "Thank you! I am now happy to take any questions."
    )

    output_filename = "hospital_management_system.pptx"
    prs.save(output_filename)
    print(f"\n[+] Successfully generated presentation: {output_filename}")
    print("[+] 14 beautifully styled slides created with speaker notes.")


if __name__ == "__main__":
    create_deck()

