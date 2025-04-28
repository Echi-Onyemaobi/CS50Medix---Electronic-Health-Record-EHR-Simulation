from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from features import login_required
import sqlite3

# Blueprint Configuration
history_bp = Blueprint("history_bp", __name__, template_folder="templates")

# DB Connection
def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Add History Route
@history_bp.route("/patient/<patient_id>/history/add", methods=["GET", "POST"])
@login_required
def add_history(patient_id):
    if request.method == "POST":
        condition_name = request.form.get("condition_name")
        diagnosis_date = request.form.get("diagnosis_date")
        status = request.form.get("status")
        notes = request.form.get("notes")

        if not condition_name or not diagnosis_date:
            flash("Condition name and diagnosis date are required.", "error")
            return redirect(request.url)

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO MedicalHistory (patient_id, condition_name, diagnosis_date, status, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (patient_id, condition_name, diagnosis_date, status, notes))

        flash("Medical history added.", "success")
        return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

    return render_template("add_history.html", patient_id=patient_id)

# View History Route
@history_bp.route("/patient/<patient_id>/history")
@login_required
def view_history(patient_id):
    with get_db_connection() as conn:
        history = conn.execute("""
            SELECT * FROM MedicalHistory
            WHERE patient_id = ?
            ORDER BY diagnosis_date DESC
        """, (patient_id,)).fetchall()

    return render_template("view_history.html", history=history, patient_id=patient_id)

# Edit History Route
@history_bp.route("/history/<int:history_id>/edit", methods=["GET", "POST"])
@login_required
def edit_history(history_id):
    with get_db_connection() as conn:
        history = conn.execute("SELECT * FROM MedicalHistory WHERE id = ?", (history_id,)).fetchone()
        if not history:
            flash("History record not found.", "error")
            return redirect(url_for("dashboard_bp.dashboard"))

    if request.method == "POST":
        condition_name = request.form.get("condition_name")
        diagnosis_date = request.form.get("diagnosis_date")
        status = request.form.get("status")
        notes = request.form.get("notes")

        with get_db_connection() as conn:
            conn.execute("""
                UPDATE MedicalHistory
                SET condition_name = ?, diagnosis_date = ?, status = ?, notes = ?
                WHERE id = ?
            """, (condition_name, diagnosis_date, status, notes, history_id))

        flash("History updated.", "success")
        return redirect(url_for("patients_bp.patient_profile", patient_id=history["patient_id"]))

    return render_template("edit_history.html", history=history)

# # Delete History Route
@history_bp.route("/history/<int:history_id>/delete", methods=["POST"])
@login_required
def delete_history(history_id):
    with get_db_connection() as conn:
        history = conn.execute("SELECT patient_id FROM MedicalHistory WHERE id = ?", (history_id,)).fetchone()
        conn.execute("DELETE FROM MedicalHistory WHERE id = ?", (history_id,))

    flash("History entry deleted.", "info")
    return redirect(url_for("patients_bp.patient_profile", patient_id=history["patient_id"]))
