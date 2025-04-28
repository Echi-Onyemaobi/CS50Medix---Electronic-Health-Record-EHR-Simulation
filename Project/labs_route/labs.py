from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import sqlite3

# Blueprint Configuration
labs_bp = Blueprint("labs_bp", __name__, template_folder='templates')

# DB Connection
def get_db_connection():
    """Open a connection to the SQLite database."""
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Add Lab Orders
@labs_bp.route("/patient/<patient_id>/labs/add", methods=["GET", "POST"])
def add_lab_order(patient_id):
    if request.method == "POST":
        order_type = request.form.get("order_type")
        order_name = request.form.get("order_name")
        notes = request.form.get("notes")
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO LabOrders (patient_id, order_date, order_type, order_name, notes)
                VALUES (?, DATE('now'), ?, ?, ?)
            """, (patient_id, order_type, order_name, notes))
        flash("Lab order placed.", "success")
        return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))
    return render_template("add_lab_order.html", patient_id=patient_id)

# Add Lab Results
@labs_bp.route("/lab_order/<int:lab_order_id>/result/add", methods=["GET", "POST"])
def add_lab_result(lab_order_id):
    patient_id = request.args.get("patient_id")
    if request.method == "POST":
        test_name = request.form.get("test_name")
        value = request.form.get("value")
        reference_range = request.form.get("reference_range")
        ref_low = request.form.get("reference_low")
        ref_high = request.form.get("reference_high")
        notes = request.form.get("notes")
        critical = int(request.form.get("critical_flag", 0))

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO LabResults (
                    lab_order_id, test_name, value, reference_range,
                    reference_low, reference_high, notes, critical_flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (lab_order_id, test_name, value, reference_range, ref_low, ref_high, notes, critical))

        flash("Lab result added.", "success")
        return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

    return render_template("add_lab_result.html", lab_order_id=lab_order_id, patient_id=patient_id)

# View Lab Orders
@labs_bp.route("/lab_orders/<patient_id>")
def lab_orders(patient_id):
    with get_db_connection() as conn:
        orders = conn.execute("""
            SELECT lo.lab_order_id, lo.patient_id, lo.order_name, lo.order_date, lo.order_type,
                   p.first_name || ' ' || p.last_name AS patient_name
            FROM LabOrders lo
            JOIN Patients p ON lo.patient_id = p.patient_id
            WHERE lo.patient_id = ?
            ORDER BY lo.order_date DESC
        """, (patient_id,)).fetchall()
    return render_template("lab_orders.html", orders=orders, patient_id=patient_id)

# View Lab Result
@labs_bp.route("/lab_order/<int:lab_order_id>/results")
def lab_results(lab_order_id):
    with get_db_connection() as conn:
        results = conn.execute("""
            SELECT lr.test_name, lr.value, lr.reference_range, lr.reference_low, lr.reference_high,
                   lr.result_date, lr.units, lr.critical_flag
            FROM LabResults lr
            WHERE lr.lab_order_id = ?
            ORDER BY lr.result_date ASC
        """, (lab_order_id,)).fetchall()

    trend_data = {}
    for r in results:
        if r["test_name"] not in trend_data:
            trend_data[r["test_name"]] = []
        trend_data[r["test_name"]].append({
            "x": r["result_date"],
            "y": r["value"]
        })

    return render_template(
        "lab_results.html",
        lab_order_id=lab_order_id,
        results=results,
        trend_data=trend_data
    )
