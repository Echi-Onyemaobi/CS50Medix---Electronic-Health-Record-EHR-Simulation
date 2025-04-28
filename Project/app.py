from flask import Flask, render_template
from flask_session import Session
import os
import sqlite3

# Import blueprints from their respective modules
from appointments_route.appointments import appointments_bp
from dashboard_route.dashboard import dashboard_bp
from history_route.history import history_bp
from labs_route.labs import labs_bp
from locations_route.locations import locations_bp
from media_route.media import media_bp
from medications_route.medication import medications_bp
from patient_route.patient import patients_bp
from authentication_route.authentication import auth_bp
from vitals_route.vitals import vitals_bp
from medications_route.interaction_check import interaction_bp

def get_db_connection():
    """Create a new database connection."""
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

app = Flask(__name__)

# Session config
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.getenv("SESSION_FILE_DIR", "/tmp/flask_sessions")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = os.getenv("SECRET_KEY", "dev_secret")

Session(app)

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(patients_bp)
app.register_blueprint(appointments_bp)
app.register_blueprint(labs_bp)
app.register_blueprint(medications_bp)
app.register_blueprint(media_bp)
app.register_blueprint(locations_bp)
app.register_blueprint(history_bp)
app.register_blueprint(vitals_bp)
app.register_blueprint(interaction_bp)


# Disable caching for development
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom 404 error page
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

# Run the app
if __name__ == "__main__":
    app.run(debug=True)
