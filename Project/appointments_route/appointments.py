from datetime import datetime
from features import login_required
from flask import Blueprint, render_template, request, redirect, flash, session, url_for
import sqlite3

# Blueprint Configuration
appointments_bp = Blueprint("appointments_bp", __name__, template_folder="templates")

# DB Connection
def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Appointment Route
@appointments_bp.route("/appointments")
@login_required
def appointments():
    """Show upcoming appointments with patient and doctor names."""
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT
              a.id,
              a.appointment_datetime AS dt,
              a.reason,
              p.first_name || ' ' || p.last_name AS patient_name,
              d.first_name || ' ' || d.last_name AS doctor_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.patient_id
            JOIN doctors  d ON a.doctor_id  = d.doctor_id
            WHERE a.appointment_datetime >= datetime('now')
            ORDER BY a.appointment_datetime
        """).fetchall()

    appointments = []
    for row in rows:
        appt = dict(row)
        appt["dt"] = datetime.fromisoformat(appt["dt"])
        appointments.append(appt)

    if not appointments:
        flash("No upcoming appointments.", "info")

    return render_template("appointments.html", appointments=appointments)

# Add Appointment Route
@appointments_bp.route("/appointment/add", methods=["GET", "POST"])
@login_required
def add_appointment():
    """Schedule a new appointment."""
    with get_db_connection() as conn:
        patients = conn.execute(
            "SELECT patient_id, first_name, last_name FROM patients"
        ).fetchall()
        doctors = conn.execute(
            "SELECT doctor_id, first_name, last_name FROM doctors"
        ).fetchall()

    if request.method == "POST":
        pid    = request.form.get("patient_id")
        did    = request.form.get("doctor_id")
        dt_str = request.form.get("appointment_datetime")
        reason = request.form.get("reason")

        if not (pid and did and dt_str and reason):
            flash("All fields are required.", "error")
            return render_template("add_appointment.html", patients=patients, doctors=doctors), 400

        try:
            datetime.fromisoformat(dt_str)
        except ValueError:
            flash("Invalid date/time.", "error")
            return render_template("add_appointment.html", patients=patients, doctors=doctors), 400

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO appointments
                  (patient_id, doctor_id, appointment_datetime, reason)
                VALUES (?, ?, ?, ?)
            """, (pid, did, dt_str, reason))

        flash("Appointment set!", "success")
        return redirect(url_for("appointments_bp.appointments"))

    return render_template("add_appointment.html", patients=patients, doctors=doctors)
