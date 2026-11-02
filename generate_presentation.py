"""
Automated PowerPoint Presentation Generator for Hospital Appointment Management System
Generates a comprehensive 16-slide presentation with modern healthcare styling.
Updated to Version 3.0: Online Payment Gateway, 50% Refund Policy, Live Gmail SMTP & Cloud Architecture.
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
    sys.exit(1)


# Palette
PRIMARY_COLOR = RGBColor(15, 41, 66)      # Deep Navy Blue (#0F2942)
TEAL_COLOR = RGBColor(14, 165, 233)        # Clinical Cyan (#0EA5E9)
SUCCESS_COLOR = RGBColor(16, 185, 129)     # Mint Green (#10B981)
DARK_TEXT = RGBColor(30, 41, 59)          # Slate (#1E293B)
MUTED_TEXT = RGBColor(100, 116, 139)      # Gray (#64748B)
CARD_BG = RGBColor(248, 250, 252)         # Light Slate (#F8FAFC)
WHITE = RGBColor(255, 255, 255)
AMBER_COLOR = RGBColor(245, 158, 11)      # Amber (#F59E0B)


def add_header(slide, title_text, subtitle_text):
    """Adds a standard branded header banner to content slides."""
    top_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(0.12))
    top_bar.fill.solid()
    top_bar.fill.fore_color.rgb = TEAL_COLOR
    top_bar.line.fill.background()

    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(8.4), Inches(1.0))
    tf = tx_box.text_frame
    tf.word_wrap = True
    tf.margin_top = Inches(0)
    tf.margin_bottom = Inches(0)
    tf.margin_left = Inches(0)

    p1 = tf.paragraphs[0]
    p1.text = title_text
    p1.font.size = Pt(22)
    p1.font.bold = True
    p1.font.color.rgb = PRIMARY_COLOR

    p2 = tf.add_paragraph()
    p2.text = subtitle_text
    p2.font.size = Pt(11)
    p2.font.color.rgb = MUTED_TEXT


def add_card(slide, left, top, width, height, title, items, title_color=PRIMARY_COLOR):
    """Creates a stylized clinical card with bullet points."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = CARD_BG
    card.line.color.rgb = RGBColor(226, 232, 240)
    card.line.width = Pt(1)

    tbox = slide.shapes.add_textbox(left + Inches(0.15), top + Inches(0.15), width - Inches(0.3), height - Inches(0.3))
    tf = tbox.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_title = tf.paragraphs[0]
    p_title.text = title
    p_title.font.bold = True
    p_title.font.size = Pt(13)
    p_title.font.color.rgb = title_color
    p_title.space_after = Pt(6)

    for itm in items:
        p_item = tf.add_paragraph()
        p_item.text = f"•  {itm}"
        p_item.font.size = Pt(9.5)
        p_item.font.color.rgb = DARK_TEXT
        p_item.space_after = Pt(3)


