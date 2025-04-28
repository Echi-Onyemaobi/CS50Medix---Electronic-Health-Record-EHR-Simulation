CS50Medix - Electronic Health Record (EHR) Simulation


Project Overview
CS50Medix is a modular Electronic Health Record (EHR) simulation platform, built using Flask, SQLite, HTML/CSS, and external APIs like RxNorm and OpenFDA.
The system models real-world healthcare workflows, including patient management, appointments, medication tracking, vital signs, lab orders, and medication interaction checking.

Goal:
Create a foundational EHR platform that mirrors the structure, usability, and extensibility of real hospital systems — while integrating live medical databases and smart validation tools.

Youtube link: https://youtu.be/wL0JrP7Eol

Technologies Used
Backend: Flask (Python)

Database: SQLite3

Frontend: HTML5, CSS3 (custom styling, responsive-ready)

External APIs:

RxNorm (for medication data & verification)

OpenFDA (for backup drug interactions if RxNorm is incomplete)

Authentication: Session-based login (@login_required decorators)

Deployment-ready structure: Flask Blueprints for modularity


Main Features

Feature	Description
        Patient Management	Add, view, edit, and delete patient records
        Appointments	Schedule appointments linked to patients and doctors
        Vitals Tracking	Record essential vitals with timestamps
        Lab Orders & Results	Order labs, input and view results
        Room Allocations	Assign patients to rooms and departments
        Medication Management	Add medications, categorize (hospital/home meds), discontinue tracking
        Medication Dictionary	Search local medications (seeded) + fallback to live RxNorm if missing
        Interaction Checker	Compare two medications, checking interactions through RxNorm (or OpenFDA if no data)
        Dynamic Autocomplete	Live medication autocomplete in forms
        Dashboard	Real-time counts of patients, upcoming appointments
        Flash Messaging	User feedback on actions (add/delete/edit/etc.)
Smart Architecture Highlights
Hybrid Medication Handling:
First search the local medication database for speed. If missing, query RxNorm live. If still missing, fallback to OpenFDA interaction records.

Expandable EHR Blueprints:
Clear separation between Patients, Appointments, Medications, and Interactions. Easy to extend further (e.g., add billing module, imaging orders).

Live Error Handling:
Graceful flash messaging and JSON errors if any API or database queries fail.

Dark Mode Ready:
Theme toggle support for dark/light mode in CSS (future enhancement).

Folder Structure
Project/
│
├── app.py
├── ehr.db
├── features.py
├── readme.md
│
├── appointments_route/
│   ├── appointments.py
│   └── templates/
│       ├── add_appointment.html
│       └── appointments.html
│
├── authentication_route/
│   ├── authentication.py
│   └── templates/
│       ├── login.html
│       ├── register.html
│       └── register_success.html
│
├── dashboard_route/
│   ├── dashboard.py
│   └── templates/
│       └── dashboard.html
│
├── history_route/
│   ├── history.py
│   └── templates/
│       ├── add_history.html
│       ├── edit_history.html
│       └── view_history.html
│
├── labs_route/
│   ├── labs.py
│   └── templates/
│       ├── add_lab_order.html
│       ├── add_lab_result.html
│       ├── lab_orders.html
│       └── lab_results.html
│
├── locations_route/
│   ├── locations.py
│   └── templates/
│       ├── assign_room.html
│       ├── departments.html
│       └── rooms.html
│
├── media_route/
│   ├── media.py
│   └── templates/
│       ├── upload_media.html
│       └── view_media.html
│
├── medications_route/
│   ├── medication.py
│   ├── interaction_check.py
│   ├── medication_builder.py
│   └── templates/
│       ├── add_medication.html
│       ├── medication_checker.html
│       ├── medication_detail.html
│       ├── medication_dictionary.html
│       └── view_medications.html
│
├── patient_route/
│   ├── patient.py
│   └── templates/
│       ├── add_patient.html
│       ├── edit_patient.html
│       ├── patient_notes.html
│       ├── patient_profile.html
│       ├── patients.html
│       └── view_patient.html
│
├── vitals_route/
│   ├── vitals.py
│   └── templates/
│       ├── add_vitals.html
│       ├── vitals_chart.html
│       ├── vitals_table.html
│       └── vitals_trends.html
│
├── templates/
│   └── layout.html
│
├── static/
│   ├── uploads/
│   └── styles.css

Future Improvement Plans (Phase 2)

Idea	Description
Role-Based Access	Nurse, Doctor, Admin logins with permissions
Vitals Charting	Plot patient vitals over time
Lab Auto-Flagging	Highlight abnormal labs automatically
Audit Trails	Track edits to patient records securely
Mobile Responsive	Full mobile version for bedside charting
RxNorm Sync	Monthly updates to local medication cache
AI Expansion	AI drug recommendations, predictive flags for adverse events
Performance Upgrades	Switch from SQLite to PostgreSQL for larger datasets

How to Run Locally
Clone the repo

Create a virtual environment

Install Flask: pip install Flask

Run app: flask run

Navigate to http://127.0.0.1:5000 to start the system

Thank You!

