from flask import Blueprint, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from ..repositories import users
from ..utils.auth import get_current_user, login_required


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/")
@login_required
def index():
    return render_template("index.html")


@auth_bp.get("/login")
def login():
    if get_current_user():
        return redirect(url_for("auth.index"))
    return render_template("login.html", error=None)


@auth_bp.post("/login")
def login_submit():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = users.get_by_username(username)

    if user and user["is_active"] and check_password_hash(user["password_hash"], password):
        session.clear()
        session["user_id"] = user["id"]
        return redirect(url_for("auth.index"))

    return render_template("login.html", error="用户名或密码不正确"), 401


@auth_bp.post("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

