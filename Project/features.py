from functools import wraps
from flask import session, redirect
import sqlite3
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)

# Decorator to ensure a user is logged in before viewing a page.
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("user_id"):
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# ID Generator Settings
DB_PATH = "ehr.db"

ROLE_PREFIX = {
    "doctor":  "DC7",
    "nurse":   "RN6",
    "patient": "PT1"
}

def generate_id(role):
    prefix = ROLE_PREFIX.get(role)
    if not prefix:
        logging.warning(f"Attempted ID generation with unknown role: {role}")
        raise ValueError(f"Unknown role: {role}")

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        if role == "patient":
            cur.execute("""
                SELECT patient_id FROM Patients
                WHERE patient_id LIKE ?
                ORDER BY ROWID DESC
                LIMIT 1
            """, (f"{prefix}%",))
        else:
            cur.execute("""
                SELECT user_id FROM users
                WHERE role = ?
                ORDER BY ROWID DESC
                LIMIT 1
            """, (role,))

        row = cur.fetchone()
    except sqlite3.Error as e:
        logging.error(f"Database error: {e}")
        raise
    finally:
        conn.close()

    if row:
        last_id = row[0]
        num = int(last_id.replace(prefix, ""))
    else:
        num = -1

    new_id = prefix + str(num + 1).zfill(4)
    return new_id
