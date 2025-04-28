from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

# Blueprint Configuration
locations_bp = Blueprint("locations_bp", __name__, template_folder="templates")

# DB Connection
def get_db_connection():
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Default list of hospital departments
DEFAULT_DEPARTMENTS = [
    'Anesthesiology', 'Cardiology', 'Emergency Department', 'Endocrinology',
    'Family Medicine', 'Gastroenterology', 'Health Information Management / Medical Records', 'Hematology',
    'ICU (Intensive Care Unit)', 'Internal Medicine', 'Laboratory / Pathology', 'Medical-Surgical',
    'Neonatology', 'Nephrology', 'Neurology', 'Neurosurgery',
    'Obstetrics and Gynecology', 'Oncology', 'Orthopedic Surgery', 'PACU',
    'Pediatrics', 'Pharmacy', 'Psychiatry', 'Pulmonology',
    'Radiology', 'Surgical', 'Urology', 'Wound Care'
]

# Initialize default departments if not already in the database
@locations_bp.route("/departments/init")
def init_departments():
    with get_db_connection() as conn:
        for dept in DEFAULT_DEPARTMENTS:
            conn.execute("INSERT OR IGNORE INTO Departments (department_name) VALUES (?)", (dept,))
    flash("Departments initialized successfully.", "success")
    return redirect(url_for("locations_bp.departments"))

# View Department Route
@locations_bp.route("/departments")
def departments():
    with get_db_connection() as conn:
        departments = conn.execute("SELECT * FROM Departments ORDER BY department_name").fetchall()
    return render_template("departments.html", departments=departments)

# View Rooms Route
@locations_bp.route("/rooms")
def rooms():
    with get_db_connection() as conn:
        rooms = conn.execute("""
            SELECT r.room_number, r.department_name, p.first_name || ' ' || p.last_name AS patient_name
            FROM RoomAllocation r
            LEFT JOIN Patients p ON r.patient_id = p.patient_id
        """).fetchall()

        departments = conn.execute("SELECT department_name FROM Departments ORDER BY department_name").fetchall()

    return render_template("rooms.html", rooms=rooms, departments=departments)



# Assign Room (Room Number + Department) Route
@locations_bp.route("/room/assign/<patient_id>", methods=["GET", "POST"])
def assign_room(patient_id):
    with get_db_connection() as conn:
        if request.method == "POST":
            room_number = request.form.get("room_number")
            department = request.form.get("department_name")

            if not room_number or not department:
                flash("Room and department are required.", "error")
                return redirect(request.url)

            conn.execute("""
                INSERT OR REPLACE INTO RoomAllocation (patient_id, room_number, department_name)
                VALUES (?, ?, ?)
            """, (patient_id, room_number, department))

            flash("Room and department assigned successfully.", "success")
            return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

        departments = conn.execute("SELECT department_name FROM Departments ORDER BY department_name").fetchall()

    return render_template("assign_room.html", patient_id=patient_id, departments=departments)
