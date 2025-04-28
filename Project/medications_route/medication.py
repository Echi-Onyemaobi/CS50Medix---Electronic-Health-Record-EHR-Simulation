from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash, session
from features import login_required
import sqlite3
import csv
import os

# Blueprint Configuration
medications_bp = Blueprint("medications_bp", __name__, template_folder='templates')

# DB Connection
def get_db_connection():
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Load the Medication Dictionary into the database if not exists
def initialize_medication_dictionary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS MedicationDictionary (
        rxcui TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dosage_form TEXT,
        strength TEXT,
        brand_name TEXT
    );
    """)
    conn.commit()

    csv_path = os.path.join(os.path.dirname(__file__), '../rxnorm_concepts.csv')
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        meds_to_insert = []
        for row in reader:
            rxcui = row['rxcui']
            name = row['name']
            dosage_form = row.get('dosage_form', None)
            strength = row.get('strength', None)
            brand_name = row.get('brand_name', None)

            meds_to_insert.append((rxcui, name, dosage_form, strength, brand_name))

        cur.executemany("""
        INSERT OR IGNORE INTO MedicationDictionary (rxcui, name, dosage_form, strength, brand_name)
        VALUES (?, ?, ?, ?, ?);
        """, meds_to_insert)

    conn.commit()
    conn.close()


# Initialize Medication Dictionary
def initialize_medication_dictionary():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS MedicationDictionary (
        rxcui TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dosage_form TEXT,
        strength TEXT,
        brand_name TEXT
    );
    """)
    conn.commit()
    conn.close()


# Add medication Route
@medications_bp.route("/patient/<patient_id>/add_medication", methods=["GET", "POST"])
@login_required
def add_medication(patient_id):
    if request.method == "POST":
        data = (
            patient_id,
            request.form.get("medication_name"),
            request.form.get("dosage"),
            request.form.get("route"),
            request.form.get("frequency"),
            request.form.get("start_date"),
            request.form.get("end_date"),
            request.form.get("status", "Active"),
            request.form.get("type", "hospital"),
            request.form.get("notes")
        )

        if not data[1] or not data[2]:
            flash("Medication name and dosage are required.", "error")
            return redirect(request.url)

        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO Medications (
                    patient_id, medication_name, dosage, route, frequency,
                    start_date, end_date, status, type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)
        flash("Medication added successfully!", "success")
        return redirect(url_for("patients_bp.patient_profile", patient_id=patient_id))

    return render_template("add_medication.html", patient_id=patient_id)

# View patient's medications Route
@medications_bp.route("/patient/<patient_id>/medications")
@login_required
def view_medications(patient_id):
    with get_db_connection() as conn:
        patient = conn.execute("SELECT first_name, last_name FROM Patients WHERE patient_id = ?", (patient_id,)).fetchone()

        hospital_meds = conn.execute("""
            SELECT * FROM Medications
            WHERE patient_id = ? AND status = 'Active' AND type = 'hospital'
            ORDER BY start_date DESC
        """, (patient_id,)).fetchall()

        home_meds = conn.execute("""
            SELECT * FROM Medications
            WHERE patient_id = ? AND type = 'home'
            ORDER BY start_date DESC
        """, (patient_id,)).fetchall()

        discontinued_meds = conn.execute("""
            SELECT * FROM Medications
            WHERE patient_id = ? AND status = 'Discontinued'
            ORDER BY end_date DESC
        """, (patient_id,)).fetchall()

    return render_template("view_medications.html",
                           patient=patient,
                           hospital_meds=hospital_meds,
                           home_meds=home_meds,
                           discontinued_meds=discontinued_meds)

