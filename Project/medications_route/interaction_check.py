# interaction_checker.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import requests
from features import login_required

# Blueprint Configuration
interaction_bp = Blueprint('interaction_bp', __name__, template_folder='templates')

# DB Connection
def get_db_connection():
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn


# Open FDA API
def query_openfda_for_interaction(med1, med2):
    """Query OpenFDA for potential interaction between two meds."""
    try:
        url = "https://api.fda.gov/drug/event.json"
        params = {"search": f'patient.drug.medicinalproduct:"{med1}"+patient.drug.medicinalproduct:"{med2}"', "limit": 10}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get('results'):
            return True  # We found cases where both meds appeared in adverse reports
    except Exception as e:
        print(f"OpenFDA fallback error: {e}")

    return False


# Utility: Find RXCUI locally, or live from RxNorm, and save if found
def get_rxcui(medication_name):
    # Try local database first
    with get_db_connection() as conn:
        result = conn.execute("""
            SELECT rxcui FROM MedicationDictionary WHERE name LIKE ?
        """, (medication_name,)).fetchone()

    if result:
        return result["rxcui"]

    # Tto fry etch from RxNorm
    try:
        response = requests.get(
            "https://rxnav.nlm.nih.gov/REST/rxcui.json",
            params={"name": medication_name}
        )
        response.raise_for_status()
        data = response.json()
        rxcui = data.get("idGroup", {}).get("rxnormId", [None])[0]

        if rxcui:
            # Save it locally for faster future access
            with get_db_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO MedicationDictionary (rxcui, name, dosage_form, strength, brand_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (rxcui, medication_name, None, None, None))
                conn.commit()
            return rxcui
    except Exception:
        pass

    return None

# API: Check Medication Interactions Route
@interaction_bp.route("/check_interactions", methods=["POST"])
@login_required
def check_interactions():
    data = request.get_json()
    med1_name = data.get('med1')
    med2_name = data.get('med2')

    if not med1_name or not med2_name:
        return jsonify({"error": "Both medications must be selected."}), 400

    rxcui1 = get_rxcui(med1_name)
    rxcui2 = get_rxcui(med2_name)

    if not rxcui1 or not rxcui2:
        return jsonify({"error": "Could not find RXCUI for one or both medications."}), 404

    # Try RxNorm interaction API first
    interactions = []
    try:
        api_url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rxcui1}+{rxcui2}"
        response = requests.get(api_url)
        response.raise_for_status()
        interaction_data = response.json()

        groups = interaction_data.get("fullInteractionTypeGroup", [])
        for group in groups:
            for interactionType in group.get("fullInteractionType", []):
                for interactionPair in interactionType.get("interactionPair", []):
                    interactions.append({
                        "description": interactionPair.get("description", "No description available"),
                        "severity": interactionPair.get("severity", "Unknown")
                    })

    except Exception as e:
        print(f"RxNorm API error: {e}")

    # Check OpenFDA if no interactions found
    if not interactions and query_openfda_for_interaction(med1_name, med2_name):
        interactions.append({
            "description": f"Potential adverse event reported between {med1_name} and {med2_name}.",
            "severity": "Warning"
        })

    # Fetch basic med profiles to compare
    with get_db_connection() as conn:
        med1 = conn.execute("SELECT * FROM MedicationDictionary WHERE name LIKE ?", (med1_name,)).fetchone()
        med2 = conn.execute("SELECT * FROM MedicationDictionary WHERE name LIKE ?", (med2_name,)).fetchone()

    med1_data = dict(med1) if med1 else {"name": med1_name}
    med2_data = dict(med2) if med2 else {"name": med2_name}

    return jsonify({
        "interactions": interactions,
        "med1": med1_data,
        "med2": med2_data
    })


# Interaction Checker Route
@interaction_bp.route("/medication_checker", methods=["GET"])
@login_required
def interaction_checker():
    return render_template("medication_checker.html")
