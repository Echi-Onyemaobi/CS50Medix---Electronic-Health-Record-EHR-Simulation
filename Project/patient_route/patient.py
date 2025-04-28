from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from features import login_required, generate_id
import sqlite3

# Blueprint Configuration
patients_bp = Blueprint("patients_bp", __name__, template_folder='templates')

# DB Connection
def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Patient Route
@patients_bp.route("/patients")
@login_required
def patients():
    with get_db_connection() as conn:
        patients = conn.execute("""
            SELECT d.department_name,
                   p.patient_id,
                   p.first_name,
                   p.last_name,
                   r.room_number
            FROM patients p
            LEFT JOIN RoomAllocation r ON p.patient_id = r.patient_id
            LEFT JOIN Departments d    ON r.department_name = d.department_name
            ORDER BY p.last_name
        """).fetchall()
    return render_template("patients.html", patients=patients)

# Add Patient Route
@patients_bp.route("/patient/add", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        patient_id = generate_id("patient")
        fn = request.form.get("first_name")
        ln = request.form.get("last_name")
        dd = request.form.get("dob_day")
        dm = request.form.get("dob_month")
        dy = request.form.get("dob_year")
        gender = request.form.get("gender")

        if not (fn and ln and dd and dm and dy and gender):
            flash("Please fill in all required fields.", "error")
            return render_template("add_patient.html"), 400

        dob = f"{dy}-{int(dm):02d}-{int(dd):02d}"
        try:
            datetime.fromisoformat(dob)
        except ValueError:
            flash("Invalid date.", "error")
            return render_template("add_patient.html"), 400

        phone   = request.form.get("phone_number")
        email   = request.form.get("email")
        address = request.form.get("address")
        blood   = request.form.get("blood_type")
        ecn     = request.form.get("emergency_contact_name")
        ecp     = request.form.get("emergency_contact_phone")
        ins     = request.form.get("insurance_provider")
        ins_no  = request.form.get("insurance_number")
        notes   = request.form.get("notes")

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO patients
                (patient_id, first_name, last_name, date_of_birth, gender,
                phone_number, email, address, blood_type,
                emergency_contact_name, emergency_contact_phone,
                insurance_provider, insurance_number, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (patient_id, fn, ln, dob, gender, phone, email, address,
                blood, ecn, ecp, ins, ins_no, notes))

        return redirect(url_for("patients_bp.patients"))

    return render_template("add_patient.html")

# View Patient Route
@patients_bp.route("/patient/<patient_id>")
@login_required
def patient_profile(patient_id):
    with get_db_connection() as conn:
        # Fetch patient details
        patient = conn.execute(
            "SELECT * FROM patients WHERE patient_id = ?", (patient_id,)
        ).fetchone()

        if not patient:
            flash("Patient not found.", "error")
            return redirect(url_for("patients_bp.patients"))

        # Fetch most recent vitals
        vitals = conn.execute("""
            SELECT * FROM Vitals
            WHERE patient_id = ?
            ORDER BY date_recorded DESC
            LIMIT 1
        """, (patient_id,)).fetchone()

        # Fetch vitals history
        vitals_history = conn.execute("""
            SELECT * FROM Vitals
            WHERE patient_id = ?
            ORDER BY date_recorded DESC
        """, (patient_id,)).fetchall()

        # Fetch room and department assignment
        room = conn.execute("""
            SELECT room_number, department_name
            FROM RoomAllocation
            WHERE patient_id = ?
        """, (patient_id,)).fetchone()

        # Fetch lab orders and lab results
        lab_orders = conn.execute(
            "SELECT * FROM LabOrders WHERE patient_id = ?", (patient_id,)
        ).fetchall()

        lab_results = {
            order["lab_order_id"]: conn.execute(
                "SELECT * FROM LabResults WHERE lab_order_id = ?", (order["lab_order_id"],)
            ).fetchall()
            for order in lab_orders
        }

        # Fetch medications
        medications = conn.execute(
            "SELECT * FROM Medications WHERE patient_id = ?", (patient_id,)
        ).fetchall()

        # Fetch medical history
        history_entries = conn.execute(
            "SELECT * FROM MedicalHistory WHERE patient_id = ?", (patient_id,)
        ).fetchall()

        # Fetch uploaded media files
        media_files = conn.execute(
            "SELECT * FROM media_attachments WHERE patient_id = ?", (patient_id,)
        ).fetchall()

        # Fetch notes
        notes = conn.execute(
            "SELECT * FROM notes WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,)
        ).fetchall()

    return render_template(
        "patient_profile.html",
        patient=patient,
        vitals=vitals,
        vitals_history=vitals_history,
        room=room,
        lab_orders=lab_orders,
        lab_results=lab_results,
        medications=medications,
        medical_history=history_entries,
        media_files=media_files,
        notes=notes
    )

# Edit Patient info Route
@patients_bp.route("/patient/<patient_id>/edit", methods=["GET", "POST"])
@login_required
def edit_patient(patient_id):
    with get_db_connection() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
        if not patient:
            flash("Patient not found.", "error")
            return redirect(url_for("patients_bp.patients"))

    if request.method == "POST":
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE patients
                SET first_name=?, last_name=?, date_of_birth=?, gender=?,
                    phone_number=?, email=?, address=?, blood_type=?,
                    emergency_contact_name=?, emergency_contact_phone=?,
                    insurance_provider=?, insurance_number=?, notes=?
                WHERE patient_id = ?
            """, (
                request.form.get("first_name"),
                request.form.get("last_name"),
                f"{request.form.get('dob_year')}-{int(request.form.get('dob_month')):02d}-{int(request.form.get('dob_day')):02d}",
                request.form.get("gender"),
                request.form.get("phone_number"),
                request.form.get("email"),
                request.form.get("address"),
                request.form.get("blood_type"),
                request.form.get("emergency_contact_name"),
                request.form.get("emergency_contact_phone"),
                request.form.get("insurance_provider"),
                request.form.get("insurance_number"),
                request.form.get("notes"),
                patient_id
            ))
        return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

    return render_template("edit_patient.html", patient=patient)

# Patient Notes Route
@patients_bp.route("/patient/<patient_id>/notes", methods=["GET", "POST"])
@login_required
def patient_notes(patient_id):
    with get_db_connection() as conn:
        if request.method == "POST":
            note = request.form.get("note")
            if not note:
                flash("Note can’t be empty.", "error")
                return redirect(request.url)
            conn.execute(
                "INSERT INTO notes (patient_id, note, created_at) VALUES (?, ?, datetime('now'))",
                (patient_id, note)
            )
            return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

        notes = conn.execute("SELECT * FROM notes WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,)).fetchall()
        patient = conn.execute("SELECT first_name, last_name FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()

    return render_template("patient_notes.html", notes=notes, patient=patient, patient_id=patient_id)