def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(5.625)  # 16:9 ratio
    blank_layout = prs.slide_layouts[6]

    # =========================================================================
    # Slide 1: Title Slide
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    bg1 = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(10), Inches(5.625))
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = PRIMARY_COLOR
    bg1.line.fill.background()

    stripe = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.3), Inches(0.15), Inches(2.4))
    stripe.fill.solid()
    stripe.fill.fore_color.rgb = TEAL_COLOR
    stripe.line.fill.background()

    tbox1 = s1.shapes.add_textbox(Inches(1.2), Inches(1.2), Inches(8.0), Inches(2.8))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True

    p = tf1.paragraphs[0]
    p.text = "Hospital Appointment\nManagement System"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = WHITE

    p_sub = tf1.add_paragraph()
    p_sub.text = "Enterprise Healthcare Platform with 10-Minute Smart Slot Scheduling & Online Payments"
    p_sub.font.size = Pt(13)
    p_sub.font.color.rgb = TEAL_COLOR

    p_meta = tf1.add_paragraph()
    p_meta.text = "Django REST Framework • React 18 + Vite • Neon PostgreSQL • Gmail SMTP • Version 3.0"
    p_meta.font.size = Pt(10)
    p_meta.font.color.rgb = RGBColor(148, 163, 184)
    p_meta.space_before = Pt(8)

    p_author = tf1.add_paragraph()
    p_author.text = "Presented by: Sreecharan (Reg No: 12204561) • CSE316 Software Engineering (CA-3)"
    p_author.font.size = Pt(9.5)
    p_author.font.color.rgb = SUCCESS_COLOR
    p_author.space_before = Pt(6)

    # =========================================================================
    # Slide 2: Executive Summary
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    add_header(s2, "Executive Summary", "Bridging patient accessibility and outpatient clinical efficiency")
    add_card(s2, Inches(0.8), Inches(1.4), Inches(2.6), Inches(3.6),
             "Operational Excellence",
             ["10-Minute Micro-Slots prevent crowded clinic queues",
              "Doctor acceptance workflow validates physician availability",
              "Automated 24-hour reminders reduce appointment dropouts",
              "Unified portal for Patients, Doctors, and Admin"])
    add_card(s2, Inches(3.7), Inches(1.4), Inches(2.6), Inches(3.6),
             "Financial & Billing Governance",
             ["Integrated online payment gateway in INR (₹)",
              "Multi-method checkout: Cards, UPI QR, Net Banking",
              "Automated 50% cancellation refund policy",
              "Printable GST-compliant official electronic invoices"])
    add_card(s2, Inches(6.6), Inches(1.4), Inches(2.6), Inches(3.6),
             "Engineering Reliability",
             ["PostgreSQL SELECT FOR UPDATE row concurrency shield",
              "Live Google Gmail SMTP transactional email relay",
              "Render cloud API + Vercel React SPA + Neon AWS DB",
              "49/49 automated unit and integration tests passed"])

    # =========================================================================
    # Slide 3: Problem Statement
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    add_header(s3, "Clinical Problem Statement", "Operational flaws in traditional outpatient department (OPD) scheduling")
    add_card(s3, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Hospital & Clinical Challenges",
             ["Overcrowded Waiting Halls: Broad block-booking (9 AM-12 PM) leads to patient congestion and infection risk.",
              "Double-Booking Disasters: Concurrent patient requests on the same physician slot create clinical schedule clashes.",
              "Lack of Doctor Control: Auto-confirmed appointments fail to accommodate doctor emergencies and ward rounds.",
              "Attendance Ambiguity: Unaccounted no-shows distort clinical audit trails and doctor billing."],
             title_color=RGBColor(225, 29, 72))
    add_card(s3, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Financial & Administrative Gaps",
             ["Payment Collection Friction: Cash counter queues delay patient consultation entry.",
              "Unclear Cancellation Terms: Patients face disputes over refunds when cancellations occur.",
              "Lost Medical Slips: Physical prescription paper slips get misplaced, destroying patient treatment history.",
              "Silent Communication: Patients miss appointments due to lack of real-time email dispatch."],
             title_color=RGBColor(225, 29, 72))

    # =========================================================================
    # Slide 4: Proposed Solution
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    add_header(s4, "The MediCare OPD Solution", "A resilient, full-stack digital scheduling and healthcare ecosystem")
    add_card(s4, Inches(0.8), Inches(1.4), Inches(2.6), Inches(3.6),
             "Smart Micro-Scheduling",
             ["Discrete 10-Minute intervals dynamically generated",
              "Real-time slot availability grid on client UI",
              "Deterministic boundary verification (minute % 10 == 0)",
              "Strict anti-double-booking database row locking"])
    add_card(s4, Inches(3.7), Inches(1.4), Inches(2.6), Inches(3.6),
             "Frictionless Online Payments",
             ["Doctor fee collection in Indian Rupees (₹)",
              "Credit/Debit Card, UPI Instant QR, Net Banking",
              "50% cancellation refund policy with admin queue",
              "Printable GST electronic medical tax invoices"])
    add_card(s4, Inches(6.6), Inches(1.4), Inches(2.6), Inches(3.6),
             "Automated Communications",
             ["Live Gmail SMTP dispatch to user login account",
              "Booking, Cancellation, Completion & Refund emails",
              "Integrated digital EMR diagnoses & prescriptions",
              "Admin governance dashboard with 30-day analytics"])

    # =========================================================================
    # Slide 5: System Architecture
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    add_header(s5, "Production Cloud System Architecture", "High-availability, decoupled three-tier cloud deployment topology")
    add_card(s5, Inches(0.8), Inches(1.4), Inches(2.6), Inches(3.6),
             "Presentation Tier (Vercel)",
             ["React 18 Single Page Application (SPA)",
              "Vite 8 build tool + Tailwind CSS styling",
              "Global edge CDN with client-side SPA routing",
              "Interactive visual slot matrix & payment modal",
              "Printable official tax invoice viewer"])
    add_card(s5, Inches(3.7), Inches(1.4), Inches(2.6), Inches(3.6),
             "Application Tier (Render)",
             ["Django 4.2 REST Framework API runtime",
              "Gunicorn WSGI container with WhiteNoise static assets",
              "SimpleJWT 30-min access & rotating refresh tokens",
              "Role-Based Access Control (RBAC) permission guards",
              "OpenAPI / Swagger interactive API documentation"])
    add_card(s5, Inches(6.6), Inches(1.4), Inches(2.6), Inches(3.6),
             "Data & Relay Tier (Neon + Google)",
             ["Neon Serverless PostgreSQL on AWS Ohio (us-east-2)",
              "PgBouncer connection pooling with SSL encryption",
              "Row-level locking (SELECT FOR UPDATE) concurrency shield",
              "Google Gmail SMTP relay (smtp.gmail.com:587 TLS)",
              "Direct transactional email dispatch to user mailboxes"])

    # =========================================================================
    # Slide 6: 10-Minute Micro-Slot Scheduling
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    add_header(s6, "10-Minute Smart Slot Scheduling", "High-concurrency anti-double-booking shield powered by PostgreSQL row locks")
    add_card(s6, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Dynamic Interval Generation Algorithm",
             ["Doctors configure general shift windows (e.g. 09:00 - 11:00).",
              "API dynamically divides shift into twelve discrete 10-minute intervals: 09:00, 09:10, 09:20... 10:50.",
              "Client displays real-time color-coded badges: Cyan (Available) vs Red Strikethrough (Booked).",
              "Validation enforces strictly future dates, doctor shift weekday matching, and 10-minute slot boundaries."])
    add_card(s6, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Database Concurrency Protection",
             ["Atomic Row Locking: Executes AvailabilitySlot.objects.select_for_update().get(...) within transaction.",
              "Active Overlap Filter: Queries existing active bookings excluding CANCELLED status.",
              "Deterministic Conflict Rejection: Returns HTTP 400 Bad Request if slot is claimed concurrently.",
              "Database Constraint: Partial UniqueConstraint(fields=['slot', 'date', 'appointment_time'], condition=~Q(status='CANCELLED'))."])

    # =========================================================================
    # Slide 7: Online Payment Gateway & Invoicing
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    add_header(s7, "Online Payment Gateway & Invoicing", "Instant multi-method consultation fee checkout in Indian Rupees (₹)")
    add_card(s7, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Multi-Method Checkout Experience",
             ["Indian Rupee (₹) Standardization: Doctor fees calibrated to INR (₹500 - ₹1200).",
              "Card Payments: Full validation for 16-digit cards, expiry (MM/YY), CVV, and brand detection (Visa/Mastercard).",
              "Instant UPI / QR Scan: Seamless handles (@okhdfcbank, @okaxis, @paytm, @ybl) and simulated scan QR.",
              "Net Banking: Direct selection across leading banks (HDFC, SBI, ICICI, Axis, Chase).",
              "Cryptographic Transaction ID: Unique TXN-XXXXXXXXXX reference assigned to every payment entity."])
    add_card(s7, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Official Electronic Tax Invoices",
             ["GST Healthcare Compliance: Official tax invoice endpoint (GET /api/appointments/{id}/receipt/).",
              "Itemized Bill: Doctor consultation service, slot time, tele-registration fee breakdown, and total paid.",
              "Audit Reference: Displays patient name, doctor specialty, transaction ID, payment method, and timestamp.",
              "Browser Print Engine: CSS @media print optimization allows one-click thermal/A4 receipt printing."])

    # =========================================================================
    # Slide 8: 50% Cancellation Refund Policy
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    add_header(s8, "50% Cancellation & Refund Policy", "Transparent patient cancellation policy with dedicated hospital admin approval queue")
    add_card(s8, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Patient Cancellation Flow",
             ["Transparent Terms: Patient alerted before confirmation that cancellations trigger a 50% refund.",
              "Automatic Accounting: System computes refund_amount = round(fee * 0.50, 2); 50% retained by hospital.",
              "Status Transition: Appointment status set to CANCELLED; payment_status set to REFUND_PENDING.",
              "Visual Tracking: Patient dashboard displays status badge: ⏳ 50% Refund Pending (₹X).",
              "Slot Liberation: The cancelled time slot immediately reopens for other patients to book."])
    add_card(s8, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Admin Approval & Execution Engine",
             ["Dedicated Admin Queue: Admin Dashboard lists all pending 50% cancellation refunds in real-time.",
              "Single-Click Approval: Admin clicks 'Approve & Initiate ₹X Refund' (POST /api/appointments/{id}/process-refund/).",
              "Refund Reference ID: System assigns unique REF-XXXXXXXX transaction identifier and records refunded_at.",
              "Audit Status: Payment marked as REFUNDED; patient badge updates to ✓ 50% Refunded (₹X).",
              "Automated Dispatch: Live email sent to patient's registered login account confirming refund dispatch."])

    # =========================================================================
    # Slide 9: Doctor Governance & Clinical Acceptance
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    add_header(s9, "Doctor Clinical Governance Lifecycle", "Strict physician-in-the-loop state machine ensuring accountability and attendance tracking")
    add_card(s9, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "The 4-State Clinical Lifecycle",
             ["PENDING: Patient submits booking request; doctor reviews clinical reason and schedule.",
              "CONFIRMED: Doctor accepts booking via /confirm/; patient receives confirmed arrival email.",
              "COMPLETED: Patient attends visit; doctor marks visit as Attended, unlocking EMR entry.",
              "EXPIRED: Patient fails to attend; doctor marks visit as Expired, replacing ambiguous 'no-show'.",
              "CANCELLED: Either party cancels; slot is freed and 50% refund queued if paid."],
             title_color=PRIMARY_COLOR)
    add_card(s9, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Governance & Clinical Safeguards",
             ["Doctor Authority: Only the assigned consulting physician can confirm, complete, or expire appointments.",
              "Precondition Enforcement: Only CONFIRMED visits can transition to COMPLETED.",
              "Immutable EMR Coupling: Prescription creation strictly requires COMPLETED state.",
              "Audit Trails: State transitions record updated_at timestamps for regulatory hospital reporting."],
             title_color=PRIMARY_COLOR)

    # =========================================================================
    # Slide 10: Role-Based User Portals
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    add_header(s10, "Role-Based User Portals (RBAC)", "Custom-tailored digital workspaces for Patients, Doctors, and Administrators")
    add_card(s10, Inches(0.8), Inches(1.4), Inches(2.6), Inches(3.6),
             "Patient Portal",
             ["Doctor discovery with specialty search and fee filters",
              "Visual 10-minute slot matrix booking & checkout",
              "Appointment management: Reschedule, Cancel & Receipt",
              "Access to digital prescriptions & medical history",
              "Real-time in-app notification center"])
    add_card(s10, Inches(3.7), Inches(1.4), Inches(2.6), Inches(3.6),
             "Doctor Workspace",
             ["Weekly availability shift window configuration",
              "Daily OPD schedule grouped by Pending & Upcoming",
              "Action buttons: Confirm, Complete, Expire, Cancel",
              "Integrated digital EMR prescription writing modal",
              "Patient attendance and fee payment indicators"])
    add_card(s10, Inches(6.6), Inches(1.4), Inches(2.6), Inches(3.6),
             "Hospital Admin Console",
             ["Doctor credential verification approval gateway",
              "Dedicated 50% Cancellation Refund Approval Queue",
              "Recharts live 30-day OPD consultation volume curves",
              "Medical department and specialty manager",
              "Hospital-wide broadcast announcement messaging"])

    # =========================================================================
    # Slide 11: Electronic Medical Records (EMR)
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    add_header(s11, "Electronic Medical Records & Prescriptions", "Eliminating paper loss with secure, digital clinical documentation")
    add_card(s11, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Clinical Documentation Workflow",
             ["Seamless Post-Visit Entry: Once marked COMPLETED, doctor clicks 'Write Record'.",
              "Structured Clinical Fields: Captures Diagnosis, Rx Prescriptions (Dosage/Frequency), and Doctor Advice.",
              "Strict 1-to-1 Association: One MedicalRecord entity per appointment; prevents duplicate records.",
              "Audit Timestamping: Permanent record of consultation date, attending doctor, and entry timestamp."])
    add_card(s11, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Patient Accessibility & Compliance",
             ["Universal Digital History: Patients access historical records under their profile from any device.",
              "Confidentiality Enforcement: Access restricted strictly to patient and attending physician.",
              "Pharmacy Hand-off: Clean formatted prescriptions ready for pharmacy dispensing.",
              "Medical Continuity: Subsequent consultations reference past diagnoses for improved patient outcomes."])

    # =========================================================================
    # Slide 12: Live Gmail SMTP Dispatch Engine
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    add_header(s12, "Live Gmail SMTP Email Dispatch Engine", "Real-time transactional email relay delivering notifications to user login inboxes")
    add_card(s12, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Gmail SMTP Relay Configuration",
             ["Authenticated Google Relay: Connects to smtp.gmail.com:587 with STARTTLS encryption.",
              "Dedicated Sender Identity: CityCare Hospital <sreecharan831@gmail.com>.",
              "Synchronous & Async Resilience: safe_dispatch_email sends in-process or queues via worker without failure.",
              "Live Verified: Zero-drop delivery confirmed live to patient inboxes (Send mail result: 1)."])
    add_card(s12, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Event-Driven Email Triggers",
             ["Booking Confirmation: Sends full appointment details, doctor specialty, slot time, and fee status.",
              "Cancellation Notice: Details cancellation and outlines the 50% refund pending admin approval.",
              "50% Refund Approval: Dispatches refund confirmation with official REF-XXXXXXXX transaction reference.",
              "Consultation Completion: Summarizes attended visit and notifies patient that prescriptions are available.",
              "Account Auditing: All emails explicitly confirm the registered login email address for security."])

    # =========================================================================
    # Slide 13: Relational Database Architecture
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    add_header(s13, "Relational Database Schema (PostgreSQL)", "Optimized relational entity design enforcing referential integrity and concurrency constraints")
    add_card(s13, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Core Relational Entities",
             ["core_user: id, email (unique login), role (PATIENT/DOCTOR/ADMIN), password (PBKDF2).",
              "core_doctorprofile: id (UUID), user_id, specialty_id, experience_years, fee (INR), is_verified.",
              "core_patientprofile: id (UUID), user_id, dob, phone, address, blood_group.",
              "core_specialty: id (UUID), name (unique), description.",
              "core_availabilityslot: id (UUID), doctor_id, day_of_week (0-6), start_time, end_time, is_active."])
    add_card(s13, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Clinical Transactional Entities",
             ["core_appointment: id (UUID), patient_id, slot_id, date, appointment_time, status, payment_status.",
              "core_payment: id (UUID), appointment_id, patient_id, doctor_id, amount (INR), method, transaction_id, status, refund_amount, refund_transaction_id, refunded_at.",
              "core_medicalrecord: id (UUID), appointment_id (1-to-1), created_by_id, diagnosis, prescription, notes.",
              "core_notification: id (UUID), user_id, title, message, is_read, created_at."])

    # =========================================================================
    # Slide 14: Technology Stack Matrix
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    add_header(s14, "Technology Stack & Cloud Infrastructure", "Modern, scalable, and open-source full-stack technology ecosystem")
    add_card(s14, Inches(0.8), Inches(1.4), Inches(2.6), Inches(3.6),
             "Frontend Ecosystem",
             ["React 18.2 with Functional Hooks",
              "Vite 8 Build Tool & HMR",
              "Tailwind CSS for responsive UI",
              "Axios with auto-refresh JWT interceptors",
              "Lucide React iconography & Recharts",
              "React Hot Toast notifications"])
    add_card(s14, Inches(3.7), Inches(1.4), Inches(2.6), Inches(3.6),
             "Backend API Ecosystem",
             ["Python 3.11 Runtime",
              "Django 4.2 LTS & DRF 3.15",
              "SimpleJWT (HMAC-SHA256 tokens)",
              "drf-spectacular (OpenAPI 3.0 / Swagger)",
              "Gunicorn WSGI Application Server",
              "WhiteNoise static file serving"])
    add_card(s14, Inches(6.6), Inches(1.4), Inches(2.6), Inches(3.6),
             "Cloud & Database Services",
             ["Vercel Global Edge CDN (Frontend SPA)",
              "Render Cloud Container (Backend API)",
              "Neon Serverless PostgreSQL (Ohio)",
              "Google Gmail SMTP Relay (Port 587)",
              "Git & GitHub automated CI/CD deployment",
              "ReportLab PDF generation engine"])

    # =========================================================================
    # Slide 15: Quality Assurance & Testing
    # =========================================================================
    s15 = prs.slides.add_slide(blank_layout)
    add_header(s15, "Quality Assurance & Test Suite (49 Tests)", "Comprehensive unit and integration test coverage verifying concurrency, payments & emails")
    add_card(s15, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Test Coverage Breakdown",
             ["10-Minute Boundary Verification: Tests that appointments strictly validate 10-minute intervals (minute % 10 == 0).",
              "Anti-Double-Booking Concurrency: Tests that concurrent booking requests on the same slot trigger HTTP 400 rejection.",
              "Online Payment & Invoicing: Tests fee payments in INR, card/UPI verification, and tax invoice generation.",
              "50% Refund Execution: Tests patient cancellation queuing, admin refund approval, and REF-XXXXXXXX generation.",
              "Email Delivery Verification: Tests that cancellation and completion trigger emails containing user login email address."])
    add_card(s15, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Execution & Verification Metrics",
             ["Test Runner: Django Automated Test Suite (manage.py test core).",
              "Passed Tests: 49 / 49 Tests Passed (100% OK, 0 Errors, 0 Failures).",
              "Execution Speed: ~15.2 seconds across all unit, integration, and security test cases.",
              "Isolated Sandbox: Uses SQLite in-memory test database with locmem.EmailBackend to guarantee test independence.",
              "Code Integrity: Full regression suite verified before every GitHub commit."])

    # =========================================================================
    # Slide 16: Deployment & Future Scope
    # =========================================================================
    s16 = prs.slides.add_slide(blank_layout)
    add_header(s16, "Live Cloud Deployment & Future Scope", "Fully deployed, production-ready healthcare management system")
    add_card(s16, Inches(0.8), Inches(1.4), Inches(4.0), Inches(3.6),
             "Live Production Environments",
             ["Frontend Application: https://hospital-management-system-alpha-olive.vercel.app/",
              "Backend REST API: https://hospital-management-api-c8y9.onrender.com/api/",
              "Swagger API Docs: https://hospital-management-api-c8y9.onrender.com/api/docs/",
              "Source Code Repository: https://github.com/Sreecharan01/Hospital-Management-System",
              "Neon Database: PostgreSQL 16 on AWS Ohio (us-east-2).",
              "SMTP Relay: Google Gmail (CityCare Hospital <sreecharan831@gmail.com>)."],
             title_color=SUCCESS_COLOR)
    add_card(s16, Inches(5.2), Inches(1.4), Inches(4.0), Inches(3.6),
             "Roadmap & Future Enhancements",
             ["WebRTC Video Teleconsultations: Direct in-browser video calling between doctors and patients.",
              "SMS / WhatsApp Gateway: Instant WhatsApp appointment reminders via Twilio or Gupshup.",
              "Pharmacy & Lab Integration: Direct routing of digital prescriptions to diagnostic labs and drugstores.",
              "Mobile Apps: React Native cross-platform iOS and Android companion applications.",
              "Multi-Hospital Tenant Support: Unified health network managing multiple clinical branches."])

    prs.save("hospital_management_system.pptx")
    print("\n[+] Successfully generated presentation: hospital_management_system.pptx (16 Slides)")


if __name__ == "__main__":
    create_deck()
