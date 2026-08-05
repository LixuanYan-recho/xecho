from flask import Flask

from . import config
from .database import initialize_database
from .routes.admin import admin_bp
from .routes.auth import auth_bp
from .routes.generate import generate_bp
from .routes.results import results_bp
from .utils.auth import get_current_user


def create_app():
    initialize_database()
    config.RESULT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    app = Flask(
        __name__,
        template_folder=str(config.PROJECT_DIR / "templates"),
        static_folder=str(config.PROJECT_DIR / "static"),
    )
    app.config.update(
        SECRET_KEY=config.SECRET_KEY,
        SESSION_COOKIE_HTTPONLY=config.SESSION_COOKIE_HTTPONLY,
        SESSION_COOKIE_SAMESITE=config.SESSION_COOKIE_SAMESITE,
    )
    app.register_blueprint(auth_bp)
    app.register_blueprint(generate_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(results_bp)

    @app.context_processor
    def inject_current_user():
        return {"current_user": get_current_user()}

    return app
