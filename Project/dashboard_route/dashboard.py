from datetime import datetime
from flask import Blueprint, render_template
from features import login_required
import sqlite3

# Blueprint configuration
dashboard_bp = Blueprint("dashboard_bp", __name__, template_folder="templates")

# DB Connection
def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Home page
@dashboard_bp.route("/")
@login_required
def dashboard():
    """Render the dashboard with key clinical and administrative metrics."""
    with get_db_connection() as conn:
        # Total active patients
        total_patients = conn.execute("""
            SELECT COUNT(*) AS count FROM Patients WHERE is_active = 1
        """).fetchone()["count"]

        # Next 5 upcoming appointments
        appointments = conn.execute("""
            SELECT a.appointment_datetime AS dt,
                   p.first_name || ' ' || p.last_name AS patient_name
            FROM Appointments a
            JOIN Patients p ON a.patient_id = p.patient_id
            WHERE a.appointment_datetime >= datetime('now')
            ORDER BY a.appointment_datetime
            LIMIT 5
        """).fetchall()

        # Labs that haven't been completed yet
        pending_labs = conn.execute("""
            SELECT COUNT(*) AS count
            FROM LabResults
            WHERE value IS NULL OR TRIM(value) = ''
        """).fetchone()["count"]

        # Patients without assigned rooms
        unassigned_patients = conn.execute("""
            SELECT COUNT(*) AS count
            FROM Patients
            WHERE is_active = 1
              AND patient_id NOT IN (SELECT patient_id FROM RoomAllocation)
        """).fetchone()["count"]

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        upcoming_appointments=appointments,
        pending_labs=pending_labs,
        unassigned_patients=unassigned_patients
    )
