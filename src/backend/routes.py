from flask import Blueprint, abort, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from .db import get_db, record_auth
from .users import User

web = Blueprint("web", __name__)


@web.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789_"
    username_is_valid = True
    if len(username) < 1 or len(username) > 40:
        username_is_valid = False
    for character in username:
        if character not in allowed_characters:
            username_is_valid = False

    if not username_is_valid or len(password) < 1 or len(password) > 128:
        message = "Enter a valid username and password."
        return render_template("login.html", error=message), 400

    connection = get_db()
    result = connection.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_row = result.fetchone()

    user_id = None
    password_is_correct = False
    if user_row is not None:
        user_id = user_row["id"]
        password_is_correct = check_password_hash(user_row["password_hash"], password)

    if not password_is_correct:
        record_auth("LOGIN_FAILED", user_id)
        message = "Invalid username or password."
        return render_template("login.html", error=message), 401

    session.clear()
    user = User(user_row)
    login_user(user)
    session.permanent = True 
    record_auth("LOGIN_SUCCESS", user.id)
    return redirect(url_for("web.dashboard"))


@web.post("/logout")
@login_required
def logout():
    record_auth("LOGOUT", current_user.id)
    logout_user()
    session.clear()
    return redirect(url_for("web.login"))


@web.get("/dashboard")
@login_required
def dashboard():
    connection = get_db()
    result = connection.execute("SELECT * FROM rooms ORDER BY id")
    rooms = result.fetchall()
    return render_template("dashboard.html", rooms=rooms)


@web.get("/admin")
@login_required
def admin():
    if current_user.role != "admin":
        abort(403)
    return render_template("admin.html")
