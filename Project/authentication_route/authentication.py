from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from features import generate_id
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

# Blueprint Configuration
auth_bp = Blueprint("auth_bp", __name__, template_folder="templates")

# DB Connection
def get_db_connection():
    conn = sqlite3.connect("ehr.db")
    conn.row_factory = sqlite3.Row
    return conn

# Registration Route
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        role = request.form.get("role")

        if not username or not password or not confirmation or not role:
            flash("All fields are required.", "error")
            return render_template("register.html"), 400
        if password != confirmation:
            flash("Passwords don't match.", "error")
            return render_template("register.html"), 400

        conn = get_db_connection()
        if conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            conn.close()
            flash("Username already exists.", "error")
            return render_template("register.html"), 400

        user_code = generate_id(role)
        hash_pw = generate_password_hash(password)

        conn.execute("""
            INSERT INTO users (username, hash, role, user_id)
            VALUES (?, ?, ?, ?)
        """, (username, hash_pw, role, user_code))
        conn.commit()
        user_row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        conn.close()

        session["user_id"] = user_row["id"]
        flash(f"Welcome, {role.capitalize()}! Your User ID is {user_code}.", "success")
        return render_template("register_success.html", user_id=user_code)

    return render_template("register.html")

# Login Route
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        user_code = request.form.get("user_id")
        password = request.form.get("password")

        if not username or not user_code or not password:
            flash("Username, User ID, and password are required.", "error")
            return render_template("login.html"), 400

        conn = get_db_connection()
        user = conn.execute("""
            SELECT * FROM users
            WHERE username = ? AND user_id = ?
        """, (username, user_code)).fetchone()
        conn.close()

        if not user or not check_password_hash(user["hash"], password):
            flash("Invalid login.", "error")
            return render_template("login.html"), 403

        session["user_id"] = user["id"]
        return redirect(url_for("dashboard_bp.dashboard"))

    return render_template("login.html")

# Logout Route
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth_bp.login"))