# Discontinue a medication Route
@medications_bp.route("/patient/<patient_id>/medications/<int:medication_id>/discontinue", methods=["POST"])
@login_required
def discontinue_medication(patient_id, medication_id):
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE Medications
            SET status = 'Discontinued', end_date = DATE('now')
            WHERE medication_id = ?
        """, (medication_id,))
    flash("Medication discontinued.", "info")
    return redirect(url_for("medications_bp.view_medications", patient_id=patient_id))

# Browse Medication Dictionary Route
@medications_bp.route("/medication_dictionary")
@login_required
def medication_dictionary():
    with get_db_connection() as conn:
        meds = conn.execute("SELECT * FROM MedicationDictionary ORDER BY name ASC").fetchall()
    return render_template("medication_dictionary.html", meds=meds)

# Search Medication Dictionary Route
@medications_bp.route("/search_medications", methods=["GET"])
@login_required
def search_medications():
    query = request.args.get("query", "").strip()
    if not query:
        flash("Please enter a search term.", "error")
        return redirect(url_for('medications_bp.medication_dictionary'))

    # First: Try to search in local database
    with get_db_connection() as conn:
        meds = conn.execute("""
            SELECT * FROM MedicationDictionary
            WHERE name LIKE ?
            ORDER BY name ASC
        """, (f"%{query}%",)).fetchall()

    if meds:
        # Found meds locally
        return render_template("medication_dictionary.html", meds=meds, search_query=query)

    # Second: Not found locally — search live RxNorm
    try:
        response = requests.get("https://rxnav.nlm.nih.gov/REST/drugs.json", params={"name": query})
        response.raise_for_status()
        data = response.json()
    except Exception:
        flash("Error searching RxNorm.", "error")
        return redirect(url_for('medications_bp.medication_dictionary'))

    meds = []
    try:
        for concept_group in data.get("drugGroup", {}).get("conceptGroup", []):
            for drug in concept_group.get("conceptProperties", []):
                meds.append({
                    "rxcui": drug.get("rxcui"),
                    "name": drug.get("name"),
                    "dosage_form": None,
                    "strength": None,
                    "brand_name": None
                })
    except Exception:
        pass

    # Save new meds into local database
    if meds:
        with get_db_connection() as conn:
            for med in meds:
                conn.execute("""
                    INSERT OR IGNORE INTO MedicationDictionary (rxcui, name, dosage_form, strength, brand_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (med["rxcui"], med["name"], med["dosage_form"], med["strength"], med["brand_name"]))
            conn.commit()

    return render_template("medication_dictionary.html", meds=meds, search_query=query)


# View Medication Details 
@medications_bp.route("/medication/<rxcui>")
@login_required
def view_medication_details(rxcui):
    with get_db_connection() as conn:
        medication = conn.execute("SELECT * FROM MedicationDictionary WHERE rxcui = ?", (rxcui,)).fetchone()

        if medication:
            return render_template("medication_detail.html", medication=medication)

    # If not found locally, fetch from RxNorm
    try:
        prop_response = requests.get(f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json")
        prop_response.raise_for_status()
        props = prop_response.json().get("properties")

        if props:
            # Insert into local db for future
            with get_db_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO MedicationDictionary (rxcui, name, dosage_form, strength, brand_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    props.get("rxcui"),
                    props.get("name"),
                    props.get("dosageFormName"),
                    props.get("strength"),
                    props.get("brandName")
                ))
                conn.commit()

            flash("Medication added to database ✅", "success")
            return render_template("medication_detail.html", medication=props)

    except Exception as e:
        flash(f"Could not fetch medication details: {str(e)}", "error")
        return redirect(url_for('medications_bp.medication_dictionary'))

    flash("Medication not found.", "error")
    return redirect(url_for('medications_bp.medication_dictionary'))



# Autocomplete medications
@medications_bp.route("/autocomplete_medications", methods=["GET"])
@login_required
def autocomplete_medications():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])

    # First: Search local database
    with get_db_connection() as conn:
        results = conn.execute("""
            SELECT rxcui, name FROM MedicationDictionary
            WHERE name LIKE ?
            ORDER BY name ASC
            LIMIT 10
        """, (f"%{query}%",)).fetchall()

    if results:
        # Found locally
        medications = [{"rxcui": row["rxcui"], "name": row["name"]} for row in results]
        return jsonify(medications)

    # Second: Not found locally — search RxNorm
    try:
        response = requests.get("https://rxnav.nlm.nih.gov/REST/drugs.json", params={"name": query})
        response.raise_for_status()
        data = response.json()
    except Exception:
        return jsonify([])

    medications = []
    try:
        for concept_group in data.get("drugGroup", {}).get("conceptGroup", []):
            for drug in concept_group.get("conceptProperties", []):
                medications.append({
                    "rxcui": drug.get("rxcui"),
                    "name": drug.get("name")
                })
    except Exception:
        pass

    # Save the meds found into local DB
    if medications:
        with get_db_connection() as conn:
            for med in medications:
                conn.execute("""
                    INSERT OR IGNORE INTO MedicationDictionary (rxcui, name, dosage_form, strength, brand_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (med["rxcui"], med["name"], None, None, None))
            conn.commit()

    return jsonify(medications)
