from functools import wraps

from flask import g, jsonify, redirect, session, url_for

from ..repositories import users


def get_current_user():
    if "current_user" not in g:
        user_id = session.get("user_id")
        g.current_user = users.get_by_id(user_id) if user_id else None
        if g.current_user and not g.current_user["is_active"]:
            session.clear()
            g.current_user = None
    return g.current_user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not get_current_user():
            return jsonify({"ok": False, "error": "登录已失效，请重新登录"}), 401
        return view(*args, **kwargs)

    return wrapped


def roles_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if not user:
                return redirect(url_for("auth.login"))
            if user["role"] not in allowed_roles:
                return redirect(url_for("auth.index"))
            return view(*args, **kwargs)

        return wrapped

    return decorator

