from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
import sqlite3

# Blueprint Configuration
vitals_bp = Blueprint("vitals_bp", __name__, template_folder="templates")

def get_db_connection():
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

@vitals_bp.route("/patient/<patient_id>/vitals", methods=["GET"])
def vitals_table(patient_id):
    with get_db_connection() as conn:
        vitals_data = conn.execute("""
            SELECT date_recorded, temperature, heart_rate, respiratory_rate,
                   blood_pressure_systolic, blood_pressure_diastolic,
                   oxygen_saturation, pain_level
            FROM Vitals
            WHERE patient_id = ?
            ORDER BY date_recorded ASC
        """, (patient_id,)).fetchall()

    return render_template("vitals_table.html", patient_id=patient_id, vitals=vitals_data)

@vitals_bp.route("/patient/<patient_id>/vitals/add", methods=["GET", "POST"])
def add_vitals(patient_id):
    if request.method == "POST":
        temp_unit = request.form.get("temp_unit", "C")
        temp = float(request.form.get("temperature"))
        if temp_unit == "F":
            temp = (temp - 32) * 5.0/9.0  # Convert to Celsius

        systolic = int(request.form.get("blood_pressure_systolic"))
        diastolic = int(request.form.get("blood_pressure_diastolic"))
        map_value = round((systolic + 2 * diastolic) / 3)

        flags = {
            "respiration": int(request.form.get("respiratory_rate")) > 20,
            "bp_sys": systolic > 120 or systolic < 80,
            "bp_dia": diastolic < 60 or diastolic > 90,
            "map": map_value < 65 or map_value > 100,
            "temperature": temp < 36.1 or temp > 37.2,
            "spo2": int(request.form.get("oxygen_saturation")) < 90
        }

        data = (
            patient_id,
            session["user_id"],
            temp,
            request.form.get("heart_rate"),
            request.form.get("respiratory_rate"),
            systolic,
            diastolic,
            request.form.get("oxygen_saturation"),
            request.form.get("pain_level"),
            map_value,
            request.form.get("oxygen_method"),
            request.form.get("oxygen_flow_rate"),
            request.form.get("blood_sugar"),
            request.form.get("pain_description"),
            json.dumps(flags),
            request.form.get("notes")
        )

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO Vitals (
                    patient_id, recorded_by, temperature, heart_rate,
                    respiratory_rate, blood_pressure_systolic, blood_pressure_diastolic,
                    oxygen_saturation, pain_level, map, oxygen_method,
                    oxygen_flow_rate, blood_sugar, pain_description, flags, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

        flash("Vitals recorded successfully with flags.", "success")
        return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

    return render_template("add_vitals.html", patient_id=patient_id)

@vitals_bp.route("/patient/<patient_id>/vitals/chart")
def vitals_chart(patient_id):
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT datetime(date_recorded) as time,
                   temperature, heart_rate,
                   blood_pressure_systolic AS bp_systolic,
                   blood_pressure_diastolic AS bp_diastolic,
                   respiratory_rate, oxygen_saturation
            FROM Vitals
            WHERE patient_id = ?
            ORDER BY date_recorded ASC
        """, (patient_id,)).fetchall()

    vitals_data = [
        {
            "time": row["time"],
            "temperature": row["temperature"],
            "heart_rate": row["heart_rate"],
            "bp_systolic": row["bp_systolic"],
            "bp_diastolic": row["bp_diastolic"],
            "respiratory_rate": row["respiratory_rate"],
            "oxygen_saturation": row["oxygen_saturation"]
        }
        for row in rows
    ]

    return render_template("vitals_chart.html", patient_id=patient_id, vitals_data=vitals_data)
