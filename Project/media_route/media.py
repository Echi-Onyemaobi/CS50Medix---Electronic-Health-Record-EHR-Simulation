from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from features import login_required
import os
import sqlite3
from werkzeug.utils import secure_filename

# Blueprint Configuration
media_bp = Blueprint("media_bp", __name__, template_folder='templates')

# DB Connection
def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Upload Media Route
@media_bp.route("/media/upload", methods=["GET", "POST"])
@login_required
def upload_media():
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        file = request.files.get("file")
        media_type = request.form.get("media_type")
        caption = request.form.get("caption")

        if not patient_id or not file:
            flash("Patient ID and file are required.", "error")
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        rel_path = f"uploads/{filename}"

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO media_attachments (
                    patient_id, uploaded_by, file_path, media_type, caption
                ) VALUES (?, ?, ?, ?, ?)
            """, (patient_id, session["user_id"], rel_path, media_type, caption))

        flash("File uploaded successfully!", "success")
        return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

    return render_template("upload_media.html")

# Patient Media Route
@media_bp.route("/patient/<patient_id>/media")
@login_required
def view_media(patient_id):
    with get_db_connection() as conn:
        media_files = conn.execute("""
            SELECT * FROM media_attachments
            WHERE patient_id = ?
            ORDER BY uploaded_at DESC
        """, (patient_id,)).fetchall()

        patient = conn.execute("""
            SELECT first_name, last_name FROM Patients
            WHERE patient_id = ?
        """, (patient_id,)).fetchone()

    return render_template("view_media.html", patient=patient, media_files=media_files, patient_id=patient_id)
