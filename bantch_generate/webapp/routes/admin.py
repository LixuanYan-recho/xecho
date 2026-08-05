import re

import mysql.connector
from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from ..config import CREATABLE_ROLES, ROLE_ADMIN, ROLE_SUPER_ADMIN
from ..repositories import results, users
from ..utils.auth import roles_required
from ..utils.environment import get_environment_value


admin_bp = Blueprint("admin", __name__)
ENV_VAR_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]{0,127}$")


@admin_bp.get("/usage")
@roles_required(ROLE_ADMIN, ROLE_SUPER_ADMIN)
def usage():
    should_query = request.args.get("query") == "1"
    return render_template(
        "usage.html",
        usage_rows=results.usage_summary() if should_query else None,
        model_rows=results.model_usage_summary() if should_query else None,
        queried=should_query,
    )


@admin_bp.get("/settings")
@roles_required(ROLE_SUPER_ADMIN)
def settings():
    return render_template("settings.html", users=users.list_all())


@admin_bp.post("/settings/users")
@roles_required(ROLE_SUPER_ADMIN)
def create_user():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    api_key_env_var = request.form.get("api_key_env_var", "").strip()
    role = request.form.get("role", "").strip()

    if not 1 <= len(username) <= 64:
        flash("账号名长度必须为 1-64 个字符。", "error")
    elif len(password) < 6:
        flash("密码至少需要 6 个字符。", "error")
    elif role not in CREATABLE_ROLES:
        flash("身份类型只能选择用户或管理员。", "error")
    elif not ENV_VAR_PATTERN.fullmatch(api_key_env_var):
        flash("密钥变量名格式不正确。", "error")
    elif not get_environment_value(api_key_env_var):
        flash(f"本机环境变量 {api_key_env_var} 未配置或为空。", "error")
    else:
        try:
            users.create(username, generate_password_hash(password), role, api_key_env_var)
        except mysql.connector.IntegrityError:
            flash("该账号名已存在。", "error")
        else:
            flash(f"账号 {username} 创建成功。", "success")

    return redirect(url_for("admin.settings"))


@admin_bp.post("/settings/users/<int:user_id>/password")
@roles_required(ROLE_SUPER_ADMIN)
def update_user_password(user_id):
    password = request.form.get("password", "")
    user = users.get_by_id(user_id)

    if not user:
        flash("账号不存在。", "error")
    elif len(password) < 6:
        flash("新密码至少需要 6 个字符。", "error")
    else:
        users.update_password(user_id, generate_password_hash(password))
        flash(f"账号 {user['username']} 的密码已修改。", "success")
    return redirect(url_for("admin.settings"))
